# AI自媒体自动选题系统 - 用户使用手册

## 目录

1. [系统介绍](#系统介绍)
2. [快速开始](#快速开始)
3. [功能详解](#功能详解)
4. [API使用指南](#api使用指南)
5. [最佳实践](#最佳实践)
6. [常见问题](#常见问题)
7. [故障排查](#故障排查)

---

## 系统介绍

### 什么是AI自媒体自动选题系统？

这是一个基于人工智能和机器学习技术的智能选题推荐系统，帮助自媒体创作者：
- 🔥 自动发现热门话题和趋势
- 🎯 获得个性化的选题推荐
- ✍️ AI辅助生成标题和大纲
- 📊 实时追踪内容表现
- 🧠 系统持续学习优化推荐

### 核心功能

| 功能模块 | 描述 | 使用场景 |
|---------|------|---------|
| 热点追踪 | 实时识别热门话题 | 快速把握热点，抢占先机 |
| 个性化推荐 | 基于兴趣的选题推荐 | 找到最适合您的选题方向 |
| 内容生成 | AI生成标题和大纲 | 提高创作效率 |
| 趋势预测 | 预测话题发展趋势 | 提前布局内容策略 |
| 数据分析 | 多维度数据分析 | 了解用户偏好和内容表现 |

---

## 快速开始

### 环境要求

**必需环境**：
- Python 3.10+
- Node.js 18+
- MySQL 8.0+
- Redis 7.0+

**可选环境**：
- MongoDB 7.0+ (用于存储非结构化数据)
- Elasticsearch 8.x (用于全文搜索)
- Docker & Docker Compose (推荐)

### 5分钟快速启动

#### 方法一：使用Docker（推荐）

```bash
# 1. 克隆项目
git clone <repository-url>
cd top_topics

# 2. 配置环境变量
cp .env.example .env
vim .env  # 修改数据库密码等配置

# 3. 一键启动
docker-compose up -d

# 4. 查看日志
docker-compose logs -f backend

# 5. 访问服务
# API文档: http://localhost:8000/swagger/
# 管理后台: http://localhost:8000/admin/
# 前端界面: http://localhost:3000
```

#### 方法二：本地开发环境

```bash
# 1. 运行安装脚本
chmod +x scripts/setup.sh
./scripts/setup.sh

# 2. 配置环境变量
cp .env.example .env
vim .env

# 3. 创建数据库
mysql -u root -p
CREATE DATABASE top_topics CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 4. 运行迁移
python backend/manage.py migrate

# 5. 创建管理员
python backend/manage.py createsuperuser

# 6. 启动服务
# 终端1: 启动Django
python backend/manage.py runserver

# 终端2: 启动Celery Worker
celery -A backend.config worker -l info

# 终端3: 启动Celery Beat
celery -A backend.config beat -l info

# 终端4: 启动前端
cd frontend/web
npm install
npm run dev
```

### 首次登录

1. 访问管理后台：http://localhost:8000/admin/
2. 使用创建的管理员账号登录
3. 配置数据源（见下一节）
4. 开始使用系统

---

## 功能详解

### 1. 数据源配置

#### 添加新的数据源

**方式一：通过管理后台**

1. 登录管理后台：http://localhost:8000/admin/
2. 进入"数据收集" → "数据源"
3. 点击"添加数据源"
4. 填写配置信息：

```
名称: 微博热搜
类型: weibo
基础URL: https://weibo.com
状态: 活跃
爬取频率: 3600 (秒)
配置: {
  "delay": 2.0,
  "pages": 5,
  "selectors": {
    "title": ".title",
    "content": ".content"
  }
}
```

**方式二：通过API**

```bash
curl -X POST http://localhost:8000/api/v1/datasources/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "知乎热门",
    "source_type": "zhihu",
    "base_url": "https://zhihu.com",
    "config": {
      "delay": 2.0,
      "pages": 3
    }
  }'
```

#### 管理数据源

```bash
# 查看所有数据源
GET /api/v1/datasources/

# 启用/禁用数据源
PATCH /api/v1/datasources/{id}/
{
  "status": "inactive"
}

# 手动触发爬取
POST /api/v1/datasources/{id}/crawl/
```

### 2. 热门话题发现

#### 获取热门话题

**API调用**：
```bash
# 获取热门话题
curl -X GET "http://localhost:8000/api/v1/topics/hot/?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例**：
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "ChatGPT应用",
      "heat_score": 0.92,
      "trend": "rising",
      "article_count": 1234,
      "keywords": ["AI", "ChatGPT", "人工智能"],
      "description": "ChatGPT在各行业的应用探讨"
    }
  ]
}
```

#### 获取趋势话题

```bash
# 获取上升话题
curl -X GET "http://localhost:8000/api/v1/topics/trending/?limit=10" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### 搜索话题

```bash
# 搜索特定话题
curl -X GET "http://localhost:8000/api/v1/topics/?search=AI&min_score=0.5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. 个性化推荐

#### 获取个人推荐

```bash
# 获取个性化推荐
curl -X GET "http://localhost:8000/api/v1/recommendations/personalized/?limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**响应示例**：
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "人工智能最新进展",
      "recommendation_score": 0.85,
      "heat_score": 0.78,
      "keywords": ["AI", "深度学习"],
      "reasons": ["您对AI领域感兴趣", "近期热门话题"]
    }
  ]
}
```

#### 提交反馈

**重要**：提交反馈可以优化推荐效果

```bash
# 点击反馈
curl -X POST http://localhost:8000/api/v1/feedback/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topic_id": 1,
    "type": "click",
    "dwell_time": 30
  }'

# 点赞反馈
curl -X POST http://localhost:8000/api/v1/feedback/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topic_id": 1,
    "type": "like"
  }'

# 分享反馈
curl -X POST http://localhost:8000/api/v1/feedback/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topic_id": 1,
    "type": "share"
  }'
```

#### 反馈类型说明

| 反馈类型 | 权重 | 说明 |
|---------|-----|------|
| click | 1.0 | 点击查看话题详情 |
| like | 2.0 | 点赞，表示喜欢 |
| share | 3.0 | 分享，表示高度认可 |
| collect | 2.5 | 收藏，表示有用 |
| skip | -1.0 | 跳过，表示不感兴趣 |

### 4. AI内容生成

#### 生成标题

```bash
curl -X POST http://localhost:8000/api/v1/content/generate_title/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["人工智能", "深度学习", "应用"],
    "category": "news",
    "n_titles": 5
  }'
```

**响应示例**：
```json
{
  "success": true,
  "data": [
    {
      "title": "人工智能的最新突破：深度学习改变世界",
      "quality_score": 0.85
    },
    {
      "title": "深度学习在实际应用中的5个关键点",
      "quality_score": 0.78
    }
  ]
}
```

#### 标题类别说明

| 类别 | 描述 | 示例 |
|-----|------|-----|
| news | 新闻类 | XX最新发布：人工智能的重大突破 |
| guide | 指南类 | 如何使用AI提高工作效率：完整指南 |
| list | 清单类 | 10个你必须知道的AI应用 |
| question | 问答类 | 为什么深度学习如此重要？ |
| shock | 震惊类 | 震惊！AI竟然能做到这些 |

#### 生成大纲

```bash
curl -X POST http://localhost:8000/api/v1/content/generate_outline/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topic_name": "人工智能在教育领域的应用",
    "keywords": ["AI教育", "个性化学习", "智能辅导"],
    "style": "informative",
    "n_sections": 4
  }'
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "title": "人工智能在教育领域的应用",
    "style": "informative",
    "introduction": {
      "content": "本文将探讨AI如何改变教育行业...",
      "key_points": ["AI教育", "个性化学习"],
      "word_count": 200
    },
    "sections": [
      {
        "number": 1,
        "title": "AI教育背景介绍",
        "key_points": [
          "发展历程：从在线教育到AI教育",
          "现状分析：当前AI教育市场规模"
        ],
        "estimated_length": 500,
        "writing_tips": ["提供客观数据", "引用权威来源"]
      }
    ],
    "conclusion": {
      "content": "综上所述，AI正在重塑教育行业...",
      "summary_points": ["AI教育", "个性化学习"],
      "call_to_action": "欢迎分享您的观点"
    },
    "quality_score": 0.82
  }
}
```

### 5. 用户偏好设置

#### 更新用户偏好

```bash
curl -X PUT http://localhost:8000/api/v1/users/update_preferences/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "categories": ["科技", "人工智能", "互联网"],
    "keywords": {
      "人工智能": 0.9,
      "机器学习": 0.85,
      "深度学习": 0.8
    }
  }'
```

#### 查看用户画像

```bash
curl -X GET http://localhost:8000/api/v1/users/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## API使用指南

### 认证方式

系统使用JWT认证，获取token：

```bash
# 登录获取token
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'

# 响应
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

# 使用token访问API
curl -X GET http://localhost:8000/api/v1/topics/hot/ \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc..."

# 刷新token
curl -X POST http://localhost:8000/api/v1/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }'
```

### API端点列表

#### 话题相关

| 端点 | 方法 | 描述 |
|-----|------|------|
| `/api/v1/topics/` | GET | 获取话题列表 |
| `/api/v1/topics/hot/` | GET | 获取热门话题 |
| `/api/v1/topics/trending/` | GET | 获取趋势话题 |
| `/api/v1/topics/{id}/` | GET | 获取话题详情 |

#### 推荐相关

| 端点 | 方法 | 描述 |
|-----|------|------|
| `/api/v1/recommendations/personalized/` | GET | 个性化推荐 |
| `/api/v1/recommendations/hot/` | GET | 热门推荐 |

#### 反馈相关

| 端点 | 方法 | 描述 |
|-----|------|------|
| `/api/v1/feedback/` | POST | 提交反馈 |

#### 内容生成

| 端点 | 方法 | 描述 |
|-----|------|------|
| `/api/v1/content/generate_title/` | POST | 生成标题 |
| `/api/v1/content/generate_outline/` | POST | 生成大纲 |

### 分页、过滤和排序

#### 分页

```bash
# 指定页码和每页数量
GET /api/v1/topics/?page=2&page_size=20
```

#### 过滤

```bash
# 按热度过滤
GET /api/v1/topics/?min_score=0.5

# 按类别过滤
GET /api/v1/topics/?category=AI

# 按趋势过滤
GET /api/v1/topics/?trend=rising
```

#### 排序

```bash
# 按热度排序
GET /api/v1/topics/?ordering=-heat_score

# 按时间排序
GET /api/v1/topics/?ordering=-created_at
```

### 错误处理

API返回统一的错误格式：

```json
{
  "success": false,
  "message": "请求失败",
  "errors": {
    "topic_id": ["该字段是必填项。"]
  }
}
```

常见HTTP状态码：
- `200` - 成功
- `201` - 创建成功
- `400` - 请求参数错误
- `401` - 未认证
- `403` - 无权限
- `404` - 资源不存在
- `500` - 服务器错误

---

## 最佳实践

### 1. 提高推荐质量的技巧

#### 持续提交反馈

```python
# 推荐：在用户浏览时自动提交反馈
async function handleTopicView(topicId, dwellTime) {
  await api.submitFeedback({
    topic_id: topicId,
    type: 'click',
    dwell_time: dwellTime
  });
}

// 在用户点赞时提交
async function handleLike(topicId) {
  await api.submitFeedback({
    topic_id: topicId,
    type: 'like'
  });
}
```

#### 定期更新用户偏好

```python
# 建议每周更新一次用户偏好
async function updatePreferences() {
  const categories = ['科技', 'AI', '互联网'];
  const keywords = {
    '人工智能': 0.9,
    '机器学习': 0.85
  };

  await api.updatePreferences({ categories, keywords });
}
```

#### 利用多个反馈维度

```python
# 综合利用停留时间、滚动深度等
async function trackEngagement(topicId) {
  const startTime = Date.now();

  // 跟踪滚动深度
  window.addEventListener('scroll', () => {
    const scrollDepth = window.scrollY / document.body.scrollHeight;

    // 提交详细反馈
    api.submitFeedback({
      topic_id: topicId,
      type: 'click',
      dwell_time: (Date.now() - startTime) / 1000,
      scroll_depth: scrollDepth
    });
  });
}
```

### 2. 内容创作工作流

推荐的内容创作流程：

```
1. 获取热门话题 → 2. 查看个性化推荐 → 3. 生成标题 → 4. 生成大纲 → 5. 创建内容
```

#### 示例工作流代码

```javascript
async function contentCreationWorkflow() {
  // 1. 获取热门话题
  const hotTopics = await api.getHotTopics(10);

  // 2. 获取个性化推荐
  const recommendations = await api.getPersonalizedRecommendations(10);

  // 3. 选择话题
  const selectedTopic = recommendations.data[0];

  // 4. 生成标题
  const titles = await api.generateTitle({
    keywords: selectedTopic.keywords,
    category: 'news',
    n_titles: 5
  });

  // 5. 选择最佳标题
  const bestTitle = titles.data.sort((a, b) =>
    b.quality_score - a.quality_score
  )[0];

  // 6. 生成大纲
  const outline = await api.generateOutline({
    topic_name: selectedTopic.name,
    keywords: selectedTopic.keywords,
    style: 'informative',
    n_sections: 4
  });

  // 7. 开始创作
  console.log('标题:', bestTitle.title);
  console.log('大纲:', outline.data);

  // 8. 创作完成后提交反馈
  await api.submitFeedback({
    topic_id: selectedTopic.id,
    type: 'like'
  });
}
```

### 3. 数据源管理最佳实践

#### 合理设置爬取频率

```python
# 推荐配置
数据源配置 = {
  "新闻网站": {
    "crawl_frequency": 3600,  # 1小时
    "delay": 2.0,             # 请求间隔2秒
    "pages": 5                # 爬取5页
  },
  "社交媒体": {
    "crawl_frequency": 1800,  # 30分钟
    "delay": 3.0,             # 请求间隔3秒（更保守）
    "pages": 3
  },
  "内容平台": {
    "crawl_frequency": 7200,  # 2小时
    "delay": 2.5,
    "pages": 10
  }
}
```

#### 监控数据源健康

```bash
# 定期检查数据源状态
curl -X GET http://localhost:8000/api/v1/datasources/stats/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# 响应示例
{
  "total_sources": 5,
  "active_sources": 4,
  "failed_sources": 1,
  "last_crawl_stats": {
    "total_crawled": 1234,
    "success_rate": 0.95
  }
}
```

### 4. 性能优化建议

#### 使用缓存

```javascript
// 前端缓存热门话题
const CACHE_KEY = 'hot_topics';
const CACHE_EXPIRE = 5 * 60 * 1000; // 5分钟

async function getHotTopics() {
  // 检查缓存
  const cached = localStorage.getItem(CACHE_KEY);
  if (cached) {
    const { data, timestamp } = JSON.parse(cached);
    if (Date.now() - timestamp < CACHE_EXPIRE) {
      return data;
    }
  }

  // 请求新数据
  const data = await api.getHotTopics();

  // 存储到缓存
  localStorage.setItem(CACHE_KEY, JSON.stringify({
    data,
    timestamp: Date.now()
  }));

  return data;
}
```

#### 批量操作

```javascript
// 批量提交反馈（减少API调用）
class FeedbackBatch {
  constructor() {
    this.queue = [];
    this.timer = null;
  }

  add(feedback) {
    this.queue.push(feedback);

    // 5秒后批量提交
    if (!this.timer) {
      this.timer = setTimeout(() => this.flush(), 5000);
    }

    // 队列满10条立即提交
    if (this.queue.length >= 10) {
      this.flush();
    }
  }

  async flush() {
    if (this.queue.length === 0) return;

    const feedbacks = [...this.queue];
    this.queue = [];
    clearTimeout(this.timer);
    this.timer = null;

    // 批量提交
    await api.batchSubmitFeedback({ feedbacks });
  }
}

const feedbackBatch = new FeedbackBatch();

// 使用
feedbackBatch.add({ topic_id: 1, type: 'click' });
feedbackBatch.add({ topic_id: 2, type: 'like' });
```

---

## 常见问题

### Q1: 如何提高推荐准确性？

**A**: 多提交反馈，包括：
- 点击查看话题详情
- 点赞喜欢的内容
- 分享有价值的话题
- 跳过不感兴趣的内容
- 定期更新偏好设置

### Q2: 生成的标题质量不高怎么办？

**A**: 尝试以下方法：
1. 提供更精准的关键词
2. 选择合适的标题类别
3. 增加生成数量，选择最佳
4. 手动调整生成结果
5. 创建自定义标题模板

### Q3: 如何添加新的数据源？

**A**: 三种方式：
1. 通过管理后台添加（推荐新手）
2. 通过API接口添加
3. 开发自定义爬虫（高级用户）

### Q4: 系统响应慢怎么办？

**A**: 检查以下方面：
1. 数据库查询是否优化
2. 是否启用缓存
3. Celery任务是否正常
4. 服务器资源是否充足

### Q5: 如何备份数据？

**A**:
```bash
# 备份MySQL数据库
mysqldump -u root -p top_topics > backup_$(date +%Y%m%d).sql

# 备份MongoDB
mongodump --uri="mongodb://localhost:27017/top_topics" --out=backup/

# 备份Redis
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb backup/redis_$(date +%Y%m%d).rdb
```

### Q6: 如何监控爬虫任务？

**A**:
```bash
# 查看Celery任务状态
celery -A backend.config inspect active

# 查看任务队列
celery -A backend.config inspect reserved

# 查看已注册任务
celery -A backend.config inspect registered

# 通过API查看爬取日志
curl -X GET http://localhost:8000/api/v1/crawl-logs/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Q7: 如何实现定时爬取？

**A**: 系统已配置定时任务：
- 每小时自动爬取活跃数据源
- 每30分钟更新话题热度
- 每天记录趋势快照

自定义定时任务：
```python
# config/celery.py
app.conf.beat_schedule = {
    'custom-task': {
        'task': 'your_task_path',
        'schedule': crontab(hour=8, minute=0),  # 每天8点
    },
}
```

### Q8: 如何处理反爬机制？

**A**: 建议策略：
1. 设置合理的请求延迟（2-3秒）
2. 使用代理IP池
3. 模拟浏览器行为
4. 设置User-Agent轮换
5. 处理验证码（人工或OCR）
6. 遵守robots.txt规则

---

## 故障排查

### 问题1: 服务无法启动

**症状**: 运行 `docker-compose up` 失败

**排查步骤**:

```bash
# 1. 检查端口占用
lsof -i :8000
lsof -i :3306
lsof -i :6379

# 2. 检查日志
docker-compose logs backend
docker-compose logs db

# 3. 检查配置文件
cat .env

# 4. 重新构建
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 问题2: 数据库连接失败

**症状**: 报错 `Can't connect to MySQL server`

**解决方案**:

```bash
# 1. 检查MySQL是否运行
docker-compose ps db

# 2. 检查MySQL日志
docker-compose logs db

# 3. 验证连接
docker-compose exec db mysql -u root -p

# 4. 检查环境变量
echo $DB_HOST
echo $DB_PASSWORD

# 5. 重启MySQL
docker-compose restart db
```

### 问题3: Celery任务不执行

**症状**: 异步任务没有执行

**排查步骤**:

```bash
# 1. 检查Celery Worker状态
docker-compose logs celery_worker

# 2. 检查Redis连接
docker-compose exec redis redis-cli ping

# 3. 检查任务队列
celery -A backend.config inspect active

# 4. 手动触发任务
celery -A backend.config call apps.data_collection.tasks.daily_crawl_all_sources

# 5. 重启Celery
docker-compose restart celery_worker celery_beat
```

### 问题4: API请求超时

**症状**: 请求返回504错误

**解决方案**:

```bash
# 1. 检查服务器负载
top
htop

# 2. 检查数据库慢查询
mysql> SHOW PROCESSLIST;

# 3. 检查缓存
docker-compose exec redis redis-cli info memory

# 4. 增加超时设置
# nginx.conf
proxy_read_timeout 300;

# 5. 优化查询
# 添加数据库索引
python manage.py dbshell
```

### 问题5: 内存占用过高

**症状**: 服务器内存不足

**解决方案**:

```bash
# 1. 查看内存使用
free -h
docker stats

# 2. 清理缓存
docker-compose exec redis redis-cli FLUSHALL

# 3. 重启服务
docker-compose restart

# 4. 调整配置
# docker-compose.yml
environment:
  - GUNICORN_WORKERS=2  # 减少worker数量
  - CELERY_CONCURRENCY=2
```

### 问题6: 推荐结果为空

**症状**: API返回空数组

**排查步骤**:

```bash
# 1. 检查是否有话题数据
curl -X GET http://localhost:8000/api/v1/topics/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# 2. 检查用户反馈历史
curl -X GET http://localhost:8000/api/v1/users/profile/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# 3. 触发数据爬取
curl -X POST http://localhost:8000/api/v1/datasources/1/crawl/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# 4. 检查话题分析任务
celery -A backend.config inspect active

# 5. 手动更新热度
celery -A backend.config call apps.topic_analysis.tasks.update_topic_heat_scores
```

### 问题7: 前端无法连接后端

**症状**: 前端显示网络错误

**解决方案**:

```bash
# 1. 检查CORS配置
# backend/config/settings/base.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
]

# 2. 检查后端是否运行
curl http://localhost:8000/api/v1/

# 3. 检查前端API配置
# frontend/web/.env
VITE_API_URL=http://localhost:8000/api/v1

# 4. 检查网络连接
ping localhost

# 5. 查看浏览器控制台
# F12 -> Network tab
```

### 日志查看

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f celery_worker

# 查看最近100行
docker-compose logs --tail=100 backend

# 保存日志到文件
docker-compose logs > logs/system.log
```

### 性能监控

```bash
# 访问Prometheus
http://localhost:9090

# 访问Grafana
http://localhost:3001
# 默认账号: admin/admin

# 查看系统指标
docker stats
```

---

## 附录

### 环境变量完整列表

| 变量名 | 描述 | 默认值 | 必需 |
|-------|------|-------|------|
| SECRET_KEY | Django密钥 | - | ✓ |
| DEBUG | 调试模式 | True | |
| DB_NAME | 数据库名 | top_topics | ✓ |
| DB_USER | 数据库用户 | root | ✓ |
| DB_PASSWORD | 数据库密码 | - | ✓ |
| DB_HOST | 数据库主机 | localhost | ✓ |
| DB_PORT | 数据库端口 | 3306 | |
| REDIS_URL | Redis连接 | redis://localhost:6379/0 | ✓ |
| CELERY_BROKER_URL | Celery代理 | redis://localhost:6379/1 | ✓ |

### 有用的命令

```bash
# Django管理命令
python manage.py help                    # 查看所有命令
python manage.py showmigrations          # 显示迁移状态
python manage.py dbshell                 # 进入数据库shell
python manage.py shell                   # Django shell
python manage.py clear_cache             # 清除缓存

# Celery命令
celery -A config inspect active         # 查看活跃任务
celery -A config inspect scheduled      # 查看定时任务
celery -A config purge                  # 清空任务队列

# Docker命令
docker-compose ps                       # 查看容器状态
docker-compose exec backend bash        # 进入容器
docker-compose restart                  # 重启服务
docker-compose down -v                  # 停止并删除数据卷

# 监控命令
docker stats                            # 容器资源使用
docker-compose logs -f --tail=100       # 实时日志
```

---

## 技术支持

- 📧 邮箱: support@example.com
- 💬 在线文档: http://localhost:8000/swagger/
- 🐛 问题反馈: https://github.com/youbin-jia/top_topics/issues
- 📚 完整文档: 查看 ARCHITECTURE.md 和 DEVELOPMENT.md

---

**版本**: v1.0.0
**最后更新**: 2026-03-10
