# 部署指南

## 1. 生产部署建议

- 使用 Docker Compose 部署后端、MySQL、Redis
- `.env` 与镜像分离管理，不写入仓库
- 建议把 `DEBUG=False`，并设置 `ALLOWED_HOSTS`

## 2. 基础部署步骤

```bash
cd /home/jyb/Code/top_topics
cp .env.example .env
docker compose up -d --build
docker exec -i top_topics_backend python manage.py migrate
```

## 3. 关键环境变量

### Django

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`

### 数据库/缓存

- `DB_*`
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`

### 话题与采集

- `ENABLED_SOCIAL_SOURCES`
- `RSSHUB_MIRRORS`
- `WECHAT_SOGOU_KEYWORDS`
- `TOPIC_SOURCE_PENALTY`
- `TOPIC_MAIN_KEYWORD_BLACKLIST`

### LLM

- `KIMI_BASE_URL`
- `KIMI_MODEL`
- `KIMI_API_KEY`
- `KIMI_ENABLED`
- `KIMI_TIMEOUT`
- `KIMI_MAX_RETRIES`
- `KIMI_FAIL_FAST_ON_TIMEOUT`
- `KIMI_CIRCUIT_COOLDOWN_SEC`

## 4. 首次数据填充

```bash
docker exec -i top_topics_backend python manage.py run_realdata_pipeline --threshold 1 --hours 24 --top-n 10
```

## 5. 日常运维命令

```bash
docker compose ps
docker compose logs -f backend
docker compose logs -f celery_worker
docker compose restart backend
```

## 6. 故障处理

### LLM 超时导致慢

- 降低 `KIMI_TIMEOUT`
- 设置 `KIMI_MAX_RETRIES=1`
- 保持 `KIMI_FAIL_FAST_ON_TIMEOUT=true`
- 必要时 `KIMI_ENABLED=false`

### 社媒抓取为空

- 核对 `ENABLED_SOCIAL_SOURCES`
- 检查 `RSSHUB_MIRRORS` 可用性
- 增加 `WECHAT_SOGOU_KEYWORDS` 覆盖面

### 话题同质化

- 调高 `TOPIC_SOURCE_PENALTY`
- 扩展 `TOPIC_MAIN_KEYWORD_BLACKLIST`
