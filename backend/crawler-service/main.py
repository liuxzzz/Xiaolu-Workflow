#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Xiaolu-Workflow 爬虫服务主入口

提供命令行接口、健康检查接口和爬虫管理功能
"""

import os
import sys
import argparse
import signal
import logging
import asyncio
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
import multiprocessing as mp

# 添加项目路径到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 第三方库
import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor, defer
from twisted.internet.task import LoopingCall
from loguru import logger

# 项目模块
from app.spiders.xiaohongshu_spider import XiaohongshuSpider
from app.settings import validate_settings


class CrawlerManager:
    """爬虫管理器"""
    
    def __init__(self):
        self.settings = get_project_settings()
        self.crawler_process = None
        self.running_spiders = {}
        self.stats = {
            'total_runs': 0,
            'successful_runs': 0,
            'failed_runs': 0,
            'last_run_time': None,
            'last_run_status': None,
        }
    
    def run_spider(self, spider_name: str, **kwargs) -> bool:
        """运行单个爬虫"""
        try:
            logger.info(f"开始运行爬虫: {spider_name}")
            
            # 创建爬虫进程
            process = CrawlerProcess(self.settings)
            
            # 根据爬虫名称选择爬虫类
            if spider_name == 'xiaohongshu':
                spider_class = XiaohongshuSpider
            else:
                raise ValueError(f"未知的爬虫: {spider_name}")
            
            # 添加爬虫到进程
            process.crawl(spider_class, **kwargs)
            
            # 启动爬虫
            process.start()
            
            # 更新统计信息
            self.stats['total_runs'] += 1
            self.stats['successful_runs'] += 1
            self.stats['last_run_time'] = datetime.now().isoformat()
            self.stats['last_run_status'] = 'success'
            
            logger.info(f"爬虫 {spider_name} 运行完成")
            return True
            
        except Exception as e:
            logger.error(f"爬虫 {spider_name} 运行失败: {e}")
            self.stats['total_runs'] += 1
            self.stats['failed_runs'] += 1
            self.stats['last_run_time'] = datetime.now().isoformat()
            self.stats['last_run_status'] = 'failed'
            return False
    
    def run_spider_async(self, spider_name: str, **kwargs):
        """异步运行爬虫"""
        def _run():
            return self.run_spider(spider_name, **kwargs)
        
        # 在新进程中运行爬虫
        process = mp.Process(target=_run)
        process.start()
        self.running_spiders[spider_name] = process
        
        return process.pid
    
    def stop_spider(self, spider_name: str) -> bool:
        """停止指定爬虫"""
        if spider_name in self.running_spiders:
            process = self.running_spiders[spider_name]
            if process.is_alive():
                process.terminate()
                process.join(timeout=10)
                if process.is_alive():
                    process.kill()
                del self.running_spiders[spider_name]
                logger.info(f"爬虫 {spider_name} 已停止")
                return True
        
        return False
    
    def get_spider_status(self, spider_name: str = None) -> Dict:
        """获取爬虫状态"""
        if spider_name:
            is_running = spider_name in self.running_spiders and \
                        self.running_spiders[spider_name].is_alive()
            return {
                'spider': spider_name,
                'running': is_running,
                'pid': self.running_spiders.get(spider_name, {}).pid if is_running else None
            }
        else:
            return {
                'running_spiders': list(self.running_spiders.keys()),
                'stats': self.stats
            }


# 创建FastAPI应用
app = FastAPI(
    title="Xiaolu-Workflow 爬虫服务",
    description="小红书内容爬虫服务API",
    version="1.0.0"
)

# 创建爬虫管理器实例
crawler_manager = CrawlerManager()


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Xiaolu-Workflow 爬虫服务",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/health")
async def health_check():
    """健康检查接口"""
    try:
        # 检查基本功能
        settings_ok = True
        try:
            validate_settings()
        except Exception as e:
            settings_ok = False
            logger.warning(f"配置验证失败: {e}")
        
        # 检查目录权限
        required_dirs = ['./downloads/images', './output', './logs']
        dirs_ok = True
        for dir_path in required_dirs:
            try:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
            except Exception:
                dirs_ok = False
                break
        
        # 综合健康状态
        healthy = settings_ok and dirs_ok
        
        return {
            "status": "healthy" if healthy else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "settings": "ok" if settings_ok else "error",
                "directories": "ok" if dirs_ok else "error",
                "running_spiders": len(crawler_manager.running_spiders)
            }
        }
    
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@app.post("/spiders/{spider_name}/start")
async def start_spider(spider_name: str, background_tasks: BackgroundTasks, 
                      keyword: str = "美妆", max_pages: int = 10):
    """启动爬虫"""
    try:
        # 检查爬虫是否已在运行
        if spider_name in crawler_manager.running_spiders:
            process = crawler_manager.running_spiders[spider_name]
            if process.is_alive():
                raise HTTPException(status_code=400, detail=f"爬虫 {spider_name} 已在运行中")
        
        # 验证参数
        if spider_name != 'xiaohongshu':
            raise HTTPException(status_code=400, detail=f"不支持的爬虫: {spider_name}")
        
        if max_pages <= 0 or max_pages > 100:
            raise HTTPException(status_code=400, detail="max_pages 必须在 1-100 之间")
        
        # 异步启动爬虫
        pid = crawler_manager.run_spider_async(
            spider_name, 
            keyword=keyword, 
            max_pages=max_pages
        )
        
        logger.info(f"爬虫 {spider_name} 启动成功，PID: {pid}")
        
        return {
            "message": f"爬虫 {spider_name} 启动成功",
            "spider": spider_name,
            "pid": pid,
            "parameters": {
                "keyword": keyword,
                "max_pages": max_pages
            },
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动爬虫失败: {e}")
        raise HTTPException(status_code=500, detail=f"启动爬虫失败: {str(e)}")


@app.post("/spiders/{spider_name}/stop")
async def stop_spider(spider_name: str):
    """停止爬虫"""
    try:
        success = crawler_manager.stop_spider(spider_name)
        
        if success:
            return {
                "message": f"爬虫 {spider_name} 停止成功",
                "spider": spider_name,
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail=f"爬虫 {spider_name} 未在运行")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止爬虫失败: {e}")
        raise HTTPException(status_code=500, detail=f"停止爬虫失败: {str(e)}")


@app.get("/spiders/{spider_name}/status")
async def get_spider_status(spider_name: str):
    """获取爬虫状态"""
    try:
        status = crawler_manager.get_spider_status(spider_name)
        return {
            "timestamp": datetime.now().isoformat(),
            **status
        }
    
    except Exception as e:
        logger.error(f"获取爬虫状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@app.get("/spiders/status")
async def get_all_spiders_status():
    """获取所有爬虫状态"""
    try:
        status = crawler_manager.get_spider_status()
        return {
            "timestamp": datetime.now().isoformat(),
            **status
        }
    
    except Exception as e:
        logger.error(f"获取爬虫状态失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取状态失败: {str(e)}")


@app.get("/metrics")
async def get_metrics():
    """获取监控指标"""
    try:
        import psutil
        
        # 系统指标
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 爬虫指标
        spider_stats = crawler_manager.stats
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_mb": memory.used // 1024 // 1024,
                "memory_total_mb": memory.total // 1024 // 1024,
                "disk_percent": disk.percent,
                "disk_used_gb": disk.used // 1024 // 1024 // 1024,
                "disk_total_gb": disk.total // 1024 // 1024 // 1024,
            },
            "spiders": {
                "running_count": len(crawler_manager.running_spiders),
                "total_runs": spider_stats['total_runs'],
                "successful_runs": spider_stats['successful_runs'],
                "failed_runs": spider_stats['failed_runs'],
                "success_rate": spider_stats['successful_runs'] / max(spider_stats['total_runs'], 1) * 100,
                "last_run_time": spider_stats['last_run_time'],
                "last_run_status": spider_stats['last_run_status'],
            }
        }
    
    except Exception as e:
        logger.error(f"获取监控指标失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取指标失败: {str(e)}")


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """设置日志配置"""
    logger.remove()  # 移除默认处理器
    
    # 控制台输出
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # 文件输出
    if log_file:
        logger.add(
            log_file,
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="10 MB",
            retention="30 days",
            compression="zip"
        )


def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"接收到信号 {signum}，正在优雅关闭...")
    
    # 停止所有运行中的爬虫
    for spider_name in list(crawler_manager.running_spiders.keys()):
        crawler_manager.stop_spider(spider_name)
    
    logger.info("所有爬虫已停止，服务即将退出")
    sys.exit(0)


def run_api_server(host: str = "0.0.0.0", port: int = 8080):
    """运行API服务器"""
    logger.info(f"启动API服务器: http://{host}:{port}")
    
    # 设置信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 启动API服务器
    uvicorn.run(
        app, 
        host=host, 
        port=port,
        log_level="info",
        access_log=True
    )


def run_spider_cli(spider_name: str, **kwargs):
    """命令行运行爬虫"""
    logger.info(f"通过命令行运行爬虫: {spider_name}")
    
    success = crawler_manager.run_spider(spider_name, **kwargs)
    
    if success:
        logger.info("爬虫运行完成")
        sys.exit(0)
    else:
        logger.error("爬虫运行失败")
        sys.exit(1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="Xiaolu-Workflow 爬虫服务")
    
    # 运行模式
    parser.add_argument('--mode', choices=['api', 'spider'], default='api',
                       help='运行模式: api(API服务器) 或 spider(命令行爬虫)')
    
    # API服务器参数
    parser.add_argument('--host', default='0.0.0.0', help='API服务器主机')
    parser.add_argument('--port', type=int, default=8080, help='API服务器端口')
    
    # 爬虫参数
    parser.add_argument('--spider', choices=['xiaohongshu'], default='xiaohongshu',
                       help='爬虫名称')
    parser.add_argument('--keyword', default='美妆', help='搜索关键词')
    parser.add_argument('--max-pages', type=int, default=10, help='最大爬取页数')
    
    # 日志参数
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='日志级别')
    parser.add_argument('--log-file', help='日志文件路径')
    
    # 开发模式
    parser.add_argument('--dev', action='store_true', help='开发模式')
    parser.add_argument('--debug', action='store_true', help='调试模式')
    
    args = parser.parse_args()
    
    # 设置日志
    log_level = 'DEBUG' if args.debug else args.log_level
    setup_logging(log_level, args.log_file)
    
    # 输出启动信息
    logger.info("=" * 60)
    logger.info("Xiaolu-Workflow 爬虫服务启动")
    logger.info(f"模式: {args.mode}")
    logger.info(f"日志级别: {log_level}")
    logger.info("=" * 60)
    
    try:
        # 验证配置
        if not args.dev:
            validate_settings()
            logger.info("配置验证通过")
        
        # 根据模式运行
        if args.mode == 'api':
            run_api_server(args.host, args.port)
        elif args.mode == 'spider':
            run_spider_cli(
                args.spider,
                keyword=args.keyword,
                max_pages=args.max_pages
            )
    
    except KeyboardInterrupt:
        logger.info("用户中断，正在退出...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
