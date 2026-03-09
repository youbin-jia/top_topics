#!/bin/bash

# 部署脚本
set -e

echo "================================"
echo "AI自媒体自动选题系统 - 部署脚本"
echo "================================"

# 拉取最新代码
echo "拉取最新代码..."
git pull origin main
echo "✓ 代码已更新"

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装/更新依赖
echo "更新依赖..."
pip install -r backend/config/requirements.txt --upgrade
echo "✓ 依赖已更新"

# 数据库迁移
echo "运行数据库迁移..."
python backend/manage.py makemigrations
python backend/manage.py migrate
echo "✓ 数据库迁移完成"

# 收集静态文件
echo "收集静态文件..."
python backend/manage.py collectstatic --noinput
echo "✓ 静态文件收集完成"

# 清理缓存
echo "清理缓存..."
python backend/manage.py clear_cache
echo "✓ 缓存已清理"

# 重启服务
echo "重启服务..."
sudo systemctl restart top_topics_backend
sudo systemctl restart top_topics_celery
sudo systemctl restart top_topics_celery_beat
sudo systemctl restart nginx
echo "✓ 服务已重启"

# 检查服务状态
echo "检查服务状态..."
sudo systemctl status top_topics_backend --no-pager
sudo systemctl status top_topics_celery --no-pager
sudo systemctl status nginx --no-pager

echo "================================"
echo "部署完成!"
echo "================================"
echo ""
echo "服务状态:"
echo "- 后端API: http://localhost:8000/api/v1/"
echo "- 管理后台: http://localhost:8000/admin/"
echo "- API文档: http://localhost:8000/swagger/"
echo ""
