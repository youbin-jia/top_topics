"""
反馈模块模型
"""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
from apps.topic_analysis.models import Topic


class UserFeedback(models.Model):
    """用户反馈"""

    FEEDBACK_TYPES = [
        ('click', '点击'),
        ('like', '点赞'),
        ('share', '分享'),
        ('collect', '收藏'),
        ('skip', '跳过'),
        ('report', '举报'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='feedbacks',
        verbose_name='用户'
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='feedbacks',
        verbose_name='话题'
    )

    # 反馈类型
    feedback_type = models.CharField(
        max_length=20,
        choices=FEEDBACK_TYPES,
        verbose_name='反馈类型'
    )

    # 反馈来源
    source = models.CharField(
        max_length=50,
        default='recommendation',
        verbose_name='反馈来源'
    )

    # 额外信息
    dwell_time = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='停留时间(秒)'
    )
    scroll_depth = models.FloatField(
        null=True,
        blank=True,
        verbose_name='滚动深度'
    )

    # 上下文
    context = models.JSONField(
        default=dict,
        verbose_name='上下文信息'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        db_table = 'user_feedbacks'
        verbose_name = '用户反馈'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['topic', 'feedback_type']),
            models.Index(fields=['feedback_type', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_feedback_type_display()} - {self.topic.name}"


class LearningModel(models.Model):
    """学习模型"""

    MODEL_TYPES = [
        ('user_preference', '用户偏好模型'),
        ('topic_similarity', '话题相似度模型'),
        ('recommendation', '推荐模型'),
    ]

    name = models.CharField(max_length=100, verbose_name='模型名称')
    model_type = models.CharField(
        max_length=50,
        choices=MODEL_TYPES,
        verbose_name='模型类型'
    )

    # 模型信息
    version = models.CharField(max_length=50, verbose_name='版本号')
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='描述'
    )

    # 模型文件
    model_file = models.CharField(
        max_length=500,
        verbose_name='模型文件路径'
    )

    # 性能指标
    accuracy = models.FloatField(default=0.0, verbose_name='准确率')
    precision = models.FloatField(default=0.0, verbose_name='精确率')
    recall = models.FloatField(default=0.0, verbose_name='召回率')
    f1_score = models.FloatField(default=0.0, verbose_name='F1分数')

    # 训练信息
    training_samples = models.IntegerField(default=0, verbose_name='训练样本数')
    training_time = models.FloatField(default=0.0, verbose_name='训练时长(秒)')

    is_active = models.BooleanField(default=False, verbose_name='是否激活')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'learning_models'
        verbose_name = '学习模型'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} v{self.version}"


class ModelPerformanceLog(models.Model):
    """模型性能日志"""

    model = models.ForeignKey(
        LearningModel,
        on_delete=models.CASCADE,
        related_name='performance_logs',
        verbose_name='模型'
    )

    # 性能指标
    metric_name = models.CharField(max_length=50, verbose_name='指标名称')
    metric_value = models.FloatField(verbose_name='指标值')

    # 额外信息
    sample_size = models.IntegerField(default=0, verbose_name='样本大小')
    details = models.JSONField(
        default=dict,
        verbose_name='详细信息'
    )

    recorded_at = models.DateTimeField(auto_now_add=True, verbose_name='记录时间')

    class Meta:
        db_table = 'model_performance_logs'
        verbose_name = '模型性能日志'
        verbose_name_plural = verbose_name
        ordering = ['-recorded_at']


class ABTestExperiment(models.Model):
    """A/B测试实验"""

    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('running', '运行中'),
        ('completed', '已完成'),
        ('paused', '已暂停'),
    ]

    name = models.CharField(max_length=200, unique=True, verbose_name='实验名称')
    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='实验描述'
    )

    # 实验配置
    control_group_ratio = models.FloatField(
        default=0.5,
        verbose_name='对照组比例'
    )
    experiment_group_ratio = models.FloatField(
        default=0.5,
        verbose_name='实验组比例'
    )

    # 变量配置
    variables = models.JSONField(
        default=dict,
        verbose_name='实验变量'
    )

    # 状态
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='状态'
    )

    # 时间信息
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='开始时间'
    )
    ended_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='结束时间'
    )

    # 结果
    results = models.JSONField(
        default=dict,
        verbose_name='实验结果'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'abtest_experiments'
        verbose_name = 'A/B测试实验'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class ABTestAssignment(models.Model):
    """A/B测试分组"""

    experiment = models.ForeignKey(
        ABTestExperiment,
        on_delete=models.CASCADE,
        related_name='assignments',
        verbose_name='实验'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='abtest_assignments',
        verbose_name='用户'
    )

    # 分组
    group = models.CharField(
        max_length=20,
        choices=[
            ('control', '对照组'),
            ('experiment', '实验组'),
        ],
        verbose_name='分组'
    )

    # 分配的变量值
    assigned_values = models.JSONField(
        default=dict,
        verbose_name='分配的变量值'
    )

    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name='分配时间')

    class Meta:
        db_table = 'abtest_assignments'
        verbose_name = 'A/B测试分组'
        verbose_name_plural = verbose_name
        unique_together = ['experiment', 'user']
