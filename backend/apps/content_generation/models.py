"""
内容生成模型
"""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
from apps.topic_analysis.models import Topic


class GeneratedContent(models.Model):
    """生成的内容"""

    CONTENT_TYPES = [
        ('title', '标题'),
        ('outline', '大纲'),
        ('summary', '摘要'),
        ('keywords', '关键词'),
    ]

    # 基本信息
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='generated_contents',
        verbose_name='用户',
        null=True,
        blank=True
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='generated_contents',
        verbose_name='话题'
    )

    # 内容类型
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPES,
        verbose_name='内容类型'
    )

    # 生成的内容
    content = models.TextField(verbose_name='生成内容')
    alternatives = models.JSONField(
        default=list,
        verbose_name='备选内容'
    )

    # 质量指标
    quality_score = models.FloatField(
        default=0.0,
        verbose_name='质量分数'
    )
    readability_score = models.FloatField(
        default=0.0,
        verbose_name='可读性分数'
    )

    # 生成参数
    generation_params = models.JSONField(
        default=dict,
        verbose_name='生成参数'
    )

    # 用户评价
    user_rating = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='用户评分'
    )
    user_feedback = models.TextField(
        null=True,
        blank=True,
        verbose_name='用户反馈'
    )

    # 时间信息
    generated_at = models.DateTimeField(auto_now_add=True, verbose_name='生成时间')

    class Meta:
        db_table = 'generated_contents'
        verbose_name = '生成内容'
        verbose_name_plural = verbose_name
        ordering = ['-generated_at']
        indexes = [
            models.Index(fields=['topic', 'content_type']),
            models.Index(fields=['user', '-generated_at']),
        ]


class TitleTemplate(models.Model):
    """标题模板"""

    CATEGORY_CHOICES = [
        ('news', '新闻类'),
        ('guide', '指南类'),
        ('list', '清单类'),
        ('story', '故事类'),
        ('question', '问答类'),
        ('shock', '震惊类'),
    ]

    name = models.CharField(max_length=100, verbose_name='模板名称')
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        verbose_name='模板分类'
    )

    # 模板内容（使用{keyword}作为占位符）
    template = models.CharField(max_length=200, verbose_name='模板内容')

    # 示例
    example = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        verbose_name='示例'
    )

    # 效果指标
    avg_ctr = models.FloatField(default=0.0, verbose_name='平均点击率')
    usage_count = models.IntegerField(default=0, verbose_name='使用次数')

    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'title_templates'
        verbose_name = '标题模板'
        verbose_name_plural = verbose_name
        ordering = ['-avg_ctr']

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"

    def render(self, **kwargs) -> str:
        """渲染模板"""
        return self.template.format(**kwargs)


class OutlineTemplate(models.Model):
    """大纲模板"""

    STYLE_CHOICES = [
        ('informative', '信息型'),
        ('persuasive', '说服型'),
        ('entertaining', '娱乐型'),
        ('educational', '教育型'),
    ]

    name = models.CharField(max_length=100, verbose_name='模板名称')
    style = models.CharField(
        max_length=20,
        choices=STYLE_CHOICES,
        verbose_name='文章风格'
    )

    # 大纲结构
    structure = models.JSONField(
        default=list,
        verbose_name='大纲结构',
        help_text='包含章节标题和要点的JSON数组'
    )

    # 适用场景
    applicable_categories = models.JSONField(
        default=list,
        verbose_name='适用分类'
    )

    # 效果指标
    avg_engagement = models.FloatField(default=0.0, verbose_name='平均互动率')
    usage_count = models.IntegerField(default=0, verbose_name='使用次数')

    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'outline_templates'
        verbose_name = '大纲模板'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.name} ({self.get_style_display()})"
