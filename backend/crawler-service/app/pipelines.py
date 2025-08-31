# -*- coding: utf-8 -*-
"""
Scrapy数据处理管道

处理爬取的数据，包括验证、清洗、存储等
"""

import os
import json
import hashlib
import logging
import psycopg2
import redis
from typing import Dict, Any, Optional
from urllib.parse import urlparse
from datetime import datetime
import requests
from scrapy import signals
from scrapy.exceptions import DropItem
from itemadapter import ItemAdapter
from .items import XiaohongshuNoteItem, XiaohongshuUserItem, XiaohongshuCommentItem


class ValidationPipeline:
    """数据验证管道"""
    
    def process_item(self, item, spider):
        """验证数据项"""
        adapter = ItemAdapter(item)
        
        # 验证必填字段
        if hasattr(item, 'validate') and not item.validate():
            raise DropItem(f"数据验证失败: {item}")
        
        # 验证URL格式
        if 'url' in adapter and adapter['url']:
            if not self._is_valid_url(adapter['url']):
                raise DropItem(f"无效的URL: {adapter['url']}")
        
        # 验证文本长度
        if 'content' in adapter and adapter['content']:
            if len(adapter['content']) > 50000:  # 限制内容长度
                adapter['content'] = adapter['content'][:50000] + "..."
        
        spider.logger.info(f"数据验证通过: {adapter.get('note_id', 'N/A')}")
        return item
    
    def _is_valid_url(self, url: str) -> bool:
        """验证URL格式"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False


class DuplicationFilterPipeline:
    """去重管道"""
    
    def __init__(self):
        self.seen_items = set()
        self.redis_client = None
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls()
    
    def open_spider(self, spider):
        """初始化Redis连接"""
        try:
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', 6379))
            redis_db = int(os.getenv('REDIS_DB', 0))
            
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True
            )
            spider.logger.info("Redis连接成功")
        except Exception as e:
            spider.logger.warning(f"Redis连接失败，使用内存去重: {e}")
    
    def process_item(self, item, spider):
        """去重处理"""
        adapter = ItemAdapter(item)
        
        # 生成唯一标识
        item_id = self._generate_item_id(adapter)
        
        # 检查是否已存在
        if self._is_duplicate(item_id, spider):
            raise DropItem(f"重复数据: {item_id}")
        
        # 记录已处理的数据
        self._mark_as_seen(item_id, spider)
        
        return item
    
    def _generate_item_id(self, adapter: ItemAdapter) -> str:
        """生成数据项唯一标识"""
        if 'note_id' in adapter:
            return f"note:{adapter['note_id']}"
        elif 'user_id' in adapter:
            return f"user:{adapter['user_id']}"
        elif 'comment_id' in adapter:
            return f"comment:{adapter['comment_id']}"
        else:
            # 基于URL生成ID
            url = adapter.get('url', '')
            return f"url:{hashlib.md5(url.encode()).hexdigest()}"
    
    def _is_duplicate(self, item_id: str, spider) -> bool:
        """检查是否重复"""
        if self.redis_client:
            try:
                return self.redis_client.sismember('scrapy:seen_items', item_id)
            except Exception as e:
                spider.logger.warning(f"Redis检查失败: {e}")
        
        return item_id in self.seen_items
    
    def _mark_as_seen(self, item_id: str, spider):
        """标记为已处理"""
        if self.redis_client:
            try:
                self.redis_client.sadd('scrapy:seen_items', item_id)
                # 设置过期时间（7天）
                self.redis_client.expire('scrapy:seen_items', 7 * 24 * 3600)
            except Exception as e:
                spider.logger.warning(f"Redis存储失败: {e}")
        
        self.seen_items.add(item_id)


class ImageDownloadPipeline:
    """图片下载管道"""
    
    def __init__(self):
        self.download_path = os.getenv('IMAGES_DOWNLOAD_PATH', './downloads/images')
        os.makedirs(self.download_path, exist_ok=True)
    
    def process_item(self, item, spider):
        """处理图片下载"""
        adapter = ItemAdapter(item)
        
        if 'images' in adapter and adapter['images']:
            downloaded_images = []
            
            for image_url in adapter['images']:
                try:
                    local_path = self._download_image(image_url, spider)
                    if local_path:
                        downloaded_images.append(local_path)
                except Exception as e:
                    spider.logger.error(f"图片下载失败 {image_url}: {e}")
            
            # 更新为本地路径
            adapter['local_images'] = downloaded_images
        
        return item
    
    def _download_image(self, url: str, spider) -> Optional[str]:
        """下载单张图片"""
        try:
            # 生成文件名
            url_hash = hashlib.md5(url.encode()).hexdigest()
            extension = self._get_image_extension(url)
            filename = f"{url_hash}{extension}"
            filepath = os.path.join(self.download_path, filename)
            
            # 如果已存在则跳过
            if os.path.exists(filepath):
                return filepath
            
            # 下载图片
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # 保存文件
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            spider.logger.info(f"图片下载成功: {filename}")
            return filepath
            
        except Exception as e:
            spider.logger.error(f"下载图片失败 {url}: {e}")
            return None
    
    def _get_image_extension(self, url: str) -> str:
        """获取图片扩展名"""
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            if ext in path:
                return ext
        
        return '.jpg'  # 默认扩展名


class DatabasePipeline:
    """数据库存储管道"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    @classmethod
    def from_crawler(cls, crawler):
        db_settings = crawler.settings.getdict('DATABASE')
        return cls(
            db_host=db_settings.get('host', os.getenv('DB_HOST', 'localhost')),
            db_port=db_settings.get('port', int(os.getenv('DB_PORT', 5432))),
            db_name=db_settings.get('name', os.getenv('DB_NAME', 'xiaolu_workflow')),
            db_user=db_settings.get('user', os.getenv('DB_USER', 'postgres')),
            db_password=db_settings.get('password', os.getenv('DB_PASSWORD', 'password'))
        )
    
    def __init__(self, db_host='localhost', db_port=5432, db_name='xiaolu_workflow', 
                 db_user='postgres', db_password='password'):
        self.db_host = db_host
        self.db_port = db_port
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
    
    def open_spider(self, spider):
        """打开数据库连接"""
        try:
            self.connection = psycopg2.connect(
                host=self.db_host,
                port=self.db_port,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password
            )
            self.cursor = self.connection.cursor()
            spider.logger.info("数据库连接成功")
        except Exception as e:
            spider.logger.error(f"数据库连接失败: {e}")
    
    def close_spider(self, spider):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        spider.logger.info("数据库连接已关闭")
    
    def process_item(self, item, spider):
        """存储数据到数据库"""
        try:
            if isinstance(item, XiaohongshuNoteItem):
                self._insert_note(item, spider)
            elif isinstance(item, XiaohongshuUserItem):
                self._insert_user(item, spider)
            elif isinstance(item, XiaohongshuCommentItem):
                self._insert_comment(item, spider)
            
            self.connection.commit()
            spider.logger.info(f"数据存储成功: {item.get('note_id', 'N/A')}")
            
        except Exception as e:
            self.connection.rollback()
            spider.logger.error(f"数据存储失败: {e}")
            raise DropItem(f"数据库存储失败: {e}")
        
        return item
    
    def _insert_note(self, item, spider):
        """插入笔记数据"""
        adapter = ItemAdapter(item)
        
        sql = """
        INSERT INTO xiaohongshu_notes (
            note_id, url, title, content, keyword, author_name, author_id, author_avatar,
            likes_count, comments_count, shares_count, images, tags, crawl_time,
            note_type, location, quality_score, is_featured
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        ) ON CONFLICT (note_id) DO UPDATE SET
            title = EXCLUDED.title,
            content = EXCLUDED.content,
            likes_count = EXCLUDED.likes_count,
            comments_count = EXCLUDED.comments_count,
            shares_count = EXCLUDED.shares_count,
            updated_at = CURRENT_TIMESTAMP
        """
        
        values = (
            adapter.get('note_id'),
            adapter.get('url'),
            adapter.get('title'),
            adapter.get('content'),
            adapter.get('keyword'),
            adapter.get('author_name'),
            adapter.get('author_id'),
            adapter.get('author_avatar'),
            adapter.get('likes_count', 0),
            adapter.get('comments_count', 0),
            adapter.get('shares_count', 0),
            json.dumps(adapter.get('images', [])),
            json.dumps(adapter.get('tags', [])),
            adapter.get('crawl_time'),
            adapter.get('note_type'),
            adapter.get('location'),
            adapter.get('quality_score'),
            adapter.get('is_featured', False)
        )
        
        self.cursor.execute(sql, values)
    
    def _insert_user(self, item, spider):
        """插入用户数据"""
        # 实现用户数据插入逻辑
        pass
    
    def _insert_comment(self, item, spider):
        """插入评论数据"""
        # 实现评论数据插入逻辑
        pass


