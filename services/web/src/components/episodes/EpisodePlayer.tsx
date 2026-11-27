"use client";

import { Play } from "lucide-react";
import { useRef } from "react";
import { EpisodeVisual } from "./EpisodeVisual";
import type { Chapter } from "@/lib/contract";

const toSeconds = (t: string) => t.split(":").reduce((acc, p) => acc * 60 + Number(p), 0);

export function EpisodePlayer({
  videoSrc,
  thumbnailUrl,
  date,
  chapters,
}: {
  videoSrc: string | null;
  thumbnailUrl: string | null;
  date: string;
  chapters: Chapter[];
}) {
  const video = useRef<HTMLVideoElement>(null);
  const seek = (t: string) => {
    const el = video.current;
    if (!el) return;
    el.currentTime = toSeconds(t);
    void el.play();
    el.scrollIntoView({ block: "nearest", behavior: "smooth" });
  };

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
      <div className="card overflow-hidden">
        {videoSrc ? (
          <video ref={video} controls preload="metadata" className="aspect-video w-full bg-black" poster={undefined}>
            <source src={videoSrc} type="video/mp4" />
          </video>
        ) : (
          <div className="relative">
            <EpisodeVisual thumbnailUrl={thumbnailUrl} date={date} />
            <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/70 to-transparent px-4 py-3 text-xs text-white/80">
              The video for this episode has not been rendered yet.
            </div>
          </div>
        )}
      </div>
      <nav aria-label="Chapters" className="card max-h-[420px] overflow-y-auto p-2">
        <h2 className="eyebrow px-3 pb-2 pt-3">Chapters</h2>
        <ol>
          {chapters.map((c) => (
            <li key={c.time + c.title}>
              <button
                type="button"
                onClick={() => seek(c.time)}
                disabled={!videoSrc}
                className="flex w-full items-start gap-3 rounded-lg px-3 py-2.5 text-left text-sm hover:bg-surface-2 disabled:cursor-default disabled:hover:bg-transparent"
              >
                <span className="num mt-0.5 inline-flex shrink-0 items-center gap-1 text-xs text-gold">
                  {videoSrc && <Play size={9} fill="currentColor" aria-hidden="true" />}
                  {c.time}
                </span>
                <span>{c.title}</span>
              </button>
            </li>
          ))}
        </ol>
      </nav>
    </div>
  );
}
