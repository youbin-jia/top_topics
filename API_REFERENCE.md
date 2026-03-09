# API接口参考文档

## 基础信息

**Base URL**: `http://localhost:8000/api/v1/`

**认证方式**: JWT Bearer Token

**内容类型**: `application/json`

---

## 认证接口

### 用户登录

获取访问令牌。

**请求**:
```http
POST /api/v1/auth/login/
Content-Type: application/json

{
  "username": "string",
  "password": "string"
}
```

**响应**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**状态码**:
- `200`: 登录成功
- `401`: 认证失败

---

### 刷新Token

刷新访问令牌。

**请求**:
```http
POST /api/v1/auth/refresh/
Content-Type: application/json

{
  "refresh": "string"
}
```

**响应**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

## 话题接口

### 获取话题列表

获取所有话题列表，支持过滤和排序。

**请求**:
```http
GET /api/v1/topics/
Authorization: Bearer <token>
```

**查询参数**:
| 参数 | 类型 | 必需 | 描述 |
|-----|------|------|------|
| page | integer | 否 | 页码，默认1 |
| page_size | integer | 否 | 每页数量，默认20 |
| search | string | 否 | 搜索关键词 |
| category | string | 否 | 话题分类 |
| min_score | float | 否 | 最小热度分数 |
| trend | string | 否 | 趋势：rising/falling/stable |
| ordering | string | 否 | 排序字段：heat_score, -created_at |

**响应**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "人工智能",
      "description": "AI相关话题",
      "keywords": ["AI", "机器学习"],
      "heat_score": 0.92,
      "trend": "rising",
      "article_count": 1234,
      "view_count": 56789,
      "first_seen_at": "2026-03-01T00:00:00Z",
      "last_updated_at": "2026-03-10T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

---

### 获取热门话题

获取热度最高的话题。

**请求**:
```http
GET /api/v1/topics/hot/
Authorization: Bearer <token>
```

**查询参数**:
| 参数 | 类型 | 必需 | 描述 |
|-----|------|------|------|
| limit | integer | 否 | 返回数量，默认10 |

**响应**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "ChatGPT应用",
      "heat_score": 0.95,
      "trend": "rising",
      "article_count": 2345,
      "keywords": ["ChatGPT", "AI"]
    }
  ]
}
```

---

### 获取趋势话题

获取上升中的话题。

**请求**:
```http
GET /api/v1/topics/trending/
Authorization: Bearer <token>
```

**查询参数**:
| 参数 | 类型 | 必需 | 描述 |
|-----|------|------|------|
| limit | integer | 否 | 返回数量，默认10 |

**响应**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "元宇宙",
      "heat_score": 0.88,
      "trend": "rising",
      "growth_rate": 0.25
    }
  ]
}
```

---

### 获取话题详情

获取单个话题的详细信息。

**请求**:
```http
GET /api/v1/topics/{id}/
Authorization: Bearer <token>
```

**路径参数**:
| 参数 | 类型 | 描述 |
|-----|------|------|
| id | integer | 话题ID |

**响应**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "name": "人工智能",
    "description": "AI技术和应用",
    "keywords": ["AI", "机器学习", "深度学习"],
    "heat_score": 0.92,
    "trend": "rising",
    "article_count": 1234,
    "view_count": 56789,
    "engagement_rate": 0.68,
    "related_topics": [
      {
        "id": 2,
        "name": "机器学习",
        "similarity": 0.85
      }
    ],
    "first_seen_at": "2026-03-01T00:00:00Z",
    "last_updated_at": "2026-03-10T00:00:00Z"
  }
}
```

---

## 推荐接口

### 获取个性化推荐

获取基于用户兴趣的个性化推荐。

**请求**:
```http
GET /api/v1/recommendations/personalized/
Authorization: Bearer <token>
```

**查询参数**:
| 参数 | 类型 | 必需 | 描述 |
|-----|------|------|------|
| limit | integer | 否 | 返回数量，默认20 |

**响应**:
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "深度学习框架比较",
      "recommendation_score": 0.85,
      "heat_score": 0.78,
      "keywords": ["深度学习", "TensorFlow", "PyTorch"],
      "reasons": [
        "您对深度学习感兴趣",
        "近期热门话题",
        "与您浏览历史相关"
      ]
    }
  ]
}
```

---

### 获取热门推荐

获取热门内容推荐。

**请求**:
```http
GET /api/v1/recommendations/hot/
Authorization: Bearer <token>
```

**查询参数**:
| 参数 | 类型 | 必需 | 描述 |
|-----|------|------|------|
| limit | integer | 否 | 返回数量，默认10 |

**响应**: 同个性化推荐

---

## 反馈接口

### 提交反馈

提交用户对话题的反馈。

**请求**:
```http
POST /api/v1/feedback/
Authorization: Bearer <token>
Content-Type: application/json

{
  "topic_id": 1,
  "type": "like",
  "dwell_time": 30,
  "scroll_depth": 0.8,
  "source": "recommendation"
}
```