class JsonWriterPipeline:
    """JSON文件写入管道"""
    
    def __init__(self):
        self.output_dir = os.getenv('JSON_OUTPUT_DIR', './output')
        os.makedirs(self.output_dir, exist_ok=True)
        self.files = {}
    
    def open_spider(self, spider):
        """打开输出文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{spider.name}_{timestamp}.jsonl"
        filepath = os.path.join(self.output_dir, filename)
        
        self.files[spider.name] = open(filepath, 'w', encoding='utf-8')
        spider.logger.info(f"JSON输出文件: {filepath}")
    
    def close_spider(self, spider):
        """关闭输出文件"""
        if spider.name in self.files:
            self.files[spider.name].close()
            del self.files[spider.name]
    
    def process_item(self, item, spider):
        """写入JSON数据"""
        adapter = ItemAdapter(item)
        line = json.dumps(dict(adapter), ensure_ascii=False, default=str) + "\n"
        
        self.files[spider.name].write(line)
        self.files[spider.name].flush()
        
        return item


class StatisticsPipeline:
    """统计信息管道"""
    
    def __init__(self):
        self.stats = {
            'items_count': 0,
            'notes_count': 0,
            'users_count': 0,
            'comments_count': 0,
            'errors_count': 0,
            'start_time': None,
            'end_time': None
        }
    
    def open_spider(self, spider):
        """记录开始时间"""
        self.stats['start_time'] = datetime.now()
        spider.logger.info("开始统计爬取数据")
    
    def close_spider(self, spider):
        """记录结束时间并输出统计信息"""
        self.stats['end_time'] = datetime.now()
        duration = self.stats['end_time'] - self.stats['start_time']
        
        spider.logger.info("=" * 50)
        spider.logger.info("爬取统计信息:")
        spider.logger.info(f"总数据量: {self.stats['items_count']}")
        spider.logger.info(f"笔记数量: {self.stats['notes_count']}")
        spider.logger.info(f"用户数量: {self.stats['users_count']}")
        spider.logger.info(f"评论数量: {self.stats['comments_count']}")
        spider.logger.info(f"错误数量: {self.stats['errors_count']}")
        spider.logger.info(f"耗时: {duration}")
        spider.logger.info("=" * 50)
    
    def process_item(self, item, spider):
        """统计数据"""
        self.stats['items_count'] += 1
        
        if isinstance(item, XiaohongshuNoteItem):
            self.stats['notes_count'] += 1
        elif isinstance(item, XiaohongshuUserItem):
            self.stats['users_count'] += 1
        elif isinstance(item, XiaohongshuCommentItem):
            self.stats['comments_count'] += 1
        
        # 每处理100条数据输出一次进度
        if self.stats['items_count'] % 100 == 0:
            spider.logger.info(f"已处理 {self.stats['items_count']} 条数据")
        
        return item
