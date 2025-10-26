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
    # Render 部署后的默认域名（如 your-app.onrender.com）
    # 限制ALLOWED_HOSTS（生产环境仅允许实际域名）
    ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

# 已安装的应用
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'cloudinary',
    'cloudinary_storage',
    'django.contrib.staticfiles',
    # 自定义应用
    'accounts',
    'shop',
    'cart',
    'orders',
    'payment',
    # 'sslserver',  # 支持 HTTPS 启动，生产环境无需
]

# 中间件
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.gzip.GZipMiddleware',  # 添加GZip压缩
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # 放在SecurityMiddleware, CommonMiddleware 之后，确保静态文件被正确处理
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
import dj_database_url
# 数据库配置
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }
if DEBUG:
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
else:
    # 生产环境：PostgreSQL（Render 托管）
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),  # 从环境变量获取连接信息
            conn_max_age=600,  # 连接池保持时间，提升性能
            ssl_require=True  # Render PostgreSQL 要求 SSL 连接（关键！）
        )
    }

# 缓存配置（使用内存缓存）
CACHES = {
    'default': {
        # 'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        # 'LOCATION': 'unique-snowflake',
        # 'BACKEND': 'django.core.cache.backends.dummy.DummyCache', # 运行性能监控脚本文件时启用
        'BACKEND': 'django_redis.cache.RedisCache',
        # 拼接 Redis 连接 URL（格式：redis://:密码@主机:端口/数据库编号）
        'LOCATION': f"redis://:{os.environ.get('REDIS_PASSWORD')}@{os.environ.get('REDIS_HOST')}:{os.environ.get('REDIS_PORT')}/0",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 5,  # 免费版 Redis 连接数有限，设为 5 即可
                'retry_on_timeout': True,
            },
            # 启用 SSL（第三方 Redis 必须配置，否则连接失败）
            'SSL': True,
        },
        'TIMEOUT': 300,  # 缓存 5 分钟，平衡性能与数据新鲜度
    }
}

# Celery 配置（若使用 Redis 作为 broker）
CELERY_BROKER_URL = f"redis://:{os.environ.get('REDIS_PASSWORD')}@{os.environ.get('REDIS_HOST')}:{os.environ.get('REDIS_PORT')}/0"  # 确保与 Redis 实际端口一致

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
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')] # 指定静态文件的源目录（你存放 CSS/JS/ 图片的地方，如 static/），Django 会从这些目录收集文件。
STATIC_URL = '/static/'  # 访问静态资源的 URL 前缀
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # 指定静态文件的目标目录（collectstatic 命令会把源目录的文件复制到这里），用于生产环境服务静态文件。




# --------------------------
# 1. 基础配置：添加 Cloudinary 到 INSTALLED_APPS
# --------------------------

# --------------------------
# 2. 媒体文件配置（核心）
# --------------------------
# 开发环境：用本地存储（方便调试）
if DEBUG:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
# 生产环境（Render）：用 Cloudinary 云存储
else:
    # 导入 Cloudinary 存储后端
    from cloudinary_storage.storage import MediaCloudinaryStorage
    # 配置 Cloudinary 密钥（从环境变量获取）
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
        'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
        'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
    }
    # 指定媒体文件的存储后端为 Cloudinary
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    # 媒体文件的 URL 前缀（Cloudinary 自动生成）
    MEDIA_URL = f'https://res.cloudinary.com/{os.environ.get('CLOUDINARY_CLOUD_NAME')}/image/upload/'

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
    INSTALLED_APPS += [
        'whitenoise.runserver_nostatic',  # 禁用 Django 自带的开发服务器静态文件服务
    ]
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
            # 关键修复：基于BASE_DIR生成绝对路径，确保Render中可找到
            'filename': os.path.join(BASE_DIR, 'logs', 'shop.log'),
        },
        'console': {
            'level': 'ERROR',  # 只输出ERROR及以上级别，避免日志冗余
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        # 2. 文件日志（保留，本地可查）
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'shop.log'),
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],  # 同时输出到控制台和文件
        'level': 'INFO',
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
# 自动创建logs目录（关键：避免目录不存在的错误）
LOG_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)  # exist_ok=True 避免重复创建报错

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
