"""
数据收集Celery任务
"""
from celery import shared_task
from django.utils import timezone
from datetime import datetime
import logging

from .models import DataSource, RawContent, CrawlLog
from .crawlers.news_crawler import NewsCrawler
from .crawlers.rss_crawler import RSSCrawler
from .crawlers.social_feed_crawler import SocialFeedCrawler

logger = logging.getLogger(__name__)


@shared_task
def crawl_source_task(source_id: int):
    """
    爬取指定数据源任务

    Args:
        source_id: 数据源ID
    """
    try:
        source = DataSource.objects.get(id=source_id)

        # 创建爬取日志
        crawl_log = CrawlLog.objects.create(
            source=source,
            status='success',
            started_at=timezone.now()
        )

        logger.info(f"开始爬取数据源: {source.name}")

        # 根据数据源类型选择爬虫
        crawler_class = get_crawler_class(source.source_type)
        crawler = crawler_class(
            source.config,
            delay=source.config.get('delay', 1.0)
        )

        # 执行爬取
        items = []
        with crawler:
            items = crawler.crawl(pages=source.config.get('pages', 1))

        # 保存数据
        saved_count = 0
        duplicate_count = 0
        invalid_count = 0

        for item in items:
            try:
                # 检查URL是否已存在
                if RawContent.objects.filter(url=item['url']).exists():
                    duplicate_count += 1
                    continue

                # 验证数据有效性
                if not is_valid_content(item):
                    invalid_count += 1
                    continue

                # 创建原始内容记录
                RawContent.objects.create(
                    title=item.get('title', ''),
                    content=item.get('content', ''),
                    url=item['url'],
                    source=source,
                    author=item.get('author', ''),
                    published_at=item.get('published_at'),
                    view_count=item.get('view_count', 0),
                    like_count=item.get('like_count', 0),
                    share_count=item.get('share_count', 0),
                    comment_count=item.get('comment_count', 0),
                    keywords=item.get('keywords', []),
                    summary=item.get('summary', ''),
                    metadata=item.get('metadata', {}),
                )
                saved_count += 1

            except Exception as e:
                logger.error(f"保存内容失败 {item.get('url')}: {e}")
                invalid_count += 1

        # 更新爬取日志
        crawl_log.status = 'success'
        crawl_log.items_crawled = len(items)
        crawl_log.items_saved = saved_count
        crawl_log.items_duplicate = duplicate_count
        crawl_log.items_invalid = invalid_count
        crawl_log.finished_at = timezone.now()
        crawl_log.duration = (crawl_log.finished_at - crawl_log.started_at).total_seconds()
        crawl_log.save()

        # 更新数据源统计
        source.total_crawled += len(items)
        source.success_count += saved_count
        source.last_crawled_at = timezone.now()
        source.save()

        logger.info(
            f"爬取完成: {source.name}, "
            f"总数={len(items)}, 保存={saved_count}, "
            f"重复={duplicate_count}, 无效={invalid_count}"
        )

        return {
            'source_id': source_id,
            'total': len(items),
            'saved': saved_count,
            'duplicate': duplicate_count,
            'invalid': invalid_count,
        }

    except DataSource.DoesNotExist:
        logger.error(f"数据源不存在: {source_id}")
        return None
    except Exception as e:
        logger.error(f"爬取任务失败: {e}")
        # 更新日志为失败状态
        crawl_log.status = 'failed'
        crawl_log.error_message = str(e)
        crawl_log.finished_at = timezone.now()
        crawl_log.save()
        raise


@shared_task
def process_raw_content_task(content_id: int):
    """
    处理原始内容任务

    Args:
        content_id: 原始内容ID
    """
    try:
        content = RawContent.objects.get(id=content_id)

        logger.info(f"开始处理内容: {content.id}")

        # 数据清洗
        content.content = clean_content(content.content)
        content.title = clean_content(content.title)

        # 提取关键词（如果还没提取）
        if not content.keywords:
            from apps.topic_analysis.utils import extract_keywords
            content.keywords = extract_keywords(content.content)

        # 生成摘要
        if not content.summary:
            from apps.topic_analysis.utils import generate_summary
            content.summary = generate_summary(content.content)

        # 更新状态
        content.status = 'processed'
        content.save()

        logger.info(f"内容处理完成: {content.id}")

        return {'content_id': content_id, 'status': 'success'}

    except RawContent.DoesNotExist:
        logger.error(f"内容不存在: {content_id}")
        return None
    except Exception as e:
        logger.error(f"内容处理失败: {e}")
        content.status = 'invalid'
        content.save()
        raise


def get_crawler_class(source_type: str):
    """获取爬虫类"""
    crawlers = {
        'rss': RSSCrawler,
        'news': NewsCrawler,
        'wechat': SocialFeedCrawler,
        'bilibili': SocialFeedCrawler,
        'xiaohongshu': SocialFeedCrawler,
        'douyin': SocialFeedCrawler,
    }
    return crawlers.get(source_type, NewsCrawler)


def is_valid_content(item: dict) -> bool:
    """验证内容是否有效"""
    if not item.get('url'):
        return False
    if not item.get('content') or len(item['content']) < 50:
        return False
    return True


def clean_content(content: str) -> str:
    """清洗内容"""
    if not content:
        return ""

    # 去除HTML标签
    from bs4 import BeautifulSoup
    content = BeautifulSoup(content, 'html.parser').get_text()

    # 去除多余空白
    content = ' '.join(content.split())

    return content.strip()
