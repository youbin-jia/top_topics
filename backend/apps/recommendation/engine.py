"""
推荐引擎核心算法
"""
from typing import List, Dict, Tuple
import numpy as np
from collections import defaultdict
from django.contrib.auth import get_user_model

User = get_user_model()


class CollaborativeFiltering:
    """协同过滤推荐"""

    def __init__(self):
        self.user_item_matrix = None
        self.item_similarity = None
        self.users = []
        self.items = []

    def build_user_item_matrix(self, interactions: Dict):
        """
        构建用户-物品矩阵

        Args:
            interactions: {user_id: {item_id: rating}}
        """
        # 收集所有用户和物品
        self.users = list(interactions.keys())
        self.items = set()
        for user_items in interactions.values():
            self.items.update(user_items.keys())
        self.items = list(self.items)

        # 构建矩阵
        n_users = len(self.users)
        n_items = len(self.items)

        self.user_item_matrix = np.zeros((n_users, n_items))

        for user_id, user_items in interactions.items():
            user_idx = self.users.index(user_id)
            for item_id, rating in user_items.items():
                item_idx = self.items.index(item_id)
                self.user_item_matrix[user_idx][item_idx] = rating

        # 计算物品相似度
        from sklearn.metrics.pairwise import cosine_similarity
        self.item_similarity = cosine_similarity(self.user_item_matrix.T)

    def recommend(
        self,
        user_id: int,
        n_recommendations: int = 10,
        exclude_items: List[int] = None
    ) -> List[Tuple[int, float]]:
        """
        生成推荐

        Args:
            user_id: 用户ID
            n_recommendations: 推荐数量
            exclude_items: 排除物品列表

        Returns:
            [(物品ID, 推荐分数)] 列表
        """
        if user_id not in self.users:
            return []

        user_idx = self.users.index(user_id)
        user_vector = self.user_item_matrix[user_idx]

        # 计算推荐分数
        scores = user_vector.dot(self.item_similarity)

        # 排除已交互物品
        if exclude_items:
            for item_id in exclude_items:
                if item_id in self.items:
                    item_idx = self.items.index(item_id)
                    scores[item_idx] = -np.inf

        # 排除已评分物品
        for i, rating in enumerate(user_vector):
            if rating > 0:
                scores[i] = -np.inf

        # 返回Top-N
        top_indices = np.argsort(scores)[-n_recommendations:][::-1]

        return [
            (self.items[idx], scores[idx])
            for idx in top_indices
            if scores[idx] > 0
        ]


class ContentBasedFiltering:
    """基于内容的推荐"""

    def __init__(self):
        self.item_features = {}
        self.user_profiles = {}

    def set_item_features(self, item_features: Dict):
        """
        设置物品特征

        Args:
            item_features: {item_id: feature_vector}
        """
        self.item_features = item_features

    def update_user_profile(self, user_id: int, liked_items: List[int]):
        """
        更新用户画像

        Args:
            user_id: 用户ID
            liked_items: 用户喜欢的物品列表
        """
        if not liked_items:
            self.user_profiles[user_id] = np.zeros_like(
                list(self.item_features.values())[0]
            )
            return

        # 计算用户特征向量（平均）
        feature_vectors = [
            self.item_features[item_id]
            for item_id in liked_items
            if item_id in self.item_features
        ]

        if feature_vectors:
            self.user_profiles[user_id] = np.mean(feature_vectors, axis=0)
        else:
            self.user_profiles[user_id] = np.zeros_like(
                list(self.item_features.values())[0]
            )

    def recommend(
        self,
        user_id: int,
        n_recommendations: int = 10,
        exclude_items: List[int] = None
    ) -> List[Tuple[int, float]]:
        """
        生成推荐

        Args:
            user_id: 用户ID
            n_recommendations: 推荐数量
            exclude_items: 排除物品列表

        Returns:
            [(物品ID, 相似度分数)] 列表
        """
        if user_id not in self.user_profiles:
            return []

        user_profile = self.user_profiles[user_id]

        # 计算用户与所有物品的相似度
        similarities = []
        for item_id, item_feature in self.item_features.items():
            if exclude_items and item_id in exclude_items:
                continue

            similarity = self._cosine_similarity(user_profile, item_feature)
            similarities.append((item_id, similarity))

        # 排序返回Top-N
        similarities.sort(key=lambda x: x[1], reverse=True)

        return similarities[:n_recommendations]

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)


