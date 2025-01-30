# 使用 Python 3.7 slim 作为基础镜像（基于 Debian）
FROM python:3.7-slim

# 设置国内镜像源，加速 APT 安装
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates tzdata curl gcc g++ make libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制当前项目到 /app 目录
COPY . /app
WORKDIR /app

# 配置 pip 国内源，并安装 Python 依赖
RUN pip config set global.index-url http://mirrors.cloud.tencent.com/pypi/simple \
    && pip config set global.trusted-host mirrors.cloud.tencent.com \
    && pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 暴露端口
EXPOSE 80

# 启动服务
CMD ["python3", "run.py", "0.0.0.0", "80"]
