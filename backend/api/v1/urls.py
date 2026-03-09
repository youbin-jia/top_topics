"""
API v1 路由配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TopicViewSet,
    RecommendationViewSet,
    FeedbackViewSet,
    ContentGenerationViewSet,
    UserViewSet,
)

# 创建路由器
router = DefaultRouter()

# 注册视图集
router.register(r'topics', TopicViewSet, basename='topic')
router.register(r'recommendations', RecommendationViewSet, basename='recommendation')
router.register(r'feedback', FeedbackViewSet, basename='feedback')
router.register(r'content', ContentGenerationViewSet, basename='content')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]
