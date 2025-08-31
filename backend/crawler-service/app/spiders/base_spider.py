# -*- coding: utf-8 -*-
"""
基础爬虫类

提供通用的爬虫功能和配置
"""

import scrapy
import random
import time
from typing import Dict, List, Optional
from urllib.parse import urljoin


class BaseSpider(scrapy.Spider):
    """基础爬虫类，提供通用功能"""
    
    # 通用配置
    allowed_domains = []
    start_urls = []
    
    # 请求间隔配置
    download_delay = 3
    randomize_download_delay = True
    
    # 用户代理列表
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
    ]
    
    def __init__(self, *args, **kwargs):
        super(BaseSpider, self).__init__(*args, **kwargs)
        self.logger.info(f"初始化爬虫: {self.name}")
    
    def start_requests(self):
        """生成初始请求"""
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                headers=self.get_headers(),
                meta={
                    'retry_times': 0,
                    'download_timeout': 30,
                }
            )
    
    def get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    def parse(self, response):
        """默认解析方法，需要在子类中重写"""
        raise NotImplementedError("parse方法需要在子类中实现")
    
    def handle_error(self, failure):
        """错误处理"""
        self.logger.error(f"请求失败: {failure.value}")
        
    def clean_text(self, text: str) -> str:
        """清理文本内容"""
        if not text:
            return ""
        
        # 去除多余空白字符
        text = ' '.join(text.split())
        # 去除首尾空白
        text = text.strip()
        
        return text
    
    def extract_text_list(self, selectors) -> List[str]:
        """提取文本列表"""
        return [self.clean_text(text) for text in selectors.getall() if text.strip()]
    
    def random_delay(self, min_delay: float = 1.0, max_delay: float = 3.0):
        """随机延迟"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
        
    def build_absolute_url(self, response, url: str) -> str:
        """构建绝对URL"""
        return urljoin(response.url, url)
