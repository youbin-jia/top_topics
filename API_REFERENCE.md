# API 参考（v1）

基础前缀：`/api/v1/`

## 1. Topics

### `GET /topics/`

参数：

- `limit`（默认 20）
- `category`（按关键词过滤）
- `min_score`（最小热度）

### `GET /topics/{id}/`

返回话题详情、标题摘要、参考链接（含 `open_url` 中转链接）。

### `GET /topics/hot/`

热门话题列表，参数：`limit`。

### `GET /topics/trending/`

上升趋势话题列表，参数：`limit`。

### `GET /topics/open-link/?url=...`

安全中转原文链接，校验协议后 302 跳转。

## 2. Recommendations

### `GET /recommendations/hot/`

热门推荐，参数：`limit`。

### `GET /recommendations/personalized/`

个性化推荐（未登录时回退热门），参数：`limit`。

## 3. Feedback

### `POST /feedback/`（需要登录）

请求示例：

```json
{
  "topic_id": 123,
  "type": "like",
  "source": "api",
  "dwell_time": 12.5,
  "scroll_depth": 0.6
}
```

## 4. Content Generation

### `POST /content/generate_title/`（需要登录）

请求示例：

```json
{
  "topic_id": 123,
  "keywords": ["AI", "创业"],
  "category": "news",
  "n_titles": 5
}
```

### `POST /content/generate_outline/`（需要登录）

请求示例：

```json
{
  "topic_id": 123,
  "topic_name": "AI 应用趋势",
  "keywords": ["AI", "应用"],
  "style": "informative",
  "n_sections": 3
}
```

## 5. Users

### `GET /users/{id}/`（需要登录）

`id` 可为 `me`。

### `GET /users/profile/`（需要登录）

返回用户画像统计。

### `PUT /users/update_preferences/`（需要登录）

请求示例：

```json
{
  "categories": ["tech", "ai"],
  "keywords": {"ai": 0.8, "创业": 0.6}
}
```

## 6. 响应约定

成功响应通常为：

```json
{
  "success": true,
  "data": {}
}
```

失败响应通常包含：

```json
{
  "success": false,
  "message": "错误说明"
}
```
