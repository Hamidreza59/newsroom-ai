#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";

const dir = resolve(process.argv[2] ?? "");
const episodePath = resolve(dir, "episode.json");
if (!process.argv[2] || !existsSync(episodePath)) {
  console.error("usage: npm run render -- <episode-dir containing episode.json>");
  process.exit(1);
}

const episode = JSON.parse(readFileSync(episodePath, "utf8"));
const seconds = episode.durationInFrames / episode.fps;
console.log(`Rendering ${episode.showName} ${episode.date} (${seconds.toFixed(1)}s) from ${dir}`);

const remotion = (args) => {
  const res = spawnSync("npx", ["remotion", ...args, `--props=${episodePath}`, `--public-dir=${dir}`],
    { stdio: "inherit" });
  if (res.status !== 0) process.exit(res.status ?? 1);
};

remotion(["render", "src/index.ts", "DailyShow", resolve(dir, "video.mp4"), "--codec=h264", "--crf=18",
  "--audio-bitrate=192k"]);
remotion(["still", "src/index.ts", "Thumbnail", resolve(dir, "thumbnail.png")]);
console.log(`Done: ${resolve(dir, "video.mp4")} and thumbnail.png`);
