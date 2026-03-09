# AI自媒体自动选题系统 - 模块开发指南

本文档提供各模块的详细开发和集成指南。

## 模块概览

系统包含以下核心模块：

1. **数据收集模块** (data_collection) - 多源数据采集
2. **话题分析模块** (topic_analysis) - 热点识别和趋势预测
3. **推荐引擎模块** (recommendation) - 个性化选题推荐
4. **内容生成模块** (content_generation) - AI辅助创作
5. **反馈学习模块** (feedback) - 自适应优化

---

## 1. 数据收集模块

### 职责

从多个数据源自动采集内容数据，包括新闻网站、社交媒体、内容平台等。

### 核心组件

#### 1.1 BaseCrawler (基础爬虫)

所有爬虫的抽象基类，提供统一的接口和公共功能。

```python
from apps.data_collection.crawlers.base import BaseCrawler

class CustomCrawler(BaseCrawler):
    def crawl(self, *args, **kwargs) -> List[Dict]:
        """实现具体的爬取逻辑"""
        pass

    def parse(self, html: str, **kwargs) -> Dict:
        """实现具体的解析逻辑"""
        pass
```

#### 1.2 数据源管理

```python
from apps.data_collection.models import DataSource

# 创建数据源
source = DataSource.objects.create(
    name='微博热搜',
    source_type='weibo',
    base_url='https://weibo.com',
    config={
        'delay': 2.0,
        'pages': 5,
        'selectors': {
            'title': '.title',
            'content': '.content',
        }
    }
)

# 触发爬取
from apps.data_collection.tasks import crawl_source_task
crawl_source_task.delay(source.id)
```

### 数据流程

```
爬虫任务启动 → HTTP请求 → HTML解析 → 数据清洗 → 去重检查 → 存储到数据库
```

### 开发新爬虫

1. 继承 `BaseCrawler` 类
2. 实现 `crawl()` 和 `parse()` 方法
3. 注册到爬虫工厂
4. 配置数据源

### 定时任务配置

```python
# config/celery.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    'crawl-every-hour': {
        'task': 'apps.data_collection.tasks.daily_crawl_all_sources',
        'schedule': crontab(minute=0),  # 每小时执行
    },
}
```

---

## 2. 话题分析模块

### 职责

识别热门话题、分析趋势、主题建模。

### 核心算法

#### 2.1 关键词提取

```python
from apps.topic_analysis.utils import extract_keywords, extract_keywords_with_weights

# TF-IDF方法
keywords = extract_keywords(text, top_k=10, method='tfidf')

# TextRank方法
keywords = extract_keywords(text, top_k=10, method='textrank')

# 带权重
keywords_with_weights = extract_keywords_with_weights(text, top_k=10)
```

#### 2.2 主题建模

```python
from apps.topic_analysis.ml_engine import TopicModeler

# 训练模型
modeler = TopicModeler(num_topics=20)
modeler.train(documents)

# 获取文档主题
topics = modeler.get_topics(document)
```

#### 2.3 热度计算

```python
from apps.topic_analysis.utils import calculate_heat_score

# 计算话题热度
heat_score = calculate_heat_score(topic)

# 热度分数 = 时间衰减 * 0.3 + 互动率 * 0.3 + 文章数 * 0.2 + 浏览数 * 0.2
```

#### 2.4 趋势预测

```python
from apps.topic_analysis.tasks import record_topic_trends, calculate_growth_rate

# 记录趋势快照
record_topic_trends.delay()

# 计算增长率
growth_rate = calculate_growth_rate(topic)
```

### API端点

```bash
# 获取热门话题
GET /api/v1/topics/hot/

# 获取趋势话题
GET /api/v1/topics/trending/

# 搜索话题
GET /api/v1/topics/?search=AI&min_score=0.5
```

---

## 3. 推荐引擎模块

### 职责

生成个性化选题推荐。

### 推荐策略

#### 3.1 协同过滤

```python
from apps.recommendation.engine import CollaborativeFiltering

cf = CollaborativeFiltering()

# 构建用户-物品矩阵
cf.build_user_item_matrix(interactions)

# 生成推荐
recommendations = cf.recommend(user_id=1, n_recommendations=10)
```

#### 3.2 基于内容

```python
from apps.recommendation.engine import ContentBasedFiltering

cb = ContentBasedFiltering()

# 设置物品特征
cb.set_item_features(item_features)

# 更新用户画像
cb.update_user_profile(user_id=1, liked_items=[1, 2, 3])

# 生成推荐
recommendations = cb.recommend(user_id=1, n_recommendations=10)
```

