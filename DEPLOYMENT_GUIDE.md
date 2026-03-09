# 部署运维手册

## 目录

1. [生产环境部署](#生产环境部署)
2. [服务器配置](#服务器配置)
3. [性能优化](#性能优化)
4. [监控告警](#监控告警)
5. [备份恢复](#备份恢复)
6. [安全加固](#安全加固)
7. [故障处理](#故障处理)

---

## 生产环境部署

### 部署架构

```
┌─────────────┐
│   用户请求   │
└──────┬──────┘
       │
┌──────▼──────┐
│   Nginx     │  (负载均衡 + 静态文件)
└──────┬──────┘
       │
       ├─────────────────┐
       │                 │
┌──────▼──────┐   ┌─────▼──────┐
│  Django     │   │  Django    │  (应用服务器集群)
│  (Gunicorn) │   │  (Gunicorn)│
└──────┬──────┘   └─────┬──────┘
       │                │
       └────────┬───────┘
                │
       ┌────────▼────────┐
       │   MySQL主从     │
       │   Redis集群     │
       │   MongoDB       │
       └─────────────────┘
```

### 服务器要求

**最低配置**:
- CPU: 4核
- 内存: 8GB
- 硬盘: 100GB SSD
- 带宽: 10Mbps

**推荐配置**:
- CPU: 8核+
- 内存: 16GB+
- 硬盘: 500GB SSD
- 带宽: 100Mbps+

### 部署步骤

#### 1. 准备服务器

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必要软件
sudo apt install -y \
  python3.11 \
  python3.11-venv \
  python3.11-dev \
  nginx \
  supervisor \
  mysql-server \
  redis-server

# 安装Docker（可选）
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```

#### 2. 克隆代码

```bash
# 创建应用目录
sudo mkdir -p /var/www/top_topics
sudo chown $USER:$USER /var/www/top_topics
cd /var/www/top_topics

# 克隆代码
git clone https://github.com/youbin-jia/top_topics.git .
```

#### 3. 配置环境变量

```bash
# 创建生产环境配置
cp .env.example .env.production
vim .env.production
```

**生产环境配置**:
```env
# Django设置
DJANGO_SETTINGS_MODULE=config.settings.production
SECRET_KEY=your-production-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# 数据库
DB_NAME=top_topics
DB_USER=top_topics_user
DB_PASSWORD=strong-password-here
DB_HOST=localhost
DB_PORT=3306

# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# 安全设置
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# 邮件配置
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-email-password
```

#### 4. 安装依赖

```bash
# 创建虚拟环境
python3.11 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r backend/config/requirements.txt

# 安装生产服务器
pip install gunicorn
```

#### 5. 初始化数据库

```bash
# 创建数据库
mysql -u root -p
CREATE DATABASE top_topics CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'top_topics_user'@'localhost' IDENTIFIED BY 'strong-password';
GRANT ALL PRIVILEGES ON top_topics.* TO 'top_topics_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# 运行迁移
python backend/manage.py migrate

# 收集静态文件
python backend/manage.py collectstatic --noinput

# 创建管理员
python backend/manage.py createsuperuser
```

#### 6. 配置Supervisor

创建Supervisor配置文件：

```bash
sudo vim /etc/supervisor/conf.d/top_topics.conf
```

```ini
[program:top_topics_backend]
directory=/var/www/top_topics
command=/var/www/top_topics/venv/bin/gunicorn \
  config.wsgi:application \
  --bind 127.0.0.1:8000 \
  --workers 4 \
  --threads 2 \
  --timeout 120 \
  --access-logfile /var/log/top_topics/access.log \
  --error-logfile /var/log/top_topics/error.log
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stopasgroup=true
killasgroup=true
environment=DJANGO_SETTINGS_MODULE="config.settings.production"

[program:top_topics_celery]
directory=/var/www/top_topics
command=/var/www/top_topics/venv/bin/celery \
  -A config worker \
  --loglevel=info \
  --concurrency=4 \
  --logfile=/var/log/top_topics/celery.log
user=www-data
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true

[program:top_topics_celery_beat]
directory=/var/www/top_topics
command=/var/www/top_topics/venv/bin/celery \
  -A config beat \
  --loglevel=info \
  --logfile=/var/log/top_topics/celery_beat.log
user=www-data
autostart=true
autorestart=true
```

创建日志目录：

```bash
sudo mkdir -p /var/log/top_topics
sudo chown www-data:www-data /var/log/top_topics
```

启动服务：

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status
```

#### 7. 配置Nginx

创建Nginx配置：

```bash
sudo vim /etc/nginx/sites-available/top_topics
```

```nginx
upstream backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL配置
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # 日志
    access_log /var/log/nginx/top_topics_access.log;
    error_log /var/log/nginx/top_topics_error.log;

    # 静态文件
    location /static/ {
        alias /var/www/top_topics/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/top_topics/media/;
        expires 7d;
    }

    # API请求
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时设置
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
        proxy_read_timeout 300;
    }

    # 其他请求转发到前端
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json application/xml;
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/top_topics /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 8. 配置SSL证书

使用Let's Encrypt：

```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 自动续期
sudo certbot renew --dry-run
```

#### 9. 配置防火墙

```bash
# 启用UFW
sudo ufw enable

# 开放端口
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS

# 查看状态
sudo ufw status
```

#### 10. 验证部署

```bash
# 检查服务状态
sudo supervisorctl status
sudo systemctl status nginx
sudo systemctl status mysql
sudo systemctl status redis

# 测试API
curl http://localhost:8000/api/v1/
curl https://yourdomain.com/api/v1/

# 查看日志
tail -f /var/log/top_topics/access.log
tail -f /var/log/nginx/top_topics_access.log
```

---

## 服务器配置

### MySQL优化

编辑 `/etc/mysql/mysql.conf.d/mysqld.cnf`:

```ini
[mysqld]
# 基本设置
max_connections = 500
max_connect_errors = 100

# 缓冲池设置（设置为物理内存的70-80%）
innodb_buffer_pool_size = 8G
innodb_buffer_pool_instances = 8

# 日志设置
innodb_log_file_size = 1G
innodb_log_buffer_size = 256M

# 查询缓存
query_cache_type = 1
query_cache_size = 256M

# 慢查询日志
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 2

# 字符集
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
```

重启MySQL：

```bash
sudo systemctl restart mysql
```

### Redis优化

编辑 `/etc/redis/redis.conf`:

```conf
# 内存设置
maxmemory 2gb
maxmemory-policy allkeys-lru

# 持久化
save 900 1
save 300 10
save 60 10000

# 性能
tcp-keepalive 300
timeout 0
```

重启Redis：

```bash
sudo systemctl restart redis
```

### 系统优化

编辑 `/etc/sysctl.conf`:

```conf
# 网络优化
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_tw_reuse = 1

# 内存优化
vm.swappiness = 10
vm.overcommit_memory = 1

# 文件描述符
fs.file-max = 65535
```

应用配置：

```bash
sudo sysctl -p
```

---

## 性能优化

### 数据库优化

#### 索引优化

```sql
-- 查看慢查询
SELECT * FROM mysql.slow_log ORDER BY start_time DESC LIMIT 10;

-- 添加索引
CREATE INDEX idx_topic_heat ON topics(heat_score DESC, created_at DESC);
CREATE INDEX idx_topic_trend ON topics(trend, heat_score);
CREATE INDEX idx_feedback_user_time ON user_feedbacks(user_id, created_at);

-- 分析表
ANALYZE TABLE topics;
ANALYZE TABLE user_feedbacks;
```

#### 查询优化

```python
# 使用select_related减少查询
topics = Topic.objects.select_related('category').all()

# 使用prefetch_related预取多对多关系
topics = Topic.objects.prefetch_related('keywords').all()

# 使用only()选择需要的字段
topics = Topic.objects.only('name', 'heat_score').all()

# 批量操作
Topic.objects.bulk_update(topics, ['heat_score', 'trend'])
```

### 缓存策略

#### Redis缓存

```python
from django.core.cache import cache

# 缓存热门话题
def get_hot_topics():
    cache_key = 'hot_topics:10'
    topics = cache.get(cache_key)
    if not topics:
        topics = Topic.objects.filter(
            status='active'
        ).order_by('-heat_score')[:10]
        cache.set(cache_key, topics, 300)  # 5分钟
    return topics

# 缓存用户推荐
def get_user_recommendations(user_id):
    cache_key = f'user_recommendations:{user_id}'
    recommendations = cache.get(cache_key)
    if not recommendations:
        recommendations = generate_recommendations(user_id)
        cache.set(cache_key, recommendations, 600)  # 10分钟
    return recommendations
```

#### 页面缓存

```python
# 在视图中使用缓存
from django.views.decorators.cache import cache_page

@cache_page(300)  # 缓存5分钟
def topic_list(request):
    topics = Topic.objects.all()
    return render(request, 'topics/list.html', {'topics': topics})
```

### Celery优化

```python
# 任务路由
app.conf.task_routes = {
    'apps.data_collection.tasks.*': {'queue': 'crawl'},
    'apps.topic_analysis.tasks.*': {'queue': 'analysis'},
    'apps.recommendation.tasks.*': {'queue': 'recommend'},
}

# 任务限流
@app.task(rate_limit='10/m')  # 每分钟10次
def process_content(content_id):
    pass

# 批量处理
@app.task
def batch_process_items(item_ids):
    items = Item.objects.filter(id__in=item_ids)
    for item in items:
        process_item(item)
```

---

## 监控告警

### Prometheus监控

#### 配置Prometheus

```yaml
# docker/prometheus/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'django'
    static_configs:
      - targets: ['backend:8000']

  - job_name: 'celery'
    static_configs:
      - targets: ['celery_worker:5555']

  - job_name: 'mysql'
    static_configs:
      - targets: ['db:9104']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:9121']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:9113']
```

#### Django监控中间件

```python
# backend/core/middleware.py
from prometheus_client import Counter, Histogram
import time

REQUEST_COUNT = Counter(
    'django_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'django_http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint']
)

class PrometheusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        # 记录指标
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.path,
            status=response.status_code
        ).inc()

        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.path
        ).observe(time.time() - start_time)

        return response
```

### Grafana仪表板

导入预置仪表板：

1. Django监控: ID 17623
2. MySQL监控: ID 7362
3. Redis监控: ID 11835
4. Nginx监控: ID 12708

### 告警规则

```yaml
# prometheus/alerts.yml
groups:
  - name: top_topics_alerts
    rules:
      # HTTP错误率告警
      - alert: HighErrorRate
        expr: rate(django_http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "高错误率告警"
          description: "5xx错误率超过5%"

      # 响应时间告警
      - alert: SlowResponse
        expr: histogram_quantile(0.95, rate(django_http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "响应时间过长"
          description: "95%的请求响应时间超过2秒"

      # 数据库连接数告警
      - alert: HighDBConnections
        expr: mysql_global_status_threads_connected > 400
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "数据库连接数过高"
          description: "MySQL连接数超过400"

      # Celery任务积压
      - alert: CeleryTaskBacklog
        expr: celery_queue_length > 1000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Celery任务积压"
          description: "Celery队列积压超过1000个任务"
```

### 日志监控

#### ELK Stack配置

```yaml
# docker-compose.yml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
    volumes:
      - es_data:/usr/share/elasticsearch/data

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    volumes:
      - ./docker/logstash/logstash.conf:/etc/logstash/conf.d/logstash.conf

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    ports:
      - "5601:5601"
```

---

## 备份恢复

### 数据库备份

#### 自动备份脚本

```bash
#!/bin/bash
# backup.sh

# 配置
DB_NAME="top_topics"
DB_USER="top_topics_user"
DB_PASS="your-password"
BACKUP_DIR="/backup/mysql"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# MySQL备份
mysqldump -u $DB_USER -p$DB_PASS $DB_NAME | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# 保留最近7天的备份
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

# 上传到云存储（可选）
# aws s3 cp $BACKUP_DIR/db_$DATE.sql.gz s3://your-bucket/backups/

echo "Backup completed: db_$DATE.sql.gz"
```

#### 定时任务

```bash
# 添加到crontab
crontab -e

# 每天凌晨2点备份
0 2 * * * /var/www/top_topics/scripts/backup.sh >> /var/log/top_topics/backup.log 2>&1
```

### Redis备份

```bash
#!/bin/bash
# redis_backup.sh

BACKUP_DIR="/backup/redis"
DATE=$(date +%Y%m%d_%H%M%S)

# 触发RDB快照
redis-cli BGSAVE

# 等待保存完成
sleep 5

# 复制快照文件
cp /var/lib/redis/dump.rdb $BACKUP_DIR/redis_$DATE.rdb

# 保留最近7天
find $BACKUP_DIR -name "*.rdb" -mtime +7 -delete

echo "Redis backup completed: redis_$DATE.rdb"
```

### 数据恢复

#### MySQL恢复

```bash
# 恢复数据库
gunzip < /backup/mysql/db_20260310.sql.gz | mysql -u root -p top_topics
```

#### Redis恢复

```bash
# 停止Redis
sudo systemctl stop redis

# 恢复数据文件
cp /backup/redis/redis_20260310.rdb /var/lib/redis/dump.rdb

# 启动Redis
sudo systemctl start redis
```

---

## 安全加固

### 1. 系统安全

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装fail2ban
sudo apt install fail2ban

# 配置fail2ban
sudo vim /etc/fail2ban/jail.local
```

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log
```

### 2. Django安全

```python
# settings/production.py

# 安全设置
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HSTS
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# 密码强度
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 允许的主机
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']
```

### 3. 数据库安全

```sql
-- 删除匿名用户
DELETE FROM mysql.user WHERE User='';

-- 禁止root远程登录
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');

-- 删除测试数据库
DROP DATABASE IF EXISTS test;

-- 刷新权限
FLUSH PRIVILEGES;
```

### 4. API安全

```python
# 速率限制
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day'
    }
}

# CORS设置
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
]

CORS_ALLOW_CREDENTIALS = True
```

---

## 故障处理

### 常见问题

#### 1. 服务无响应

```bash
# 检查服务状态
sudo supervisorctl status
sudo systemctl status nginx

# 查看错误日志
tail -f /var/log/top_topics/error.log
tail -f /var/log/nginx/error.log

# 重启服务
sudo supervisorctl restart all
sudo systemctl restart nginx
```

#### 2. 数据库连接失败

```bash
# 检查MySQL状态
sudo systemctl status mysql

# 查看连接数
mysql -u root -p -e "SHOW PROCESSLIST;"

# 查看最大连接数
mysql -u root -p -e "SHOW VARIABLES LIKE 'max_connections';"

# 重启MySQL
sudo systemctl restart mysql
```

#### 3. 内存不足

```bash
# 查看内存使用
free -h
top

# 清理缓存
sudo sync && sudo sysctl -w vm.drop_caches=3

# 重启服务
sudo supervisorctl restart all
```

#### 4. 磁盘空间不足

```bash
# 查看磁盘使用
df -h
du -sh /var/log/*

# 清理日志
sudo rm -f /var/log/nginx/*.log.old
sudo rm -f /var/log/top_topics/*.log.*

# 清理Docker
docker system prune -a
```

### 应急响应流程

```
1. 发现问题 → 2. 检查日志 → 3. 定位原因 → 4. 快速修复 → 5. 验证恢复 → 6. 总结文档
```

---

**文档版本**: v1.0.0
**最后更新**: 2026-03-10
