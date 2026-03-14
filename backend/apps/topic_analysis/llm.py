"""
Kimi(OpenAI兼容)话题总结客户端：
- 输入若干原文标题/摘要
- 输出适合短视频的标题与概要
"""
import json
import logging
import re
import time
from typing import Dict, List
from urllib.parse import urlparse
from urllib import request as urlrequest
from urllib.error import URLError, HTTPError

from django.conf import settings

logger = logging.getLogger(__name__)

_JSON_OBJECT_RE = re.compile(r"\{[\s\S]*\}")


def _clean_text(text: str, max_len: int = 500) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", str(text)).strip()
    return text[:max_len]


def _fallback_title_summary(keyword: str, source_items: List[Dict]) -> Dict[str, str]:
    """
    规则兜底：当 LLM 不可用/调用失败时，仍生成可读标题与概要。
    """
    raw_keyword = _clean_text(keyword, 40)
    if not raw_keyword:
        raw_keyword = "热门话题"
    lower_kw = raw_keyword.lower().replace(" ", "")
    if lower_kw in {"http", "https"} or lower_kw.startswith("http"):
        raw_keyword = ""

    if not raw_keyword:
        for item in source_items[:5]:
            candidate = _clean_text(item.get("title") or item.get("summary") or "", 80)
            if not candidate:
                continue
            m = re.search(r"[\u4e00-\u9fff]{2,12}", candidate)
            if m:
                raw_keyword = m.group(0)
                break
    keyword = raw_keyword or "热门话题"
    parts = []
    for item in source_items[:3]:
        snippet = _clean_text(item.get("summary") or item.get("title") or "", 120)
        if snippet:
            parts.append(snippet)
    summary = "；".join(parts)[:500] if parts else f"{keyword}相关动态持续发酵，建议从背景、影响和趋势三个角度制作短视频。"

    # 标题采用稳定模板，避免“单词/截断句”这种不可用标题
    if len(keyword) > 20:
        keyword = keyword[:20]
    title = f"{keyword}持续发酵：你需要知道的最新进展与关键影响"
    title = _clean_text(title, 60)
    if len(title) < 12:
        title = "今日热点追踪：事件最新进展与关键影响"

    return {
        "title": title,
        "summary": summary,
    }


def _extract_json_text(content: str) -> Dict:
    if not content:
        return {}
    text = content.strip()
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    match = _JSON_OBJECT_RE.search(text)
    if not match:
        return {}
    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _short_url(url: str) -> str:
    text = _clean_text(url or "", 300)
    if not text:
        return ""
    try:
        parsed = urlparse(text)
        if parsed.netloc:
            return parsed.netloc[:80]
    except Exception:
        pass
    return text[:80]


def _estimate_chars_tokens(messages: List[Dict]) -> Dict[str, int]:
    # 粗略估算：中文场景下约 1 token ≈ 1.8 字符
    chars = len(json.dumps(messages, ensure_ascii=False))
    return {"chars": chars, "tokens": max(1, int(chars / 1.8))}