class HybridRecommender:
    """混合推荐器"""

    def __init__(
        self,
        cf_weight: float = 0.5,
        cb_weight: float = 0.3,
        hot_weight: float = 0.2
    ):
        self.cf_weight = cf_weight
        self.cb_weight = cb_weight
        self.hot_weight = hot_weight

        self.cf_recommender = CollaborativeFiltering()
        self.cb_recommender = ContentBasedFiltering()

    def recommend(
        self,
        user_id: int,
        n_recommendations: int = 20,
        exclude_items: List[int] = None
    ) -> List[Tuple[int, float]]:
        """
        混合推荐

        Args:
            user_id: 用户ID
            n_recommendations: 推荐数量
            exclude_items: 排除物品列表

        Returns:
            [(物品ID, 混合分数)] 列表
        """
        # 1. 协同过滤推荐
        cf_recommendations = self.cf_recommender.recommend(
            user_id,
            n_recommendations=n_recommendations * 2,
            exclude_items=exclude_items
        )
        cf_scores = {item_id: score for item_id, score in cf_recommendations}

        # 2. 基于内容推荐
        cb_recommendations = self.cb_recommender.recommend(
            user_id,
            n_recommendations=n_recommendations * 2,
            exclude_items=exclude_items
        )
        cb_scores = {item_id: score for item_id, score in cb_recommendations}

        # 3. 热门推荐
        hot_recommendations = self._get_hot_items(n_recommendations * 2)
        hot_scores = {item_id: score for item_id, score in hot_recommendations}

        # 4. 合并分数
        all_items = set(cf_scores.keys()) | set(cb_scores.keys()) | set(hot_scores.keys())

        hybrid_scores = []
        for item_id in all_items:
            cf_score = cf_scores.get(item_id, 0)
            cb_score = cb_scores.get(item_id, 0)
            hot_score = hot_scores.get(item_id, 0)

            # 加权平均
            hybrid_score = (
                self.cf_weight * cf_score +
                self.cb_weight * cb_score +
                self.hot_weight * hot_score
            )

            hybrid_scores.append((item_id, hybrid_score))

        # 5. 排序返回
        hybrid_scores.sort(key=lambda x: x[1], reverse=True)

        return hybrid_scores[:n_recommendations]

    def _get_hot_items(self, n: int) -> List[Tuple[int, float]]:
        """获取热门物品"""
        from apps.topic_analysis.models import Topic

        hot_topics = Topic.objects.filter(
            status__in=['active', 'trending']
        ).order_by('-heat_score')[:n]

        return [(topic.id, topic.heat_score) for topic in hot_topics]


class DiversityReRank:
    """多样性重排序"""

    def __init__(self, lambda_param: float = 0.5):
        """
        Args:
            lambda_param: 多样性参数 (0-1)，越大多样性越高
        """
        self.lambda_param = lambda_param

    def re_rank(
        self,
        recommendations: List[Tuple[int, float]],
        item_features: Dict,
        n: int = None
    ) -> List[Tuple[int, float]]:
        """
        多样性重排序

        Args:
            recommendations: 原始推荐列表
            item_features: 物品特征
            n: 返回数量

        Returns:
            重排序后的推荐列表
        """
        if n is None:
            n = len(recommendations)

        selected = []
        remaining = list(recommendations)

        while len(selected) < n and remaining:
            best_score = -np.inf
            best_item = None
            best_idx = -1

            for idx, (item_id, relevance) in enumerate(remaining):
                # 相关性分数
                relevance_score = relevance

                # 多样性分数
                if selected:
                    selected_features = [
                        item_features[i]
                        for i, _ in selected
                        if i in item_features
                    ]
                    if selected_features and item_id in item_features:
                        # 计算与已选物品的平均相似度
                        item_feature = item_features[item_id]
                        similarities = [
                            self._cosine_similarity(item_feature, sf)
                            for sf in selected_features
                        ]
                        diversity_score = 1 - np.mean(similarities)
                    else:
                        diversity_score = 1
                else:
                    diversity_score = 1

                # 综合分数
                score = (
                    (1 - self.lambda_param) * relevance_score +
                    self.lambda_param * diversity_score
                )

                if score > best_score:
                    best_score = score
                    best_item = (item_id, relevance)
                    best_idx = idx

            if best_item:
                selected.append(best_item)
                remaining.pop(best_idx)

        return selected

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """计算余弦相似度"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return dot_product / (norm1 * norm2)
