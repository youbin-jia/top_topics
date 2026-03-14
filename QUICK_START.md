# 快速开始

## 1) 启动服务

```bash
cd /home/jyb/Code/top_topics
cp .env.example .env
docker compose up -d --build
```

## 2) 初始化（首次）

```bash
docker exec -i top_topics_backend python manage.py migrate
docker exec -i top_topics_backend python manage.py createsuperuser
```

## 3) 拉取真实数据并生成话题

```bash
docker exec -i top_topics_backend python manage.py run_realdata_pipeline --threshold 1 --hours 24 --top-n 10
```

## 4) 验证

- API 文档：`http://localhost:8000/swagger/`
- 热门话题：`http://localhost:8000/api/v1/topics/hot/`
- 推荐列表：`http://localhost:8000/api/v1/recommendations/hot/`

## 5) 最小可用环境变量

```env
SECRET_KEY=change-me
DB_NAME=top_topics
DB_USER=root
DB_PASSWORD=your-password
DB_HOST=mysql
DB_PORT=3306

KIMI_BASE_URL=https://api.moonshot.cn/v1
KIMI_MODEL=kimi-k2.5
KIMI_API_KEY=sk-xxxx
```

## 6) 常见问题

### LLM 一直超时

- 把 `KIMI_TIMEOUT` 调低（如 12）
- `KIMI_MAX_RETRIES=1`
- 保持 `KIMI_FAIL_FAST_ON_TIMEOUT=true`
- 需要完全关闭模型时：`KIMI_ENABLED=false`

### 某平台抓不到数据

- 检查是否启用：`ENABLED_SOCIAL_SOURCES`
- 检查镜像：`RSSHUB_MIRRORS`
- 公众号可增加词池：`WECHAT_SOGOU_KEYWORDS`

### 只做处理，不重新抓取

```bash
docker exec -i top_topics_backend python manage.py run_realdata_pipeline --no-crawl --threshold 1 --hours 24 --top-n 10
```
