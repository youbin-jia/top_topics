"""
反馈学习和自适应调整
"""
from typing import Dict, List
from datetime import datetime, timedelta
from django.db.models import Count, Avg
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


class FeedbackAnalyzer:
    """反馈分析器"""

    def analyze_user_feedback_pattern(
        self,
        user_id: int,
        days: int = 7
    ) -> Dict:
        """
        分析用户反馈模式

        Args:
            user_id: 用户ID
            days: 分析天数

        Returns:
            分析结果
        """
        from .models import UserFeedback
        from django.utils import timezone

        start_date = timezone.now() - timedelta(days=days)

        feedbacks = UserFeedback.objects.filter(
            user_id=user_id,
            created_at__gte=start_date
        )

        # 统计各类型反馈数量
        feedback_counts = feedbacks.values('feedback_type').annotate(
            count=Count('id')
        )

        # 计算平均停留时间
        avg_dwell_time = feedbacks.filter(
            dwell_time__isnull=False
        ).aggregate(
            avg=Avg('dwell_time')
        )['avg'] or 0

        # 计算滚动深度
        avg_scroll_depth = feedbacks.filter(
            scroll_depth__isnull=False
        ).aggregate(
            avg=Avg('scroll_depth')
        )['avg'] or 0

        # 计算互动率
        total_feedbacks = feedbacks.count()
        positive_feedbacks = feedbacks.filter(
            feedback_type__in=['like', 'share', 'collect']
        ).count()

        engagement_rate = (
            positive_feedbacks / total_feedbacks
            if total_feedbacks > 0 else 0
        )

        return {
            'feedback_counts': {
                item['feedback_type']: item['count']
                for item in feedback_counts
            },
            'avg_dwell_time': avg_dwell_time,
            'avg_scroll_depth': avg_scroll_depth,
            'engagement_rate': engagement_rate,
            'total_feedbacks': total_feedbacks,
        }

    def analyze_topic_performance(
        self,
        topic_id: int,
        days: int = 7
    ) -> Dict:
        """
        分析话题表现

        Args:
            topic_id: 话题ID
            days: 分析天数

        Returns:
            分析结果
        """
        from .models import UserFeedback
        from django.utils import timezone

        start_date = timezone.now() - timedelta(days=days)

        feedbacks = UserFeedback.objects.filter(
            topic_id=topic_id,
            created_at__gte=start_date
        )

        # 统计各类型反馈
        feedback_stats = {}
        for feedback_type, _ in UserFeedback.FEEDBACK_TYPES:
            count = feedbacks.filter(feedback_type=feedback_type).count()
            feedback_stats[feedback_type] = count

        # 计算点击率
        impressions = feedbacks.count()
        clicks = feedbacks.filter(feedback_type='click').count()
        ctr = clicks / impressions if impressions > 0 else 0

        # 计算互动率
        positive_actions = feedbacks.filter(
            feedback_type__in=['like', 'share', 'collect']
        ).count()
        engagement_rate = positive_actions / impressions if impressions > 0 else 0

        # 计算跳过率
        skips = feedbacks.filter(feedback_type='skip').count()
        skip_rate = skips / impressions if impressions > 0 else 0

        return {
            'feedback_stats': feedback_stats,
            'ctr': ctr,
            'engagement_rate': engagement_rate,
            'skip_rate': skip_rate,
            'total_impressions': impressions,
        }

    def get_recommendation_performance(
        self,
        recommendation_type: str = None,
        days: int = 7
    ) -> Dict:
        """
        获取推荐系统性能

        Args:
            recommendation_type: 推荐类型
            days: 分析天数

        Returns:
            性能指标
        """
        from apps.recommendation.models import Recommendation
        from django.utils import timezone

        start_date = timezone.now() - timedelta(days=days)

        recommendations = Recommendation.objects.filter(
            recommended_at__gte=start_date
        )

        if recommendation_type:
            recommendations = recommendations.filter(
                recommendation_type=recommendation_type
            )

        total = recommendations.count()

        if total == 0:
            return {
                'ctr': 0,
                'engagement_rate': 0,
                'avg_score': 0,
            }

        # 点击率
        clicked = recommendations.filter(feedback='click').count()
        ctr = clicked / total

        # 互动率
        engaged = recommendations.filter(
            feedback__in=['like', 'share', 'collect']
        ).count()
        engagement_rate = engaged / total

        # 平均推荐分数
        avg_score = recommendations.aggregate(
            avg=Avg('score')
        )['avg'] or 0

        return {
            'ctr': ctr,
            'engagement_rate': engagement_rate,
            'avg_score': avg_score,
            'total_recommendations': total,
        }


class ModelRetrainer:
    """模型重训练器"""

    def should_retrain(
        self,
        model_type: str,
        threshold: float = 0.05
    ) -> bool:
        """
        判断是否需要重训练

        Args:
            model_type: 模型类型
            threshold: 性能下降阈值

        Returns:
            是否需要重训练
        """
        from .models import ModelPerformanceLog, LearningModel

        try:
            # 获取当前活跃模型
            active_model = LearningModel.objects.get(
                model_type=model_type,
                is_active=True
            )

            # 获取最近的性能日志
            recent_logs = ModelPerformanceLog.objects.filter(
                model=active_model
            ).order_by('-recorded_at')[:10]

            if len(recent_logs) < 2:
                return False

            # 比较最近和之前的性能
            recent_avg = sum(log.metric_value for log in recent_logs[:5]) / 5
            previous_avg = sum(log.metric_value for log in recent_logs[5:10]) / 5

            # 性能下降超过阈值
            if recent_avg < previous_avg * (1 - threshold):
                return True

            return False

        except LearningModel.DoesNotExist:
            return True

    def trigger_retraining(
        self,
        model_type: str,
        training_params: Dict = None
    ):
        """
        触发模型重训练

        Args:
            model_type: 模型类型
            training_params: 训练参数
        """
        from .tasks import retrain_model_task

        # 异步执行训练任务
        retrain_model_task.delay(
            model_type,
            training_params or {}
        )
