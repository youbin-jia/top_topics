"""
话题分析模型
"""
from django.db import models
from apps.data_collection.models import RawContent


class Topic(models.Model):
    """话题"""

    STATUS_CHOICES = [
        ('active', '活跃'),
        ('inactive', '不活跃'),
        ('trending', '热门'),
    ]

    # 基本信息
    name = models.CharField(max_length=200, unique=True, verbose_name='话题名称')
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='话题描述'
    )

    # 关键词
    keywords = models.JSONField(default=list, verbose_name='关键词')
    main_keyword = models.CharField(
        max_length=100,
        verbose_name='主关键词'
    )

    # 热度指标
    heat_score = models.FloatField(default=0.0, verbose_name='热度分数')
    trend = models.CharField(
        max_length=20,
        choices=[
            ('rising', '上升'),
            ('falling', '下降'),
            ('stable', '稳定'),
        ],
        default='stable',
        verbose_name='趋势'
    )

    # 统计信息
    article_count = models.IntegerField(default=0, verbose_name='文章数量')
    view_count = models.IntegerField(default=0, verbose_name='总浏览数')
    engagement_rate = models.FloatField(default=0.0, verbose_name='互动率')

    # 状态
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name='状态'
    )

    # 时间信息
    first_seen_at = models.DateTimeField(auto_now_add=True, verbose_name='首次发现时间')
    last_updated_at = models.DateTimeField(auto_now=True, verbose_name='最后更新时间')

    # 相关话题
    related_topics = models.ManyToManyField(
        'self',
        blank=True,
        verbose_name='相关话题'
    )

    class Meta:
        db_table = 'topics'
        verbose_name = '话题'
        verbose_name_plural = verbose_name
        ordering = ['-heat_score']

    def __str__(self):
        return self.name

    def update_heat_score(self):
        """更新热度分数"""
        from .utils import calculate_heat_score
        self.heat_score = calculate_heat_score(self)
        self.save()


class TopicCluster(models.Model):
    """话题聚类"""

    name = models.CharField(max_length=200, verbose_name='聚类名称')
    topics = models.ManyToManyField(
        Topic,
        related_name='clusters',
        verbose_name='包含话题'
    )

    # 聚类特征
    center_keywords = models.JSONField(
        default=list,
        verbose_name='中心关键词'
    )
    coherence_score = models.FloatField(
        default=0.0,
        verbose_name='一致性分数'
    )

    # 统计信息
    total_articles = models.IntegerField(default=0, verbose_name='总文章数')
    total_views = models.IntegerField(default=0, verbose_name='总浏览数')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'topic_clusters'
        verbose_name = '话题聚类'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class TopicTrend(models.Model):
    """话题趋势记录"""

    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='trends',
        verbose_name='话题'
    )

    # 记录时间
    recorded_at = models.DateTimeField(verbose_name='记录时间')

    # 热度指标
    heat_score = models.FloatField(verbose_name='热度分数')
    article_count = models.IntegerField(verbose_name='文章数量')
    view_count = models.IntegerField(verbose_name='浏览数')
    engagement_rate = models.FloatField(verbose_name='互动率')

    # 趋势指标
    growth_rate = models.FloatField(default=0.0, verbose_name='增长率')
    velocity = models.FloatField(default=0.0, verbose_name='速度')
    acceleration = models.FloatField(default=0.0, verbose_name='加速度')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'topic_trends'
        verbose_name = '话题趋势'
        verbose_name_plural = verbose_name
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['topic', 'recorded_at']),
        ]


class ContentTopicRelation(models.Model):
    """内容与话题关联"""

    content = models.ForeignKey(
        RawContent,
        on_delete=models.CASCADE,
        related_name='topic_relations',
        verbose_name='内容'
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='content_relations',
        verbose_name='话题'
    )

    # 关联强度
    relevance_score = models.FloatField(
        default=0.0,
        verbose_name='相关性分数'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'content_topic_relations'
        verbose_name = '内容话题关联'
        verbose_name_plural = verbose_name
        unique_together = ['content', 'topic']
        indexes = [
            models.Index(fields=['topic', 'relevance_score']),
        ]
