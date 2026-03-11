FROM node:20-alpine AS builder

WORKDIR /app

COPY apps/workflow-ui/package.json apps/workflow-ui/package-lock.json* ./
RUN npm install

COPY apps/workflow-ui/ ./
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY apps/workflow-ui/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
