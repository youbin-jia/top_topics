# Node 镜像（国内镜像源），用于构建和运行 Vite 开发服务器
FROM node:20-alpine

WORKDIR /app

# 复制依赖清单（无 lock 时也可构建）
COPY package.json ./

# 安装依赖
RUN npm install

# 复制源码（生产构建时可利用层缓存，开发时由 volume 覆盖）
COPY . .

# 暴露端口（与 docker-compose 中 3000:3000 一致）
EXPOSE 3000

# 开发模式：Vite 监听 0.0.0.0:3000 以在容器内可访问
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
