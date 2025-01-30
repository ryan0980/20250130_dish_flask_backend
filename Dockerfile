# 更改基础镜像为 Python 3.8+
FROM python:3.8-slim

# 更新 apt 并安装必要工具
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates tzdata curl gcc g++ make libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# 配置国内 pip 源
RUN pip config set global.index-url http://mirrors.cloud.tencent.com/pypi/simple \
    && pip config set global.trusted-host mirrors.cloud.tencent.com \
    && pip install --upgrade pip

# 复制项目代码
COPY . /app
WORKDIR /app

# 先安装 numpy，避免依赖冲突
RUN pip install numpy>=1.19,<1.24

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口
EXPOSE 80

# 启动服务
CMD ["python3", "run.py", "0.0.0.0", "80"]
