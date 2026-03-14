"""
话题分析Celery任务
"""
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import logging
import re
from collections import defaultdict

from .models import Topic, TopicTrend, ContentTopicRelation
from apps.data_collection.models import RawContent
from .llm import generate_topic_title_summary

logger = logging.getLogger(__name__)

_INVALID_KEYWORD_RE = re.compile(r"^[\W_]+$", flags=re.UNICODE)
_KEYWORD_STOPWORDS = {
    "全文", "查看", "推荐", "视频", "文章", "内容", "我们", "你们", "他们", "这个",
    "那个", "以及", "相关", "今日", "热点", "更多", "最新", "如何", "为什么",
}
_MAIN_KEYWORD_BLACKLIST = set(getattr(settings, "TOPIC_MAIN_KEYWORD_BLACKLIST", []))

_TITLE_NORMALIZE_RE = re.compile(r"[^\w\u4e00-\u9fff]+", flags=re.UNICODE)


def _normalize_keyword(keyword: str) -> str:
    text = re.sub(r"\s+", "", str(keyword or "")).strip()
    if not text:
        return ""
    if _INVALID_KEYWORD_RE.match(text):
        return ""
    return text[:40]


def _is_valid_keyword(keyword: str) -> bool:
    if not keyword or len(keyword) < 2:
        return False
    if keyword in _KEYWORD_STOPWORDS:
        return False
    if keyword in _MAIN_KEYWORD_BLACKLIST:
        return False
    return True


def _content_rank_score(content: RawContent) -> float:
    # 代表性排序：互动 + 新鲜度
    interactions = (
        (content.view_count or 0) * 0.05
        + (content.like_count or 0) * 0.5
        + (content.comment_count or 0) * 1.2
        + (content.share_count or 0) * 1.5
    )
    published = content.published_at or content.crawled_at
    if not published:
        return interactions
    age_hours = max((timezone.now() - published).total_seconds() / 3600, 0.0)
    freshness = max(0.0, 48 - age_hours) / 48
    return interactions + freshness * 10


def _build_source_items(contents, max_items=3):
    """将候选内容压缩为 LLM 输入，默认仅取最具代表性的 3 条以节省 token。"""
    ranked = sorted(contents, key=_content_rank_score, reverse=True)
    items = []
    for c in ranked[:max_items]:
        items.append(
            {
                "title": (c.title or "")[:80],
                "summary": (c.summary or c.content or "")[:140],
                "url": c.url,
            }
        )
    return items


def _normalize_topic_title(title: str, fallback_keyword: str) -> str:
    """清洗并规范标题，避免空标题/异常字符。"""
    cleaned = re.sub(r"\s+", " ", (title or "")).strip().strip("“”\"'")
    cleaned = re.sub(r"[\\r\\n\\t]+", " ", cleaned).strip()
    if len(cleaned) > 80:
        cleaned = cleaned[:80]
    if len(cleaned) < 8:
        cleaned = f"{fallback_keyword}：最新进展与核心看点"
    return cleaned


def _build_topic_keywords(main_keyword: str, contents, max_items=12):
    """聚合关键词，保留检索能力。"""
    merged = [main_keyword]
    for c in contents:
        for kw in (c.keywords or []):
            kw = str(kw).strip()
            if kw and kw not in merged:
                merged.append(kw)
            if len(merged) >= max_items:
                return merged
    return merged[:max_items]


def _normalize_title_key(title: str) -> str:
    """
    将标题标准化为“去符号+小写”的 key，用于近重复判定。
    """
    if not title:
        return ""
    text = re.sub(r"#\d+$", "", title.strip())
    text = _TITLE_NORMALIZE_RE.sub("", text).lower()
    return text[:80]


def _build_existing_title_keys() -> set:
    keys = set()
    for name in Topic.objects.values_list("name", flat=True):
        key = _normalize_title_key(name)
        if key:
            keys.add(key)
    return keys


