# 用户操作手册

## 1. 你能做什么

- 拉取实时内容并生成热点话题
- 查看热门/趋势话题
- 查看话题详情与原文参考链接
- 获取个性化推荐并提交反馈

## 2. 一次完整操作

### 步骤 1：执行流水线

```bash
docker exec -i top_topics_backend python manage.py run_realdata_pipeline --threshold 1 --hours 24 --top-n 10
```

### 步骤 2：查看热门话题

访问 `GET /api/v1/topics/hot/`。

### 步骤 3：查看话题详情

访问 `GET /api/v1/topics/{id}/`，关注：

- `title_summary`
- `description`
- `reference_links` 与 `open_url`

### 步骤 4：获取推荐

访问 `GET /api/v1/recommendations/personalized/`（未登录时回退热门）。

### 步骤 5：提交反馈

`POST /api/v1/feedback/`，反馈会进入偏好学习流程。

## 3. 常见配置场景

### 临时停用某些平台抓取

```env
ENABLED_SOCIAL_SOURCES=wechat,bilibili
```

### 扩展公众号词池

```env
WECHAT_SOGOU_KEYWORDS=科技,AI,互联网,创业,数码,手机,电商,出海
WECHAT_SOGOU_MAX_PER_KEYWORD=8
```

### 暂停 LLM，仅保留规则兜底

```env
KIMI_ENABLED=false
```

## 4. 故障排查

### 问题：模型请求全超时

处理：

1. 降低 `KIMI_TIMEOUT` 到 `10-12`
2. 把 `KIMI_MAX_RETRIES` 设为 `1`
3. 保持 `KIMI_FAIL_FAST_ON_TIMEOUT=true`
4. 必要时先 `KIMI_ENABLED=false`

### 问题：话题标题质量差

处理：

1. 先确认 `TopN` 是否过大（建议 10）
2. 调整 `TOPIC_MAIN_KEYWORD_BLACKLIST`
3. 保持聚类开启（不要加 `--no-cluster-first`）

### 问题：平台数据为空

处理：

1. 查看该平台是否在 `ENABLED_SOCIAL_SOURCES`
2. 检查 `RSSHUB_MIRRORS` 是否可用
3. 公众号场景加大 `WECHAT_SOGOU_KEYWORDS`