**请求体参数**:
| 参数 | 类型 | 必需 | 描述 |
|-----|------|------|------|
| topic_id | integer | 是 | 话题ID |
| type | string | 是 | 反馈类型：click/like/share/collect/skip |
| dwell_time | integer | 否 | 停留时间（秒） |
| scroll_depth | float | 否 | 滚动深度（0-1） |
| source | string | 否 | 反馈来源 |

**响应**:
```json
{
  "success": true,
  "message": "反馈已记录"
}
```

**状态码**:
- `201`: 创建成功
- `400`: 参数错误

---

## 内容生成接口

### 生成标题

AI生成多个备选标题。

**请求**:
```http
POST /api/v1/content/generate_title/
Authorization: Bearer <token>
Content-Type: application/json

{
  "topic_id": 1,
  "keywords": ["AI", "深度学习"],
  "category": "news",
  "n_titles": 5
}
```

**请求体参数**:
| 参数 | 类型 | 必需 | 描述 |
|-----|------|------|------|
| topic_id | integer | 否 | 话题ID |
| keywords | array | 是 | 关键词列表 |
| category | string | 否 | 标题类别：news/guide/list/question/shock |
| n_titles | integer | 否 | 生成数量，默认5 |

**响应**:
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

---

### 生成大纲

AI生成文章大纲。

**请求**:
```http
POST /api/v1/content/generate_outline/
Authorization: Bearer <token>
Content-Type: application/json

{
  "topic_id": 1,
  "topic_name": "AI在教育中的应用",
  "keywords": ["AI", "教育", "个性化学习"],
  "style": "informative",
  "n_sections": 4
}
```

**请求体参数**:
| 参数 | 类型 | 必需 | 描述 |
|-----|------|------|------|
| topic_id | integer | 否 | 话题ID |
| topic_name | string | 是 | 主题名称 |
| keywords | array | 是 | 关键词列表 |
| style | string | 否 | 文章风格：informative/persuasive/entertaining/educational |
| n_sections | integer | 否 | 章节数量，默认3 |

**响应**:
```json
{
  "success": true,
  "data": {
    "title": "AI在教育中的应用",
    "style": "informative",
    "quality_score": 0.82,
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
        "writing_tips": [
          "提供客观数据",
          "引用权威来源"
        ]
      }
    ],
    "conclusion": {
      "content": "综上所述，AI正在重塑教育行业...",
      "summary_points": ["AI教育", "个性化学习"],
      "call_to_action": "欢迎分享您的观点",
      "word_count": 150
    }
  }
}
```

---

## 用户接口

### 获取用户信息

获取当前登录用户信息。

**请求**:
```http
GET /api/v1/users/me/
Authorization: Bearer <token>
```

**响应**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "user123",
    "email": "user@example.com",
    "role": "creator",
    "bio": "AI技术爱好者",
    "preferred_categories": ["科技", "AI", "互联网"],
    "top_interests": ["人工智能", "机器学习", "深度学习"],
    "created_at": "2026-01-01T00:00:00Z"
  }
}
```

---

### 获取用户画像

获取用户详细画像和行为统计。

**请求**:
```http
GET /api/v1/users/profile/
Authorization: Bearer <token>
```

**响应**:
```json
{
  "success": true,
  "data": {
    "user_id": 1,
    "total_clicks": 123,
    "total_likes": 45,
    "total_shares": 12,
    "total_collects": 23,
    "active_days": 30,
    "last_active_at": "2026-03-10T00:00:00Z",
    "top_interests": [
      {"keyword": "人工智能", "score": 0.95},
      {"keyword": "机器学习", "score": 0.88}
    ]
  }
}
```

---

### 更新用户偏好

更新用户的兴趣偏好设置。

**请求**:
```http
PUT /api/v1/users/update_preferences/
Authorization: Bearer <token>
Content-Type: application/json

{
  "categories": ["科技", "AI", "互联网"],
  "keywords": {
    "人工智能": 0.9,
    "机器学习": 0.85,
    "深度学习": 0.8
  }
}
```

**响应**:
```json
{
  "success": true,
  "message": "偏好已更新"
}
```

---

## 错误响应格式

所有错误响应遵循统一格式：

```json
{
  "success": false,
  "message": "请求失败的具体原因",
  "errors": {
    "field_name": ["错误详情1", "错误详情2"]
  }
}
```

**常见错误码**:

| 状态码 | 描述 | 可能原因 |
|-------|------|---------|
| 400 | 请求参数错误 | 缺少必填字段、字段格式错误 |
| 401 | 未认证 | Token无效或已过期 |
| 403 | 无权限 | 没有访问该资源的权限 |
| 404 | 资源不存在 | 请求的话题、用户等不存在 |
| 429 | 请求过于频繁 | 触发速率限制 |
| 500 | 服务器内部错误 | 服务器异常 |

---

## 速率限制

API请求受到速率限制：

- **认证接口**: 5次/分钟
- **其他接口**: 60次/分钟
- **内容生成**: 10次/分钟

超出限制将返回 `429 Too Many Requests`。

---

## 分页

支持分页的接口返回格式：

```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 100,
    "total_pages": 5,
    "has_next": true,
    "has_previous": false
  }
}
```

**分页参数**:
- `page`: 页码，从1开始
- `page_size`: 每页数量，默认20，最大100

---

## 过滤和排序

### 过滤

通过查询参数过滤：

```http
GET /api/v1/topics/?category=AI&min_score=0.5&trend=rising
```

### 排序

通过`ordering`参数排序：

```http
GET /api/v1/topics/?ordering=-heat_score