def _collect_keyword_candidates(contents, threshold=1):
    keyword_freq = defaultdict(int)
    keyword_contents = defaultdict(list)

    for content in contents:
        seen = set()
        for raw_kw in (content.keywords or []):
            kw = _normalize_keyword(raw_kw)
            if not _is_valid_keyword(kw) or kw in seen:
                continue
            seen.add(kw)
            keyword_freq[kw] += 1
            keyword_contents[kw].append(content)

    candidates = []
    for keyword, freq in keyword_freq.items():
        if freq < threshold:
            continue
        if Topic.objects.filter(main_keyword=keyword).exists():
            continue
        related_contents = keyword_contents[keyword]
        content_ids = {c.id for c in related_contents}
        source_ids = {c.source_id for c in related_contents}
        recent_count = sum(
            1 for c in related_contents
            if c.crawled_at and c.crawled_at >= timezone.now() - timedelta(hours=24)
        )
        candidates.append(
            {
                "keyword": keyword,
                "contents": related_contents,
                "content_ids": content_ids,
                "article_count": len(content_ids),
                "freq": freq,
                "recent_count": recent_count,
                "source_diversity": len(source_ids),
                "cluster_keywords": [keyword],
            }
        )
    return candidates


def _jaccard(set1, set2) -> float:
    if not set1 or not set2:
        return 0.0
    union = len(set1 | set2)
    if union == 0:
        return 0.0
    return len(set1 & set2) / union


def _cluster_candidates(candidates, overlap_threshold=0.35):
    if not candidates:
        return []
    ranked = sorted(candidates, key=lambda c: (c["article_count"], c["freq"]), reverse=True)
    used = set()
    clusters = []

    for i, candidate in enumerate(ranked):
        if i in used:
            continue
        used.add(i)
        cluster_members = [candidate]

        for j in range(i + 1, len(ranked)):
            if j in used:
                continue
            other = ranked[j]
            if _jaccard(candidate["content_ids"], other["content_ids"]) >= overlap_threshold:
                used.add(j)
                cluster_members.append(other)

        merged_map = {}
        for member in cluster_members:
            for content in member["contents"]:
                merged_map[content.id] = content
        merged_contents = list(merged_map.values())
        representative = sorted(
            cluster_members,
            key=lambda c: (c["article_count"], c["source_diversity"], c["freq"]),
            reverse=True,
        )[0]

        source_ids = {c.source_id for c in merged_contents}
        recent_count = sum(
            1 for c in merged_contents
            if c.crawled_at and c.crawled_at >= timezone.now() - timedelta(hours=24)
        )
        cluster_keywords = []
        for member in cluster_members:
            for kw in member["cluster_keywords"]:
                if kw not in cluster_keywords:
                    cluster_keywords.append(kw)

        clusters.append(
            {
                "keyword": representative["keyword"],
                "contents": merged_contents,
                "content_ids": {c.id for c in merged_contents},
                "article_count": len(merged_contents),
                "freq": sum(m["freq"] for m in cluster_members),
                "recent_count": recent_count,
                "source_diversity": len(source_ids),
                "cluster_keywords": cluster_keywords[:12],
            }
        )
    return clusters


def _rank_candidates(candidates):
    ranked = []
    for c in candidates:
        c["base_score"] = (
            c["article_count"] * 0.55
            + c["recent_count"] * 0.25
            + c["source_diversity"] * 0.20
        )
        c["score"] = c["base_score"]
        ranked.append(c)
    return sorted(ranked, key=lambda x: (x["score"], x["freq"]), reverse=True)


def _candidate_primary_source(c: dict) -> str:
    counter = defaultdict(int)
    for content in c.get("contents", []):
        source_type = getattr(getattr(content, "source", None), "source_type", "") or "unknown"
        counter[source_type] += 1
    if not counter:
        return "unknown"
    return max(counter.items(), key=lambda it: it[1])[0]


def _select_diverse_topn(candidates, top_n):
    """
    基于同源惩罚的贪心选择，降低 TopN 中单一来源过度集中。
    """
    if top_n is None or top_n <= 0 or len(candidates) <= top_n:
        return list(candidates)

    source_penalty = float(getattr(settings, "TOPIC_SOURCE_PENALTY", 0.35))
    selected = []
    selected_source_counts = defaultdict(int)
    pool = list(candidates)

    for _ in range(min(top_n, len(pool))):
        best_idx = None
        best_score = None

        for idx, candidate in enumerate(pool):
            source_type = _candidate_primary_source(candidate)
            penalty = selected_source_counts[source_type] * source_penalty
            adjusted_score = candidate.get("base_score", candidate.get("score", 0.0)) - penalty
            if best_score is None or adjusted_score > best_score:
                best_score = adjusted_score
                best_idx = idx

        chosen = pool.pop(best_idx)
        chosen["score"] = best_score if best_score is not None else chosen.get("score", 0.0)
        selected.append(chosen)
        selected_source_counts[_candidate_primary_source(chosen)] += 1

    return selected


