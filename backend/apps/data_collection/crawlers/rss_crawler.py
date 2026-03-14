"""
RSS/Atom 订阅源爬虫：从 RSS 地址拉取实时文章，无需站点专属选择器。
"""
import re
from typing import List, Dict
from datetime import datetime
import logging

import feedparser
from bs4 import BeautifulSoup

from .base import BaseCrawler

logger = logging.getLogger(__name__)

# 匹配 4 字节 UTF-8（如 emoji），MySQL utf8 仅支持 3 字节，保存前过滤避免 Incorrect string value
_RE_4_BYTE = re.compile(r"[\U00010000-\U0010FFFF]", flags=re.UNICODE)


def _strip_4byte_utf8(text: str) -> str:
    """去掉 emoji 等 4 字节字符，避免 MySQL utf8 列保存报错；若库表已是 utf8mb4 可去掉此步"""
    if not text:
        return text
    return _RE_4_BYTE.sub("", text).strip()


def _parse_date(entry) -> datetime:
    """解析 RSS 条目的发布时间"""
    for attr in ('published_parsed', 'updated_parsed', 'created_parsed'):
        parsed = getattr(entry, attr, None)
        if parsed:
            try:
                from time import mktime
                return datetime.fromtimestamp(mktime(parsed))
            except Exception:
                pass
    return datetime.now()


def _extract_text(html_or_text: str, max_len: int = 5000) -> str:
    """从 HTML 或纯文本中提取纯文本"""
    if not html_or_text:
        return ""
    text = html_or_text.strip()
    if len(text) < 20:
        return text
    if "<" in text and ">" in text:
        soup = BeautifulSoup(text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)
    return text[:max_len].strip()


class RSSCrawler(BaseCrawler):
    """RSS/Atom 订阅爬虫：config 需包含 feed_url"""

    def crawl(self, pages: int = 1) -> List[Dict]:
        """
        拉取 RSS 源中的条目（pages 对 RSS 无效，保留接口兼容）。
        config 示例: {"feed_url": "https://example.com/feed.xml"}
        """
        feed_url = self.config.get("feed_url") or self.config.get("base_url")
        if not feed_url:
            self.logger.error("RSS 配置缺少 feed_url 或 base_url")
            return []

        self.logger.info("正在拉取 RSS: %s", feed_url)
        try:
            resp = self.session.get(feed_url, timeout=self.timeout)
            resp.raise_for_status()
            feed = feedparser.parse(resp.content)
        except Exception as e:
            self.logger.exception("RSS 请求失败: %s", feed_url)
            raise

        if getattr(feed, "bozo", False) and not feed.entries:
            self.logger.warning("RSS 解析可能有问题: %s", feed_url)
        if not feed.entries:
            self.logger.info("RSS 无条目: %s", feed_url)
            return []

        items = []
        for entry in feed.entries[:50]:  # 单次最多 50 条
            link = getattr(entry, "link", None)
            if not link:
                continue
            title = getattr(entry, "title", "") or ""
            summary = getattr(entry, "summary", None) or getattr(entry, "description", None) or ""
            content = getattr(entry, "content", None)
            if content and isinstance(content, list) and len(content) > 0:
                body = content[0].get("value", "") if isinstance(content[0], dict) else str(content[0])
            else:
                body = summary
            text = _extract_text(title + "\n" + body, max_len=10000)
            if len(text) < 30:
                continue
            published_at = _parse_date(entry)
            title_clean = _strip_4byte_utf8(_extract_text(title, max_len=500))
            summary_clean = _strip_4byte_utf8(_extract_text(summary, max_len=300))
            text_clean = _strip_4byte_utf8(text)
            items.append({
                "url": link,
                "title": title_clean,
                "content": text_clean,
                "author": _strip_4byte_utf8(getattr(entry, "author", "") or ""),
                "published_at": published_at,
                "view_count": 0,
                "like_count": 0,
                "share_count": 0,
                "comment_count": 0,
                "keywords": [],
                "summary": summary_clean,
                "metadata": {"source": "rss"},
            })
        self.logger.info("RSS 拉取到 %d 条", len(items))
        return items

    def parse(self, html: str, **kwargs) -> Dict:
        """RSS 不需要解析 HTML 页面，由 crawl 直接产出条目"""
        return {}
