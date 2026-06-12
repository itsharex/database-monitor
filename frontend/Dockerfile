# 国内网络可设置镜像：docker compose build --build-arg REGISTRY_MIRROR=docker.m.daocloud.io/library/
ARG REGISTRY_MIRROR=

# 构建阶段
FROM ${REGISTRY_MIRROR}node:20-alpine AS builder

WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

# 运行阶段
FROM ${REGISTRY_MIRROR}nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