#### 3.3 混合推荐

```python
from apps.recommendation.engine import HybridRecommender

hybrid = HybridRecommender(
    cf_weight=0.5,
    cb_weight=0.3,
    hot_weight=0.2
)

# 生成推荐
recommendations = hybrid.recommend(user_id=1, n_recommendations=20)
```

#### 3.4 多样性重排序

```python
from apps.recommendation.engine import DiversityReRank

rerank = DiversityReRank(lambda_param=0.5)

# 重排序
re_ranked = rerank.re_rank(recommendations, item_features, n=20)
```

### 实时更新

```python
# 监听用户反馈
from apps.recommendation.models import Recommendation

# 更新推荐记录
Recommendation.objects.filter(
    user=user,
    topic_id=topic_id
).update(feedback='like', feedback_at=timezone.now())
```

---

## 4. 内容生成模块

### 职责

AI辅助生成标题、大纲等创作内容。

### 核心功能

#### 4.1 标题生成

```python
from apps.content_generation.generators import TitleGenerator

generator = TitleGenerator()

# 生成标题
titles = generator.generate(
    keywords=['人工智能', '深度学习'],
    category='news',
    n_titles=5
)

# 返回示例：
# [
#   {'title': '人工智能的最新进展', 'quality_score': 0.85},
#   {'title': '深度学习：改变世界的力量', 'quality_score': 0.78},
#   ...
# ]
```

#### 4.2 大纲生成

```python
from apps.content_generation.generators import OutlineGenerator

generator = OutlineGenerator()

# 生成大纲
outline = generator.generate(
    topic='人工智能的发展',
    keywords=['AI', '机器学习', '深度学习'],
    style='informative',
    n_sections=4
)

# 返回示例：
# {
#   'title': '人工智能的发展',
#   'introduction': {...},
#   'sections': [
#     {'title': '背景介绍', 'key_points': [...]},
#     {'title': '核心技术', 'key_points': [...]},
#     ...
#   ],
#   'conclusion': {...}
# }
```

#### 4.3 质量评分

```python
from apps.content_generation.generators import ContentQualityScorer

scorer = ContentQualityScorer()

# 标题质量评分
title_score = scorer.score_title('人工智能的最新进展')

# 大纲质量评分
outline_score = scorer.score_outline(outline)
```

### 模板管理

```python
from apps.content_generation.models import TitleTemplate

# 创建标题模板
template = TitleTemplate.objects.create(
    name='震惊类标题',
    category='shock',
    template='震惊！关于{keyword}的{num}个真相',
    example='震惊！关于AI的10个真相'
)

# 使用模板
title = template.render(keyword='人工智能', num=5)
```

---

## 5. 反馈学习模块

### 职责

收集用户反馈，自适应优化推荐算法。

### 核心组件

#### 5.1 反馈收集

```python
from apps.feedback.models import UserFeedback

# 创建反馈
feedback = UserFeedback.objects.create(
    user=user,
    topic_id=topic_id,
    feedback_type='like',
    dwell_time=30,  # 停留时间
    scroll_depth=0.8,  # 滚动深度
)
```

#### 5.2 自适应学习

```python
from apps.feedback.learner import AdaptiveLearner

learner = AdaptiveLearner(learning_rate=0.1)

# 更新用户偏好
new_score = learner.update_user_preference(
    user_id=user_id,
    topic_id=topic_id,
    feedback_type='like'
)

# 更新用户兴趣关键词
learner.update_user_interests(
    user_id=user_id,
    keywords=['AI', '机器学习'],
    feedback_type='like'
)
```

#### 5.3 反馈分析

```python
from apps.feedback.learner import FeedbackAnalyzer

analyzer = FeedbackAnalyzer()

# 分析用户反馈模式
user_pattern = analyzer.analyze_user_feedback_pattern(
    user_id=user_id,
    days=7
)

# 分析话题表现
topic_performance = analyzer.analyze_topic_performance(
    topic_id=topic_id,
    days=7
)

# 获取推荐系统性能
system_performance = analyzer.get_recommendation_performance(
    recommendation_type='personalized',
    days=7
)
```

#### 5.4 A/B测试

