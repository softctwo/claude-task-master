# Node.js 20
FROM node:20-alpine

WORKDIR /app

# 复制 package.json
COPY apps/web/package.json ./
RUN npm install

# 复制应用代码
COPY apps/web/ ./

# 暴露端口
EXPOSE 3000

# 启动命令
CMD ["npm", "run", "dev"]
