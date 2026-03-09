# AI自媒体自动选题系统

基于NLP和机器学习的智能选题推荐系统，帮助自媒体创作者自动发现热门话题、生成个性化选题推荐。

## 项目特点

- 🤖 **智能选题**: 基于机器学习的个性化选题推荐
- 🔥 **热点追踪**: 实时识别和分析热门话题
- 📊 **数据分析**: 多维度数据分析，洞察内容趋势
- ✍️ **内容辅助**: AI辅助生成标题和大纲
- 📈 **自适应学习**: 根据用户反馈持续优化推荐

## 技术栈

### 后端
- Django 4.2 + Django REST Framework
- MySQL 8.0 + MongoDB
- Redis + Celery
- Elasticsearch

### 机器学习
- Gensim (主题建模)
- scikit-learn (推荐算法)
- jieba (中文分词)
- TensorFlow/PyTorch (深度学习)

### 前端
- React 18 / Vue.js 3
- Ant Design / Element Plus

### DevOps
- Docker + Docker Compose
- Nginx
- Prometheus + Grafana

## 快速开始

### 使用Docker（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd top_topics

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置必要的配置

# 启动服务
docker-compose up -d

# 访问服务
# 前端: http://localhost:3000
# 后端API: http://localhost:8000/api/v1/
# API文档: http://localhost:8000/swagger/
```

### 本地开发

#### 后端设置

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r backend/config/requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 数据库迁移
python backend/manage.py makemigrations
python backend/manage.py migrate

# 创建管理员
python backend/manage.py createsuperuser

# 启动开发服务器
python backend/manage.py runserver

# 启动Celery
celery -A backend.config worker -l info
celery -A backend.config beat -l info
```

#### 前端设置

```bash
cd frontend/web
npm install
npm run dev
```

## 项目结构

```
top_topics/
├── backend/              # 后端服务
│   ├── config/          # 配置文件
│   ├── apps/            # 应用模块
│   │   ├── data_collection/    # 数据收集
│   │   ├── topic_analysis/     # 话题分析
│   │   ├── recommendation/     # 推荐引擎
│   │   ├── content_generation/ # 内容生成
│   │   ├── feedback/           # 反馈学习
│   │   └── users/              # 用户管理
│   ├── core/            # 核心功能
│   └── api/             # API接口
├── frontend/            # 前端应用
├── workers/             # 后台任务
├── ml_models/           # 机器学习模型
├── data/                # 数据文件
├── tests/               # 测试
├── docs/                # 文档
└── docker/              # Docker配置
```

## 核心功能模块

### 1. 数据收集模块

自动从多个数据源采集内容数据：
- 新闻网站
- 社交媒体（微博、知乎等）
- 内容平台（B站、YouTube等）

```python
# 手动触发爬虫
from apps.data_collection.tasks import crawl_source_task

crawl_source_task.delay(source_id=1)
```

### 2. 话题分析模块

识别热门话题和趋势：
- 主题建模（LDA）
- 热度计算
- 趋势预测

```python
# 分析内容话题
from apps.topic_analysis.tasks import analyze_content_topic_task

analyze_content_topic_task.delay(content_id=1)
```

### 3. 推荐引擎模块

个性化选题推荐：
- 协同过滤
- 基于内容的推荐
- 混合推荐

```python
# 生成推荐
from apps.recommendation.engine import HybridRecommender

recommender = HybridRecommender()
recommendations = recommender.recommend(user_id=1, n_recommendations=10)
```

### 4. 内容生成模块

AI辅助内容创作：
- 标题生成
- 大纲生成
- 摘要生成

```python
# 生成标题
from apps.content_generation.generators import TitleGenerator

generator = TitleGenerator()
titles = generator.generate(keywords=['AI', '机器学习'], n_titles=5)
```

### 5. 反馈学习模块

持续优化推荐算法：
- 用户反馈收集
- 自适应学习
- A/B测试

```python
# 更新用户偏好
from apps.feedback.learner import AdaptiveLearner

learner = AdaptiveLearner()
learner.update_user_preference(user_id=1, topic_id=1, feedback_type='like')
```

## API使用示例

### 获取热门话题

```bash
curl -X GET "http://localhost:8000/api/v1/topics/hot/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 获取个性化推荐

```bash
curl -X GET "http://localhost:8000/api/v1/recommendations/personalized/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 提交反馈

```bash
curl -X POST "http://localhost:8000/api/v1/feedback/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topic_id": 1,
    "type": "like"
  }'
```

### 生成标题

```bash
curl -X POST "http://localhost:8000/api/v1/content/generate_title/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["人工智能", "深度学习"],
    "category": "news",
    "n_titles": 5
  }'
```

## 开发指南

详细的开发指南请查看 [DEVELOPMENT.md](DEVELOPMENT.md)

### 运行测试

```bash
# 单元测试
pytest tests/unit/

# 集成测试
pytest tests/integration/

# 覆盖率测试
pytest --cov=backend tests/
```

### 代码质量

```bash
# 代码格式化
black backend/

# 代码检查
flake8 backend/

# 类型检查
mypy backend/
```

## 部署

详细部署指南请查看 [DEVELOPMENT.md](DEVELOPMENT.md#部署指南)

### 生产环境部署

```bash
# 使用Docker部署
docker-compose -f docker-compose.prod.yml up -d

# 或使用Kubernetes
kubectl apply -f k8s/
```

## 监控

- API文档: http://localhost:8000/swagger/
- 监控面板: http://localhost:3001 (Grafana)
- 日志查看: ELK Stack

## 性能优化

详细优化建议请查看 [ARCHITECTURE.md](ARCHITECTURE.md#性能优化)

## 架构设计

详细架构文档请查看 [ARCHITECTURE.md](ARCHITECTURE.md)

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 联系方式

- 项目主页: https://github.com/youbin-jia/top_topics
- 问题反馈: https://github.com/youbin-jia/top_topics/issues
- 邮箱: contact@example.com

## 致谢

感谢所有贡献者和开源项目：
- Django
- scikit-learn
- Gensim
- jieba

---

**注意**: 这是一个完整的生产级别项目架构，实际部署时需要根据具体需求调整配置。
