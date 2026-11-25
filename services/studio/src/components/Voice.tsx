import React, { createContext, useContext } from "react";
import { Html5Audio, staticFile, useCurrentFrame } from "remotion";
import type { Caption } from "../types";

/** How an anchor is delivering the current line; drives expressions and gestures. */
export type Delivery = { emphasis: number; question: number; exclaim: number };

export const NO_DELIVERY: Delivery = { emphasis: 0, question: 0, exclaim: 0 };

type VoiceState = {
  a: number;
  b: number;
  speaker: "a" | "b" | null;
  delivery: Record<"a" | "b", Delivery>;
};

const VoiceContext = createContext<VoiceState>({
  a: 0, b: 0, speaker: null, delivery: { a: NO_DELIVERY, b: NO_DELIVERY },
});

export const useVoice = () => useContext(VoiceContext);

const EMPHASIS = /^(\d|record|biggest|first|new|major|billion|million|surge\w*|plung\w*|jump\w*|soar\w*|tumbl\w*|fell|rose|launch\w*|breakthrough|huge|massive|today|now|only|never|every|all|top|lead\w*)$/i;

const synthetic = (frame: number) =>
  0.25 + 0.55 * Math.abs(Math.sin(frame * 0.75) * Math.cos(frame * 0.31));

const bell = (distance: number, width: number) => Math.max(0, 1 - (distance / width) ** 2);

const deliveryFor = (cap: Caption | undefined, frame: number): Delivery => {
  if (!cap) return NO_DELIVERY;
  const len = Math.max(1, cap.endFrame - cap.startFrame);
  const words = cap.text.split(/\s+/);
  const total = cap.text.length || 1;
  let offset = 0;
  let emphasis = 0;
  for (const raw of words) {
    const word = raw.replace(/[^\w%.-]/g, "");
    const at = cap.startFrame + (offset / total) * len;
    if (EMPHASIS.test(word)) emphasis = Math.max(emphasis, bell(frame - at - 4, 12));
    offset += raw.length + 1;
  }
  const tail = (frame - cap.startFrame) / len;
  const ending = Math.min(1, Math.max(0, (tail - 0.35) / 0.4));
  const after = frame > cap.endFrame ? Math.max(0, 1 - (frame - cap.endFrame) / 18) : 1;
  const text = cap.text.trim();
  return {
    emphasis,
    question: text.endsWith("?") ? ending * after : 0,
    exclaim: text.endsWith("!") ? ending * after : 0,
  };
};

/** Plays the narration and exposes each anchor's mouth openness and delivery, per frame. */
export const Voice: React.FC<{
  audioFile: string | null;
  mouths: Record<string, number[]>;
  captions: Caption[];
  children: React.ReactNode;
}> = ({ audioFile, mouths, captions, children }) => {
  const frame = useCurrentFrame();
  const active = captions.find((c) => frame >= c.startFrame && frame < c.endFrame);
  const recent = [...captions].reverse().find((c) => frame >= c.startFrame);
  const lingering = recent && frame < recent.endFrame + 18 ? recent : undefined;
  const level = (id: "a" | "b") =>
    mouths[id]?.length ? (mouths[id][frame] ?? 0) : active?.speaker === id ? synthetic(frame) : 0;
  const current = active ?? lingering;
  const delivery = (id: "a" | "b") => (current?.speaker === id ? deliveryFor(current, frame) : NO_DELIVERY);
  const state: VoiceState = {
    a: level("a"),
    b: level("b"),
    speaker: (active ?? recent)?.speaker ?? null,
    delivery: { a: delivery("a"), b: delivery("b") },
  };
  return (
    <VoiceContext.Provider value={state}>
      {audioFile && <Html5Audio src={staticFile(audioFile)} />}
      {children}
    </VoiceContext.Provider>
  );
};
