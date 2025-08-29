# Xiaolu-Workflow 技术架构文档

## 项目概述

Xiaolu-Workflow 是一个基于小红书内容的智能文案生成平台，包含数据采集、内容管理、AI生成和分发功能。

## 技术架构

### 整体架构
- **架构模式**: 微服务架构
- **部署方式**: Docker容器化部署
- **通信方式**: REST API + 消息队列

### 技术栈

#### 前端
- **框架**: Next.js 14 + React 18 + TypeScript
- **UI库**: Tailwind CSS + shadcn/ui
- **状态管理**: Zustand
- **HTTP客户端**: Axios
- **构建工具**: Turbopack

#### 后端服务

##### 1. 爬虫服务 (Python)
```
crawler-service/
├── app/
│   ├── spiders/
│   │   ├── xiaohongshu_spider.py
│   │   └── base_spider.py
│   ├── items.py
│   ├── pipelines.py
│   ├── middlewares.py
│   └── settings.py
├── requirements.txt
└── Dockerfile
```

##### 2. 内容管理服务 (Node.js)
```
content-service/
├── src/
│   ├── controllers/
│   ├── models/
│   ├── routes/
│   ├── middleware/
│   ├── services/
│   └── utils/
├── package.json
├── tsconfig.json
└── Dockerfile
```

##### 3. AI文案生成服务 (Python)
```
ai-service/
├── app/
│   ├── models/
│   ├── services/
│   ├── api/
│   └── utils/
├── requirements.txt
└── Dockerfile
```

##### 4. 定时任务服务
```
scheduler-service/
├── tasks/
├── celery_app.py
├── requirements.txt
└── Dockerfile
```

#### 数据存储
- **主数据库**: PostgreSQL 15
- **缓存**: Redis 7
- **对象存储**: AWS S3 / 阿里云OSS

### 项目结构

```
xiaolu-workflow/
├── frontend/                    # Next.js前端应用
│   ├── src/
│   │   ├── app/                # App Router
│   │   ├── components/         # React组件
│   │   ├── hooks/             # 自定义Hooks
│   │   ├── lib/               # 工具函数
│   │   ├── stores/            # Zustand状态管理
│   │   └── types/             # TypeScript类型定义
│   ├── public/                # 静态资源
│   ├── package.json
│   ├── next.config.js
│   └── tailwind.config.js
│
├── backend/
│   ├── crawler-service/       # 爬虫服务
│   ├── content-service/       # 内容管理服务
│   ├── ai-service/           # AI生成服务
│   └── scheduler-service/     # 定时任务服务
│
├── database/
│   ├── migrations/           # 数据库迁移文件
│   ├── seeds/               # 种子数据
│   └── schema.sql           # 数据库结构
│
├── docker/
│   ├── docker-compose.yml   # 开发环境
│   ├── docker-compose.prod.yml # 生产环境
│   └── nginx/               # Nginx配置
│
├── docs/                    # 文档
├── scripts/                 # 部署脚本
└── README.md
```

## 核心功能模块

### 1. 数据采集模块
- **功能**: 定时爬取小红书笔记数据
- **技术**: Scrapy + Selenium + 代理池
- **调度**: Celery定时任务
- **存储**: PostgreSQL + OSS

### 2. 内容管理模块
- **功能**: 笔记浏览、筛选、精选
- **技术**: React + Next.js响应式设计
- **特性**: 移动端适配、实时搜索、批量操作

### 3. AI生成模块
- **功能**: 基于精选笔记生成爆款文案
- **技术**: LangChain + OpenAI/Claude API
- **特性**: 多模型支持、模板定制、质量评估

### 4. 分发模块（待实现）
- **功能**: 自动发布到小红书等平台
- **技术**: 平台API集成
- **特性**: 定时发布、数据统计

## 部署架构

### 开发环境
```yaml
# docker-compose.yml
version: '3.8'
services:
  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
  
  content-service:
    build: ./backend/content-service
    ports:
      - "3001:3000"
  
  ai-service:
    build: ./backend/ai-service
    ports:
      - "8000:8000"
  
  crawler-service:
    build: ./backend/crawler-service
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: xiaolu_workflow
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
  
  redis:
    image: redis:7
    ports:
      - "6379:6379"
```

### 生产环境
- **容器编排**: Docker Swarm / Kubernetes
- **负载均衡**: Nginx
- **监控**: Prometheus + Grafana
- **日志**: ELK Stack
- **CI/CD**: GitHub Actions

## API设计

### 内容管理API
```
GET    /api/notes              # 获取笔记列表
POST   /api/notes              # 创建笔记
GET    /api/notes/:id          # 获取笔记详情
PUT    /api/notes/:id/select   # 精选笔记
DELETE /api/notes/:id          # 删除笔记

GET    /api/categories         # 获取分类列表
POST   /api/categories         # 创建分类
```

### AI生成API
```
POST   /api/ai/generate        # 生成文案
GET    /api/ai/templates       # 获取模板列表
POST   /api/ai/templates       # 创建模板
```

### 用户管理API
```
POST   /api/auth/login         # 用户登录
POST   /api/auth/logout        # 用户登出
GET    /api/users/profile      # 获取用户信息
```

## 数据流程

1. **数据采集流程**
   - 定时任务触发爬虫
   - 爬取小红书笔记数据
   - 数据清洗和存储
   - 图片下载到OSS

2. **内容管理流程**
   - 用户浏览爬取的笔记
   - 筛选和标记精选笔记
   - 批量操作和分类管理

3. **AI生成流程**
   - 选择精选笔记
   - 配置生成参数
   - 调用AI模型生成文案
   - 人工审核和优化

4. **内容分发流程**（待实现）
   - 选择生成的文案
   - 配置发布参数
   - 自动发布到平台
   - 数据统计和分析

## 安全考虑

- **认证授权**: JWT Token + RBAC
- **数据加密**: HTTPS + 数据库加密
- **防爬保护**: 代理轮换 + 请求限流
- **输入验证**: 参数校验 + SQL注入防护
- **敏感信息**: 环境变量 + 密钥管理

## 性能优化

- **缓存策略**: Redis多层缓存
- **数据库优化**: 索引优化 + 读写分离
- **CDN加速**: 静态资源CDN
- **异步处理**: 消息队列 + 后台任务
- **前端优化**: 代码分割 + 懒加载

## 监控告警

- **应用监控**: APM工具
- **系统监控**: 资源使用率
- **业务监控**: 关键指标
- **日志监控**: 错误日志分析
- **告警通知**: 邮件 + 钉钉

这个架构设计考虑了可扩展性、可维护性和性能，能够支撑产品的长期发展。
