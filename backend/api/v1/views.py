"""
API v1 视图
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class TopicViewSet(viewsets.ReadOnlyModelViewSet):
    """话题视图集"""

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        from apps.topic_analysis.models import Topic
        queryset = Topic.objects.filter(status__in=['active', 'trending'])

        # 过滤参数
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(keywords__contains=[category])

        min_score = self.request.query_params.get('min_score')
        if min_score:
            queryset = queryset.filter(heat_score__gte=float(min_score))

        return queryset

    def list(self, request):
        """获取话题列表"""
        queryset = self.get_queryset()
        limit = int(request.query_params.get('limit', 20))
        topics = queryset[:limit]

        data = [
            {
                'id': topic.id,
                'name': topic.name,
                'description': topic.description,
                'keywords': topic.keywords,
                'heat_score': topic.heat_score,
                'trend': topic.trend,
                'article_count': topic.article_count,
            }
            for topic in topics
        ]

        return Response({
            'success': True,
            'data': data
        })

    @action(detail=False, methods=['get'])
    def hot(self, request):
        """获取热门话题"""
        limit = int(request.query_params.get('limit', 10))
        topics = self.get_queryset().order_by('-heat_score')[:limit]

        data = [
            {
                'id': topic.id,
                'name': topic.name,
                'heat_score': topic.heat_score,
                'trend': topic.trend,
                'article_count': topic.article_count,
            }
            for topic in topics
        ]

        return Response({
            'success': True,
            'data': data
        })

    @action(detail=False, methods=['get'])
    def trending(self, request):
        """获取趋势话题"""
        limit = int(request.query_params.get('limit', 10))
        topics = self.get_queryset().filter(trend='rising')[:limit]

        data = [
            {
                'id': topic.id,
                'name': topic.name,
                'heat_score': topic.heat_score,
                'growth_rate': self._get_growth_rate(topic),
            }
            for topic in topics
        ]

        return Response({
            'success': True,
            'data': data
        })

    def _get_growth_rate(self, topic):
        """获取增长率"""
        from apps.topic_analysis.models import TopicTrend

        recent_trends = TopicTrend.objects.filter(
            topic=topic
        ).order_by('-recorded_at')[:2]

        if len(recent_trends) >= 2:
            return recent_trends[0].growth_rate
        return 0.0


class RecommendationViewSet(viewsets.ViewSet):
    """推荐视图集"""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def personalized(self, request):
        """个性化推荐"""
        user = request.user
        limit = int(request.query_params.get('limit', 20))

        # 生成推荐
        from apps.recommendation.engine import HybridRecommender
        recommender = HybridRecommender()

        recommendations = recommender.recommend(
            user.id,
            n_recommendations=limit
        )

        # 获取话题详情
        from apps.topic_analysis.models import Topic
        topic_ids = [item[0] for item in recommendations]
        topics = Topic.objects.filter(id__in=topic_ids)
        topic_map = {topic.id: topic for topic in topics}

        # 构建返回数据
        data = []
        for topic_id, score in recommendations:
            topic = topic_map.get(topic_id)
            if topic:
                data.append({
                    'id': topic.id,
                    'name': topic.name,
                    'description': topic.description,
                    'keywords': topic.keywords,
                    'heat_score': topic.heat_score,
                    'trend': topic.trend,
                    'recommendation_score': score,
                })

        # 保存推荐记录
        from apps.recommendation.models import Recommendation
        for rank, item in enumerate(data, 1):
            Recommendation.objects.create(
                user=user,
                topic_id=item['id'],
                recommendation_type='personalized',
                score=item['recommendation_score'],
                rank=rank
            )

        return Response({
            'success': True,
            'data': data
        })

    @action(detail=False, methods=['get'])
    def hot(self, request):
        """热门推荐"""
        limit = int(request.query_params.get('limit', 10))

        from apps.topic_analysis.models import Topic
        topics = Topic.objects.filter(
            status__in=['active', 'trending']
        ).order_by('-heat_score')[:limit]

        data = [
            {
                'id': topic.id,
                'name': topic.name,
                'heat_score': topic.heat_score,
                'trend': topic.trend,
            }
            for topic in topics
        ]

        return Response({
            'success': True,
            'data': data
        })


class FeedbackViewSet(viewsets.ViewSet):
    """反馈视图集"""

    permission_classes = [IsAuthenticated]

    def create(self, request):
        """提交反馈"""
        user = request.user
        topic_id = request.data.get('topic_id')
        feedback_type = request.data.get('type')

        if not topic_id or not feedback_type:
            return Response({
                'success': False,
                'message': '缺少必要参数'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 创建反馈
        from apps.feedback.models import UserFeedback
        feedback = UserFeedback.objects.create(
            user=user,
            topic_id=topic_id,
            feedback_type=feedback_type,
            source=request.data.get('source', 'api'),
            dwell_time=request.data.get('dwell_time'),
            scroll_depth=request.data.get('scroll_depth'),
        )

        # 更新用户偏好
        from apps.feedback.learner import AdaptiveLearner
        learner = AdaptiveLearner()
        learner.update_user_preference(
            user.id,
            topic_id,
            feedback_type
        )

        # 更新推荐记录
        from apps.recommendation.models import Recommendation
        Recommendation.objects.filter(
            user=user,
            topic_id=topic_id,
            feedback__isnull=True
        ).update(
            feedback=feedback_type,
            feedback_at=timezone.now()
        )

        return Response({
            'success': True,
            'message': '反馈已记录'
        })


class ContentGenerationViewSet(viewsets.ViewSet):
    """内容生成视图集"""

    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def generate_title(self, request):
        """生成标题"""
        topic_id = request.data.get('topic_id')
        keywords = request.data.get('keywords', [])
        category = request.data.get('category', 'news')
        n_titles = request.data.get('n_titles', 5)

        if not keywords and topic_id:
            # 从话题获取关键词
            from apps.topic_analysis.models import Topic
            try:
                topic = Topic.objects.get(id=topic_id)
                keywords = topic.keywords
            except Topic.DoesNotExist:
                pass

        # 生成标题
        from apps.content_generation.generators import TitleGenerator
        generator = TitleGenerator()
        titles = generator.generate(
            keywords=keywords,
            category=category,
            n_titles=n_titles
        )

        # 质量评分
        from apps.content_generation.generators import ContentQualityScorer
        scorer = ContentQualityScorer()
        scored_titles = [
            {
                'title': title,
                'quality_score': scorer.score_title(title)
            }
            for title in titles
        ]

        # 保存生成记录
        from apps.content_generation.models import GeneratedContent
        if topic_id:
            GeneratedContent.objects.create(
                user=request.user,
                topic_id=topic_id,
                content_type='title',
                content='\n'.join(titles),
                alternatives=scored_titles,
                generation_params={
                    'keywords': keywords,
                    'category': category,
                }
            )

        return Response({
            'success': True,
            'data': scored_titles
        })

    @action(detail=False, methods=['post'])
    def generate_outline(self, request):
        """生成大纲"""
        topic_id = request.data.get('topic_id')
        topic_name = request.data.get('topic_name')
        keywords = request.data.get('keywords', [])
        style = request.data.get('style', 'informative')
        n_sections = request.data.get('n_sections', 3)

        if topic_id:
            from apps.topic_analysis.models import Topic
            try:
                topic = Topic.objects.get(id=topic_id)
                topic_name = topic.name
                if not keywords:
                    keywords = topic.keywords
            except Topic.DoesNotExist:
                pass

        # 生成大纲
        from apps.content_generation.generators import OutlineGenerator
        generator = OutlineGenerator()
        outline = generator.generate(
            topic=topic_name or '未命名主题',
            keywords=keywords,
            style=style,
            n_sections=n_sections
        )

        # 质量评分
        from apps.content_generation.generators import ContentQualityScorer
        scorer = ContentQualityScorer()
        quality_score = scorer.score_outline(outline)

        outline['quality_score'] = quality_score

        # 保存生成记录
        from apps.content_generation.models import GeneratedContent
        if topic_id:
            GeneratedContent.objects.create(
                user=request.user,
                topic_id=topic_id,
                content_type='outline',
                content=str(outline),
                generation_params={
                    'style': style,
                    'n_sections': n_sections,
                },
                quality_score=quality_score
            )

        return Response({
            'success': True,
            'data': outline
        })


class UserViewSet(viewsets.ViewSet):
    """用户视图集"""

    permission_classes = [IsAuthenticated]

    def retrieve(self, request, pk=None):
        """获取用户信息"""
        if pk == 'me':
            user = request.user
        else:
            from django.shortcuts import get_object_or_404
            user = get_object_or_404(User, pk=pk)

        data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'bio': user.bio,
            'preferred_categories': user.preferred_categories,
            'top_interests': user.get_top_interests(10),
            'created_at': user.created_at,
        }

        return Response({
            'success': True,
            'data': data
        })

    @action(detail=False, methods=['get'])
    def profile(self, request):
        """获取用户画像"""
        user = request.user

        from apps.users.models import UserProfile
        profile, created = UserProfile.objects.get_or_create(user=user)

        data = {
            'user_id': user.id,
            'total_clicks': profile.total_clicks,
            'total_likes': profile.total_likes,
            'total_shares': profile.total_shares,
            'total_collects': profile.total_collects,
            'active_days': profile.active_days,
            'last_active_at': profile.last_active_at,
            'top_interests': user.get_top_interests(20),
        }

        return Response({
            'success': True,
            'data': data
        })

    @action(detail=False, methods=['put'])
    def update_preferences(self, request):
        """更新用户偏好"""
        user = request.user

        categories = request.data.get('categories')
        if categories:
            user.preferred_categories = categories

        keywords = request.data.get('keywords')
        if keywords:
            user.keywords_interests = keywords

        user.save()

        return Response({
            'success': True,
            'message': '偏好已更新'
        })
