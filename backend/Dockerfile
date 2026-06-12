# 国内网络可设置镜像：docker compose build --build-arg REGISTRY_MIRROR=docker.m.daocloud.io/library/
ARG REGISTRY_MIRROR=
FROM ${REGISTRY_MIRROR}python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 创建数据目录
RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
