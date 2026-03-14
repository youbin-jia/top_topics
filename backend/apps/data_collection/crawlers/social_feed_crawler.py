"""
多平台社媒/内容站 MVP 采集器（基于 RSS/Atom 聚合源）：
- 支持在一个 DataSource 内配置多个 feed_url
- 用 platform 字段标记来源平台（xiaohongshu/wechat/bilibili/douyin 等）
"""
import re
import hashlib
from datetime import datetime, timezone as dt_timezone
from time import mktime
from typing import Dict, List, Set
from urllib.parse import quote

import feedparser
from bs4 import BeautifulSoup

from .base import BaseCrawler

# 过滤 4 字节字符，避免非 utf8mb4 场景下写库失败
_RE_4_BYTE = re.compile(r"[\U00010000-\U0010FFFF]", flags=re.UNICODE)


def _strip_4byte_utf8(text: str) -> str:
    if not text:
        return text
    return _RE_4_BYTE.sub("", text).strip()


def _parse_date(entry) -> datetime:
    for attr in ("published_parsed", "updated_parsed", "created_parsed"):
        parsed = getattr(entry, attr, None)
        if parsed:
            try:
                return datetime.fromtimestamp(mktime(parsed))
            except Exception:
                pass
    return datetime.now()


def _now_utc() -> datetime:
    return datetime.now(dt_timezone.utc)


def _extract_text(html_or_text: str, max_len: int = 4000) -> str:
    if not html_or_text:
        return ""
    text = str(html_or_text).strip()
    if "<" in text and ">" in text:
        soup = BeautifulSoup(text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]


