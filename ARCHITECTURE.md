# 系统架构文档

本文描述当前已落地的后端架构（非泛化蓝图），与代码实现保持一致。

## 1. 总览

```text
DataSource/RawContent
    └─(crawl_source_task)
        data_collection.crawlers
            ├─ RSS 拉取
            ├─ RSSHub 多镜像
            └─ 平台 API/HTML 兜底
                 ↓
          process_raw_content_task
                 ↓
          discover_new_topics
            ├─ 候选聚类
            ├─ 去同质化排序
            ├─ TopN 截断
            └─ LLM/规则总结
                 ↓
         update_topic_heat_scores
                 ↓
              API v1
```

## 2. 模块分层

### 2.1 采集层 `apps.data_collection`

- `DataSource` 维护源配置与状态
- `RawContent` 存储原始抓取内容
- `social_feed_crawler.py` 负责社媒场景：
  - RSSHub 镜像列表轮询
  - B 站、抖音 API 兜底
  - 公众号（搜狗）和小红书页面兜底
  - 去重与短链化处理（避免超长 URL 入库失败）

### 2.2 分析层 `apps.topic_analysis`

- `tasks.py` 核心流程：
  - 关键词聚合
  - 候选聚类与代表生成
  - 同源惩罚、关键词黑名单、标题去重
  - TopN 筛选后调用 LLM（非全量）
- `llm.py`：
  - Kimi 调用（OpenAI 兼容）
  - token 粗估日志
  - 超时重试、失败兜底
  - 熔断机制（超时后冷却期内跳过 LLM）

### 2.3 推荐与反馈层

- `apps.recommendation`：个性化与热门推荐融合
- `apps.feedback`：记录反馈并更新兴趣偏好

### 2.4 API 层 `api/v1`

- `TopicViewSet`：话题列表、热门、趋势、详情、链接中转
- `RecommendationViewSet`：热门与个性化推荐
- `FeedbackViewSet`：反馈上报
- `ContentGenerationViewSet`：标题/大纲生成
- `UserViewSet`：用户信息与偏好更新

## 3. 关键流程

### 3.1 一键流水线

命令：`python manage.py run_realdata_pipeline`

阶段：

1. 确保默认数据源存在并修复配置（含社媒开关）
2. 拉取 active 数据源
3. 处理 pending 原始内容
4. 发现新话题（可配置聚类、阈值、TopN）
5. 更新热度

### 3.2 LLM 生成策略

- 默认只对 TopN 候选调用，控制成本与延迟
- 任何异常都可回落规则摘要，不阻断主流程
- 连续超时会触发熔断，避免每个候选都重复超时

## 4. 配置驱动能力

### 4.1 社媒采集

- `ENABLED_SOCIAL_SOURCES`
- `RSSHUB_MIRRORS`
- `WECHAT_SOGOU_KEYWORDS`
- `WECHAT_SOGOU_MAX_PER_KEYWORD`

### 4.2 去同质化

- `TOPIC_SOURCE_PENALTY`
- `TOPIC_MAIN_KEYWORD_BLACKLIST`

### 4.3 LLM 稳定性

- `KIMI_ENABLED`
- `KIMI_TIMEOUT`
- `KIMI_MAX_RETRIES`
- `KIMI_FAIL_FAST_ON_TIMEOUT`
- `KIMI_CIRCUIT_COOLDOWN_SEC`

## 5. 数据模型（核心）

- `DataSource`：采集源
- `RawContent`：原始内容
- `Topic`：话题实体
- `ContentTopicRelation`：内容-话题关联
- `Recommendation`：推荐记录
- `UserFeedback`：反馈事件

## 6. 设计取舍

- 以“稳定产出”为第一优先：宁可规则兜底，也不让流水线挂起
- 以“多样性”为质量底线：排序层抑制同源/同标题/泛词集中
- 以“可运维”为目标：核心行为尽量由环境变量控制
