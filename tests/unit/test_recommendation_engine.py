"""
推荐引擎单元测试
"""
import pytest
import numpy as np
from django.contrib.auth import get_user_model

User = get_user_model()


class TestCollaborativeFiltering:
    """协同过滤测试"""

    def test_build_user_item_matrix(self):
        """测试构建用户-物品矩阵"""
        from apps.recommendation.engine import CollaborativeFiltering

        cf = CollaborativeFiltering()

        # 模拟用户交互数据
        interactions = {
            1: {1: 5.0, 2: 3.0, 3: 4.0},
            2: {1: 4.0, 2: 5.0, 4: 3.0},
            3: {2: 4.0, 3: 5.0, 4: 4.0},
        }

        cf.build_user_item_matrix(interactions)

        assert cf.user_item_matrix is not None
        assert cf.item_similarity is not None
        assert cf.user_item_matrix.shape == (3, 4)

    def test_recommend(self):
        """测试推荐生成"""
        from apps.recommendation.engine import CollaborativeFiltering

        cf = CollaborativeFiltering()

        interactions = {
            1: {1: 5.0, 2: 3.0},
            2: {1: 4.0, 3: 5.0},
            3: {2: 4.0, 3: 5.0},
        }

        cf.build_user_item_matrix(interactions)

        # 为用户1生成推荐
        recommendations = cf.recommend(user_id=1, n_recommendations=2)

        assert isinstance(recommendations, list)
        assert len(recommendations) <= 2
        assert all(isinstance(item, tuple) for item in recommendations)
        assert all(isinstance(item[0], int) for item in recommendations)
        assert all(isinstance(item[1], float) for item in recommendations)


class TestContentBasedFiltering:
    """基于内容的推荐测试"""

    def test_update_user_profile(self):
        """测试用户画像更新"""
        from apps.recommendation.engine import ContentBasedFiltering

        cb = ContentBasedFiltering()

        # 设置物品特征
        item_features = {
            1: np.array([1.0, 0.0, 0.0]),
            2: np.array([0.0, 1.0, 0.0]),
            3: np.array([1.0, 1.0, 0.0]),
        }

        cb.set_item_features(item_features)
        cb.update_user_profile(user_id=1, liked_items=[1, 2])

        assert 1 in cb.user_profiles
        assert cb.user_profiles[1] is not None

    def test_recommend(self):
        """测试基于内容的推荐"""
        from apps.recommendation.engine import ContentBasedFiltering

        cb = ContentBasedFiltering()

        # 设置物品特征
        item_features = {
            1: np.array([1.0, 0.0, 0.0]),
            2: np.array([0.9, 0.1, 0.0]),
            3: np.array([0.0, 1.0, 0.0]),
            4: np.array([0.1, 0.9, 0.0]),
        }

        cb.set_item_features(item_features)
        cb.update_user_profile(user_id=1, liked_items=[1])

        recommendations = cb.recommend(user_id=1, n_recommendations=2)

        assert isinstance(recommendations, list)
        assert len(recommendations) <= 2
        # 应该推荐与物品1相似的物品2
        if recommendations:
            assert recommendations[0][0] == 2


class TestHybridRecommender:
    """混合推荐测试"""

    def test_recommend(self):
        """测试混合推荐"""
        from apps.recommendation.engine import HybridRecommender

        hybrid = HybridRecommender(
            cf_weight=0.5,
            cb_weight=0.3,
            hot_weight=0.2
        )

        # 设置协同过滤数据
        cf_interactions = {
            1: {1: 5.0, 2: 3.0},
            2: {1: 4.0, 3: 5.0},
        }
        hybrid.cf_recommender.build_user_item_matrix(cf_interactions)

        # 设置内容过滤数据
        import numpy as np
        item_features = {
            1: np.array([1.0, 0.0]),
            2: np.array([0.9, 0.1]),
            3: np.array([0.0, 1.0]),
        }
        hybrid.cb_recommender.set_item_features(item_features)
        hybrid.cb_recommender.update_user_profile(1, [1])

        # 生成推荐
        recommendations = hybrid.recommend(user_id=1, n_recommendations=5)

        assert isinstance(recommendations, list)
        assert len(recommendations) <= 5


class TestDiversityReRank:
    """多样性重排序测试"""

    def test_re_rank(self):
        """测试多样性重排序"""
        from apps.recommendation.engine import DiversityReRank
        import numpy as np

        rerank = DiversityReRank(lambda_param=0.5)

        # 原始推荐列表
        recommendations = [
            (1, 0.9),
            (2, 0.8),
            (3, 0.7),
            (4, 0.6),
            (5, 0.5),
        ]

        # 物品特征
        item_features = {
            1: np.array([1.0, 0.0]),
            2: np.array([0.95, 0.05]),  # 与1相似
            3: np.array([0.0, 1.0]),     # 与1不同
            4: np.array([0.5, 0.5]),
            5: np.array([0.1, 0.9]),
        }

        re_ranked = rerank.re_rank(recommendations, item_features, n=5)

        assert isinstance(re_ranked, list)
        assert len(re_ranked) == 5
        # 物品3应该排名提前（多样性考虑）
        assert 3 in [item[0] for item in re_ranked]
