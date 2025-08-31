# -*- coding: utf-8 -*-
"""
Scrapy项目配置

定义爬虫的各种配置参数
"""

import os
from pathlib import Path

# Scrapy项目配置
BOT_NAME = 'xiaolu_crawler'

SPIDER_MODULES = ['app.spiders']
NEWSPIDER_MODULE = 'app.spiders'

# 机器人协议
ROBOTSTXT_OBEY = False

# 并发配置
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 1

# 下载延迟配置
DOWNLOAD_DELAY = 3
RANDOMIZE_DOWNLOAD_DELAY = True

# AutoThrottle扩展
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 60
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False

# HTTP缓存
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR = 'httpcache'
HTTPCACHE_IGNORE_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Cookie配置
COOKIES_ENABLED = True
COOKIES_DEBUG = False

# 重试配置
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 522, 524, 408, 429]
RETRY_PRIORITY_ADJUST = -1

# 重定向配置
REDIRECT_ENABLED = True
REDIRECT_MAX_TIMES = 20

# 下载器中间件
DOWNLOADER_MIDDLEWARES = {
    # 默认中间件
    'scrapy.downloadermiddlewares.robotstxt.RobotsTxtMiddleware': 100,
    'scrapy.downloadermiddlewares.httpauth.HttpAuthMiddleware': 300,
    'scrapy.downloadermiddlewares.downloadtimeout.DownloadTimeoutMiddleware': 350,
    'scrapy.downloadermiddlewares.defaultheaders.DefaultHeadersMiddleware': 400,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,  # 禁用默认UA中间件
    'scrapy.downloadermiddlewares.retry.RetryMiddleware': None,  # 禁用默认重试中间件
    'scrapy.downloadermiddlewares.redirect.MetaRefreshMiddleware': 580,
    'scrapy.downloadermiddlewares.redirect.RedirectMiddleware': 600,
    'scrapy.downloadermiddlewares.cookies.CookiesMiddleware': 700,
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 750,
    'scrapy.downloadermiddlewares.stats.DownloaderStats': 850,
    'scrapy.downloadermiddlewares.httpcache.HttpCacheMiddleware': 900,
    
    # 自定义中间件
    'app.middlewares.RotateUserAgentMiddleware': 450,
    'app.middlewares.HeadersMiddleware': 500,
    'app.middlewares.DelayMiddleware': 550,
    'app.middlewares.RetryMiddleware': 650,
    'app.middlewares.CookiesMiddleware': 720,
    # 'app.middlewares.ProxyMiddleware': 760,  # 可选启用
    # 'app.middlewares.SeleniumMiddleware': 800,  # 可选启用
}

# 数据处理管道
ITEM_PIPELINES = {
    'app.pipelines.ValidationPipeline': 100,
    'app.pipelines.DuplicationFilterPipeline': 200,
    'app.pipelines.ImageDownloadPipeline': 300,
    'app.pipelines.DatabasePipeline': 400,
    'app.pipelines.JsonWriterPipeline': 500,
    'app.pipelines.StatisticsPipeline': 600,
}

# 扩展配置
EXTENSIONS = {
    'scrapy.extensions.telnet.TelnetConsole': None,  # 禁用Telnet控制台
    'scrapy.extensions.logstats.LogStats': 300,
    'scrapy.extensions.memusage.MemoryUsage': 500,
    'scrapy.extensions.closespider.CloseSpider': 600,
}

# 日志配置
LOG_LEVEL = 'INFO'
LOG_FILE = None  # 设置为文件路径以输出到文件
LOG_ENCODING = 'utf-8'
LOG_STDOUT = True
LOG_FORMAT = '%(levelname)s: %(message)s'

# 统计收集
STATS_CLASS = 'scrapy.statscollectors.MemoryStatsCollector'

# Telnet Console (已禁用)
TELNETCONSOLE_ENABLED = False

# 默认请求头
DEFAULT_REQUEST_HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}

# 数据库配置
DATABASE = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'name': os.getenv('DB_NAME', 'xiaolu_workflow'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'password'),
}

# Redis配置
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# 文件存储配置
IMAGES_STORE = os.getenv('IMAGES_STORE', './downloads/images')
IMAGES_DOWNLOAD_PATH = os.getenv('IMAGES_DOWNLOAD_PATH', './downloads/images')
JSON_OUTPUT_DIR = os.getenv('JSON_OUTPUT_DIR', './output')

# 创建必要的目录
for directory in [IMAGES_STORE, IMAGES_DOWNLOAD_PATH, JSON_OUTPUT_DIR]:
    Path(directory).mkdir(parents=True, exist_ok=True)

# 代理配置
USE_PROXY = os.getenv('USE_PROXY', 'False').lower() == 'true'
PROXY_FILE = os.getenv('PROXY_FILE', 'proxies.txt')
PROXY_LIST = os.getenv('PROXY_LIST', '')

# Selenium配置
USE_SELENIUM = os.getenv('USE_SELENIUM', 'False').lower() == 'true'
SELENIUM_TIMEOUT = int(os.getenv('SELENIUM_TIMEOUT', 30))

# 下载超时配置
DOWNLOAD_TIMEOUT = 30
DOWNLOAD_MAXSIZE = 1073741824  # 1GB
DOWNLOAD_WARNSIZE = 33554432   # 32MB

# 延迟配置
DELAY_MIN = float(os.getenv('DELAY_MIN', 1.0))
DELAY_MAX = float(os.getenv('DELAY_MAX', 3.0))

