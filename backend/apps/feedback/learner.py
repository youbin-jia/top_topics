"""
反馈学习和自适应调整
"""
from typing import Dict, List
from django.contrib.auth import get_user_model

User = get_user_model()


class AdaptiveLearner:
    """自适应学习器"""

    # 反馈权重配置
    FEEDBACK_WEIGHTS = {
        'click': 1.0,
        'like': 2.0,
        'share': 3.0,
        'collect': 2.5,
        'skip': -1.0,
        'report': -5.0,
    }

    def __init__(self, learning_rate: float = 0.1):
        """
        Args:
            learning_rate: 学习率
        """
        self.learning_rate = learning_rate

    def update_user_preference(
        self,
        user_id: int,
        topic_id: int,
        feedback_type: str,
        metadata: Dict = None
    ) -> float:
        """
        更新用户偏好

        Args:
            user_id: 用户ID
            topic_id: 话题ID
            feedback_type: 反馈类型
            metadata: 元数据

        Returns:
            更新后的偏好分数
        """
        from apps.recommendation.models import UserTopicPreference

        # 获取或创建用户话题偏好
        preference, created = UserTopicPreference.objects.get_or_create(
            user_id=user_id,
            topic_id=topic_id
        )

        # 获取反馈权重
        feedback_weight = self.FEEDBACK_WEIGHTS.get(feedback_type, 0)

        # 根据反馈类型更新计数
        if feedback_type == 'click':
            preference.click_count += 1
        elif feedback_type == 'like':
            preference.like_count += 1
        elif feedback_type == 'share':
            preference.share_count += 1
        elif feedback_type == 'collect':
            preference.collect_count += 1
        elif feedback_type == 'skip':
            preference.skip_count += 1

        # 计算新的偏好分数
        # 使用加权平均
        total_interactions = (
            preference.click_count +
            preference.like_count +
            preference.share_count +
            preference.collect_count
        )

        if total_interactions > 0:
            weighted_score = (
                preference.click_count * 1.0 +
                preference.like_count * 2.0 +
                preference.share_count * 3.0 +
                preference.collect_count * 2.5 -
                preference.skip_count * 1.0
            ) / total_interactions
        else:
            weighted_score = 0

        # 渐进式更新
        old_score = preference.preference_score
        new_score = old_score * (1 - self.learning_rate) + weighted_score * self.learning_rate

        preference.preference_score = new_score
        preference.save()

        return new_score

    def update_user_interests(
        self,
        user_id: int,
        keywords: List[str],
        feedback_type: str
    ):
        """
        更新用户兴趣关键词

        Args:
            user_id: 用户ID
            keywords: 关键词列表
            feedback_type: 反馈类型
        """
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return

        # 获取反馈权重
        weight = self.FEEDBACK_WEIGHTS.get(feedback_type, 0) * 0.1

        # 更新关键词兴趣
        for keyword in keywords:
            if keyword in user.keywords_interests:
                # 渐进式更新
                old_weight = user.keywords_interests[keyword]
                new_weight = old_weight * 0.8 + weight * 0.2
                user.keywords_interests[keyword] = new_weight
            else:
                user.keywords_interests[keyword] = weight

        user.save()

    def batch_update_from_feedback(
        self,
        feedbacks: List[Dict]
    ) -> Dict:
        """
        批量从反馈更新

        Args:
            feedbacks: 反馈列表

        Returns:
            更新统计
        """
        stats = {
            'updated_preferences': 0,
            'updated_interests': 0,
            'errors': 0,
        }

        for feedback in feedbacks:
            try:
                user_id = feedback['user_id']
                topic_id = feedback['topic_id']
                feedback_type = feedback['feedback_type']

                # 更新用户偏好
                self.update_user_preference(
                    user_id,
                    topic_id,
                    feedback_type
                )
                stats['updated_preferences'] += 1

                # 更新用户兴趣
                if 'keywords' in feedback:
                    self.update_user_interests(
                        user_id,
                        feedback['keywords'],
                        feedback_type
                    )
                    stats['updated_interests'] += 1

            except Exception as e:
                stats['errors'] += 1
                continue

        return stats


