# -*- coding: utf-8 -*-
"""
小红书爬虫

专门用于采集小红书笔记数据
"""

import scrapy
import json
import re
from typing import Dict, List, Optional, Generator
from urllib.parse import urljoin, urlparse
from .base_spider import BaseSpider
from ..items import XiaohongshuNoteItem


class XiaohongshuSpider(BaseSpider):
    """小红书爬虫"""
    
    name = 'xiaohongshu'
    allowed_domains = ['xiaohongshu.com', 'xhscdn.com']
    
    # 小红书相关配置
    custom_settings = {
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': True,
        'CONCURRENT_REQUESTS': 1,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 1,
        'COOKIES_ENABLED': True,
        'ROBOTSTXT_OBEY': False,
    }
    
    def __init__(self, keyword: str = None, max_pages: int = 10, *args, **kwargs):
        super(XiaohongshuSpider, self).__init__(*args, **kwargs)
        self.keyword = keyword or "美妆"
        self.max_pages = int(max_pages)
        self.page_count = 0
        
        # 构建搜索URL
        self.start_urls = [
            f'https://www.xiaohongshu.com/search_result?keyword={self.keyword}&type=51'
        ]
        
        self.logger.info(f"开始采集关键词: {self.keyword}, 最大页数: {self.max_pages}")
    
    def get_headers(self) -> Dict[str, str]:
        """获取小红书专用请求头"""
        headers = super().get_headers()
        headers.update({
            'Referer': 'https://www.xiaohongshu.com/',
            'Origin': 'https://www.xiaohongshu.com',
            'sec-ch-ua': '"Google Chrome";v="91", "Chromium";v="91", ";Not A Brand";v="99"',
            'sec-ch-ua-mobile': '?0',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
        })
        return headers
    
    def parse(self, response):
        """解析搜索结果页面"""
        self.logger.info(f"解析页面: {response.url}")
        
        # 提取笔记链接
        note_urls = self.extract_note_urls(response)
        
        for url in note_urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse_note,
                headers=self.get_headers(),
                meta={'dont_cache': True}
            )
        
        # 处理分页
        if self.page_count < self.max_pages:
            next_page = self.get_next_page(response)
            if next_page:
                self.page_count += 1
                yield scrapy.Request(
                    url=next_page,
                    callback=self.parse,
                    headers=self.get_headers(),
                    meta={'dont_cache': True}
                )
    
    def extract_note_urls(self, response) -> List[str]:
        """从搜索页面提取笔记URL"""
        urls = []
        
        # 方法1: 从链接标签提取
        note_links = response.css('a[href*="/explore/"]::attr(href)').getall()
        for link in note_links:
            if '/explore/' in link:
                full_url = urljoin(response.url, link)
                urls.append(full_url)
        
        # 方法2: 从JavaScript数据中提取（如果有的话）
        script_data = response.css('script:contains("window.__INITIAL_STATE__")::text').get()
        if script_data:
            urls.extend(self.extract_urls_from_script(script_data))
        
        # 去重
        urls = list(set(urls))
        self.logger.info(f"提取到 {len(urls)} 个笔记链接")
        
        return urls
    
    def extract_urls_from_script(self, script_text: str) -> List[str]:
        """从JavaScript代码中提取笔记URL"""
        urls = []
        try:
            # 提取note_id
            note_id_pattern = r'"note_id":\s*"([^"]+)"'
            note_ids = re.findall(note_id_pattern, script_text)
            
            for note_id in note_ids:
                url = f"https://www.xiaohongshu.com/explore/{note_id}"
                urls.append(url)
                
        except Exception as e:
            self.logger.error(f"解析JavaScript数据失败: {e}")
        
        return urls
    
    def get_next_page(self, response) -> Optional[str]:
        """获取下一页URL"""
        # 这里需要根据小红书的实际分页机制来实现
        # 可能需要分析Ajax请求或者JavaScript生成的分页链接
        return None
    
    def parse_note(self, response):
        """解析单个笔记页面"""
        self.logger.info(f"解析笔记: {response.url}")
        
        try:
            # 提取笔记ID
            note_id = self.extract_note_id(response.url)
            if not note_id:
                self.logger.warning(f"无法提取笔记ID: {response.url}")
                return
            
            # 创建Item
            item = XiaohongshuNoteItem()
            
            # 基础信息
            item['note_id'] = note_id
            item['url'] = response.url
            item['keyword'] = self.keyword
            
            # 提取标题
            item['title'] = self.extract_title(response)
            
            # 提取内容
            item['content'] = self.extract_content(response)
            
            # 提取作者信息
            author_info = self.extract_author_info(response)
            item.update(author_info)
            
            # 提取统计信息
            stats = self.extract_stats(response)
            item.update(stats)
            
            # 提取图片
            item['images'] = self.extract_images(response)
            
            # 提取标签
            item['tags'] = self.extract_tags(response)
            
            # 添加采集时间戳
            item['crawl_time'] = self.get_current_timestamp()
            
            yield item
            
        except Exception as e:
            self.logger.error(f"解析笔记失败 {response.url}: {e}")
    
    def extract_note_id(self, url: str) -> Optional[str]:
        """从URL中提取笔记ID"""
        match = re.search(r'/explore/([a-zA-Z0-9]+)', url)
        return match.group(1) if match else None
    
    def extract_title(self, response) -> str:
        """提取笔记标题"""
        selectors = [
            'h1.title::text',
            '.note-title::text',
            'title::text',
        ]
        
        for selector in selectors:
            title = response.css(selector).get()
            if title:
                return self.clean_text(title)
        
        return ""
    
    def extract_content(self, response) -> str:
        """提取笔记内容"""
        selectors = [
            '.note-content::text',
            '.desc::text',
            '[class*="content"]::text',
        ]
        
        content_parts = []
        for selector in selectors:
            texts = response.css(selector).getall()
            content_parts.extend(texts)
        
        content = ' '.join(content_parts)
        return self.clean_text(content)
    
    def extract_author_info(self, response) -> Dict[str, str]:
        """提取作者信息"""
        return {
            'author_name': self.clean_text(response.css('.author-name::text').get() or ""),
            'author_id': self.clean_text(response.css('[data-author-id]::attr(data-author-id)').get() or ""),
            'author_avatar': response.css('.author-avatar img::attr(src)').get() or "",
        }
    
    def extract_stats(self, response) -> Dict[str, int]:
        """提取统计信息"""
        def extract_number(text: str) -> int:
            if not text:
                return 0
            # 提取数字，处理k/w等单位
            number_text = re.search(r'([\d.]+)([kw万千]?)', text.lower())
            if number_text:
                num = float(number_text.group(1))
                unit = number_text.group(2)
                if unit in ['k', '千']:
                    num *= 1000
                elif unit in ['w', '万']:
                    num *= 10000
                return int(num)
            return 0
        
        likes_text = response.css('.like-count::text').get() or "0"
        comments_text = response.css('.comment-count::text').get() or "0"
        shares_text = response.css('.share-count::text').get() or "0"
        
        return {
            'likes_count': extract_number(likes_text),
            'comments_count': extract_number(comments_text),
            'shares_count': extract_number(shares_text),
        }
    
    def extract_images(self, response) -> List[str]:
        """提取图片URL"""
        image_urls = []
        
        # 提取所有图片
        img_selectors = [
            '.note-images img::attr(src)',
            '.gallery img::attr(src)',
            '[class*="image"] img::attr(src)',
        ]
        
        for selector in img_selectors:
            urls = response.css(selector).getall()
            image_urls.extend(urls)
        
        # 过滤和清理URL
        cleaned_urls = []
        for url in image_urls:
            if url and url.startswith(('http', '//')):
                if url.startswith('//'):
                    url = 'https:' + url
                cleaned_urls.append(url)
        
        return list(set(cleaned_urls))  # 去重
    
    def extract_tags(self, response) -> List[str]:
        """提取标签"""
        tag_selectors = [
            '.tag::text',
            '.hashtag::text',
            '[class*="tag"]::text',
        ]
        
        tags = []
        for selector in tag_selectors:
            tag_texts = response.css(selector).getall()
            tags.extend(tag_texts)
        
        # 清理标签
        cleaned_tags = []
        for tag in tags:
            tag = self.clean_text(tag)
            if tag and tag.startswith('#'):
                tag = tag[1:]  # 移除#号
            if tag:
                cleaned_tags.append(tag)
        
        return list(set(cleaned_tags))  # 去重
    
    def get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
