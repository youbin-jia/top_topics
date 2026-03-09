"""
开发环境配置
"""
from .base import *

DEBUG = True

# 开发环境允许所有主机
ALLOWED_HOSTS = ['*']

# 开发环境数据库
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'top_topics_dev'),
        'USER': os.environ.get('DB_USER', 'root'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '3306'),
    }
}

# 开发环境CORS
CORS_ALLOW_ALL_ORIGINS = True

# 开发环境邮件设置（打印到控制台）
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# 开发环境工具
INSTALLED_APPS += [
    'django_extensions',
]

# 开发环境中间件（添加调试工具）
MIDDLEWARE.insert(0, 'django.middleware.common.CommonMiddleware')

# 静态文件自动重载
INSTALLED_APPS += ['django.contrib.staticfiles']

# 开发环境缓存（使用本地内存）
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# 开发环境设置详细日志
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['apps']['level'] = 'DEBUG'