# 多字段排序
GET /api/v1/topics/?ordering=-heat_score,created_at
```

**排序规则**:
- 前缀`-`表示降序
- 无前缀表示升序
- 支持多字段排序，用逗号分隔

---

## 批量操作

### 批量提交反馈

```http
POST /api/v1/feedback/batch/
Authorization: Bearer <token>
Content-Type: application/json

{
  "feedbacks": [
    {
      "topic_id": 1,
      "type": "click"
    },
    {
      "topic_id": 2,
      "type": "like"
    }
  ]
}
```

---

## Webhook通知（可选）

系统支持Webhook通知，当特定事件发生时推送通知：

### 配置Webhook

```http
POST /api/v1/webhooks/
Authorization: Bearer <token>
Content-Type: application/json

{
  "url": "https://your-server.com/webhook",
  "events": ["topic.trending", "recommendation.ready"],
  "secret": "your_webhook_secret"
}
```

### Webhook载荷示例

```json
{
  "event": "topic.trending",
  "timestamp": "2026-03-10T00:00:00Z",
  "data": {
    "topic_id": 1,
    "topic_name": "AI突破",
    "heat_score": 0.95
  },
  "signature": "sha256=..."
}
```

---

## SDK和客户端库

### Python SDK

```python
from top_topics_client import TopTopicsClient

# 初始化客户端
client = TopTopicsClient(
    base_url='http://localhost:8000/api/v1',
    username='your_username',
    password='your_password'
)

# 获取热门话题
hot_topics = client.topics.get_hot(limit=10)

# 获取推荐
recommendations = client.recommendations.get_personalized()

# 提交反馈
client.feedback.submit(topic_id=1, type='like')

# 生成标题
titles = client.content.generate_title(
    keywords=['AI', '深度学习'],
    category='news'
)
```

### JavaScript SDK

```javascript
import { TopTopicsClient } from '@toptopics/sdk';

const client = new TopTopicsClient({
  baseURL: 'http://localhost:8000/api/v1',
  username: 'your_username',
  password: 'your_password'
});

// 获取热门话题
const hotTopics = await client.topics.getHot({ limit: 10 });

// 获取推荐
const recommendations = await client.recommendations.getPersonalized();

// 提交反馈
await client.feedback.submit({
  topic_id: 1,
  type: 'like'
});

// 生成标题
const titles = await client.content.generateTitle({
  keywords: ['AI', '深度学习'],
  category: 'news'
});
```

---

## API版本控制

当前API版本: `v1`

未来版本发布时，将：
- 旧版本API继续可用6个月
- 在响应头中添加弃用警告
- 提供迁移指南

访问不同版本：
- `/api/v1/` - 当前稳定版本
- `/api/v2/` - 未来版本（如适用）

---

## 测试API

### Swagger UI

访问交互式API文档：
```
http://localhost:8000/swagger/
```

在Swagger UI中可以：
- 查看所有API端点
- 直接测试API调用
- 查看请求/响应示例

### ReDoc

访问美观的API文档：
```
http://localhost:8000/redoc/
```

### Postman Collection

导入Postman集合进行测试：
```
下载链接: http://localhost:8000/api/v1/schema/
```

---

## 最佳实践

### 1. 缓存Token

```javascript
// 存储token
localStorage.setItem('access_token', response.access);
localStorage.setItem('refresh_token', response.refresh);

// 自动刷新token
axios.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token');
      const { access } = await refreshTokenAPI(refreshToken);
      localStorage.setItem('access_token', access);
      error.config.headers.Authorization = `Bearer ${access}`;
      return axios.request(error.config);
    }
    return Promise.reject(error);
  }
);
```

### 2. 错误处理

```javascript
try {
  const response = await api.getTopics();
  // 处理成功响应
} catch (error) {
  if (error.response) {
    switch (error.response.status) {
      case 401:
        // Token过期，重新登录
        break;
      case 429:
        // 请求过于频繁，稍后重试
        await sleep(60000);
        break;
      default:
        // 显示错误消息
        console.error(error.response.data.message);
    }
  }
}
```

### 3. 批量请求优化

```javascript
// 使用批量接口减少请求次数
const topicIds = [1, 2, 3, 4, 5];

// 不好的做法：多次请求
for (const id of topicIds) {
  await api.getTopic(id);  // 5次请求
}

// 好的做法：批量请求
const topics = await api.getTopics({ ids: topicIds });  // 1次请求
```

---

**API文档版本**: v1.0.0
**最后更新**: 2026-03-10
