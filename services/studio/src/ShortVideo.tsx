import React from "react";
import { AbsoluteFill, interpolate, Sequence, useCurrentFrame } from "remotion";
import { Logo } from "./components/Chrome";
import { NewsroomSet, useCamera, WORLD } from "./components/Newsroom";
import { Voice } from "./components/Voice";
import { TvContent } from "./DailyShow";
import { anchorColor, body, color, display, layout } from "./theme";
import type { Episode } from "./types";

const W = 1080;

const BigCaption: React.FC<{ episode: Episode }> = ({ episode }) => {
  const frame = useCurrentFrame();
  const cap = episode.captions.find((c) => frame >= c.startFrame && frame < c.endFrame + 4);
  if (!cap) return null;
  const name = episode.anchors.find((a) => a.id === cap.speaker)?.name ?? "";
  const opacity = interpolate(frame, [cap.startFrame, cap.startFrame + 4], [0, 1], { extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", left: 60, right: 60, top: 1440, opacity, textAlign: "center" }}>
      <div style={{ display: "inline-block", padding: "6px 18px", borderRadius: 10, background: anchorColor(cap.speaker),
                    color: color.bg0, fontFamily: display, fontWeight: 700, fontSize: 30, letterSpacing: 3 }}>
        {name.toUpperCase()}
      </div>
      <div style={{ marginTop: 18, fontFamily: body, fontWeight: 700, fontSize: 44, lineHeight: 1.22, color: color.text,
                    textShadow: "0 4px 18px rgba(0,0,0,0.7)" }}>
        {cap.text}
      </div>
    </div>
  );
};

/** One vertical frame of the show: the studio camera on top, the big-screen graphic below. */
const VerticalShow: React.FC<{ episode: Episode }> = ({ episode }) => {
  const camera = useCamera(episode, true);
  const studioScale = W / WORLD.w;
  const tvScale = W / layout.contentW;
  return (
    <Voice audioFile={episode.audioFile} mouths={episode.mouths ?? {}} captions={episode.captions}>
      <div style={{ position: "absolute", left: 0, top: 150, width: W, height: WORLD.h * studioScale, overflow: "hidden" }}>
        <div style={{ position: "absolute", left: 0, top: 0, width: WORLD.w, height: WORLD.h, transformOrigin: "0 0",
                      transform: `scale(${studioScale})` }}>
          <div style={{ position: "absolute", inset: 0, transformOrigin: "0 0", transform: camera.transform }}>
            <NewsroomSet episode={episode} tv={<TvContent episode={episode} />} />
          </div>
        </div>
      </div>
      <div style={{ position: "absolute", left: 0, top: 790, width: W, height: layout.contentH * tvScale, overflow: "hidden",
                    background: color.bg0 }}>
        <div style={{ position: "absolute", left: 0, top: 0, width: layout.contentW, height: layout.contentH,
                      transformOrigin: "0 0", transform: `scale(${tvScale})` }}>
          <TvContent episode={episode} />
        </div>
      </div>
      <BigCaption episode={episode} />
    </Voice>
  );
};

/** YouTube Short: the cold open plus the top story, re-framed for 1080x1920. */
export const ShortVideo: React.FC<Episode> = (episode) => {
  const clips = episode.short?.clips ?? [];
  let at = 0;
  return (
    <AbsoluteFill style={{ background: `linear-gradient(180deg, ${color.bg1}, ${color.bg0})` }}>
      {clips.map((clip, i) => {
        const len = clip.endFrame - clip.startFrame;
        const from = at;
        at += len;
        return (
          <Sequence key={i} from={from} durationInFrames={len}>
            <Sequence from={-clip.startFrame}>
              <VerticalShow episode={episode} />
            </Sequence>
          </Sequence>
        );
      })}
      <div style={{ position: "absolute", top: 40, left: 0, right: 0, display: "flex", justifyContent: "center" }}>
        <Logo name={episode.showName} size={44} />
      </div>
      <div style={{ position: "absolute", bottom: 46, left: 0, right: 0, textAlign: "center", fontFamily: body,
                    fontSize: 34, fontWeight: 700, color: color.gold, letterSpacing: 2 }}>
        FULL EPISODE ON THE CHANNEL
      </div>
    </AbsoluteFill>
  );
};
