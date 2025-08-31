# Xiaolu-Workflow 爬虫服务

基于 Scrapy 的小红书内容爬虫服务，用于采集小红书笔记数据。

## 功能特性

- 🕷️ 基于 Scrapy 框架的高性能爬虫
- 🎯 专门针对小红书平台优化
- 🔄 支持多种反反爬虫策略
- 📊 完整的数据处理管道
- 🐳 Docker 容器化部署
- 📡 RESTful API 接口
- 📈 实时监控和指标
- 🛡️ 数据验证和去重

## 技术架构

- **爬虫框架**: Scrapy 2.11.0
- **浏览器自动化**: Selenium + Chrome
- **数据库**: PostgreSQL
- **缓存**: Redis
- **API框架**: FastAPI
- **日志**: Loguru
- **监控**: Prometheus + Grafana

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd backend/crawler-service

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp env.example .env

# 编辑配置文件
vim .env
```

必须配置的环境变量：
- `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`: 数据库连接信息
- `REDIS_HOST`, `REDIS_PORT`: Redis 连接信息

### 3. 运行方式

#### API 服务模式（推荐）

```bash
# 启动 API 服务
python main.py --mode api

# 指定端口
python main.py --mode api --port 8080
```

API 接口：
- `GET /health` - 健康检查
- `POST /spiders/xiaohongshu/start` - 启动爬虫
- `POST /spiders/xiaohongshu/stop` - 停止爬虫
- `GET /spiders/xiaohongshu/status` - 爬虫状态
- `GET /metrics` - 监控指标

#### 命令行模式

```bash
# 直接运行爬虫
python main.py --mode spider --keyword "美妆" --max-pages 10

# 调试模式
python main.py --mode spider --debug --keyword "护肤"
```

### 4. Docker 部署

```bash
# 构建镜像
docker build -t xiaolu-crawler .

# 运行容器
docker run -d \
  --name xiaolu-crawler \
  -p 8080:8080 \
  -e DB_HOST=host.docker.internal \
  -e REDIS_HOST=host.docker.internal \
  xiaolu-crawler

# 查看日志
docker logs -f xiaolu-crawler
```

## 配置说明

### 主要配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `CONCURRENT_REQUESTS` | 并发请求数 | 8 |
| `DOWNLOAD_DELAY` | 下载延迟(秒) | 3 |
| `MAX_PAGES_PER_KEYWORD` | 每个关键词最大页数 | 10 |
| `USE_PROXY` | 是否使用代理 | false |
| `USE_SELENIUM` | 是否使用Selenium | false |

### 爬虫参数

- `keyword`: 搜索关键词（默认：美妆）
- `max_pages`: 最大爬取页数（默认：10）

## API 使用示例

### 启动爬虫

```bash
curl -X POST "http://localhost:8080/spiders/xiaohongshu/start" \
  -H "Content-Type: application/json" \
  -d '{
    "keyword": "护肤",
    "max_pages": 5
  }'
```

### 查看状态

```bash
curl "http://localhost:8080/spiders/xiaohongshu/status"
```

### 获取指标

```bash
curl "http://localhost:8080/metrics"
```

## 数据输出

爬取的数据会输出到多个位置：

1. **数据库**: PostgreSQL 表 `xiaohongshu_notes`
2. **JSON 文件**: `./output/` 目录下的 JSON Lines 格式文件
3. **图片文件**: `./downloads/images/` 目录

### 数据字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `note_id` | String | 笔记唯一ID |
| `title` | String | 笔记标题 |
| `content` | String | 笔记内容 |
| `author_name` | String | 作者名称 |
| `likes_count` | Integer | 点赞数 |
| `comments_count` | Integer | 评论数 |
| `images` | Array | 图片URL列表 |
| `tags` | Array | 标签列表 |
| `crawl_time` | String | 采集时间 |

## 反反爬虫策略

1. **用户代理轮换**: 随机选择不同的 User-Agent
2. **请求延迟**: 随机延迟请求间隔
3. **代理轮换**: 支持HTTP代理池
4. **Cookie管理**: 自动管理和持久化Cookie
5. **Selenium渲染**: 处理JavaScript动态内容
6. **请求头伪装**: 模拟真实浏览器请求

## 监控和日志

### 日志配置

- 控制台输出：彩色格式化日志
- 文件输出：自动轮转和压缩
- 日志级别：DEBUG/INFO/WARNING/ERROR

### 监控指标

- 系统指标：CPU、内存、磁盘使用率
- 爬虫指标：运行次数、成功率、耗时
- 业务指标：数据量、错误率

## 开发指南

### 项目结构

```
crawler-service/
├── app/
│   ├── spiders/          # 爬虫模块
│   │   ├── base_spider.py      # 基础爬虫类
│   │   └── xiaohongshu_spider.py # 小红书爬虫
│   ├── items.py          # 数据项定义
│   ├── pipelines.py      # 数据处理管道
│   ├── middlewares.py    # 中间件
│   └── settings.py       # 配置文件
├── main.py               # 主入口文件
├── requirements.txt      # 依赖列表
├── Dockerfile           # Docker镜像配置
├── scrapy.cfg           # Scrapy配置
└── README.md            # 项目文档
```

### 扩展爬虫

1. 继承 `BaseSpider` 类
2. 实现 `parse` 方法
3. 定义数据项结构
4. 配置管道处理

### 添加中间件

1. 在 `middlewares.py` 中实现中间件类
2. 在 `settings.py` 中注册中间件
3. 配置执行优先级

## 故障排查

### 常见问题

1. **Chrome/ChromeDriver版本不匹配**
   ```bash
   # 查看Chrome版本
   google-chrome --version
   
   # 更新ChromeDriver
   pip install --upgrade webdriver-manager
   ```

2. **数据库连接失败**
   ```bash
   # 检查数据库连接
   psql -h $DB_HOST -U $DB_USER -d $DB_NAME
   ```

3. **代理连接超时**
   ```bash
   # 测试代理可用性
   curl --proxy http://proxy:port http://httpbin.org/ip
   ```

### 调试模式

```bash
# 启用调试模式
python main.py --debug --mode spider

# 查看详细日志
tail -f logs/crawler.log
```

## 性能优化

1. **并发控制**: 根据目标网站调整并发数
2. **缓存策略**: 启用HTTP缓存减少重复请求
3. **图片下载**: 可选择性下载图片节省带宽
4. **数据库优化**: 使用批量插入提高写入性能

## 安全注意事项

1. 遵守 robots.txt 协议
2. 控制请求频率避免对目标网站造成压力
3. 不要爬取用户隐私信息
4. 妥善保管代理和Cookie信息
5. 定期更新反爬虫策略

## 许可证

本项目基于 MIT 许可证开源。

## 贡献指南

欢迎提交 Issue 和 Pull Request 来改进项目。

## 联系方式

如有问题请联系项目维护者。