```python
from apps.feedback.models import ABTestExperiment

# 创建实验
experiment = ABTestExperiment.objects.create(
    name='推荐算法A/B测试',
    description='测试新的协同过滤算法',
    control_group_ratio=0.5,
    experiment_group_ratio=0.5,
    variables={
        'cf_weight': {'control': 0.5, 'experiment': 0.7},
        'cb_weight': {'control': 0.3, 'experiment': 0.2},
    },
    status='running'
)

# 分配用户到实验组
from apps.feedback.models import ABTestAssignment

assignment = ABTestAssignment.objects.create(
    experiment=experiment,
    user=user,
    group='experiment',
    assigned_values={'cf_weight': 0.7, 'cb_weight': 0.2}
)
```

---

## 集成示例

### 完整的推荐流程

```python
# 1. 数据收集
from apps.data_collection.tasks import crawl_source_task
crawl_source_task.delay(source_id=1)

# 2. 话题分析
from apps.topic_analysis.tasks import analyze_content_topic_task
analyze_content_topic_task.delay(content_id=1)

# 3. 生成推荐
from apps.recommendation.engine import HybridRecommender
recommender = HybridRecommender()
recommendations = recommender.recommend(user_id=1)

# 4. 用户反馈
from apps.feedback.learner import AdaptiveLearner
learner = AdaptiveLearner()
learner.update_user_preference(user_id=1, topic_id=1, feedback_type='like')

# 5. 内容生成
from apps.content_generation.generators import TitleGenerator
generator = TitleGenerator()
titles = generator.generate(keywords=['AI'], n_titles=5)
```

---

## 性能优化建议

### 数据库优化

```python
# 使用select_related/prefetch_related减少查询
topics = Topic.objects.select_related('category').prefetch_related('tags')

# 使用索引
class Topic(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['heat_score', '-created_at']),
        ]
```

### 缓存策略

```python
from django.core.cache import cache

# 缓存热门话题
cache_key = f'hot_topics:{limit}'
topics = cache.get(cache_key)
if not topics:
    topics = Topic.objects.filter(status='active').order_by('-heat_score')[:limit]
    cache.set(cache_key, topics, 300)  # 5分钟
```

### 异步处理

```python
# 使用Celery异步任务
@shared_task
def heavy_computation_task(data):
    # 执行耗时计算
    return result

# 调用
result = heavy_computation_task.delay(data)
```

---

## 监控和日志

### 日志配置

```python
import logging

logger = logging.getLogger(__name__)

# 记录关键操作
logger.info(f"User {user_id} liked topic {topic_id}")
logger.error(f"Failed to generate recommendations: {error}")
```

### 性能监控

```python
from utils.monitoring import monitor_performance

@monitor_performance
def generate_recommendations(user_id):
    # 生成推荐逻辑
    pass
```

---

## 测试

### 单元测试

```python
# tests/unit/test_topic_analysis.py
def test_extract_keywords():
    from apps.topic_analysis.utils import extract_keywords

    text = "人工智能和机器学习"
    keywords = extract_keywords(text)

    assert len(keywords) > 0
    assert '人工智能' in keywords
```

### 集成测试

```python
# tests/integration/test_flow.py
def test_recommendation_flow():
    # 测试完整流程
    pass
```

---

## 扩展开发

### 添加新的数据源

1. 创建爬虫类继承 `BaseCrawler`
2. 实现爬取和解析逻辑
3. 注册到爬虫工厂

### 添加新的推荐算法

1. 创建推荐器类
2. 实现 `recommend()` 方法
3. 集成到 `HybridRecommender`

### 添加新的内容生成功能

1. 创建生成器类
2. 实现生成逻辑
3. 添加质量评分

---

## 最佳实践

1. **模块化设计**: 保持模块独立，通过明确的接口通信
2. **异步处理**: 使用Celery处理耗时任务
3. **缓存策略**: 合理使用缓存减少数据库压力
4. **错误处理**: 完善的异常处理和日志记录
5. **测试覆盖**: 保持高测试覆盖率
6. **文档更新**: 及时更新开发文档

---

## 问题排查

### 常见问题

**Q: 爬虫被反爬怎么办？**
A: 设置合理的delay、使用代理、模拟浏览器行为

**Q: 推荐效果不好？**
A: 检查数据质量、调整算法权重、收集更多反馈

**Q: 性能瓶颈？**
A: 使用缓存、优化数据库查询、增加异步处理

---

## 参考资料

- [Django文档](https://docs.djangoproject.com/)
- [Celery文档](https://docs.celeryproject.org/)
- [Gensim文档](https://radimrehurek.com/gensim/)
- [scikit-learn文档](https://scikit-learn.org/)
