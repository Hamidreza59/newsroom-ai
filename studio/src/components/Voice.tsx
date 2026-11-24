import React, { createContext, useContext } from "react";
import { Html5Audio, staticFile, useCurrentFrame } from "remotion";
import type { Caption } from "../types";

type VoiceState = { a: number; b: number; speaker: "a" | "b" | null };

const VoiceContext = createContext<VoiceState>({ a: 0, b: 0, speaker: null });

export const useVoice = () => useContext(VoiceContext);

const synthetic = (frame: number) =>
  0.25 + 0.55 * Math.abs(Math.sin(frame * 0.75) * Math.cos(frame * 0.31));

/** Plays the narration and exposes each anchor's mouth openness (precomputed per frame). */
export const Voice: React.FC<{
  audioFile: string | null;
  mouths: Record<string, number[]>;
  captions: Caption[];
  children: React.ReactNode;
}> = ({ audioFile, mouths, captions, children }) => {
  const frame = useCurrentFrame();
  const active = captions.find((c) => frame >= c.startFrame && frame < c.endFrame);
  const recent = [...captions].reverse().find((c) => frame >= c.startFrame);
  const level = (id: "a" | "b") =>
    mouths[id]?.length ? (mouths[id][frame] ?? 0) : active?.speaker === id ? synthetic(frame) : 0;
  const state: VoiceState = { a: level("a"), b: level("b"), speaker: (active ?? recent)?.speaker ?? null };
  return (
    <VoiceContext.Provider value={state}>
      {audioFile && <Html5Audio src={staticFile(audioFile)} />}
      {children}
    </VoiceContext.Provider>
  );
};
