"""
数据收集模型
"""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class DataSource(models.Model):
    """数据源"""

    SOURCE_TYPES = [
        ('rss', 'RSS/Atom 订阅'),
        ('news', '新闻网站'),
        ('weibo', '微博'),
        ('zhihu', '知乎'),
        ('wechat', '微信公众号'),
        ('bilibili', 'B站'),
        ('xiaohongshu', '小红书'),
        ('douyin', '抖音'),
        ('twitter', 'Twitter'),
        ('other', '其他'),
    ]

    STATUS_CHOICES = [
        ('active', '活跃'),
        ('inactive', '停用'),
        ('error', '错误'),
    ]

    name = models.CharField(max_length=100, verbose_name='数据源名称')
    source_type = models.CharField(
        max_length=50,
        choices=SOURCE_TYPES,
        verbose_name='数据源类型'
    )
    base_url = models.URLField(verbose_name='基础URL')
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='状态'
    )

    # 爬取配置
    crawl_frequency = models.IntegerField(
        default=3600,
        verbose_name='爬取频率(秒)'
    )
    last_crawled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='最后爬取时间'
    )

    # 统计信息
    total_crawled = models.IntegerField(default=0, verbose_name='总爬取数')
    success_count = models.IntegerField(default=0, verbose_name='成功数')
    error_count = models.IntegerField(default=0, verbose_name='失败数')

    # 配置
    config = models.JSONField(
        default=dict,
        verbose_name='爬取配置'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'data_sources'
        verbose_name = '数据源'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_source_type_display()})"


class RawContent(models.Model):
    """原始内容"""

    CONTENT_STATUS = [
        ('pending', '待处理'),
        ('processed', '已处理'),
        ('invalid', '无效'),
        ('duplicate', '重复'),
    ]

    # 基本信息
    title = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='标题'
    )
    content = models.TextField(verbose_name='内容')
    url = models.URLField(unique=True, verbose_name='原始链接')
    source = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name='contents',
        verbose_name='数据源'
    )

    # 元数据
    author = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name='作者'
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='发布时间'
    )
    crawled_at = models.DateTimeField(auto_now_add=True, verbose_name='爬取时间')

    # 统计数据
    view_count = models.IntegerField(default=0, verbose_name='浏览数')
    like_count = models.IntegerField(default=0, verbose_name='点赞数')
    share_count = models.IntegerField(default=0, verbose_name='分享数')
    comment_count = models.IntegerField(default=0, verbose_name='评论数')

    # 处理状态
    status = models.CharField(
        max_length=20,
        choices=CONTENT_STATUS,
        default='pending',
        verbose_name='处理状态'
    )

    # 提取的关键信息
    keywords = models.JSONField(
        default=list,
        verbose_name='关键词'
    )
    summary = models.TextField(
        null=True,
        blank=True,
        verbose_name='摘要'
    )

    # 其他元数据
    metadata = models.JSONField(
        default=dict,
        verbose_name='其他元数据'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'raw_contents'
        verbose_name = '原始内容'
        verbose_name_plural = verbose_name
        ordering = ['-crawled_at']
        indexes = [
            models.Index(fields=['status', 'crawled_at']),
            models.Index(fields=['source', 'published_at']),
        ]

    def __str__(self):
        return self.title or f"内容#{self.id}"


class CrawlLog(models.Model):
    """爬取日志"""

    STATUS_CHOICES = [
        ('success', '成功'),
        ('failed', '失败'),
        ('partial', '部分成功'),
    ]

    source = models.ForeignKey(
        DataSource,
        on_delete=models.CASCADE,
        related_name='crawl_logs',
        verbose_name='数据源'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        verbose_name='状态'
    )

    # 统计
    items_crawled = models.IntegerField(default=0, verbose_name='爬取数量')
    items_saved = models.IntegerField(default=0, verbose_name='保存数量')
    items_duplicate = models.IntegerField(default=0, verbose_name='重复数量')
    items_invalid = models.IntegerField(default=0, verbose_name='无效数量')

    # 错误信息
    error_message = models.TextField(
        null=True,
        blank=True,
        verbose_name='错误信息'
    )

    # 性能指标
    duration = models.FloatField(default=0, verbose_name='耗时(秒)')
    started_at = models.DateTimeField(verbose_name='开始时间')
    finished_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='结束时间'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'crawl_logs'
        verbose_name = '爬取日志'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.source.name} - {self.status} - {self.created_at}"
