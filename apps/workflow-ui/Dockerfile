FROM node:20-alpine AS builder

WORKDIR /app

COPY apps/workflow-ui/package.json apps/workflow-ui/package-lock.json* ./
RUN npm install

COPY apps/workflow-ui/ ./

# CI에서 .env(VITE_* 버전 정보)를 생성하여 전달, 로컬 빌드 시 빈 파일로 대체
RUN test -f .env || touch .env
RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app

# gettext: entrypoint.sh에서 envsubst로 config.js 내 K8s 런타임 변수 치환
RUN apk add --no-cache gettext && npm install express

# Copy built assets, server, and package.json for "type": "module"
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/server.js ./
COPY --from=builder /app/package.json ./
COPY --from=builder /app/entrypoint.sh ./

# push-to-github 파이프라인에서 버전 추출용
COPY --from=builder /app/.env ./

RUN chmod +x entrypoint.sh

EXPOSE 3000

CMD ["./entrypoint.sh"]
