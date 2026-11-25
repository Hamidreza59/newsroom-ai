FROM node:22-bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    chromium libnss3 libdbus-1-3 libatk1.0-0 libasound2 libxrandr2 libxkbcommon-dev libxfixes3 \
    libxcomposite1 libxdamage1 libgbm-dev libcups2 libcairo2 libpango-1.0-0 ffmpeg ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY services/studio/package.json services/studio/package-lock.json services/studio/.npmrc ./
RUN npm ci
COPY services/studio/ ./
ENV REMOTION_CHROME_EXECUTABLE=/usr/bin/chromium
RUN useradd --create-home --uid 10001 newsroom && chown -R newsroom /app
USER newsroom
VOLUME /data/out
ENTRYPOINT ["npm", "run", "--silent", "render", "--"]
CMD ["/data/out"]
