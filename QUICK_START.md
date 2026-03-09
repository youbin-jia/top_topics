# AI自媒体自动选题系统 - 快速开始指南

## 🚀 5分钟快速启动

### 前置条件

确保已安装：
- Docker & Docker Compose
- Git

### 第一步：获取代码

```bash
git clone https://github.com/youbin-jia/top_topics.git
cd top_topics
```

### 第二步：配置环境

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置（必须修改数据库密码）
vim .env
```

**最小配置示例**：
```env
SECRET_KEY=your-secret-key-here-change-it
DB_PASSWORD=your-database-password
DEBUG=True
```

### 第三步：启动服务

```bash
# 一键启动所有服务
docker-compose up -d

# 查看启动日志
docker-compose logs -f backend
```

等待看到以下日志表示启动成功：
```
✅ Django is running at http://0.0.0.0:8000
✅ Celery worker is ready
✅ Database connection successful
```

### 第四步：初始化

```bash
# 创建管理员账号
docker-compose exec backend python manage.py createsuperuser

# 输入用户名、邮箱和密码
Username: admin
Email: admin@example.com
Password: ********
```

### 第五步：访问系统

系统已成功启动！现在可以访问：

| 服务 | 地址 | 说明 |
|------|------|------|
| 🌐 API文档 | http://localhost:8000/swagger/ | 交互式API文档 |
| 🔧 管理后台 | http://localhost:8000/admin/ | Django管理界面 |
| 💻 前端界面 | http://localhost:3000 | 用户界面（如果启动） |
| 📊 监控面板 | http://localhost:3001 | Grafana监控 |

---

## 📖 基础使用流程

### 1. 登录获取Token

```bash
# 使用curl登录
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your_password"
  }'

# 响应
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

# 保存token
export TOKEN="eyJ0eXAiOiJKV1QiLCJhbGc..."
```

### 2. 添加数据源

```bash
# 通过管理后台（推荐）
# 访问 http://localhost:8000/admin/
# 数据收集 → 数据源 → 添加数据源

# 或通过API
curl -X POST http://localhost:8000/api/v1/datasources/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "示例新闻源",
    "source_type": "news",
    "base_url": "https://example.com/news",
    "config": {
      "delay": 2.0,
      "pages": 3
    }
  }'
```

### 3. 获取热门话题

```bash
# 获取热门话题
curl -X GET "http://localhost:8000/api/v1/topics/hot/?limit=10" \
  -H "Authorization: Bearer $TOKEN"

# 响应示例
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "人工智能最新进展",
      "heat_score": 0.92,
      "keywords": ["AI", "深度学习"],
      "trend": "rising"
    }
  ]
}
```

### 4. 获取个性化推荐

```bash
# 获取推荐
curl -X GET "http://localhost:8000/api/v1/recommendations/personalized/" \
  -H "Authorization: Bearer $TOKEN"
```

### 5. 生成内容

```bash
# 生成标题
curl -X POST http://localhost:8000/api/v1/content/generate_title/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["人工智能", "应用"],
    "category": "news",
    "n_titles": 5
  }'

# 生成大纲
curl -X POST http://localhost:8000/api/v1/content/generate_outline/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topic_name": "AI应用场景",
    "keywords": ["AI", "应用"],
    "style": "informative"
  }'
```

### 6. 提交反馈

```bash
# 提交点赞反馈
curl -X POST http://localhost:8000/api/v1/feedback/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topic_id": 1,
    "type": "like"
  }'
```

---

## 🔧 常用操作

### 查看服务状态

```bash
# 查看所有容器状态
docker-compose ps

# 查看资源使用
docker stats

# 查看日志
docker-compose logs -f backend
docker-compose logs -f celery_worker
```

### 管理任务

```bash
# 查看Celery任务
docker-compose exec backend celery -A config inspect active

# 手动触发爬取
docker-compose exec backend celery -A config call \
  apps.data_collection.tasks.daily_crawl_all_sources

# 重启服务
docker-compose restart backend
docker-compose restart celery_worker
```

### 数据库操作

```bash
# 进入数据库
docker-compose exec db mysql -u root -p

# 备份数据库
docker-compose exec db mysqldump -u root -p top_topics > backup.sql

# 执行迁移
docker-compose exec backend python manage.py migrate
```

### 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷（清空数据）
docker-compose down -v
```

---

## 🐛 故障排查

### 问题：服务启动失败

```bash
# 检查端口占用
lsof -i :8000
lsof -i :3306

# 查看错误日志
docker-compose logs backend

# 重新构建
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 问题：数据库连接失败

```bash
# 检查数据库是否运行
docker-compose ps db

# 查看数据库日志
docker-compose logs db

# 重启数据库
docker-compose restart db

# 等待30秒后重试
sleep 30
docker-compose restart backend
```

### 问题：API请求失败

```bash
# 检查后端日志
docker-compose logs backend

# 检查token是否有效
curl -X POST http://localhost:8000/api/v1/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "your_refresh_token"}'

# 检查CORS配置
# 编辑 .env 文件
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

---

## 📚 下一步

1. **配置数据源**：添加更多数据源以获取更丰富的话题
2. **提交反馈**：多提交反馈以优化推荐质量
3. **创建内容**：使用AI辅助生成标题和大纲
4. **监控性能**：访问Grafana查看系统性能
5. **阅读文档**：查看 [USER_GUIDE.md](USER_GUIDE.md) 了解更多功能

---

## 💡 提示

- 首次运行需要下载数据库镜像，可能需要几分钟
- 建议至少配置2GB内存给Docker
- 生产环境请修改默认密码和密钥
- 定期备份重要数据

---

## 🎯 快速示例脚本

创建一个完整的测试脚本：

```bash
#!/bin/bash
# test_api.sh - 测试API功能

# 配置
API_URL="http://localhost:8000/api/v1"
USERNAME="admin"
PASSWORD="your_password"

# 1. 登录
echo "1. 登录获取Token..."
TOKEN=$(curl -s -X POST $API_URL/auth/login/ \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}" \
  | jq -r '.access')

echo "Token: $TOKEN"

# 2. 获取热门话题
echo -e "\n2. 获取热门话题..."
curl -s -X GET "$API_URL/topics/hot/?limit=5" \
  -H "Authorization: Bearer $TOKEN" | jq

# 3. 获取个性化推荐
echo -e "\n3. 获取个性化推荐..."
curl -s -X GET "$API_URL/recommendations/personalized/" \
  -H "Authorization: Bearer $TOKEN" | jq

# 4. 生成标题
echo -e "\n4. 生成标题..."
curl -s -X POST "$API_URL/content/generate_title/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["AI", "深度学习"],
    "category": "news",
    "n_titles": 3
  }' | jq

# 5. 提交反馈
echo -e "\n5. 提交反馈..."
curl -s -X POST "$API_URL/feedback/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "topic_id": 1,
    "type": "like"
  }' | jq

echo -e "\n✅ 测试完成！"
```

运行测试：
```bash
chmod +x test_api.sh
./test_api.sh
```

---

## 📞 获取帮助

- 📖 完整文档：查看 [USER_GUIDE.md](USER_GUIDE.md)
- 🔧 开发指南：查看 [DEVELOPMENT.md](DEVELOPMENT.md)
- 🏗️ 架构设计：查看 [ARCHITECTURE.md](ARCHITECTURE.md)
- 💬 API文档：http://localhost:8000/swagger/

---

**准备就绪！开始使用AI自媒体选题系统吧！** 🎉
