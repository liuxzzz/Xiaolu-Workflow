# -*- coding: utf-8 -*-
"""
Scrapy中间件

提供请求/响应处理、代理轮换、反反爬等功能
"""

import os
import random
import time
import json
import logging
from typing import List, Dict, Optional, Union
from urllib.parse import urlparse
import requests
from scrapy import signals
from scrapy.http import HtmlResponse
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.downloadermiddlewares.httpproxy import HttpProxyMiddleware
from scrapy.exceptions import NotConfigured, IgnoreRequest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class RotateUserAgentMiddleware:
    """用户代理轮换中间件"""
    
    def __init__(self):
        self.user_agents = [
            # Chrome Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36',
            
            # Chrome macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
            
            # Firefox Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0',
            
            # Firefox macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
            
            # Safari macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            
            # Edge Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59',
        ]
    
    def process_request(self, request, spider):
        """处理请求，随机选择User-Agent"""
        user_agent = random.choice(self.user_agents)
        request.headers['User-Agent'] = user_agent
        return None


class ProxyMiddleware:
    """代理中间件"""
    
    def __init__(self):
        self.proxies = []
        self.current_proxy_index = 0
        self.proxy_file = os.getenv('PROXY_FILE', 'proxies.txt')
        self.load_proxies()
    
    @classmethod
    def from_crawler(cls, crawler):
        # 检查是否启用代理
        if not crawler.settings.getbool('USE_PROXY', False):
            raise NotConfigured('代理中间件未启用')
        return cls()
    
    def load_proxies(self):
        """加载代理列表"""
        if os.path.exists(self.proxy_file):
            with open(self.proxy_file, 'r') as f:
                self.proxies = [line.strip() for line in f if line.strip()]
        
        # 如果没有代理文件，使用环境变量
        if not self.proxies:
            proxy_env = os.getenv('PROXY_LIST', '')
            if proxy_env:
                self.proxies = [p.strip() for p in proxy_env.split(',') if p.strip()]
        
        if self.proxies:
            logging.info(f"加载了 {len(self.proxies)} 个代理")
        else:
            logging.warning("未找到可用代理")
    
    def get_random_proxy(self) -> Optional[str]:
        """获取随机代理"""
        if not self.proxies:
            return None
        
        return random.choice(self.proxies)
    
    def process_request(self, request, spider):
        """为请求设置代理"""
        proxy = self.get_random_proxy()
        if proxy:
            request.meta['proxy'] = f"http://{proxy}"
            spider.logger.debug(f"使用代理: {proxy}")
        return None
    
    def process_exception(self, request, exception, spider):
        """代理异常处理"""
        if 'proxy' in request.meta:
            failed_proxy = request.meta['proxy']
            spider.logger.warning(f"代理失败: {failed_proxy}")
            
            # 可以在这里实现代理健康检查和移除逻辑
            
        return None


class DelayMiddleware:
    """延迟中间件"""
    
    def __init__(self):
        self.delay_range = (1, 3)  # 延迟范围（秒）
    
    @classmethod
    def from_crawler(cls, crawler):
        delay_min = crawler.settings.getfloat('DELAY_MIN', 1.0)
        delay_max = crawler.settings.getfloat('DELAY_MAX', 3.0)
        
        middleware = cls()
        middleware.delay_range = (delay_min, delay_max)
        return middleware
    
    def process_request(self, request, spider):
        """添加随机延迟"""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)
        spider.logger.debug(f"延迟 {delay:.2f} 秒")
        return None


