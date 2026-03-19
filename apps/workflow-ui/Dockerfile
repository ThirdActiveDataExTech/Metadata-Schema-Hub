FROM node:20-alpine AS builder

WORKDIR /app

COPY apps/workflow-ui/package.json apps/workflow-ui/package-lock.json* ./
RUN npm install

COPY apps/workflow-ui/ ./
RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app

# Install production dependencies and gettext for envsubst
RUN apk add --no-cache gettext && npm install express

# Copy built assets, server, and package.json for "type": "module"
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/server.js ./
COPY --from=builder /app/package.json ./
COPY --from=builder /app/entrypoint.sh ./

RUN chmod +x entrypoint.sh

EXPOSE 3000

CMD ["./entrypoint.sh"]
