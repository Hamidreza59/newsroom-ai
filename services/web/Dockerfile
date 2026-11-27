FROM node:22-bookworm-slim AS build
WORKDIR /app
COPY package.json package-lock.json .npmrc ./
COPY packages/brand/package.json packages/brand/package.json
COPY services/studio/package.json services/studio/package.json
COPY services/web/package.json services/web/package.json
RUN npm ci --workspace @newsroom/web --include-workspace-root
COPY packages packages
COPY services/web services/web
ARG NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL NEXT_TELEMETRY_DISABLED=1
RUN npm run build -w @newsroom/web

FROM node:22-bookworm-slim
RUN useradd --create-home --uid 10001 newsroom
WORKDIR /app
ENV NODE_ENV=production NEXT_TELEMETRY_DISABLED=1 PORT=3000 HOSTNAME=0.0.0.0 API_URL=http://newsroom-api:8000
COPY --from=build --chown=newsroom /app/services/web/.next/standalone ./
COPY --from=build --chown=newsroom /app/services/web/.next/static services/web/.next/static
USER newsroom
EXPOSE 3000
CMD ["node", "services/web/server.js"]
