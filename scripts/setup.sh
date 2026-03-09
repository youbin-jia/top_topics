#!/bin/bash

# 设置脚本
set -e

echo "================================"
echo "AI自媒体自动选题系统 - 安装脚本"
echo "================================"

# 检查Python版本
echo "检查Python版本..."
python_version=$(python --version 2>&1 | awk '{print $2}')
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "错误: 需要Python $required_version 或更高版本"
    exit 1
fi

echo "✓ Python版本: $python_version"

# 创建虚拟环境
echo "创建虚拟环境..."
if [ ! -d "venv" ]; then
    python -m venv venv
    echo "✓ 虚拟环境已创建"
else
    echo "✓ 虚拟环境已存在"
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装Python依赖..."
pip install --upgrade pip
pip install -r backend/config/requirements.txt
echo "✓ Python依赖安装完成"

# 检查并创建.env文件
if [ ! -f ".env" ]; then
    echo "创建.env配置文件..."
    cp .env.example .env
    echo "✓ .env文件已创建，请编辑配置"
else
    echo "✓ .env文件已存在"
fi

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p logs
mkdir -p data/raw
mkdir -p data/processed
mkdir -p data/models
mkdir -p ml_models
echo "✓ 目录创建完成"

# 数据库迁移
echo "运行数据库迁移..."
python backend/manage.py makemigrations
python backend/manage.py migrate
echo "✓ 数据库迁移完成"

# 创建超级用户（可选）
echo "是否创建超级用户? (y/n)"
read create_superuser

if [ "$create_superuser" = "y" ]; then
    python backend/manage.py createsuperuser
fi

# 安装中文分词词典
echo "下载中文分词词典..."
python -c "import jieba; jieba.initialize()"
echo "✓ 分词词典下载完成"

# 下载spaCy模型
echo "下载spaCy中文模型..."
python -m spacy download zh_core_web_sm
echo "✓ spaCy模型下载完成"

echo "================================"
echo "安装完成!"
echo "================================"
echo ""
echo "下一步操作:"
echo "1. 编辑 .env 文件，配置数据库等信息"
echo "2. 运行开发服务器: python backend/manage.py runserver"
echo "3. 启动Celery: celery -A backend.config worker -l info"
echo "4. 启动Celery Beat: celery -A backend.config beat -l info"
echo "5. 访问 http://localhost:8000/admin/ 管理后台"
echo "6. 访问 http://localhost:8000/swagger/ API文档"
echo ""
