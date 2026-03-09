"""
话题分析单元测试
"""
import pytest
from datetime import datetime, timedelta
from django.utils import timezone


@pytest.mark.django_db
class TestTopicModeling:
    """主题建模测试"""

    def test_extract_keywords_tfidf(self):
        """测试TF-IDF关键词提取"""
        from apps.topic_analysis.utils import extract_keywords

        text = """
        人工智能是计算机科学的一个分支，它企图了解智能的实质，
        并生产出一种新的能以人类智能相似的方式做出反应的智能机器。
        机器学习是人工智能的核心研究领域之一。
        """

        keywords = extract_keywords(text, top_k=10, method='tfidf')

        assert isinstance(keywords, list)
        assert len(keywords) <= 10
        assert '人工智能' in keywords or '机器学习' in keywords

    def test_extract_keywords_textrank(self):
        """测试TextRank关键词提取"""
        from apps.topic_analysis.utils import extract_keywords

        text = "深度学习是机器学习的一个子领域，神经网络是深度学习的基础。"

        keywords = extract_keywords(text, top_k=5, method='textrank')

        assert isinstance(keywords, list)
        assert len(keywords) <= 5

    def test_extract_keywords_with_weights(self):
        """测试带权重的关键词提取"""
        from apps.topic_analysis.utils import extract_keywords_with_weights

        text = "Python是一种流行的编程语言，广泛用于数据科学和人工智能。"

        keywords = extract_keywords_with_weights(text, top_k=5)

        assert isinstance(keywords, list)
        assert len(keywords) <= 5
        assert all(isinstance(item, tuple) for item in keywords)
        assert all(isinstance(item[0], str) for item in keywords)
        assert all(isinstance(item[1], float) for item in keywords)


@pytest.mark.django_db
class TestHeatScoreCalculation:
    """热度计算测试"""

    def test_calculate_time_decay(self):
        """测试时间衰减计算"""
        from apps.topic_analysis.utils import calculate_time_decay

        # 最近的时间
        recent_time = timezone.now()
        decay_recent = calculate_time_decay(recent_time)
        assert 0.9 <= decay_recent <= 1.0

        # 24小时前
        hours_ago = timezone.now() - timedelta(hours=24)
        decay_24h = calculate_time_decay(hours_ago, half_life=24)
        assert 0.4 <= decay_24h <= 0.6

        # 很久以前
        long_ago = timezone.now() - timedelta(days=7)
        decay_long = calculate_time_decay(long_ago)
        assert 0.0 <= decay_long < 0.1

    def test_calculate_heat_score(self):
        """测试热度分数计算"""
        from apps.topic_analysis.models import Topic
        from apps.topic_analysis.utils import calculate_heat_score

        # 创建测试话题
        topic = Topic.objects.create(
            name='测试话题',
            main_keyword='测试',
            article_count=50,
            view_count=10000,
            engagement_rate=0.5,
        )

        heat_score = calculate_heat_score(topic)

        assert isinstance(heat_score, float)
        assert 0.0 <= heat_score <= 1.0


@pytest.mark.django_db
class TestTextProcessing:
    """文本处理测试"""

    def test_tokenize(self):
        """测试中文分词"""
        from apps.topic_analysis.utils import tokenize

        text = "人工智能正在改变我们的生活方式"
        tokens = tokenize(text)

        assert isinstance(tokens, list)
        assert len(tokens) > 0
        assert all(isinstance(token, str) for token in tokens)

    def test_generate_summary(self):
        """测试摘要生成"""
        from apps.topic_analysis.utils import generate_summary

        long_text = "这是一个很长的文本。" * 100
        summary = generate_summary(long_text, max_length=100)

        assert isinstance(summary, str)
        assert len(summary) <= 103  # 考虑省略号

    def test_calculate_similarity(self):
        """测试文本相似度计算"""
        from apps.topic_analysis.utils import calculate_similarity

        text1 = "人工智能和机器学习"
        text2 = "机器学习和人工智能"
        text3 = "完全不同的内容"

        similarity_high = calculate_similarity(text1, text2)
        similarity_low = calculate_similarity(text1, text3)

        assert 0.0 <= similarity_high <= 1.0
        assert 0.0 <= similarity_low <= 1.0
        assert similarity_high > similarity_low
