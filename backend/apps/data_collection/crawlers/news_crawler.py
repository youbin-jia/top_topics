"""
新闻爬虫示例
"""
from typing import List, Dict
from datetime import datetime
from bs4 import BeautifulSoup
from .base import BaseCrawler


class NewsCrawler(BaseCrawler):
    """新闻网站爬虫"""

    def crawl(self, pages: int = 1) -> List[Dict]:
        """
        爬取新闻列表

        Args:
            pages: 爬取页数

        Returns:
            新闻列表
        """
        all_news = []

        for page in range(1, pages + 1):
            self.logger.info(f"正在爬取第 {page} 页")

            # 构建列表页URL
            list_url = self._build_list_url(page)

            # 请求列表页
            response = self.request(list_url)
            if not response:
                continue

            # 解析列表页获取文章链接
            article_urls = self._parse_list_page(response.text)

            # 爬取每篇文章
            for article_url in article_urls:
                try:
                    article_data = self._crawl_article(article_url)
                    if article_data:
                        all_news.append(article_data)
                except Exception as e:
                    self.logger.error(f"爬取文章失败 {article_url}: {e}")
                    continue

        return all_news

    def parse(self, html: str, **kwargs) -> Dict:
        """解析文章页面"""
        soup = BeautifulSoup(html, 'html.parser')

        # 提取标题
        title = self._extract_title(soup)

        # 提取内容
        content = self._extract_content(soup)

        # 提取作者
        author = self._extract_author(soup)

        # 提取发布时间
        published_at = self._extract_publish_time(soup)

        # 提取关键词
        keywords = self._extract_keywords(soup)

        return {
            'title': title,
            'content': content,
            'author': author,
            'published_at': published_at,
            'keywords': keywords,
        }

    def _build_list_url(self, page: int) -> str:
        """构建列表页URL"""
        base_url = self.config.get('base_url')
        list_pattern = self.config.get('list_pattern', '/page/{}')

        return f"{base_url}{list_pattern.format(page)}"

    def _parse_list_page(self, html: str) -> List[str]:
        """解析列表页，提取文章链接"""
        soup = BeautifulSoup(html, 'html.parser')
        article_urls = []

        # 根据配置的选择器提取链接
        article_selector = self.config.get('article_selector', 'a.article-link')

        for link in soup.select(article_selector):
            href = link.get('href')
            if href:
                # 处理相对路径
                if not href.startswith('http'):
                    href = self.config['base_url'] + href
                article_urls.append(href)

        return article_urls

    def _crawl_article(self, url: str) -> Dict:
        """爬取单篇文章"""
        response = self.request(url)
        if not response:
            return None

        # 解析文章
        article_data = self.parse(response.text)

        # 添加URL和爬取时间
        article_data['url'] = url
        article_data['crawled_at'] = datetime.now()

        # 提取统计数据
        article_data.update(self._extract_stats(response.text))

        return article_data

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """提取标题"""
        title_selector = self.config.get('title_selector', 'h1.title')
        title_elem = soup.select_one(title_selector)
        return self.clean_text(title_elem.get_text()) if title_elem else ""

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """提取内容"""
        content_selector = self.config.get('content_selector', 'div.content')
        content_elem = soup.select_one(content_selector)

        if content_elem:
            # 移除不需要的标签
            for tag in content_elem.find_all(['script', 'style', 'iframe']):
                tag.decompose()
            return self.clean_text(content_elem.get_text())

        return ""

    def _extract_author(self, soup: BeautifulSoup) -> str:
        """提取作者"""
        author_selector = self.config.get('author_selector', 'span.author')
        author_elem = soup.select_one(author_selector)
        return self.clean_text(author_elem.get_text()) if author_elem else ""

    def _extract_publish_time(self, soup: BeautifulSoup) -> datetime:
        """提取发布时间"""
        time_selector = self.config.get('time_selector', 'time.published')
        time_elem = soup.select_one(time_selector)

        if time_elem:
            # 尝试解析datetime属性
            datetime_str = time_elem.get('datetime')
            if datetime_str:
                try:
                    return datetime.fromisoformat(datetime_str)
                except ValueError:
                    pass

            # 尝试解析文本内容
            time_text = self.clean_text(time_elem.get_text())
            # 这里可以添加更多的时间解析逻辑
            try:
                return datetime.strptime(time_text, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                pass

        return datetime.now()

    def _extract_keywords(self, soup: BeautifulSoup) -> List[str]:
        """提取关键词"""
        keywords = []

        # 从meta标签提取
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords:
            keywords_str = meta_keywords.get('content', '')
            keywords.extend([k.strip() for k in keywords_str.split(',')])

        # 从标签提取
        tag_selector = self.config.get('tag_selector', 'a.tag')
        for tag in soup.select(tag_selector):
            keywords.append(self.clean_text(tag.get_text()))

        return list(set(keywords))  # 去重

    def _extract_stats(self, html: str) -> Dict:
        """提取统计数据（浏览、点赞等）"""
        # 这里需要根据具体网站实现
        # 返回示例数据
        return {
            'view_count': 0,
            'like_count': 0,
            'share_count': 0,
            'comment_count': 0,
        }
