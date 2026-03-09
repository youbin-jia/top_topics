"""
基础爬虫类
"""
import time
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    """基础爬虫抽象类"""

    def __init__(
        self,
        source_config: Dict,
        delay: float = 1.0,
        timeout: int = 30,
        max_retries: int = 3
    ):
        """
        初始化爬虫

        Args:
            source_config: 数据源配置
            delay: 请求延迟（秒）
            timeout: 请求超时（秒）
            max_retries: 最大重试次数
        """
        self.config = source_config
        self.delay = delay
        self.timeout = timeout

        # 创建会话
        self.session = self._create_session(max_retries)

        # 设置请求头
        self.session.headers.update({
            'User-Agent': source_config.get(
                'user_agent',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            ),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

        # 添加自定义请求头
        if 'headers' in source_config:
            self.session.headers.update(source_config['headers'])

        # Cookie处理
        if 'cookies' in source_config:
            self.session.cookies.update(source_config['cookies'])

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def _create_session(self, max_retries: int) -> requests.Session:
        """创建带有重试机制的会话"""
        session = requests.Session()

        # 重试策略
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def request(
        self,
        url: str,
        method: str = 'GET',
        **kwargs
    ) -> Optional[requests.Response]:
        """
        发送HTTP请求

        Args:
            url: 请求URL
            method: 请求方法
            **kwargs: requests库其他参数

        Returns:
            Response对象或None
        """
        try:
            # 设置默认超时
            if 'timeout' not in kwargs:
                kwargs['timeout'] = self.timeout

            # 请求延迟
            time.sleep(self.delay)

            # 发送请求
            if method.upper() == 'GET':
                response = self.session.get(url, **kwargs)
            elif method.upper() == 'POST':
                response = self.session.post(url, **kwargs)
            else:
                raise ValueError(f"不支持的请求方法: {method}")

            response.raise_for_status()
            response.encoding = response.apparent_encoding

            self.logger.info(f"成功请求: {url}")
            return response

        except requests.RequestException as e:
            self.logger.error(f"请求失败: {url}, 错误: {e}")
            return None

    def parse_html(self, html: str, parser: str = 'html.parser') -> BeautifulSoup:
        """解析HTML"""
        return BeautifulSoup(html, parser)

    @abstractmethod
    def crawl(self, *args, **kwargs) -> List[Dict]:
        """
        执行爬取（子类必须实现）

        Returns:
            爬取到的数据列表
        """
        pass

    @abstractmethod
    def parse(self, html: str, **kwargs) -> Dict:
        """
        解析页面内容（子类必须实现）

        Args:
            html: HTML内容

        Returns:
            解析后的数据字典
        """
        pass

    def clean_text(self, text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        # 去除多余空白
        text = ' '.join(text.split())
        # 去除特殊字符
        text = text.strip()
        return text

    def extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """提取图片URL"""
        images = []
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                # 处理相对路径
                if not src.startswith('http'):
                    from urllib.parse import urljoin
                    src = urljoin(base_url, src)
                images.append(src)
        return images

    def close(self):
        """关闭会话"""
        self.session.close()
        self.logger.info("爬虫会话已关闭")

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()