class KimiTopicSummarizer:
    """Kimi（OpenAI兼容）话题标题/概要生成器"""
    _circuit_open_until_ts = 0.0
    _circuit_reason = ""

    def __init__(self):
        self.base_url = getattr(settings, "KIMI_BASE_URL", "").rstrip("/")
        self.api_key = getattr(settings, "KIMI_API_KEY", "")
        self.model = getattr(settings, "KIMI_MODEL", "kimi-k2.5")
        self.force_enabled = bool(getattr(settings, "KIMI_ENABLED", True))
        self.timeout = int(getattr(settings, "KIMI_TIMEOUT", 20))
        self.max_retries = int(getattr(settings, "KIMI_MAX_RETRIES", 2))
        self.fail_fast_on_timeout = bool(getattr(settings, "KIMI_FAIL_FAST_ON_TIMEOUT", True))
        self.circuit_cooldown_sec = int(getattr(settings, "KIMI_CIRCUIT_COOLDOWN_SEC", 600))

    @property
    def enabled(self) -> bool:
        return bool(self.force_enabled and self.base_url and self.api_key and self.model)

    @classmethod
    def _is_circuit_open(cls) -> bool:
        return time.time() < cls._circuit_open_until_ts

    @classmethod
    def _open_circuit(cls, cooldown_sec: int, reason: str) -> None:
        cls._circuit_open_until_ts = time.time() + max(30, cooldown_sec)
        cls._circuit_reason = reason
        logger.warning("Kimi 熔断开启: cooldown=%ss reason=%s", max(30, cooldown_sec), reason)

    @classmethod
    def _close_circuit(cls) -> None:
        cls._circuit_open_until_ts = 0.0
        cls._circuit_reason = ""

    @staticmethod
    def _is_timeout_like_error(exc: Exception) -> bool:
        text = str(exc).lower()
        return (
            "timed out" in text
            or "timeout" in text
            or "time out" in text
            or "read operation timed out" in text
        )

    def _chat_endpoint(self) -> str:
        """
        兼容两种配置：
        - KIMI_BASE_URL=https://api.moonshot.cn
        - KIMI_BASE_URL=https://api.moonshot.cn/v1
        """
        if self.base_url.endswith("/v1"):
            return f"{self.base_url}/chat/completions"
        return f"{self.base_url}/v1/chat/completions"

    def _chat(self, messages: List[Dict]) -> str:
        url = self._chat_endpoint()
        payload = {
            "model": self.model,
            "messages": messages,
            # Moonshot 的 kimi-k2.5 当前要求 temperature 必须为 1
            "temperature": 1,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urlrequest.Request(
            url=url,
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlrequest.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8", errors="ignore")
        except HTTPError as exc:
            # 保留服务端错误正文，便于定位 400 的具体字段问题
            err_body = ""
            try:
                err_body = exc.read().decode("utf-8", errors="ignore")
            except Exception:
                err_body = ""
            detail = f"{exc}"
            if err_body:
                detail = f"{exc}; body={err_body[:500]}"
            raise HTTPError(exc.url, exc.code, detail, exc.hdrs, exc.fp)
        parsed = json.loads(body)
        return (
            parsed.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )

    def generate(self, keyword: str, source_items: List[Dict]) -> Dict[str, str]:
        fallback = _fallback_title_summary(keyword, source_items)
        if not self.enabled:
            return fallback
        if self._is_circuit_open():
            logger.info("Kimi 熔断中，跳过调用并使用规则兜底: %s", self._circuit_reason or "unknown")
            return fallback

        compact_items = []
        for item in source_items[:3]:
            compact_items.append(
                {
                    "title": _clean_text(item.get("title", ""), 80),
                    "summary": _clean_text(item.get("summary", ""), 140),
                    "url": _short_url(item.get("url", "")),
                }
            )

        system_prompt = (
            "你是中文短视频选题编辑。请根据输入的新闻摘要，输出JSON对象，字段如下："
            "title(可直接作为短视频标题，16-34字，信息明确，不夸张，不使用营销党标题)、"
            "summary(2-3句，说明事件背景、核心变化和看点，120-260字)、"
            "tags(3-6个短标签)。"
            "只输出JSON，不要输出其他文本。"
        )
        user_prompt = json.dumps(
            {
                "keyword": keyword,
                "sources": compact_items,
            },
            ensure_ascii=False,
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        estimate = _estimate_chars_tokens(messages)
        logger.info(
            "Kimi 请求准备: model=%s sources=%s chars=%s est_tokens=%s",
            self.model,
            len(compact_items),
            estimate["chars"],
            estimate["tokens"],
        )

        circuit_opened = False
        for idx in range(self.max_retries + 1):
            try:
                content = self._chat(messages)
                parsed = _extract_json_text(content)
                title = _clean_text(parsed.get("title", ""), 80)
                summary = _clean_text(parsed.get("summary", ""), 600)
                if not title or len(title) < 8:
                    title = fallback["title"]
                if not summary or len(summary) < 20:
                    summary = fallback["summary"]
                self._close_circuit()
                return {"title": title, "summary": summary}
            except (HTTPError, URLError, TimeoutError, ValueError, KeyError) as exc:
                logger.warning("Kimi 生成失败（重试 %s/%s）: %s", idx + 1, self.max_retries + 1, exc)
                if self.fail_fast_on_timeout and self._is_timeout_like_error(exc):
                    self._open_circuit(self.circuit_cooldown_sec, "timeout")
                    circuit_opened = True
                    break
                time.sleep(0.8 * (idx + 1))
            except Exception as exc:
                logger.exception("Kimi 调用异常: %s", exc)
                self._open_circuit(self.circuit_cooldown_sec, "unexpected_error")
                circuit_opened = True
                break
        if not circuit_opened:
            self._open_circuit(self.circuit_cooldown_sec, "retry_exhausted")
        return fallback


def generate_topic_title_summary(keyword: str, source_items: List[Dict]) -> Dict[str, str]:
    """
    对外统一入口：返回 {"title": "...", "summary": "..."}。
    """
    summarizer = KimiTopicSummarizer()
    return summarizer.generate(keyword, source_items)


def rule_based_title_summary(keyword: str, source_items: List[Dict]) -> Dict[str, str]:
    """供其它流程直接复用规则兜底逻辑。"""
    return _fallback_title_summary(keyword, source_items)