# 内存限制
MEMUSAGE_ENABLED = True
MEMUSAGE_LIMIT_MB = 2048
MEMUSAGE_WARNING_MB = 1024

# 关闭爬虫条件
CLOSESPIDER_TIMEOUT = 3600  # 1小时后关闭
CLOSESPIDER_ITEMCOUNT = 10000  # 爬取10000条数据后关闭
CLOSESPIDER_PAGECOUNT = 1000   # 访问1000个页面后关闭
CLOSESPIDER_ERRORCOUNT = 100   # 出现100个错误后关闭

# Feed导出配置
FEEDS = {
    'output/%(name)s_%(time)s.json': {
        'format': 'json',
        'encoding': 'utf8',
        'store_empty': False,
        'fields': None,
        'indent': 2,
        'item_export_kwargs': {
            'ensure_ascii': False,
        },
    },
    'output/%(name)s_%(time)s.csv': {
        'format': 'csv',
        'encoding': 'utf8',
        'store_empty': False,
        'fields': ['note_id', 'title', 'author_name', 'likes_count', 'comments_count', 'crawl_time'],
    },
}

# DNS配置
DNSCACHE_ENABLED = True
DNSCACHE_SIZE = 10000
DNS_TIMEOUT = 60

# 媒体管道配置
MEDIA_ALLOW_REDIRECTS = True
IMAGES_EXPIRES = 90
IMAGES_THUMBS = {
    'small': (50, 50),
    'big': (270, 270),
}
IMAGES_MIN_HEIGHT = 110
IMAGES_MIN_WIDTH = 110

# 请求指纹
REQUEST_FINGERPRINTER_IMPLEMENTATION = '2.7'

# 小红书特定配置
XIAOHONGSHU_SETTINGS = {
    'MAX_PAGES_PER_KEYWORD': int(os.getenv('MAX_PAGES_PER_KEYWORD', 10)),
    'KEYWORDS': os.getenv('KEYWORDS', '美妆,时尚,护肤').split(','),
    'ENABLE_COMMENTS': os.getenv('ENABLE_COMMENTS', 'False').lower() == 'true',
    'ENABLE_USER_INFO': os.getenv('ENABLE_USER_INFO', 'False').lower() == 'true',
    'MIN_LIKES_COUNT': int(os.getenv('MIN_LIKES_COUNT', 100)),
    'MIN_COMMENTS_COUNT': int(os.getenv('MIN_COMMENTS_COUNT', 10)),
}

# 质量控制配置
QUALITY_CONTROL = {
    'MIN_CONTENT_LENGTH': 50,
    'MAX_CONTENT_LENGTH': 10000,
    'REQUIRED_FIELDS': ['note_id', 'title', 'content', 'author_name'],
    'FILTER_DUPLICATES': True,
    'ENABLE_QUALITY_SCORE': True,
}

# 反爬策略配置
ANTI_CRAWLER = {
    'MAX_REQUESTS_PER_MINUTE': 30,
    'ENABLE_CAPTCHA_DETECTION': True,
    'BACKUP_STRATEGY': 'retry',  # retry, skip, stop
    'COOLDOWN_TIME': 300,  # 5分钟冷却时间
}

# 监控配置
MONITORING = {
    'ENABLE_METRICS': True,
    'METRICS_PORT': int(os.getenv('METRICS_PORT', 9090)),
    'ENABLE_ALERTS': False,
    'ALERT_WEBHOOK': os.getenv('ALERT_WEBHOOK', ''),
}

# 环境特定配置
if os.getenv('ENVIRONMENT') == 'production':
    # 生产环境配置
    LOG_LEVEL = 'WARNING'
    CONCURRENT_REQUESTS = 8
    DOWNLOAD_DELAY = 5
    AUTOTHROTTLE_TARGET_CONCURRENCY = 0.5
    
elif os.getenv('ENVIRONMENT') == 'development':
    # 开发环境配置
    LOG_LEVEL = 'DEBUG'
    CONCURRENT_REQUESTS = 1
    DOWNLOAD_DELAY = 1
    HTTPCACHE_ENABLED = False

# 自定义设置验证
def validate_settings():
    """验证设置的有效性"""
    errors = []
    
    # 检查必要的环境变量
    required_env_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    for var in required_env_vars:
        if not os.getenv(var):
            errors.append(f"缺少环境变量: {var}")
    
    # 检查数值范围
    if CONCURRENT_REQUESTS <= 0:
        errors.append("CONCURRENT_REQUESTS 必须大于 0")
    
    if DOWNLOAD_DELAY < 0:
        errors.append("DOWNLOAD_DELAY 不能为负数")
    
    # 检查目录权限
    for directory in [IMAGES_STORE, JSON_OUTPUT_DIR]:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
        except PermissionError:
            errors.append(f"没有目录写入权限: {directory}")
    
    if errors:
        raise ValueError("配置验证失败:\n" + "\n".join(errors))

# 在导入时进行验证（仅在生产环境）
if os.getenv('ENVIRONMENT') == 'production':
    validate_settings()

# 导出常用配置给其他模块使用
__all__ = [
    'DATABASE',
    'REDIS_HOST', 'REDIS_PORT', 'REDIS_DB',
    'XIAOHONGSHU_SETTINGS',
    'QUALITY_CONTROL',
    'ANTI_CRAWLER',
]