class SeleniumMiddleware:
    """Selenium中间件，用于处理JavaScript渲染的页面"""
    
    def __init__(self):
        self.driver = None
        self.timeout = 30
    
    @classmethod
    def from_crawler(cls, crawler):
        # 检查是否启用Selenium
        if not crawler.settings.getbool('USE_SELENIUM', False):
            raise NotConfigured('Selenium中间件未启用')
        
        middleware = cls()
        middleware.timeout = crawler.settings.getint('SELENIUM_TIMEOUT', 30)
        return middleware
    
    def open_spider(self, spider):
        """初始化Selenium WebDriver"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # 无头模式
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # 禁用图片加载以提高速度
            prefs = {"profile.managed_default_content_settings.images": 2}
            chrome_options.add_experimental_option("prefs", prefs)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(self.timeout)
            
            spider.logger.info("Selenium WebDriver 初始化成功")
            
        except Exception as e:
            spider.logger.error(f"Selenium WebDriver 初始化失败: {e}")
            raise
    
    def close_spider(self, spider):
        """关闭WebDriver"""
        if self.driver:
            self.driver.quit()
            spider.logger.info("Selenium WebDriver 已关闭")
    
    def process_request(self, request, spider):
        """使用Selenium处理请求"""
        # 只对特定URL使用Selenium
        if not self._should_use_selenium(request.url):
            return None
        
        try:
            spider.logger.debug(f"使用Selenium处理: {request.url}")
            
            self.driver.get(request.url)
            
            # 等待页面加载完成
            self._wait_for_page_load(spider)
            
            # 处理反爬检测
            self._handle_anti_crawler(spider)
            
            # 获取页面源码
            html = self.driver.page_source
            
            # 创建响应对象
            response = HtmlResponse(
                url=request.url,
                body=html.encode('utf-8'),
                encoding='utf-8',
                request=request
            )
            
            return response
            
        except Exception as e:
            spider.logger.error(f"Selenium处理失败 {request.url}: {e}")
            return None
    
    def _should_use_selenium(self, url: str) -> bool:
        """判断是否需要使用Selenium"""
        # 可以根据URL特征判断
        selenium_patterns = [
            'xiaohongshu.com',
            # 可以添加其他需要JavaScript渲染的域名
        ]
        
        for pattern in selenium_patterns:
            if pattern in url:
                return True
        
        return False
    
    def _wait_for_page_load(self, spider):
        """等待页面加载完成"""
        try:
            # 等待页面中的关键元素加载
            wait = WebDriverWait(self.driver, 10)
            
            # 小红书特定的等待条件
            if 'xiaohongshu.com' in self.driver.current_url:
                # 等待笔记内容区域加载
                wait.until(
                    EC.any_of(
                        EC.presence_of_element_located((By.CSS_SELECTOR, '.note-item')),
                        EC.presence_of_element_located((By.CSS_SELECTOR, '.feeds-page')),
                        EC.presence_of_element_located((By.CSS_SELECTOR, '.note-detail'))
                    )
                )
            
            # 额外等待JavaScript执行
            time.sleep(2)
            
        except Exception as e:
            spider.logger.warning(f"页面加载等待超时: {e}")
    
    def _handle_anti_crawler(self, spider):
        """处理反爬检测"""
        try:
            # 检查是否有验证码或登录要求
            if self.driver.find_elements(By.CSS_SELECTOR, '.captcha, .login-form, .verify'):
                spider.logger.warning("检测到反爬验证，需要人工处理")
                # 这里可以实现自动处理逻辑或抛出异常
                
        except Exception as e:
            spider.logger.debug(f"反爬检测处理异常: {e}")


class RetryMiddleware(RetryMiddleware):
    """自定义重试中间件"""
    
    def __init__(self, settings):
        super().__init__(settings)
        self.max_retry_times = settings.getint('RETRY_TIMES', 3)
        self.retry_http_codes = set(int(x) for x in settings.getlist('RETRY_HTTP_CODES'))
        self.priority_adjust = settings.getint('RETRY_PRIORITY_ADJUST', -1)
    
    def process_response(self, request, response, spider):
        """处理响应重试"""
        # 检查是否需要重试
        if response.status in self.retry_http_codes:
            reason = f'HTTP {response.status}'
            return self._retry(request, reason, spider) or response
        
        # 检查响应内容是否有效
        if self._is_invalid_response(response):
            reason = '响应内容无效'
            return self._retry(request, reason, spider) or response
        
        return response
    
    def process_exception(self, request, exception, spider):
        """处理异常重试"""
        if isinstance(exception, self.EXCEPTIONS_TO_RETRY):
            return self._retry(request, exception.__class__.__name__, spider)
    
    def _is_invalid_response(self, response) -> bool:
        """检查响应是否无效"""
        # 检查响应长度
        if len(response.body) < 100:
            return True
        
        # 检查是否包含错误信息
        error_indicators = [
            'access denied',
            'blocked',
            '访问被拒绝',
            '系统繁忙',
            'too many requests'
        ]
        
        body_text = response.text.lower()
        for indicator in error_indicators:
            if indicator in body_text:
                return True
        
        return False


class HeadersMiddleware:
    """请求头中间件"""
    
    def __init__(self):
        self.default_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
        }
    
    def process_request(self, request, spider):
        """添加通用请求头"""
        # 设置默认请求头
        for key, value in self.default_headers.items():
            if key not in request.headers:
                request.headers[key] = value
        
        # 特定站点的请求头
        if 'xiaohongshu.com' in request.url:
            request.headers.update({
                'Referer': 'https://www.xiaohongshu.com/',
                'Origin': 'https://www.xiaohongshu.com',
                'sec-ch-ua': '"Google Chrome";v="91", "Chromium";v="91", ";Not A Brand";v="99"',
                'sec-ch-ua-mobile': '?0',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'same-origin',
            })
        
        return None


class CookiesMiddleware:
    """Cookie管理中间件"""
    
    def __init__(self):
        self.cookies_file = os.getenv('COOKIES_FILE', 'cookies.json')
        self.cookies = {}
        self.load_cookies()
    
    def load_cookies(self):
        """加载Cookie"""
        if os.path.exists(self.cookies_file):
            try:
                with open(self.cookies_file, 'r') as f:
                    self.cookies = json.load(f)
                logging.info(f"加载了 {len(self.cookies)} 个Cookie")
            except Exception as e:
                logging.error(f"加载Cookie失败: {e}")
    
    def save_cookies(self):
        """保存Cookie"""
        try:
            with open(self.cookies_file, 'w') as f:
                json.dump(self.cookies, f, indent=2)
        except Exception as e:
            logging.error(f"保存Cookie失败: {e}")
    
    def process_request(self, request, spider):
        """添加Cookie到请求"""
        domain = urlparse(request.url).netloc
        
        if domain in self.cookies:
            for cookie in self.cookies[domain]:
                request.cookies[cookie['name']] = cookie['value']
        
        return None
    
    def process_response(self, request, response, spider):
        """从响应中提取Cookie"""
        domain = urlparse(request.url).netloc
        
        if 'Set-Cookie' in response.headers:
            if domain not in self.cookies:
                self.cookies[domain] = []
            
            # 这里可以实现Cookie解析和存储逻辑
            # 简化处理，实际使用时需要完善
        
        return response
