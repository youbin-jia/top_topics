# 模块开发指南

## 1. `apps.data_collection`

职责：

- 管理 `DataSource`
- 抓取并落库 `RawContent`
- 对多平台做 RSSHub + API/HTML 双路兜底

关键文件：

- `models.py`
- `tasks.py`
- `crawlers/social_feed_crawler.py`
- `management/commands/run_realdata_pipeline.py`

## 2. `apps.topic_analysis`

职责：

- 从处理后的内容中发现候选话题
- 聚类、去同质化排序、TopN 截断
- 调用 LLM 生成标题与概要（带兜底）

关键文件：

- `tasks.py`
- `llm.py`
- `models.py`
- `management/commands/backfill_topic_descriptions.py`

## 3. `apps.recommendation`

职责：

- 计算个性化推荐
- 维护推荐记录与排序结果

关键文件：

- `engine.py`
- `models.py`

## 4. `apps.feedback`

职责：

- 接收反馈事件
- 更新用户兴趣偏好

关键文件：

- `models.py`
- `learner.py`

## 5. `apps.content_generation`

职责：

- 生成标题和大纲
- 提供质量打分

关键文件：

- `generators.py`
- `models.py`

## 6. `api/v1`

职责：

- 暴露 REST API
- 统一返回结构

关键文件：

- `urls.py`
- `views.py`

## 7. 配置模块 `config/settings`

职责：

- 按环境读取配置
- 提供采集、去同质化、LLM 开关与参数

关键文件：

- `base.py`
- `development.py`