def _ensure_unique_topic_title(title: str, existing_title_keys=None) -> str:
    """标题去重，避免 unique 冲突。"""
    existing_title_keys = existing_title_keys or set()
    title_key = _normalize_title_key(title)
    if (
        title_key
        and title_key not in existing_title_keys
        and not Topic.objects.filter(name=title).exists()
    ):
        existing_title_keys.add(title_key)
        return title

    base = title
    base_key = _normalize_title_key(base)
    idx = 2
    while True:
        candidate = f"{base} #{idx}"
        candidate_key = _normalize_title_key(candidate)
        if (
            candidate_key
            and candidate_key not in existing_title_keys
            and not Topic.objects.filter(name=candidate).exists()
        ):
            existing_title_keys.add(candidate_key)
            return candidate
        if base_key and base_key not in existing_title_keys and idx > 99:
            # 极端情况下 fallback：强制注入时间戳片段避免长循环
            fallback = f"{base} {int(timezone.now().timestamp()) % 100000}"
            fallback_key = _normalize_title_key(fallback)
            if fallback_key:
                existing_title_keys.add(fallback_key)
            return fallback[:80]
        idx += 1


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
def discover_new_topics(threshold=None, hours=24, top_n=10, cluster_first=True):
    """
    发现新话题：从已处理内容中聚合关键词，创建话题。
    threshold: 关键词出现次数阈值，默认 1（数据少时也能发现话题）；数据多时可传 2 或 5。
    hours: 只统计最近 N 小时的内容，默认 24；传 None 表示不限制时间。
    top_n: 聚类排序后仅保留前 N 个候选调用 LLM，默认 10。
    cluster_first: 是否先聚类再排序，默认开启。
    """
    threshold = threshold if threshold is not None else 1
    qs = RawContent.objects.filter(status='processed').exclude(keywords=[]).select_related('source')
    if hours is not None:
        qs = qs.filter(crawled_at__gte=timezone.now() - timedelta(hours=hours))
    recent_contents = list(qs)
    candidates = _collect_keyword_candidates(recent_contents, threshold=threshold)
    if cluster_first:
        candidates = _cluster_candidates(candidates)
    ranked_candidates = _rank_candidates(candidates)

    selected_candidates = _select_diverse_topn(ranked_candidates, top_n)

    new_topics = []
    llm_calls = 0
    existing_title_keys = _build_existing_title_keys()
    selected_source_distribution = defaultdict(int)

    for candidate in selected_candidates:
        keyword = candidate["keyword"]
        contents = candidate["contents"]
        source_items = _build_source_items(contents)
        llm_calls += 1
        llm_result = generate_topic_title_summary(keyword, source_items)
        topic_title = _normalize_topic_title(llm_result.get("title", ""), keyword)
        topic_title = _ensure_unique_topic_title(topic_title, existing_title_keys=existing_title_keys)
        topic_summary = (llm_result.get("summary", "") or "").strip()[:500]
        topic_keywords = _build_topic_keywords(keyword, contents, max_items=12)
        for kw in candidate.get("cluster_keywords", []):
            kw = _normalize_keyword(kw)
            if kw and kw not in topic_keywords and len(topic_keywords) < 12:
                topic_keywords.append(kw)

        selected_source_distribution[_candidate_primary_source(candidate)] += 1

        topic = Topic.objects.create(
            name=topic_title,
            main_keyword=keyword,
            keywords=topic_keywords,
            description=topic_summary or None,
            article_count=candidate["article_count"],
            status='active'
        )

        # 关联内容
        for content in contents:
            ContentTopicRelation.objects.get_or_create(
                content=content,
                topic=topic,
                defaults={"relevance_score": 1.0},
            )

        new_topics.append(topic.id)

    logger.info(
        "发现新话题: %s (候选=%s, 入围=%s, LLM=%s, cluster_first=%s)",
        len(new_topics),
        len(candidates),
        len(selected_candidates),
        llm_calls,
        cluster_first,
    )
    logger.info("TopN 来源分布: %s", dict(selected_source_distribution))

    return {
        'new_topics': new_topics,
        'candidate_count': len(candidates),
        'selected_count': len(selected_candidates),
        'llm_calls': llm_calls,
    }


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
