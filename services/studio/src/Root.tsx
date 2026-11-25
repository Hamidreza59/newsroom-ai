import React from "react";
import { Composition, type CalculateMetadataFunction } from "remotion";
import { DailyShow } from "./DailyShow";
import sample from "./sample-episode.json";
import { ShortVideo } from "./ShortVideo";
import { Thumbnail } from "./Thumbnail";
import type { Episode } from "./types";

const sampleEpisode = sample as Episode;

const showMetadata: CalculateMetadataFunction<Episode> = ({ props }) => ({
  durationInFrames: props.durationInFrames,
  fps: props.fps,
  width: props.width,
  height: props.height,
});

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="DailyShow"
      component={DailyShow}
      durationInFrames={sampleEpisode.durationInFrames}
      fps={sampleEpisode.fps}
      width={1920}
      height={1080}
      defaultProps={sampleEpisode}
      calculateMetadata={showMetadata}
    />
    <Composition
      id="Short"
      component={ShortVideo}
      durationInFrames={sampleEpisode.short?.durationInFrames ?? 1}
      fps={sampleEpisode.fps}
      width={1080}
      height={1920}
      defaultProps={sampleEpisode}
      calculateMetadata={({ props }) => ({ durationInFrames: Math.max(1, props.short?.durationInFrames ?? 1) })}
    />
    <Composition
      id="Thumbnail"
      component={Thumbnail}
      durationInFrames={1}
      fps={30}
      width={1280}
      height={720}
      defaultProps={sampleEpisode}
    />
  </>
);
