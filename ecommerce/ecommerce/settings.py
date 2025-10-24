"""
Django settings for ecommerce project.
"""

import os
from pathlib import Path

# # 项目根目录
# BASE_DIR = Path(__file__).resolve().parent.parent
# 项目根目录（确保自动拼接的路径正确）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))



# 调试模式
# 将 DEBUG 配置改为「字符串转布尔值」的逻辑，确保环境变量 'False' 能正确转为布尔值 False
# 原理：无论环境变量是 'True'/'true' 还是 'False'/'false'，先转小写再对比，确保得到正确的布尔值。
# 示例：若环境变量 DJANGO_DEBUG = 'False'，则 'False'.lower() == 'true' 结果为 False，if not DEBUG 会生效。
DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() == 'true'  # 生产环境设为False
# DEBUG = True
# 安全密钥，从环境变量中获取，需要先设置在环境变量中 setx DJANGO_SECRET_KEY "your secret_key" /m
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')  # 从环境变量获取密钥（生产环境必须更换）
# 允许的主机
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    'testserver',  # 添加这行以支持测试
]

if not DEBUG:
    # 限制ALLOWED_HOSTS（生产环境仅允许实际域名）
    ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

# 已安装的应用
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 自定义应用
    'accounts',
    'shop',
    'cart',
    'orders',
    'payment',
    'sslserver',  # 支持 HTTPS 启动
]

# 中间件
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # 添加此行（需在 SecurityMiddleware 之后）
    'django.middleware.gzip.GZipMiddleware',  # 添加GZip压缩
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',# CSRF 中间件（必须在 Session 之后）
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# 根URL配置
ROOT_URLCONF = 'ecommerce.urls'

# 模板配置
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        # app_dirs（是否自动搜索应用内的 templates 目录）
        # 和 loaders（自定义模板加载器）是互斥的
        # 'APP_DIRS': True,  # 注释或删除此行（与 loaders 冲突）
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'shop.context_processors.categories',  # 全局分类上下文
                'cart.context_processors.cart',
            ],
            # 启用模板缓存.减少重复渲染耗时
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    # 手动指定应用内模板的加载器（替代 APP_DIRS=True 的功能）
                    # 先从 DIRS 加载,在该目录下找到base.html就不会去应用中寻找base
                    # 若没有第一行，且应用中没有base.html，则会提示模板不存在的错误
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
        },
    },
]

# 数据库配置
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }
DATABASES = {#数据库配置。此处使用数据库为本机的mysql
    'default': {
        # 'ENGINE': 'django.db.backends.mysql',
        'ENGINE': 'dj_db_conn_pool.backends.mysql',  # 替换为连接池引擎
        'NAME': "djangoEcommerce",
        'USER': "root",
        # 'PASSWORD': "password",
        'PASSWORD': os.environ.get('DB_PASSWORD'),  # 建议从环境变量获取密码
        'HOST': "localhost",
        'PORT': "3306",
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
        'POOL_OPTIONS': {  # 连接池配置
            'POOL_SIZE': 20,  # 连接池大小
            'MAX_OVERFLOW': 10,  # 最大溢出连接数
            'RECYCLE': 300,  # 连接回收时间（秒）
        },
        # 连接池配置（如果需要）
        'CONN_MAX_AGE': 60,  # 保持数据库连接 60 秒
        'TIME_ZONE': 'Asia/Shanghai',  # 为数据库连接设置时区
    }
}

# 缓存配置（使用内存缓存）
CACHES = {
    'default': {
        # 'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        # 'LOCATION': 'unique-snowflake',
        # 'BACKEND': 'django.core.cache.backends.dummy.DummyCache', # 运行性能监控脚本文件时启用
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Celery 配置（若使用 Redis 作为 broker）
CELERY_BROKER_URL = "redis://127.0.0.1:6379/0"  # 确保与 Redis 实际端口一致

# Session 配置优化
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_COOKIE_AGE = 1209600  # 2周，单位秒
SESSION_SAVE_EVERY_REQUEST = False

# 将 request.user 识别为自定义的User实例
AUTH_USER_MODEL = 'accounts.User'  # 替换为你的应用名（如 User 模型在 accounts 应用，则写 'accounts.User'）

# 密码验证
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 10}  # 密码最小长度设为10位
    },
    # 添加密码历史验证（需安装django-password-validators）
    {
        'NAME': 'accounts.validators.UniquePasswordValidator',
        'OPTIONS': {'history_limit': 5}
    },
]

# 购物车session配置
CART_SESSION_ID = 'cart'

# 国际化
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

# 静态文件配置
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'staticfiles')]
STATIC_URL = '/static/'  # 访问静态资源的 URL 前缀
STATIC_ROOT = os.path.join(BASE_DIR, 'static')  # 静态资源收集的目标目录（绝对路径）

# 媒体文件配置
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# 登录/登出重定向配置
LOGIN_REDIRECT_URL = 'accounts:dashboard'  # 默认登录后重定向页面
LOGIN_URL = 'accounts:login'  # 登录页面URL
LOGOUT_REDIRECT_URL = 'shop:product_list'  # 登出后重定向页面

# 默认主键类型
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 支付配置
# STRIPE_PUBLISHABLE_KEY = 'pk_test_51SHOPIIupTaNQFIkEXf15xv1ECue28tZkZ3UUMvz5h5PuRiyFuepiIaz2kq8eKlvESgYPWCJhZUtLZhBEIHTJd8C00009qgjaX'
# STRIPE_SECRET_KEY = 'sk_test_51SHOPIIupTaNQFIktRjM8sC9VD1t0iZkralAe0P3fv8jgFjZASE1rTN9wAst8CKy7lI4yF7fIm48pVcPu0siXwlQ00okl1mxGk'
# STRIPE_WEBHOOK_SECRET = 'whsec_your_test_webhook_secret'
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')

