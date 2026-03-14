# 开发指南

## 1. 本地开发环境

```bash
cd /home/jyb/Code/top_topics
python -m venv .venv
source .venv/bin/activate
pip install -r backend/config/requirements.txt
cp .env.example .env
```

数据库迁移：

```bash
python backend/manage.py migrate
python backend/manage.py createsuperuser
```

## 2. 启动方式

### 方式 A：容器开发（推荐）

```bash
docker compose up -d --build
```

### 方式 B：本机进程开发

```bash
python backend/manage.py runserver
celery -A config worker -l info
celery -A config beat -l info
```

## 3. 核心代码位置

- 采集：`backend/apps/data_collection/`
- 话题分析：`backend/apps/topic_analysis/`
- 推荐：`backend/apps/recommendation/`
- 反馈学习：`backend/apps/feedback/`
- API：`backend/api/v1/`
- 配置：`backend/config/settings/base.py`

## 4. 真实数据流水线调试

```bash
docker exec -i top_topics_backend python manage.py run_realdata_pipeline --threshold 1 --hours 24 --top-n 10
```

只验证分析阶段：

```bash
docker exec -i top_topics_backend python manage.py run_realdata_pipeline --no-crawl --threshold 1 --hours 24 --top-n 10
```

## 5. LLM 相关调试

关键配置：

- `KIMI_ENABLED`
- `KIMI_TIMEOUT`
- `KIMI_MAX_RETRIES`
- `KIMI_FAIL_FAST_ON_TIMEOUT`
- `KIMI_CIRCUIT_COOLDOWN_SEC`

建议排错顺序：

1. 先确认 `.env` 中 `KIMI_BASE_URL/KIMI_MODEL/KIMI_API_KEY` 正确
2. 观察日志中的 `Kimi 请求准备` 与超时信息
3. 若持续超时，先用 `KIMI_ENABLED=false` 验证流程稳定性

## 6. 文档与配置同步规范

- 涉及新增环境变量时，必须同步更新：
  - `.env.example`
  - `README.md`
  - `ARCHITECTURE.md`（如影响架构行为）
- 涉及采集策略变更时，必须同步更新：
  - `docs/MODULE_GUIDE.md`
  - `USER_GUIDE.md` 的故障排查部分

## 7. 测试与检查

```bash
python3 -m py_compile backend/apps/topic_analysis/llm.py
python3 -m py_compile backend/apps/data_collection/management/commands/run_realdata_pipeline.py
```

如需跑 pytest：

```bash
pytest
```
