import React, { createContext, useContext } from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { layout } from "../theme";

const SceneDuration = createContext(1);

export const SceneDurationProvider = SceneDuration.Provider;

export const useSceneDuration = () => useContext(SceneDuration);

export const SceneFrame: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const frame = useCurrentFrame();
  const durationInFrames = useSceneDuration();
  const enter = interpolate(frame, [0, 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 10, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  return (
    <div
      style={{
        position: "absolute", left: 0, top: 0, width: layout.contentW,
        height: layout.contentH, opacity: Math.min(enter, exit),
        transform: `translateY(${(1 - enter) * 30}px) scale(${0.98 + 0.02 * enter})`,
      }}
    >
      {children}
    </div>
  );
};

export const reveal = (frame: number, at: number, len = 14) =>
  interpolate(frame, [at, at + len], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
