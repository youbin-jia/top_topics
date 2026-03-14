# AI 自媒体自动选题系统

基于 Django 的热点采集与话题分析系统，支持多源抓取、聚类去同质化、TopN 送入大模型总结，并通过 API 提供热点与推荐能力。

## 当前能力（2026-03）

- 多源采集：RSS + 社媒（`wechat` / `bilibili` / `xiaohongshu` / `douyin`）
- 容灾策略：RSSHub 多镜像 + 平台 API/HTML 兜底抓取
- 话题生成：先聚类再排序，仅对 `TopN` 调用 LLM，降低 token 成本
- 去同质化：同源惩罚 + 主关键词黑名单 + 标题归一去重
- LLM 稳定性：失败重试 + 超时熔断 + 规则兜底（保证流水线可完成）

## 技术栈

- 后端：Django 4.2、DRF、Celery
- 数据：MySQL（主库）、Redis（缓存/队列）
- 处理：jieba、BeautifulSoup、feedparser、requests
- 前端：`frontend/web`（独立工程）
- 部署：Docker Compose

## 快速启动（Docker）

```bash
cd /home/jyb/Code/top_topics
cp .env.example .env
docker compose up -d --build
```

访问地址：

- API 根：`http://localhost:8000/api/v1/`
- Swagger：`http://localhost:8000/swagger/`

## 运行真实数据流水线

```bash
docker exec -i top_topics_backend python manage.py run_realdata_pipeline --threshold 1 --hours 24 --top-n 10
```

常用参数：

- `--no-crawl`：只处理已有 `RawContent`
- `--threshold`：话题发现阈值
- `--hours`：统计窗口（小时）
- `--top-n`：仅对前 N 个候选调用 LLM
- `--no-cluster-first`：关闭先聚类后筛选

## 关键环境变量

### LLM（Kimi）

- `KIMI_BASE_URL`（如 `https://api.moonshot.cn/v1`）
- `KIMI_MODEL`（如 `kimi-k2.5`）
- `KIMI_API_KEY`
- `KIMI_ENABLED`（`true/false`）
- `KIMI_TIMEOUT`、`KIMI_MAX_RETRIES`
- `KIMI_FAIL_FAST_ON_TIMEOUT`
- `KIMI_CIRCUIT_COOLDOWN_SEC`

### 社媒采集与容灾

- `ENABLED_SOCIAL_SOURCES=wechat,bilibili,xiaohongshu,douyin`
- `RSSHUB_MIRRORS=https://rsshub.app,https://rsshub.rssforever.com,...`
- `WECHAT_SOGOU_KEYWORDS=科技,AI,互联网,创业,数码`
- `WECHAT_SOGOU_MAX_PER_KEYWORD=6`

### 去同质化

- `TOPIC_SOURCE_PENALTY=0.35`
- `TOPIC_MAIN_KEYWORD_BLACKLIST=全文,查看,推荐,...`

## 目录结构（实际）

```text
top_topics/
├── backend/
│   ├── api/v1/                      # API 入口
│   ├── apps/
│   │   ├── data_collection/         # 采集与入库
│   │   ├── topic_analysis/          # 话题发现、聚类、LLM总结
│   │   ├── recommendation/          # 推荐服务
│   │   ├── content_generation/      # 标题/大纲生成
│   │   ├── feedback/                # 反馈学习
│   │   └── users/                   # 用户域
│   └── config/                      # settings/urls/celery
├── frontend/
├── docs/
└── *.md                             # 文档入口
```

## 文档入口

- 架构：`ARCHITECTURE.md`
- 快速上手：`QUICK_START.md`
- API：`API_REFERENCE.md`
- 开发：`DEVELOPMENT.md`
- 部署：`DEPLOYMENT_GUIDE.md`
- 用户操作：`USER_GUIDE.md`
- 文档索引：`DOCUMENTATION_INDEX.md`
