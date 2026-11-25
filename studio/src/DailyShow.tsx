import React from "react";
import { AbsoluteFill, interpolate, Sequence, useCurrentFrame } from "remotion";
import { AlertCard } from "./components/AlertCard";
import { Header } from "./components/Chrome";
import { LowerThird } from "./components/LowerThird";
import { NewsroomSet, useCamera, WORLD } from "./components/Newsroom";
import { Ticker } from "./components/Ticker";
import { Voice } from "./components/Voice";
import { IntroScene } from "./scenes/IntroScene";
import { MarketScene } from "./scenes/MarketScene";
import { NewsScene } from "./scenes/NewsScene";
import { OutroScene } from "./scenes/OutroScene";
import { SceneDurationProvider } from "./scenes/SceneFrame";
import { ColdOpenScene, ExplainerScene, QuizScene } from "./scenes/SegmentScenes";
import { color } from "./theme";
import type { Episode, Scene } from "./types";

const LABELS: Record<string, string> = {
  coldopen: "TOP STORY", intro: "TODAY", market: "MARKETS", explainer: "AI IN 30 SECONDS",
  quiz: "DAILY QUIZ", outro: "THAT'S A WRAP",
};

export const sceneLabel = (s: Scene | undefined) =>
  !s ? "" : s.type === "news" ? `STORY ${s.index}/${s.total}` : LABELS[s.type] ?? "";

const SceneView: React.FC<{ episode: Episode; scene: Scene }> = ({ episode, scene }) => {
  switch (scene.type) {
    case "coldopen":
      return <ColdOpenScene scene={scene} episode={episode} />;
    case "explainer":
      return <ExplainerScene scene={scene} />;
    case "quiz":
      return <QuizScene scene={scene} />;
    case "intro":
      return <IntroScene episode={episode} />;
    case "market":
      return <MarketScene episode={episode} scene={scene} />;
    case "news":
      return <NewsScene scene={scene} />;
    case "outro":
      return <OutroScene episode={episode} />;
  }
};

export const TvContent: React.FC<{ episode: Episode }> = ({ episode }) => (
  <>
    {episode.scenes.map((scene, i) => (
      <Sequence key={i} from={scene.startFrame} durationInFrames={scene.durationInFrames} layout="none">
        <Sequence from={scene.alertFrames ?? 0} layout="none">
          <SceneDurationProvider value={scene.durationInFrames - (scene.alertFrames ?? 0)}>
            <SceneView episode={episode} scene={scene} />
          </SceneDurationProvider>
        </Sequence>
        {scene.alertFrames > 0 && <AlertCard scene={scene} />}
      </Sequence>
    ))}
  </>
);

export const DailyShow: React.FC<Episode> = (episode) => {
  const frame = useCurrentFrame();
  const current = [...episode.scenes].reverse().find((s) => frame >= s.startFrame);
  const camera = useCamera(episode);
  const fadeIn = interpolate(frame, [0, 12], [1, 0], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ background: color.bg0, overflow: "hidden" }}>
      <Voice audioFile={episode.audioFile} mouths={episode.mouths ?? {}} captions={episode.captions}>
        <div style={{ position: "absolute", left: 0, top: 0, width: WORLD.w, height: WORLD.h,
                      transformOrigin: "0 0", transform: camera.transform }}>
          <NewsroomSet episode={episode} tv={<TvContent episode={episode} />} />
        </div>
        <LowerThird captions={episode.captions} anchors={episode.anchors} />
      </Voice>
      <div style={{ opacity: camera.shot === "tv" ? 0 : 1 }}>
        <Header showName={episode.showName} date={episode.date} label={sceneLabel(current)} />
      </div>
      <Ticker quotes={episode.ticker} asOf={episode.market.asOf} sample={episode.market.sampleData} />
      <AbsoluteFill style={{ background: "#000", opacity: fadeIn }} />
    </AbsoluteFill>
  );
};
