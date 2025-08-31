# Xiaolu-Workflow 爬虫服务 Docker镜像

# 使用官方Python 3.11基础镜像
FROM python:3.11-slim as base

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    # 基础工具
    curl \
    wget \
    unzip \
    gnupg \
    software-properties-common \
    # 编译工具
    gcc \
    g++ \
    make \
    # Python扩展依赖
    python3-dev \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    libpng-dev \
    libfreetype6-dev \
    # Chrome浏览器依赖
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    xdg-utils \
    # 清理缓存
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 安装Chrome浏览器
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 安装ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+') \
    && CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION%.*}") \
    && wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /tmp/ \
    && mv /tmp/chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    && rm /tmp/chromedriver.zip

# 创建非root用户
RUN groupadd -r crawler && useradd -r -g crawler -s /bin/bash crawler

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt \
    && pip cache purge

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p /app/downloads/images \
    && mkdir -p /app/output \
    && mkdir -p /app/logs \
    && mkdir -p /app/httpcache

# 设置目录权限
RUN chown -R crawler:crawler /app

# 切换到非root用户
USER crawler

# 设置Python路径
ENV PYTHONPATH=/app

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)" || exit 1

# 暴露端口（用于健康检查和监控）
EXPOSE 8080

# 默认命令
CMD ["python", "main.py"]

# === 多阶段构建：生产环境镜像 ===
FROM base as production

# 生产环境配置
ENV ENVIRONMENT=production \
    LOG_LEVEL=WARNING \
    CONCURRENT_REQUESTS=8

# 移除开发工具
RUN pip uninstall -y \
    jupyter \
    ipython \
    black \
    isort \
    flake8 \
    pytest \
    pytest-cov

# === 多阶段构建：开发环境镜像 ===
FROM base as development

# 开发环境配置
ENV ENVIRONMENT=development \
    LOG_LEVEL=DEBUG \
    CONCURRENT_REQUESTS=1

# 安装开发依赖
COPY requirements-dev.txt* ./
RUN if [ -f requirements-dev.txt ]; then pip install -r requirements-dev.txt; fi

# 开发环境暴露更多端口
EXPOSE 8888 9090

# 开发环境启动命令（可以启动Jupyter）
CMD ["python", "main.py", "--dev"]

# === 调试镜像 ===
FROM development as debug

# 安装调试工具
RUN pip install \
    pdb++ \
    ipdb \
    memory-profiler \
    line-profiler

# 调试模式环境变量
ENV DEBUG=1 \
    LOG_LEVEL=DEBUG

# 调试启动命令
CMD ["python", "-u", "main.py", "--debug"]