class SocialFeedCrawler(BaseCrawler):
    """
    config 示例：
    {
      "platform": "bilibili",
      "feed_urls": ["https://rsshub.app/bilibili/hot-search"],
      "feed_url": "https://rsshub.app/douyin/hot_search"
    }
    """

    def __init__(
        self,
        source_config: Dict,
        delay: float = 1.0,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        cfg = source_config or {}
        fast_timeout = int(cfg.get("timeout") or timeout or 8)
        fast_retries = int(cfg.get("max_retries") or max_retries or 1)
        fast_delay = float(cfg.get("delay") or delay or 0.2)
        super().__init__(
            source_config=cfg,
            delay=fast_delay,
            timeout=fast_timeout,
            max_retries=fast_retries,
        )

    def _normalize_urls(self, value) -> List[str]:
        urls = []
        if isinstance(value, str):
            value = [value]
        for item in value or []:
            text = str(item or "").strip()
            if text:
                urls.append(text)
        return urls

    def _append_item(
        self,
        items: List[Dict],
        seen_urls: Set[str],
        link: str,
        title: str,
        summary: str,
        body: str,
        author: str,
        published_at: datetime,
        platform: str,
        source_name: str,
    ) -> None:
        if not link or link in seen_urls:
            return
        text = _extract_text(f"{title}\n{body}", max_len=9000)
        if len(text) < 30:
            return
        seen_urls.add(link)
        items.append(
            {
                "url": link,
                "title": _strip_4byte_utf8(_extract_text(title, max_len=300)),
                "content": _strip_4byte_utf8(text),
                "author": _strip_4byte_utf8(author or ""),
                "published_at": published_at,
                "view_count": 0,
                "like_count": 0,
                "share_count": 0,
                "comment_count": 0,
                "keywords": [],
                "summary": _strip_4byte_utf8(_extract_text(summary, max_len=320)),
                "metadata": {
                    "source": "social_feed",
                    "platform": platform,
                    "source_name": source_name,
                },
            }
        )

    def _crawl_feed_urls(self, feed_urls: List[str], platform: str, items: List[Dict], seen_urls: Set[str]) -> None:
        for feed_url in feed_urls:
            try:
                resp = self.session.get(feed_url, timeout=self.timeout)
                resp.raise_for_status()
                feed = feedparser.parse(resp.content)
            except Exception as exc:
                self.logger.warning("拉取平台 feed 失败: %s, err=%s", feed_url, exc)
                continue

            added = 0
            for entry in getattr(feed, "entries", [])[:30]:
                link = getattr(entry, "link", "") or ""
                title = getattr(entry, "title", "") or ""
                summary = getattr(entry, "summary", None) or getattr(entry, "description", None) or ""
                content = getattr(entry, "content", None)
                if content and isinstance(content, list) and content:
                    body = content[0].get("value", "") if isinstance(content[0], dict) else str(content[0])
                else:
                    body = summary
                before = len(items)
                self._append_item(
                    items=items,
                    seen_urls=seen_urls,
                    link=link,
                    title=title,
                    summary=summary,
                    body=body,
                    author=getattr(entry, "author", "") or "",
                    published_at=_parse_date(entry),
                    platform=platform,
                    source_name=feed_url,
                )
                if len(items) > before:
                    added += 1
            self.logger.info("平台 feed 拉取完成: platform=%s url=%s added=%s", platform, feed_url, added)

    def _crawl_bilibili_popular_api(self, api_url: str, platform: str, items: List[Dict], seen_urls: Set[str]) -> int:
        resp = self.session.get(
            api_url,
            timeout=self.timeout,
            headers={"User-Agent": "Mozilla/5.0 (compatible; TopTopicsBot/1.0)"},
        )
        resp.raise_for_status()
        data = resp.json()
        entries = ((data or {}).get("data") or {}).get("list") or []
        added = 0
        for row in entries[:30]:
            title = str(row.get("title") or "").strip()
            if not title:
                continue
            link = str(row.get("short_link_v2") or row.get("short_link") or row.get("url") or "").strip()
            if not link:
                aid = row.get("aid")
                if aid:
                    link = f"https://www.bilibili.com/video/av{aid}"
            summary = str(row.get("desc") or row.get("rcmd_reason") or "").strip()
            body = f"{title}\n{summary}"
            before = len(items)
            self._append_item(
                items=items,
                seen_urls=seen_urls,
                link=link,
                title=title,
                summary=summary,
                body=body,
                author=str(row.get("owner", {}).get("name") or ""),
                published_at=_now_utc(),
                platform=platform,
                source_name=api_url,
            )
            if len(items) > before:
                added += 1
        return added

    def _crawl_douyin_hot_api(self, api_url: str, platform: str, items: List[Dict], seen_urls: Set[str]) -> int:
        resp = self.session.get(
            api_url,
            timeout=self.timeout,
            headers={"User-Agent": "Mozilla/5.0 (compatible; TopTopicsBot/1.0)"},
        )
        resp.raise_for_status()
        data = resp.json()
        entries = (data or {}).get("word_list") or []
        added = 0
        for row in entries[:30]:
            word = str(row.get("word") or "").strip()
            if not word:
                continue
            link = f"https://www.douyin.com/search/{quote(word)}"
            hot_value = row.get("hot_value")
            label = row.get("label")
            summary = f"热度值: {hot_value or 0}; 标签: {label or 0}"
            body = (
                f"抖音热搜词: {word}。"
                f"当前热度值为 {hot_value or 0}，标签为 {label or 0}。"
                "该条目由抖音热榜接口抓取，可用于后续热点聚类与趋势判断。"
            )
            before = len(items)
            self._append_item(
                items=items,
                seen_urls=seen_urls,
                link=link,
                title=word,
                summary=summary,
                body=body,
                author="douyin_hot",
                published_at=_now_utc(),
                platform=platform,
                source_name=api_url,
            )
            if len(items) > before:
                added += 1
        return added

    def _crawl_wechat_sogou_api(self, api_url: str, platform: str, endpoint: Dict, items: List[Dict], seen_urls: Set[str]) -> int:
        keywords = endpoint.get("keywords") or ["科技", "AI", "互联网", "创业", "数码"]
        max_per_keyword = int(endpoint.get("max_per_keyword") or 6)
        headers = {"User-Agent": "Mozilla/5.0 (compatible; TopTopicsBot/1.0)"}
        added = 0

        for kw in keywords:
            query_url = f"{api_url}?type=2&query={quote(str(kw))}"
            resp = self.session.get(query_url, timeout=self.timeout, headers=headers)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            rows = soup.select("ul.news-list li")
            for row in rows[:max_per_keyword]:
                title_el = row.select_one("h3 a")
                if not title_el:
                    continue
                title = _extract_text(title_el.get_text(" ", strip=True), max_len=120)
                rel = str(title_el.get("href") or "").strip()
                if not rel:
                    continue
                original_url = rel if rel.startswith("http") else f"https://weixin.sogou.com{rel}"
                # 搜狗跳转链接通常很长（超出 URLField 200），落库使用短链接，原始链接放入摘要/正文。
                digest = hashlib.md5(original_url.encode("utf-8")).hexdigest()[:12]
                link = (
                    "https://weixin.sogou.com/weixin"
                    f"?type=2&query={quote(str(kw))}&_rid={digest}"
                )
                summary_el = row.select_one("p.txt-info")
                summary = _extract_text(summary_el.get_text(" ", strip=True) if summary_el else "", max_len=280)
                account_el = row.select_one(".s-p .all-time-y2")
                author = _extract_text(account_el.get_text(" ", strip=True) if account_el else "", max_len=60)
                ts_match = re.search(r"timeConvert\('(\d+)'\)", str(row))
                if ts_match:
                    published_at = datetime.fromtimestamp(int(ts_match.group(1)), tz=dt_timezone.utc)
                else:
                    published_at = _now_utc()
                long_summary = summary or "该文章来自公众号搜索结果页，反映当前关键词下的内容热度与讨论方向。"
                body = (
                    f"公众号检索词: {kw}。"
                    f"文章标题: {title}。"
                    f"来源账号: {author or '未知'}。"
                    f"摘要: {long_summary}。"
                    f"原始跳转: {original_url[:180]}。"
                    "该条目由微信搜狗检索接口抓取，可用于后续热点聚类与趋势判断。"
                )
                before = len(items)
                self._append_item(
                    items=items,
                    seen_urls=seen_urls,
                    link=link,
                    title=title,
                    summary=summary or f"公众号: {author or '未知'}",
                    body=body,
                    author=author or "wechat_sogou",
                    published_at=published_at,
                    platform=platform,
                    source_name=query_url,
                )
                if len(items) > before:
                    added += 1
        return added

    def _crawl_xiaohongshu_explore_api(self, api_url: str, platform: str, items: List[Dict], seen_urls: Set[str]) -> int:
        resp = self.session.get(
            api_url,
            timeout=self.timeout,
            headers={"User-Agent": "Mozilla/5.0 (compatible; TopTopicsBot/1.0)"},
        )
        resp.raise_for_status()
        html = resp.text
        m = re.search(r"window\.__INITIAL_STATE__=(\{.*?\})</script>", html, flags=re.S)
        if not m:
            return 0
        state_text = (
            m.group(1)
            .replace(":undefined", ":null")
            .replace("undefined,", "null,")
            .replace("undefined}", "null}")
        )
        try:
            import json
            state = json.loads(state_text)
        except Exception:
            return 0
        feeds = ((state.get("feed") or {}).get("feeds")) or []
        added = 0
        for row in feeds[:30]:
            card = row.get("noteCard") or {}
            note_id = str(row.get("id") or "").strip()
            xsec_token = str(row.get("xsecToken") or "").strip()
            if not note_id:
                continue
            title = _extract_text(card.get("displayTitle") or card.get("title") or "", max_len=120)
            if not title:
                continue
            link = f"https://www.xiaohongshu.com/explore/{note_id}"
            if xsec_token:
                link += f"?xsec_token={quote(xsec_token)}"
            user = card.get("user") or {}
            author = _extract_text(user.get("nickName") or user.get("nickname") or "", max_len=60)
            interact = card.get("interactInfo") or {}
            liked = _extract_text(str(interact.get("likedCount") or "0"), max_len=20)
            summary = f"点赞: {liked}"
            body = (
                f"小红书热门内容: {title}。"
                f"作者: {author or '未知'}。"
                f"点赞数据: {liked}。"
                "该条目来自小红书 explore 首屏数据。"
            )
            before = len(items)
            self._append_item(
                items=items,
                seen_urls=seen_urls,
                link=link,
                title=title,
                summary=summary,
                body=body,
                author=author or "xiaohongshu_explore",
                published_at=_now_utc(),
                platform=platform,
                source_name=api_url,
            )
            if len(items) > before:
                added += 1
        return added

    def _crawl_api_endpoints(self, api_endpoints: List[Dict], platform: str, items: List[Dict], seen_urls: Set[str]) -> None:
        for endpoint in api_endpoints:
            if isinstance(endpoint, str):
                endpoint = {"url": endpoint, "format": "auto"}
            api_url = str((endpoint or {}).get("url") or "").strip()
            data_format = str((endpoint or {}).get("format") or "auto").strip().lower()
            if not api_url:
                continue
            try:
                added = 0
                if data_format in ("bilibili_popular", "auto") and platform == "bilibili":
                    added = self._crawl_bilibili_popular_api(api_url, platform, items, seen_urls)
                elif data_format in ("douyin_hot", "auto") and platform == "douyin":
                    added = self._crawl_douyin_hot_api(api_url, platform, items, seen_urls)
                elif data_format in ("wechat_sogou", "auto") and platform == "wechat":
                    added = self._crawl_wechat_sogou_api(api_url, platform, endpoint, items, seen_urls)
                elif data_format in ("xiaohongshu_explore", "auto") and platform == "xiaohongshu":
                    added = self._crawl_xiaohongshu_explore_api(api_url, platform, items, seen_urls)
                self.logger.info(
                    "平台 API 拉取完成: platform=%s url=%s format=%s added=%s",
                    platform,
                    api_url,
                    data_format,
                    added,
                )
            except Exception as exc:
                self.logger.warning("拉取平台 API 失败: %s, err=%s", api_url, exc)

    def crawl(self, pages: int = 1) -> List[Dict]:
        feed_urls = self.config.get("feed_urls") or []
        single = self.config.get("feed_url") or self.config.get("base_url")
        if single and single not in feed_urls:
            feed_urls.append(single)
        feed_urls = self._normalize_urls(feed_urls)

        platform = (self.config.get("platform") or "social").strip().lower()
        items: List[Dict] = []
        seen_urls: Set[str] = set()

        if feed_urls:
            self._crawl_feed_urls(feed_urls, platform, items, seen_urls)

        # 无法通过 RSS/Atom 获取时，支持配置 API 兜底
        if not items:
            api_endpoints = self.config.get("api_endpoints") or []
            self._crawl_api_endpoints(api_endpoints, platform, items, seen_urls)

        self.logger.info("社媒聚合拉取完成: platform=%s items=%d", platform, len(items))
        return items

    def parse(self, html: str, **kwargs) -> Dict:
        return {}
