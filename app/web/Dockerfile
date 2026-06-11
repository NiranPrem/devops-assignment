FROM node:22-alpine

RUN apk update && apk upgrade --no-cache

RUN addgroup -S app && adduser -S app -G app

WORKDIR /app

COPY --chown=app:app package*.json ./
RUN npm ci --omit=dev 2>/dev/null || true

COPY --chown=app:app . .

USER app

EXPOSE 3000

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
  CMD wget -qO- http://localhost:3000/healthz || exit 1

CMD ["node", "server.js"]
