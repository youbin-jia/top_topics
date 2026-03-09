"""
集成测试 - 推荐流程
"""
import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestRecommendationFlow(TestCase):
    """推荐流程集成测试"""

    def setUp(self):
        """设置测试环境"""
        self.client = APIClient()

        # 创建测试用户
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # 认证
        self.client.force_authenticate(user=self.user)

        # 创建测试话题
        from apps.topic_analysis.models import Topic

        self.topics = []
        for i in range(5):
            topic = Topic.objects.create(
                name=f'测试话题{i+1}',
                main_keyword=f'关键词{i+1}',
                keywords=[f'关键词{i+1}', f'标签{i+1}'],
                article_count=i * 10,
                view_count=i * 100,
                heat_score=0.5 + i * 0.1,
            )
            self.topics.append(topic)

    def test_get_hot_topics(self):
        """测试获取热门话题"""
        response = self.client.get('/api/v1/topics/hot/')

        assert response.status_code == 200
        data = response.json()

        assert data['success'] is True
        assert isinstance(data['data'], list)
        assert len(data['data']) <= 10

    def test_get_personalized_recommendations(self):
        """测试获取个性化推荐"""
        response = self.client.get('/api/v1/recommendations/personalized/')

        assert response.status_code == 200
        data = response.json()

        assert data['success'] is True
        assert isinstance(data['data'], list)

    def test_submit_feedback_and_update_preference(self):
        """测试提交反馈并更新偏好"""
        # 1. 提交反馈
        feedback_data = {
            'topic_id': self.topics[0].id,
            'type': 'like',
        }

        response = self.client.post('/api/v1/feedback/', feedback_data)

        assert response.status_code == 201
        assert response.json()['success'] is True

        # 2. 检查用户偏好是否更新
        from apps.recommendation.models import UserTopicPreference

        preference = UserTopicPreference.objects.filter(
            user=self.user,
            topic=self.topics[0]
        ).first()

        assert preference is not None
        assert preference.like_count == 1
        assert preference.preference_score > 0

        # 3. 再次获取推荐，应该包含偏好调整
        response = self.client.get('/api/v1/recommendations/personalized/')

        assert response.status_code == 200

    def test_generate_title(self):
        """测试标题生成"""
        content_data = {
            'keywords': ['人工智能', '机器学习'],
            'category': 'news',
            'n_titles': 5,
        }

        response = self.client.post('/api/v1/content/generate_title/', content_data)

        assert response.status_code == 200
        data = response.json()

        assert data['success'] is True
        assert isinstance(data['data'], list)
        assert len(data['data']) <= 5

    def test_generate_outline(self):
        """测试大纲生成"""
        content_data = {
            'topic_name': '人工智能的发展',
            'keywords': ['AI', '深度学习'],
            'style': 'informative',
            'n_sections': 3,
        }

        response = self.client.post('/api/v1/content/generate_outline/', content_data)

        assert response.status_code == 200
        data = response.json()

        assert data['success'] is True
        assert 'data' in data
        assert 'title' in data['data']
        assert 'sections' in data['data']
        assert len(data['data']['sections']) <= 3

    def test_full_recommendation_flow(self):
        """测试完整推荐流程"""
        # 1. 获取推荐
        response = self.client.get('/api/v1/recommendations/personalized/')
        assert response.status_code == 200

        recommendations = response.json()['data']
        assert len(recommendations) > 0

        # 2. 浏览第一个推荐
        first_topic_id = recommendations[0]['id']

        # 提交点击反馈
        response = self.client.post('/api/v1/feedback/', {
            'topic_id': first_topic_id,
            'type': 'click',
            'dwell_time': 30,
        })
        assert response.status_code == 201

        # 3. 点赞
        response = self.client.post('/api/v1/feedback/', {
            'topic_id': first_topic_id,
            'type': 'like',
        })
        assert response.status_code == 201

        # 4. 生成相关内容
        response = self.client.post('/api/v1/content/generate_title/', {
            'topic_id': first_topic_id,
        })
        assert response.status_code == 200

        # 5. 再次获取推荐，验证个性化效果
        response = self.client.get('/api/v1/recommendations/personalized/')
        assert response.status_code == 200
