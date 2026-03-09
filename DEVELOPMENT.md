# AI自媒体自动选题系统 - 开发指南

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- MySQL 8.0+
- MongoDB 7.0+
- Redis 7.0+
- Docker & Docker Compose (推荐)

### 本地开发环境设置

#### 1. 克隆项目
```bash
git clone <repository-url>
cd top_topics
```

#### 2. 后端设置
```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r backend/config/requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等

# 数据库迁移
python backend/manage.py makemigrations
python backend/manage.py migrate

# 创建超级用户
python backend/manage.py createsuperuser

# 运行开发服务器
python backend/manage.py runserver
```

#### 3. 前端设置
```bash
cd frontend/web
npm install
npm run dev
```

#### 4. 启动Celery
```bash
# 启动Celery worker
celery -A backend.config worker -l info

# 启动Celery beat (定时任务)
celery -A backend.config beat -l info
```

### 使用Docker快速启动

```bash
docker-compose up -d
```

访问:
- 前端: http://localhost:3000
- 后端API: http://localhost:8000/api/v1/
- 管理后台: http://localhost:8000/admin/

## 模块开发指南

### 数据收集模块 (data_collection)

**职责**: 从多个数据源采集内容数据

**关键文件**:
```
apps/data_collection/
├── crawlers/          # 爬虫实现
│   ├── base.py       # 基础爬虫类
│   ├── weibo.py      # 微博爬虫
│   ├── zhihu.py      # 知乎爬虫
│   └── news.py       # 新闻爬虫
├── processors/        # 数据处理器
│   ├── cleaner.py    # 数据清洗
│   └── deduplicator.py # 去重
├── tasks.py          # Celery任务
└── models.py         # 数据模型
```

**开发示例**:
```python
# crawlers/base.py
from abc import ABC, abstractmethod
from typing import List, Dict
import requests
from bs4 import BeautifulSoup

class BaseCrawler(ABC):
    """基础爬虫类"""

    def __init__(self, config: Dict):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 ...'
        })

    @abstractmethod
    def crawl(self, url: str) -> List[Dict]:
        """爬取数据"""
        pass

    @abstractmethod
    def parse(self, html: str) -> Dict:
        """解析数据"""
        pass

    def request(self, url: str, **kwargs) -> requests.Response:
        """发送请求"""
        try:
            response = self.session.get(url, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            self.logger.error(f"请求失败: {url}, 错误: {e}")
            raise
```

**任务调度**:
```python
# tasks.py
from celery import shared_task
from .crawlers import WeiboCrawler, ZhihuCrawler

@shared_task
def crawl_weibo_task():
    """微博爬虫任务"""
    crawler = WeiboCrawler()
    data = crawler.crawl()
    return process_and_save(data)

@shared_task
def daily_crawl_all():
    """每日定时爬取所有源"""
    crawl_weibo_task.delay()
    crawl_zhihu_task.delay()
    # ...
```

### 热点话题识别模块 (topic_analysis)

**职责**: 识别热点话题、趋势预测

**关键算法**:
```python
# ml_engine/topic_modeling.py
from gensim import corpora, models
from typing import List, Dict

class TopicModeler:
    """LDA主题建模"""

    def __init__(self, num_topics: int = 10):
        self.num_topics = num_topics
        self.dictionary = None
        self.lda_model = None

    def train(self, documents: List[List[str]]):
        """训练模型"""
        # 创建词典
        self.dictionary = corpora.Dictionary(documents)
        # 创建语料库
        corpus = [self.dictionary.doc2bow(doc) for doc in documents]
        # 训练LDA模型
        self.lda_model = models.LdaModel(
            corpus,
            num_topics=self.num_topics,
            id2word=self.dictionary,
            passes=10
        )

    def get_topics(self, document: List[str]) -> List[Dict]:
        """获取文档主题"""
        bow = self.dictionary.doc2bow(document)
        topics = self.lda_model.get_document_topics(bow)
        return [
            {
                'topic_id': topic_id,
                'probability': prob,
                'keywords': self.lda_model.show_topic(topic_id, topn=10)
            }
            for topic_id, prob in topics
        ]
```

