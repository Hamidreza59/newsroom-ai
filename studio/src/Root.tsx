import React from "react";
import { Composition, type CalculateMetadataFunction } from "remotion";
import { DailyShow } from "./DailyShow";
import sample from "./sample-episode.json";
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
