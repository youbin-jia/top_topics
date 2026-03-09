"""
话题分析Celery任务
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

from .models import Topic, TopicTrend, ContentTopicRelation
from apps.data_collection.models import RawContent

logger = logging.getLogger(__name__)


@shared_task
def analyze_content_topic_task(content_id: int):
    """
    分析内容话题任务

    Args:
        content_id: 内容ID
    """
    try:
        content = RawContent.objects.get(id=content_id)

        logger.info(f"开始分析内容话题: {content.id}")

        # 提取关键词
        from .utils import extract_keywords
        if not content.keywords:
            content.keywords = extract_keywords(content.content, top_k=15)
            content.save()

        # 识别话题
        topics = identify_topics(content.keywords)

        # 创建内容-话题关联
        for topic, relevance in topics:
            ContentTopicRelation.objects.get_or_create(
                content=content,
                topic=topic,
                defaults={'relevance_score': relevance}
            )

        logger.info(f"内容话题分析完成: {content.id}, 关联话题数: {len(topics)}")

        return {
            'content_id': content_id,
            'topics_count': len(topics)
        }

    except RawContent.DoesNotExist:
        logger.error(f"内容不存在: {content_id}")
        return None
    except Exception as e:
        logger.error(f"话题分析失败: {e}")
        raise


@shared_task
def update_topic_heat_scores():
    """
    更新所有话题热度分数
    """
    topics = Topic.objects.all()

    updated_count = 0
    for topic in topics:
        try:
            # 计算热度
            topic.update_heat_score()

            # 计算趋势
            from .utils import calculate_trend
            topic.trend = calculate_trend(topic)

            topic.save()
            updated_count += 1

        except Exception as e:
            logger.error(f"更新话题热度失败 {topic.id}: {e}")

    logger.info(f"话题热度更新完成: {updated_count}/{topics.count()}")

    return {'updated_count': updated_count}


@shared_task
def record_topic_trends():
    """
    记录话题趋势快照
    """
    topics = Topic.objects.filter(status__in=['active', 'trending'])

    recorded_count = 0
    for topic in topics:
        try:
            # 计算增长率
            growth_rate = calculate_growth_rate(topic)

            # 创建趋势记录
            TopicTrend.objects.create(
                topic=topic,
                recorded_at=timezone.now(),
                heat_score=topic.heat_score,
                article_count=topic.article_count,
                view_count=topic.view_count,
                engagement_rate=topic.engagement_rate,
                growth_rate=growth_rate
            )

            recorded_count += 1

        except Exception as e:
            logger.error(f"记录话题趋势失败 {topic.id}: {e}")

    logger.info(f"话题趋势记录完成: {recorded_count}")

    return {'recorded_count': recorded_count}


@shared_task
def discover_new_topics():
    """
    发现新话题
    """
    # 获取最近24小时的未处理内容
    recent_contents = RawContent.objects.filter(
        status='processed',
        crawled_at__gte=timezone.now() - timedelta(hours=24)
    ).exclude(keywords=[])

    # 聚合关键词
    keyword_freq = {}
    keyword_contents = {}

    for content in recent_contents:
        for keyword in content.keywords:
            if keyword not in keyword_freq:
                keyword_freq[keyword] = 0
                keyword_contents[keyword] = []

            keyword_freq[keyword] += 1
            keyword_contents[keyword].append(content)

    # 筛选高频关键词
    new_topics = []
    threshold = 5  # 出现5次以上视为潜在话题

    for keyword, freq in keyword_freq.items():
        if freq >= threshold:
            # 检查话题是否已存在
            if not Topic.objects.filter(name=keyword).exists():
                # 创建新话题
                topic = Topic.objects.create(
                    name=keyword,
                    main_keyword=keyword,
                    keywords=[keyword],
                    article_count=freq,
                    status='active'
                )

                # 关联内容
                for content in keyword_contents[keyword]:
                    ContentTopicRelation.objects.create(
                        content=content,
                        topic=topic,
                        relevance_score=1.0
                    )

                new_topics.append(topic.id)

    logger.info(f"发现新话题: {len(new_topics)}")

    return {'new_topics': new_topics}


@shared_task
def cluster_similar_topics():
    """
    聚类相似话题
    """
    from .models import TopicCluster
    from sklearn.cluster import DBSCAN
    import numpy as np

    # 获取所有活跃话题
    topics = list(Topic.objects.filter(status__in=['active', 'trending']))

    if len(topics) < 2:
        return {'clusters': 0}

    # 构建话题相似度矩阵
    n_topics = len(topics)
    similarity_matrix = np.zeros((n_topics, n_topics))

    for i, topic1 in enumerate(topics):
        for j, topic2 in enumerate(topics):
            if i == j:
                similarity_matrix[i][j] = 1.0
            else:
                # 计算关键词相似度
                keywords1 = set(topic1.keywords)
                keywords2 = set(topic2.keywords)

                if keywords1 and keywords2:
                    intersection = len(keywords1 & keywords2)
                    union = len(keywords1 | keywords2)
                    similarity_matrix[i][j] = intersection / union

    # 使用DBSCAN聚类
    clustering = DBSCAN(
        eps=0.3,
        min_samples=2,
        metric='precomputed'
    ).fit(1 - similarity_matrix)

    # 创建聚类
    labels = clustering.labels_
    cluster_dict = {}

    for topic, label in zip(topics, labels):
        if label == -1:  # 噪声点
            continue

        if label not in cluster_dict:
            cluster_dict[label] = []

        cluster_dict[label].append(topic)

    # 保存聚类结果
    cluster_count = 0
    for label, cluster_topics in cluster_dict.items():
        if len(cluster_topics) < 2:
            continue

        # 创建聚类
        cluster = TopicCluster.objects.create(
            name=f"聚类-{cluster_count}",
            coherence_score=calculate_cluster_coherence(cluster_topics)
        )
        cluster.topics.set(cluster_topics)
        cluster.save()

        cluster_count += 1

    logger.info(f"话题聚类完成: 创建 {cluster_count} 个聚类")

    return {'clusters': cluster_count}


def identify_topics(keywords: list):
    """
    识别内容所属话题

    Args:
        keywords: 关键词列表

    Returns:
        [(话题, 相关性分数)] 列表
    """
    from .utils import find_similar_topics

    # 查找相似话题
    similar_topics = find_similar_topics(keywords, threshold=0.2, limit=5)

    return similar_topics


def calculate_growth_rate(topic) -> float:
    """
    计算话题增长率

    Args:
        topic: Topic对象

    Returns:
        增长率
    """
    # 获取最近的趋势记录
    recent_trends = TopicTrend.objects.filter(
        topic=topic
    ).order_by('-recorded_at')[:2]

    if len(recent_trends) < 2:
        return 0.0

    current = recent_trends[0].heat_score
    previous = recent_trends[1].heat_score

    if previous == 0:
        return 0.0

    growth_rate = (current - previous) / previous

    return growth_rate


def calculate_cluster_coherence(topics: list) -> float:
    """
    计算聚类一致性分数

    Args:
        topics: 话题列表

    Returns:
        一致性分数
    """
    if len(topics) < 2:
        return 0.0

    # 计算所有话题关键词的平均重叠度
    total_overlap = 0
    count = 0

    for i, topic1 in enumerate(topics):
        for topic2 in topics[i+1:]:
            keywords1 = set(topic1.keywords)
            keywords2 = set(topic2.keywords)

            if keywords1 and keywords2:
                intersection = len(keywords1 & keywords2)
                union = len(keywords1 | keywords2)
                overlap = intersection / union

                total_overlap += overlap
                count += 1

    return total_overlap / count if count > 0 else 0.0