**热度计算**:
```python
# analyzers/heat_score.py
from datetime import datetime, timedelta
import math

class HeatScoreCalculator:
    """热度分数计算器"""

    def calculate(
        self,
        publish_time: datetime,
        view_count: int,
        like_count: int,
        share_count: int,
        comment_count: int
    ) -> float:
        """计算热度分数"""
        # 时间衰减因子
        hours_elapsed = (datetime.now() - publish_time).total_seconds() / 3600
        time_decay = math.exp(-hours_elapsed / 24)  # 24小时半衰期

        # 互动率
        engagement = (
            like_count * 1.0 +
            share_count * 3.0 +
            comment_count * 2.0
        ) / max(view_count, 1)

        # 综合热度
        heat_score = (
            time_decay * 0.3 +
            engagement * 0.4 +
            math.log10(view_count + 1) * 0.3
        )

        return heat_score
```

### 推荐引擎模块 (recommendation)

**职责**: 个性化选题推荐

**推荐算法实现**:
```python
# ml_engine/recommender.py
from typing import List, Dict
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.metrics.pairwise import cosine_similarity

class CollaborativeFiltering:
    """协同过滤推荐"""

    def __init__(self, n_factors: int = 50):
        self.n_factors = n_factors
        self.user_item_matrix = None
        self.item_similarity = None

    def fit(self, interactions: Dict[int, Dict[int, float]]):
        """训练模型"""
        # 构建用户-物品矩阵
        users = list(interactions.keys())
        items = set()
        for user_items in interactions.values():
            items.update(user_items.keys())
        items = list(items)

        # 创建稀疏矩阵
        data = []
        row = []
        col = []
        for user_id, user_items in interactions.items():
            for item_id, rating in user_items.items():
                data.append(rating)
                row.append(users.index(user_id))
                col.append(items.index(item_id))

        self.user_item_matrix = csr_matrix(
            (data, (row, col)),
            shape=(len(users), len(items))
        )

        # 计算物品相似度
        self.item_similarity = cosine_similarity(self.user_item_matrix.T)

    def recommend(
        self,
        user_id: int,
        n_recommendations: int = 10
    ) -> List[int]:
        """生成推荐"""
        user_vector = self.user_item_matrix[user_id]
        scores = user_vector.dot(self.item_similarity)
        # 排除已交互物品
        scores[user_vector.nonzero()[1]] = -np.inf
        # 返回Top-N
        top_items = np.argsort(scores)[-n_recommendations:][::-1]
        return top_items.tolist()
```

**推荐API**:
```python
# api/v1/recommendations.py
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

class RecommendationViewSet(viewsets.ViewSet):
    """推荐接口"""

    @action(detail=False, methods=['get'])
    def personalized(self, request):
        """个性化推荐"""
        user_id = request.user.id
        limit = int(request.query_params.get('limit', 10))

        # 获取用户特征
        user_features = self.get_user_features(user_id)

        # 生成候选
        candidates = self.generate_candidates(user_features)

        # 排序
        ranked = self.rank_candidates(candidates, user_features)

        # 过滤
        filtered = self.filter_candidates(ranked, user_id)

        return Response({
            'success': True,
            'data': filtered[:limit]
        })

    def generate_candidates(self, user_features):
        """多路召回"""
        candidates = []

        # 协同过滤召回
        cf_items = self.cf_recommender.recommend(user_features['user_id'])
        candidates.extend(cf_items)

        # 内容召回
        content_items = self.content_recommender.recommend(user_features)
        candidates.extend(content_items)

        # 热门召回
        hot_items = self.hot_recommender.recommend()
        candidates.extend(hot_items)

        return candidates
```

### 内容生成模块 (content_generation)

**职责**: 生成选题大纲和标题

**标题生成**:
```python
# generators/title_generator.py
from transformers import pipeline
from typing import List, Dict

class TitleGenerator:
    """标题生成器"""

    def __init__(self):
        self.generator = pipeline(
            'text-generation',
            model='gpt2-chinese-cluecorpussmall',
            device=0
        )

    def generate(
        self,
        keywords: List[str],
        style: str = 'normal',
        n_titles: int = 5
    ) -> List[str]:
        """生成标题"""
        # 构建prompt
        prompt = self._build_prompt(keywords, style)

        # 生成标题
        results = self.generator(
            prompt,
            max_length=30,
            num_return_sequences=n_titles,
            temperature=0.8
        )

        titles = [r['generated_text'] for r in results]
        return self._postprocess(titles)

    def _build_prompt(self, keywords: List[str], style: str) -> str:
        """构建提示词"""
        keyword_str = '、'.join(keywords)

        styles = {
            'normal': f'关于{keyword_str}的文章标题：',
            'attractive': f'震惊！关于{keyword_str}的惊人真相：',
            'guide': f'{keyword_str}完全指南：'
        }

        return styles.get(style, styles['normal'])
```

