"""
用户模型
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from typing import List, Dict


class User(AbstractUser):
    """自定义用户模型"""

    # 用户角色
    ROLE_CHOICES = [
        ('user', '普通用户'),
        ('creator', '创作者'),
        ('admin', '管理员'),
    ]

    # 扩展字段
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='user',
        verbose_name='用户角色'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        null=True,
        blank=True,
        verbose_name='头像'
    )
    bio = models.TextField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name='个人简介'
    )

    # 用户偏好设置
    preferred_categories = models.JSONField(
        default=list,
        verbose_name='偏好领域'
    )
    keywords_interests = models.JSONField(
        default=dict,
        verbose_name='关键词兴趣'
    )

    # 统计信息
    total_views = models.IntegerField(
        default=0,
        verbose_name='总浏览数'
    )
    total_recommendations = models.IntegerField(
        default=0,
        verbose_name='总推荐数'
    )

    # 时间戳
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.username

    def update_interests(self, keywords: Dict[str, float]):
        """更新用户兴趣关键词"""
        for keyword, weight in keywords.items():
            if keyword in self.keywords_interests:
                # 渐进式更新
                self.keywords_interests[keyword] = (
                    self.keywords_interests[keyword] * 0.8 + weight * 0.2
                )
            else:
                self.keywords_interests[keyword] = weight
        self.save()

    def get_top_interests(self, n: int = 10) -> List[str]:
        """获取用户最感兴趣的N个关键词"""
        sorted_interests = sorted(
            self.keywords_interests.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [item[0] for item in sorted_interests[:n]]


class UserProfile(models.Model):
    """用户详细画像"""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )

    # 用户行为统计
    total_clicks = models.IntegerField(default=0, verbose_name='总点击数')
    total_likes = models.IntegerField(default=0, verbose_name='总点赞数')
    total_shares = models.IntegerField(default=0, verbose_name='总分享数')
    total_collects = models.IntegerField(default=0, verbose_name='总收藏数')

    # 活跃度
    last_active_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='最后活跃时间'
    )
    active_days = models.IntegerField(default=0, verbose_name='活跃天数')

    # 偏好时间段
    preferred_time_slots = models.JSONField(
        default=list,
        verbose_name='偏好时间段'
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'user_profiles'
        verbose_name = '用户画像'
        verbose_name_plural = verbose_name

    def update_behavior(self, behavior_type: str):
        """更新用户行为统计"""
        from django.utils import timezone

        if behavior_type == 'click':
            self.total_clicks += 1
        elif behavior_type == 'like':
            self.total_likes += 1
        elif behavior_type == 'share':
            self.total_shares += 1
        elif behavior_type == 'collect':
            self.total_collects += 1

        self.last_active_at = timezone.now()
        self.save()
