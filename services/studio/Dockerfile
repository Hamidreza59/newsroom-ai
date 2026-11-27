FROM node:22-bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium libnss3 libdbus-1-3 libatk1.0-0 libasound2 libxrandr2 libxkbcommon-dev libxfixes3 \
    libxcomposite1 libxdamage1 libgbm-dev libcups2 libcairo2 libpango-1.0-0 ffmpeg ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY package.json package-lock.json .npmrc ./
COPY packages/brand/package.json packages/brand/package.json
COPY services/studio/package.json services/studio/package.json
COPY services/web/package.json services/web/package.json
RUN npm ci --workspace newsroom-studio --include-workspace-root
COPY packages/brand packages/brand
COPY services/studio services/studio
WORKDIR /app/services/studio
ENV REMOTION_CHROME_EXECUTABLE=/usr/bin/chromium
RUN useradd --create-home --uid 10001 newsroom && chown -R newsroom /app
USER newsroom
VOLUME /data/out
ENTRYPOINT ["npm", "run", "--silent", "render", "--"]
CMD ["/data/out"]