**大纲生成**:
```python
# generators/outline_generator.py
from typing import List, Dict

class OutlineGenerator:
    """文章大纲生成器"""

    def generate(
        self,
        topic: str,
        keywords: List[str],
        style: str = 'informative'
    ) -> Dict:
        """生成文章大纲"""
        # 分析主题
        main_points = self._extract_main_points(topic, keywords)

        # 生成结构
        outline = {
            'title': topic,
            'introduction': self._generate_intro(topic, keywords),
            'sections': [],
            'conclusion': self._generate_conclusion(topic)
        }

        # 生成各节
        for point in main_points:
            section = {
                'heading': point['title'],
                'key_points': point['sub_points'],
                'estimated_length': point['word_count']
            }
            outline['sections'].append(section)

        return outline

    def _extract_main_points(self, topic, keywords):
        """提取主要观点"""
        # 使用NLP提取关键点
        # 这里简化实现
        return [
            {
                'title': f'{topic}的背景',
                'sub_points': ['发展历程', '现状分析'],
                'word_count': 500
            },
            {
                'title': f'{topic}的核心要点',
                'sub_points': keywords[:3],
                'word_count': 1000
            },
            {
                'title': f'{topic}的影响',
                'sub_points': ['积极影响', '潜在风险'],
                'word_count': 500
            }
        ]
```

### 反馈学习模块 (feedback)

**职责**: 收集反馈、优化算法

**反馈收集**:
```python
# models.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class UserFeedback(models.Model):
    """用户反馈"""
    FEEDBACK_TYPES = [
        ('click', '点击'),
        ('like', '点赞'),
        ('share', '分享'),
        ('collect', '收藏'),
        ('skip', '跳过'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    topic = models.ForeignKey('topic_analysis.Topic', on_delete=models.CASCADE)
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['topic', 'feedback_type'])
        ]
```

**自适应学习**:
```python
# learners/adaptive_learner.py
from typing import Dict, List
from datetime import datetime, timedelta

class AdaptiveLearner:
    """自适应学习器"""

    def __init__(self, learning_rate: float = 0.01):
        self.learning_rate = learning_rate
        self.user_profiles = {}

    def update_user_profile(
        self,
        user_id: int,
        feedback: Dict
    ):
        """更新用户画像"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = self._init_profile()

        profile = self.user_profiles[user_id]

        # 根据反馈调整兴趣权重
        topic_features = feedback['topic_features']
        feedback_weight = self._get_feedback_weight(feedback['type'])

        for feature, value in topic_features.items():
            if feature not in profile['interests']:
                profile['interests'][feature] = 0

            # 梯度更新
            profile['interests'][feature] += (
                self.learning_rate *
                feedback_weight *
                value
            )

        # 时间衰减
        self._apply_time_decay(profile)

    def _get_feedback_weight(self, feedback_type: str) -> float:
        """获取反馈权重"""
        weights = {
            'click': 1.0,
            'like': 2.0,
            'share': 3.0,
            'collect': 2.5,
            'skip': -1.0
        }
        return weights.get(feedback_type, 0)
```

## 测试指南

### 单元测试

```python
# tests/unit/test_topic_modeling.py
import pytest
from ml_engine.topic_modeling import TopicModeler

@pytest.fixture
def sample_documents():
    return [
        ['人工智能', '深度学习', '神经网络'],
        ['机器学习', '数据科学', 'Python'],
        ['自然语言处理', '文本分析', '人工智能']
    ]

def test_topic_modeling(sample_documents):
    """测试主题建模"""
    modeler = TopicModeler(num_topics=2)
    modeler.train(sample_documents)

    # 测试主题提取
    doc = ['人工智能', '深度学习']
    topics = modeler.get_topics(doc)

    assert len(topics) > 0
    assert all('topic_id' in t for t in topics)
    assert all('probability' in t for t in topics)
```

### 集成测试

```python
# tests/integration/test_recommendation_flow.py
import pytest
from django.test import TestCase
from rest_framework.test import APIClient

class RecommendationFlowTestCase(TestCase):
    """推荐流程集成测试"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.client.force_authenticate(user=self.user)

    def test_full_recommendation_flow(self):
        """测试完整推荐流程"""
        # 1. 获取推荐
        response = self.client.get('/api/v1/recommendations/personalized/')
        assert response.status_code == 200
        recommendations = response.json()['data']
        assert len(recommendations) > 0

        # 2. 提交反馈
        topic_id = recommendations[0]['id']
        response = self.client.post(
            f'/api/v1/topics/{topic_id}/feedback/',
            {'type': 'like'}
        )
        assert response.status_code == 201

        # 3. 验证更新
        response = self.client.get('/api/v1/recommendations/personalized/')
        new_recommendations = response.json()['data']
        assert len(new_recommendations) > 0
```

