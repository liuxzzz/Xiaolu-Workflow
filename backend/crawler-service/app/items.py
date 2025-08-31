# -*- coding: utf-8 -*-
"""
Scrapy数据项定义

定义爬取的数据结构
"""

import scrapy
from typing import List, Optional


class XiaohongshuNoteItem(scrapy.Item):
    """小红书笔记数据项"""
    
    # 基础信息
    note_id = scrapy.Field()          # 笔记ID
    url = scrapy.Field()              # 笔记URL
    title = scrapy.Field()            # 笔记标题
    content = scrapy.Field()          # 笔记内容
    keyword = scrapy.Field()          # 搜索关键词
    
    # 作者信息
    author_name = scrapy.Field()      # 作者名称
    author_id = scrapy.Field()        # 作者ID
    author_avatar = scrapy.Field()    # 作者头像URL
    
    # 统计信息
    likes_count = scrapy.Field()      # 点赞数
    comments_count = scrapy.Field()   # 评论数
    shares_count = scrapy.Field()     # 分享数
    
    # 媒体内容
    images = scrapy.Field()           # 图片URL列表
    video_url = scrapy.Field()        # 视频URL（如果有）
    
    # 分类和标签
    tags = scrapy.Field()             # 标签列表
    category = scrapy.Field()         # 分类
    
    # 时间信息
    publish_time = scrapy.Field()     # 发布时间
    crawl_time = scrapy.Field()       # 采集时间
    
    # 其他信息
    note_type = scrapy.Field()        # 笔记类型（图文/视频）
    location = scrapy.Field()         # 位置信息
    topics = scrapy.Field()           # 话题列表
    
    # 质量评估
    quality_score = scrapy.Field()    # 质量评分
    is_featured = scrapy.Field()      # 是否精选
    
    def __setitem__(self, key, value):
        """设置字段值时的预处理"""
        # 文本字段清理
        if key in ['title', 'content', 'author_name'] and value:
            value = self._clean_text(value)
        
        # 数字字段转换
        if key in ['likes_count', 'comments_count', 'shares_count'] and value:
            value = self._to_int(value)
        
        # 列表字段处理
        if key in ['images', 'tags', 'topics'] and value:
            if not isinstance(value, list):
                value = [value] if value else []
            value = [item for item in value if item]  # 过滤空值
        
        # 布尔字段处理
        if key == 'is_featured' and value is not None:
            value = bool(value)
        
        super().__setitem__(key, value)
    
    def _clean_text(self, text: str) -> str:
        """清理文本内容"""
        if not text:
            return ""
        
        # 去除多余空白字符
        text = ' '.join(text.split())
        # 去除首尾空白
        text = text.strip()
        # 限制长度
        if len(text) > 10000:
            text = text[:10000] + "..."
        
        return text
    
    def _to_int(self, value) -> int:
        """转换为整数"""
        if isinstance(value, int):
            return value
        
        if isinstance(value, str):
            # 移除非数字字符
            import re
            number_text = re.search(r'(\d+)', value)
            if number_text:
                return int(number_text.group(1))
        
        return 0
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return dict(self)
    
    def validate(self) -> bool:
        """验证数据完整性"""
        required_fields = ['note_id', 'url', 'title']
        
        for field in required_fields:
            if not self.get(field):
                return False
        
        return True
    
    def get_summary(self) -> str:
        """获取数据摘要"""
        return f"笔记 {self.get('note_id', 'N/A')}: {self.get('title', 'N/A')[:50]}..."


class XiaohongshuUserItem(scrapy.Item):
    """小红书用户数据项"""
    
    # 基础信息
    user_id = scrapy.Field()          # 用户ID
    username = scrapy.Field()         # 用户名
    nickname = scrapy.Field()         # 昵称
    avatar_url = scrapy.Field()       # 头像URL
    profile_url = scrapy.Field()      # 个人主页URL
    
    # 个人信息
    bio = scrapy.Field()              # 个人简介
    gender = scrapy.Field()           # 性别
    location = scrapy.Field()         # 位置
    age = scrapy.Field()              # 年龄
    
    # 统计信息
    followers_count = scrapy.Field()   # 粉丝数
    following_count = scrapy.Field()   # 关注数
    notes_count = scrapy.Field()       # 笔记数
    likes_received = scrapy.Field()    # 获赞数
    
    # 认证信息
    is_verified = scrapy.Field()       # 是否认证
    verification_type = scrapy.Field() # 认证类型
    
    # 时间信息
    join_time = scrapy.Field()         # 注册时间
    last_active = scrapy.Field()       # 最后活跃时间
    crawl_time = scrapy.Field()        # 采集时间
    
    def validate(self) -> bool:
        """验证数据完整性"""
        required_fields = ['user_id', 'username', 'profile_url']
        
        for field in required_fields:
            if not self.get(field):
                return False
        
        return True


class XiaohongshuCommentItem(scrapy.Item):
    """小红书评论数据项"""
    
    # 基础信息
    comment_id = scrapy.Field()       # 评论ID
    note_id = scrapy.Field()          # 所属笔记ID
    content = scrapy.Field()          # 评论内容
    
    # 用户信息
    user_id = scrapy.Field()          # 评论用户ID
    username = scrapy.Field()         # 用户名
    user_avatar = scrapy.Field()      # 用户头像
    
    # 统计信息
    likes_count = scrapy.Field()      # 点赞数
    reply_count = scrapy.Field()      # 回复数
    
    # 时间信息
    publish_time = scrapy.Field()     # 发布时间
    crawl_time = scrapy.Field()       # 采集时间
    
    # 其他信息
    is_author_reply = scrapy.Field()  # 是否作者回复
    parent_comment_id = scrapy.Field() # 父评论ID（如果是回复）
    
    def validate(self) -> bool:
        """验证数据完整性"""
        required_fields = ['comment_id', 'note_id', 'content', 'user_id']
        
        for field in required_fields:
            if not self.get(field):
                return False
        
        return True
