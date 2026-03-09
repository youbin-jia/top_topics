"""
推荐引擎模型
"""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
from apps.topic_analysis.models import Topic


class Recommendation(models.Model):
    """推荐记录"""

    RECOMMENDATION_TYPES = [
        ('personalized', '个性化推荐'),
        ('hot', '热门推荐'),
        ('trending', '趋势推荐'),
        ('related', '相关推荐'),
    ]

    # 基本信息
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recommendations',
        verbose_name='用户'
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='recommendations',
        verbose_name='话题'
    )

    # 推荐类型
    recommendation_type = models.CharField(
        max_length=20,
        choices=RECOMMENDATION_TYPES,
        verbose_name='推荐类型'
    )

    # 推荐分数
    score = models.FloatField(default=0.0, verbose_name='推荐分数')
    rank = models.IntegerField(default=0, verbose_name='排名')

    # 推荐原因
    reasons = models.JSONField(
        default=list,
        verbose_name='推荐原因'
    )

    # 用户反馈
    feedback = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        choices=[
            ('click', '点击'),
            ('like', '点赞'),
            ('share', '分享'),
            ('collect', '收藏'),
            ('skip', '跳过'),
        ],
        verbose_name='用户反馈'
    )
    feedback_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='反馈时间'
    )

    # 时间信息
    recommended_at = models.DateTimeField(auto_now_add=True, verbose_name='推荐时间')

    class Meta:
        db_table = 'recommendations'
        verbose_name = '推荐记录'
        verbose_name_plural = verbose_name
        ordering = ['-score']
        indexes = [
            models.Index(fields=['user', 'recommended_at']),
            models.Index(fields=['topic', 'recommendation_type']),
        ]


class UserTopicPreference(models.Model):
    """用户话题偏好"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='topic_preferences',
        verbose_name='用户'
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='user_preferences',
        verbose_name='话题'
    )

    # 偏好分数
    preference_score = models.FloatField(default=0.0, verbose_name='偏好分数')

    # 统计信息
    click_count = models.IntegerField(default=0, verbose_name='点击次数')
    like_count = models.IntegerField(default=0, verbose_name='点赞次数')
    share_count = models.IntegerField(default=0, verbose_name='分享次数')
    collect_count = models.IntegerField(default=0, verbose_name='收藏次数')
    skip_count = models.IntegerField(default=0, verbose_name='跳过次数')

    # 时间信息
    first_interacted_at = models.DateTimeField(auto_now_add=True, verbose_name='首次互动时间')
    last_interacted_at = models.DateTimeField(auto_now=True, verbose_name='最后互动时间')

    class Meta:
        db_table = 'user_topic_preferences'
        verbose_name = '用户话题偏好'
        verbose_name_plural = verbose_name
        unique_together = ['user', 'topic']
        indexes = [
            models.Index(fields=['user', '-preference_score']),
        ]


class RecommendationConfig(models.Model):
    """推荐配置"""

    name = models.CharField(max_length=100, unique=True, verbose_name='配置名称')

    # 推荐策略权重
    cf_weight = models.FloatField(default=0.3, verbose_name='协同过滤权重')
    content_weight = models.FloatField(default=0.3, verbose_name='内容推荐权重')
    hot_weight = models.FloatField(default=0.2, verbose_name='热门推荐权重')
    trending_weight = models.FloatField(default=0.2, verbose_name='趋势推荐权重')

    # 过滤参数
    min_score = models.FloatField(default=0.1, verbose_name='最小推荐分数')
    max_items = models.IntegerField(default=20, verbose_name='最大推荐数量')

    # 多样性参数
    diversity_enabled = models.BooleanField(default=True, verbose_name='启用多样性')
    diversity_lambda = models.FloatField(default=0.5, verbose_name='多样性参数')

    # 时间衰减
    time_decay_enabled = models.BooleanField(default=True, verbose_name='启用时间衰减')
    time_decay_factor = models.FloatField(default=0.9, verbose_name='时间衰减因子')

    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'recommendation_configs'
        verbose_name = '推荐配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.name


class RecommendationMetric(models.Model):
    """推荐效果指标"""

    date = models.DateField(verbose_name='日期')

    # 统计指标
    total_recommendations = models.IntegerField(default=0, verbose_name='总推荐数')
    total_clicks = models.IntegerField(default=0, verbose_name='总点击数')
    total_likes = models.IntegerField(default=0, verbose_name='总点赞数')
    total_shares = models.IntegerField(default=0, verbose_name='总分享数')
    total_collects = models.IntegerField(default=0, verbose_name='总收藏数')

    # 效果指标
    ctr = models.FloatField(default=0.0, verbose_name='点击率')
    engagement_rate = models.FloatField(default=0.0, verbose_name='互动率')

    # 分类型指标
    personalized_ctr = models.FloatField(default=0.0, verbose_name='个性化点击率')
    hot_ctr = models.FloatField(default=0.0, verbose_name='热门点击率')
    trending_ctr = models.FloatField(default=0.0, verbose_name='趋势点击率')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'recommendation_metrics'
        verbose_name = '推荐效果指标'
        verbose_name_plural = verbose_name
        ordering = ['-date']
        unique_together = ['date']