### 性能测试

```python
# tests/performance/test_api_performance.py
import pytest
from rest_framework.test import APIClient
from django.test import TestCase
import time

class APIPerformanceTestCase(TestCase):
    """API性能测试"""

    def test_recommendation_response_time(self):
        """推荐接口响应时间测试"""
        client = APIClient()
        user = User.objects.create_user('user', 'pass')
        client.force_authenticate(user=user)

        start_time = time.time()
        response = client.get('/api/v1/recommendations/personalized/')
        end_time = time.time()

        assert response.status_code == 200
        assert (end_time - start_time) < 0.5  # 500ms内响应
```

## API文档

### 推荐接口

**获取个性化推荐**
```http
GET /api/v1/recommendations/personalized/
Authorization: Bearer <token>

Response:
{
  "success": true,
  "data": [
    {
      "id": 1,
      "title": "人工智能的最新进展",
      "heat_score": 0.85,
      "keywords": ["AI", "深度学习"],
      "source": "知乎",
      "published_at": "2026-03-10T00:00:00Z"
    }
  ]
}
```

### 话题接口

**获取热点话题**
```http
GET /api/v1/topics/hot/
Authorization: Bearer <token>

Response:
{
  "success": true,
  "data": [
    {
      "id": 1,
      "topic": "ChatGPT应用",
      "heat_score": 0.92,
      "trend": "rising",
      "related_articles": 1234
    }
  ]
}
```

### 反馈接口

**提交反馈**
```http
POST /api/v1/topics/{id}/feedback/
Authorization: Bearer <token>

Body:
{
  "type": "like"  // click, like, share, collect, skip
}

Response:
{
  "success": true,
  "message": "反馈已记录"
}
```

## 部署指南

### 生产环境配置

```python
# config/settings/production.py
import os
from .base import *

DEBUG = False

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# 数据库
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}

# 缓存
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# 安全设置
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
```

### Docker部署

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: mysql:8.0
    environment:
      MYSQL_DATABASE: top_topics
      MYSQL_ROOT_PASSWORD: ${DB_PASSWORD}
    volumes:
      - db_data:/var/lib/mysql

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  backend:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
    env_file:
      - .env

  celery:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    command: celery -A config worker -l info
    volumes:
      - ./backend:/app
    depends_on:
      - db
      - redis
    env_file:
      - .env

  frontend:
    build:
      context: ./frontend/web
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - backend

volumes:
  db_data:
  redis_data:
```

## 监控与日志

### 日志配置

```python
# config/settings/base.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/top_topics/app.log',
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
        },
        'apps': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
        },
    },
}
```

### 性能监控

```python
# utils/monitoring.py
from functools import wraps
import time
import logging

logger = logging.getLogger(__name__)

def monitor_performance(func):
    """性能监控装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(
                f"{func.__name__} executed in {duration:.2f}s"
            )
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"{func.__name__} failed after {duration:.2f}s: {e}"
            )
            raise
    return wrapper
```

## 常见问题

### 1. 数据库连接问题
```bash
# 检查MySQL状态
mysql -u root -p -e "SHOW STATUS;"

# 重置连接
python manage.py dbshell
```

### 2. Celery任务不执行
```bash
# 检查Celery状态
celery -A config inspect active

# 重启Celery
pkill -f celery
celery -A config worker -l info
```

### 3. 内存占用过高
- 检查数据加载方式，使用生成器而非列表
- 限制模型加载数量
- 启用数据分页

## 最佳实践

### 代码风格
- 遵循PEP 8规范
- 使用Black格式化代码
- 类型注解（Type Hints）
- 文档字符串（Docstrings）

### Git提交规范
```
feat: 添加新功能
fix: 修复bug
docs: 文档更新
style: 代码格式调整
refactor: 重构代码
test: 测试相关
chore: 构建/工具相关
```

### 代码审查清单
- [ ] 代码是否符合设计规范
- [ ] 是否有充分的测试覆盖
- [ ] 性能是否达标
- [ ] 安全性是否考虑
- [ ] 文档是否完善

## 持续改进

### 代码质量
- 使用pylint进行静态分析
- 使用coverage.py检查测试覆盖率
- 定期进行代码审查

### 性能优化
- 定期进行性能测试
- 分析慢查询日志
- 优化缓存策略

### 算法迭代
- 收集用户反馈数据
- A/B测试新算法
- 监控模型性能指标
