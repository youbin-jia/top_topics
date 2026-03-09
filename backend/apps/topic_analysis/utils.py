"""
话题分析工具函数
"""
from typing import List, Dict, Tuple
import jieba
import jieba.analyse
from collections import Counter
import math
from datetime import datetime, timedelta


def extract_keywords(
    text: str,
    top_k: int = 10,
    method: str = 'tfidf'
) -> List[str]:
    """
    提取关键词

    Args:
        text: 文本内容
        top_k: 返回关键词数量
        method: 提取方法 ('tfidf' 或 'textrank')

    Returns:
        关键词列表
    """
    if not text or len(text.strip()) < 10:
        return []

    if method == 'tfidf':
        keywords = jieba.analyse.extract_tags(
            text,
            topK=top_k,
            withWeight=False
        )
    elif method == 'textrank':
        keywords = jieba.analyse.textrank(
            text,
            topK=top_k,
            withWeight=False
        )
    else:
        keywords = []

    return keywords


def extract_keywords_with_weights(
    text: str,
    top_k: int = 10,
    method: str = 'tfidf'
) -> List[Tuple[str, float]]:
    """
    提取关键词及其权重

    Args:
        text: 文本内容
        top_k: 返回关键词数量
        method: 提取方法

    Returns:
        (关键词, 权重) 列表
    """
    if not text or len(text.strip()) < 10:
        return []

    if method == 'tfidf':
        keywords = jieba.analyse.extract_tags(
            text,
            topK=top_k,
            withWeight=True
        )
    elif method == 'textrank':
        keywords = jieba.analyse.textrank(
            text,
            topK=top_k,
            withWeight=True
        )
    else:
        keywords = []

    return keywords


def calculate_heat_score(topic) -> float:
    """
    计算话题热度分数

    Args:
        topic: Topic对象

    Returns:
        热度分数 (0-1)
    """
    from django.utils import timezone

    # 时间衰减因子 (最近的文章权重更高)
    time_decay = calculate_time_decay(topic.last_updated_at)

    # 互动率
    if topic.article_count > 0:
        engagement_rate = topic.engagement_rate
    else:
        engagement_rate = 0

    # 文章数量归一化
    article_score = min(topic.article_count / 100, 1.0)

    # 浏览数归一化
    view_score = min(math.log10(topic.view_count + 1) / 6, 1.0)

    # 综合热度
    heat_score = (
        time_decay * 0.3 +
        engagement_rate * 0.3 +
        article_score * 0.2 +
        view_score * 0.2
    )

    return min(max(heat_score, 0.0), 1.0)


def calculate_time_decay(
    timestamp: datetime,
    half_life: int = 24
) -> float:
    """
    计算时间衰减因子

    Args:
        timestamp: 时间戳
        half_life: 半衰期（小时）

    Returns:
        衰减因子 (0-1)
    """
    from django.utils import timezone

    if not timestamp:
        return 0.0

    now = timezone.now()
    hours_elapsed = (now - timestamp).total_seconds() / 3600

    # 指数衰减
    decay = math.exp(-hours_elapsed / half_life)

    return max(min(decay, 1.0), 0.0)


def calculate_trend(topic) -> str:
    """
    计算话题趋势

    Args:
        topic: Topic对象

    Returns:
        趋势类型 ('rising', 'falling', 'stable')
    """
    from .models import TopicTrend

    # 获取最近24小时的趋势记录
    recent_trends = TopicTrend.objects.filter(
        topic=topic
    ).order_by('-recorded_at')[:24]

    if len(recent_trends) < 2:
        return 'stable'

    # 计算平均增长率
    growth_rates = [t.growth_rate for t in recent_trends]
    avg_growth = sum(growth_rates) / len(growth_rates)

    # 判断趋势
    if avg_growth > 0.1:
        return 'rising'
    elif avg_growth < -0.1:
        return 'falling'
    else:
        return 'stable'


def generate_summary(text: str, max_length: int = 200) -> str:
    """
    生成文本摘要

    Args:
        text: 原文本
        max_length: 最大长度

    Returns:
        摘要文本
    """
    if not text or len(text) <= max_length:
        return text

    # 简单实现：截取前N个字符
    # TODO: 使用更高级的摘要算法
    summary = text[:max_length]

    # 尝试在句子结束处截断
    last_period = summary.rfind('。')
    last_exclamation = summary.rfind('！')
    last_question = summary.rfind('？')

    last_sentence_end = max(last_period, last_exclamation, last_question)

    if last_sentence_end > max_length * 0.7:
        summary = summary[:last_sentence_end + 1]
    else:
        summary = summary + '...'

    return summary


def tokenize(text: str) -> List[str]:
    """
    中文分词

    Args:
        text: 文本

    Returns:
        分词列表
    """
    if not text:
        return []

    # 使用jieba分词
    tokens = jieba.cut(text, cut_all=False)

    # 过滤停用词和标点
    stop_words = set(['的', '了', '和', '是', '在', '有', '我', '他', '她', '它'])
    tokens = [
        token.strip()
        for token in tokens
        if token.strip() and token not in stop_words
    ]

    return tokens


def calculate_similarity(text1: str, text2: str) -> float:
    """
    计算文本相似度

    Args:
        text1: 文本1
        text2: 文本2

    Returns:
        相似度分数 (0-1)
    """
    # 分词
    tokens1 = set(tokenize(text1))
    tokens2 = set(tokenize(text2))

    if not tokens1 or not tokens2:
        return 0.0

    # Jaccard相似度
    intersection = len(tokens1 & tokens2)
    union = len(tokens1 | tokens2)

    similarity = intersection / union if union > 0 else 0.0

    return similarity


def find_similar_topics(
    keywords: List[str],
    threshold: float = 0.3,
    limit: int = 10
) -> List:
    """
    查找相似话题

    Args:
        keywords: 关键词列表
        threshold: 相似度阈值
        limit: 返回数量限制

    Returns:
        相似话题列表
    """
    from .models import Topic

    # 获取所有活跃话题
    topics = Topic.objects.filter(status__in=['active', 'trending'])

    similar_topics = []

    for topic in topics:
        # 计算关键词重叠度
        topic_keywords = set(topic.keywords)
        query_keywords = set(keywords)

        intersection = len(topic_keywords & query_keywords)
        union = len(topic_keywords | query_keywords)

        similarity = intersection / union if union > 0 else 0.0

        if similarity >= threshold:
            similar_topics.append((topic, similarity))

    # 按相似度排序
    similar_topics.sort(key=lambda x: x[1], reverse=True)

    return similar_topics[:limit]