DEFAULT_FROM_EMAIL = 'noreply@yourdomain.com'  # 默认发件人

# 调试工具栏配置
# if DEBUG:
#     INSTALLED_APPS += [
#         'debug_toolbar',
#         'querycount',
#     ]
#
#     MIDDLEWARE += [
#                      'debug_toolbar.middleware.DebugToolbarMiddleware',
#                      'querycount.middleware.QueryCountMiddleware',
#                  ]
#
#     # Django Debug Toolbar
#     DEBUG_TOOLBAR_PANELS = [
#         'debug_toolbar.panels.history.HistoryPanel',
#         'debug_toolbar.panels.versions.VersionsPanel',
#         'debug_toolbar.panels.timer.TimerPanel',
#         'debug_toolbar.panels.settings.SettingsPanel',
#         'debug_toolbar.panels.headers.HeadersPanel',
#         'debug_toolbar.panels.request.RequestPanel',
#         'debug_toolbar.panels.sql.SQLPanel',
#         'debug_toolbar.panels.staticfiles.StaticFilesPanel',
#         'debug_toolbar.panels.templates.TemplatesPanel',
#         'debug_toolbar.panels.cache.CachePanel',
#         'debug_toolbar.panels.signals.SignalsPanel',
#         'debug_toolbar.panels.logging.LoggingPanel',
#         'debug_toolbar.panels.redirects.RedirectsPanel',
#         'debug_toolbar.panels.profiling.ProfilingPanel',
#     ]
#
#     DEBUG_TOOLBAR_CONFIG = {
#         'SHOW_TOOLBAR_CALLBACK': lambda request: True,
#     }
#
#     # 查询计数配置
#     QUERYCOUNT = {
#         'THRESHOLDS': {
#             'MEDIUM': 50,
#             'HIGH': 200,
#             'MIN_TIME_TO_LOG': 0,
#             'MIN_QUERY_COUNT_TO_LOG': 0
#         },
#         'DISPLAY_DUPLICATES': True,
#     }

# Django Silk配置（生产环境不要启用）
if DEBUG:
    INSTALLED_APPS += ['silk']
    MIDDLEWARE = ['silk.middleware.SilkyMiddleware'] + MIDDLEWARE

    SILKY_PYTHON_PROFILER = True
    SILKY_PYTHON_PROFILER_BINARY = True
    SILKY_META = True


# 会话缓存
SESSION_CACHE_ALIAS = 'default'

# 缓存超时设置
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 300  # 5分钟
CACHE_MIDDLEWARE_KEY_PREFIX = 'shop'

# 静态文件优化
# settings.py（仅开发环境）
if DEBUG:
    # 禁用压缩和哈希，加快静态资源加载
    STATICFILES_STORAGE = 'whitenoise.storage.WhiteNoiseStorage'
else:
    # 生产环境仍启用压缩和缓存
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# 压缩静态文件
COMPRESS_ENABLED = True  # 启用压缩（生产环境自动启用，开发环境需手动开启）
COMPRESS_ROOT = STATIC_ROOT  # 压缩文件的输出目录（与静态资源根目录一致）
COMPRESS_URL = STATIC_URL  # 压缩文件的访问 URL
COMPRESS_OFFLINE = True

# 日志配置（记录错误和安全事件）
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': 'logs/shop.log',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
        'shop': {  # 记录shop应用的日志
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
        'django.security': {  # 安全相关日志
            'handlers': ['file', 'console'],
            'level': 'WARNING',
            'propagate': True,
        },
        'django.contrib.auth': {  # 认证日志（如登录失败）
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# settings.py
INSTALLED_APPS += ['compressor']  # 添加到已安装应用
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',  # 压缩器查找器
]
COMPRESS_CSS_FILTERS = [
    'compressor.filters.css_default.CssAbsoluteFilter',
    'compressor.filters.cssmin.CSSMinFilter',  # CSS压缩
]
COMPRESS_JS_FILTERS = [
    'compressor.filters.jsmin.JSMinFilter',  # JS压缩
]

# 生产环境安全配置
if not DEBUG:
    # 告诉 Django 信任本地代理（解决开发环境 HTTPS 协议识别问题）
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    # HTTPS强制重定向
    SECURE_SSL_REDIRECT = False
    # HSTS配置
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True# 2. 信任本地HTTPS来源（避免“请求来源不被信任”导致的验证失败）
    CSRF_TRUSTED_ORIGINS = [
        'https://127.0.0.1:8000',  # 你的HTTPS访问地址
        'https://localhost:8000'   # 若用localhost访问，也需添加
    ]
    # 安全Cookie
    SESSION_COOKIE_SECURE = False # 本地https开发是为False。生产环境必须改为True
    CSRF_COOKIE_SECURE = False  # 本地https开发是为False。生产环境必须改为True
    # 其他安全头
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]
# 可选：自定义哈希器降低迭代次数（仅开发/测试用）
from django.contrib.auth.hashers import PBKDF2PasswordHasher
class FastPBKDF2PasswordHasher(PBKDF2PasswordHasher):
    iterations = 500  # 默认是 150000，降低为 1000 加速验证，生产环境需要保持默认值
PASSWORD_HASHERS.insert(0, 'ecommerce.settings.FastPBKDF2PasswordHasher')
