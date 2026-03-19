FROM node:20-alpine AS builder

WORKDIR /app

COPY apps/workflow-ui/package.json apps/workflow-ui/package-lock.json* ./
RUN npm install

COPY apps/workflow-ui/ ./
RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app

# Install production dependencies only
RUN npm install express http-proxy-middleware

# Copy built assets, server, and package.json for "type": "module"
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/server.js ./
COPY --from=builder /app/package.json ./

EXPOSE 3000

CMD ["node", "server.js"]
