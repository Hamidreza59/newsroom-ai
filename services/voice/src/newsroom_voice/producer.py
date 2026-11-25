from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np
import soundfile as sf
from newsroom_core.config import DISCLAIMER, Settings
from newsroom_core.models import (
    Anchor,
    Caption,
    Episode,
    EpMarket,
    EpQuote,
    Line,
    MarketSnapshot,
    Quote,
    Scene,
    ShortClip,
    ShortSpec,
    ShowScript,
    YouTubeMeta,
)

from newsroom_voice.sfx import ALERT_SECONDS, news_alert
from newsroom_voice.speech import split_sentences
from newsroom_voice.tts import TtsEngine

log = logging.getLogger("newsroom_voice.producer")

LEAD_IN_S = 1.2
SENTENCE_GAP_S = 0.2
TURN_GAP_S = 0.35
SCENE_GAP_S = 0.55
OUTRO_TAIL_S = 2.5
MARKET_MIN_S = 12.0
SHORT_MAX_S = 58


class TooLong(Exception):
    def __init__(self, seconds: float):
        super().__init__(f"episode would run {seconds:.1f}s")
        self.seconds = seconds


@dataclass
class _SceneSpec:
    scene: Scene
    lines: list[Line]


def _ep_quote(q: Quote, with_series: bool = False) -> EpQuote:
    return EpQuote(symbol=q.symbol, name=q.name, price=q.price, change=q.change,
                   change_pct=q.change_pct, series=q.series if with_series else [])


def mouth_envelope(audio: np.ndarray, rate: int, fps: int, frames: int) -> list[float]:
    """Per-frame mouth openness (0..1) from narration loudness, with attack/release smoothing."""
    hop = rate / fps
    rms = np.zeros(frames, dtype=np.float32)
    for f in range(frames):
        chunk = audio[int(f * hop): int((f + 1) * hop)]
        if len(chunk):
            rms[f] = float(np.sqrt(np.mean(chunk.astype(np.float64) ** 2)))
    voiced = rms[rms > 1e-4]
    ref = float(np.percentile(voiced, 90)) if len(voiced) else 1.0
    level = np.clip(rms / max(ref, 1e-6), 0, 1)
    out, prev = [], 0.0
    for v in level:
        v = 0.0 if v < 0.12 else float(v)
        prev = prev + (v - prev) * (0.75 if v > prev else 0.35)
        out.append(round(prev, 2))
    return out


def speaker_mouths(envelope: list[float], captions: list[Caption]) -> dict[str, list[float]]:
    """Split one loudness envelope into per-anchor tracks using who speaks each caption."""
    tracks = {"a": [0.0] * len(envelope), "b": [0.0] * len(envelope)}
    for c in captions:
        for f in range(c.start_frame, min(c.end_frame, len(envelope))):
            tracks[c.speaker][f] = envelope[f]
    return tracks


def _timestamp(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"


def _srt_time(frame: int, fps: int) -> str:
    ms = int(frame / fps * 1000)
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


class Producer:
    role = "producer"

    def __init__(self, settings: Settings, tts: TtsEngine):
        self.settings = settings
        self.tts = tts
        self.names = settings.anchor_names
        self._cache: dict[tuple[str, str], np.ndarray] = {}

    def _speak(self, sentence: str, speaker: str) -> np.ndarray:
        key = (speaker, sentence)
        if key not in self._cache:
            self._cache[key] = self.tts.synth(sentence, speaker)
        return self._cache[key]

    def _transcript(self, lines: list[Line]) -> str:
        return " ".join(f"{self.names[ln.speaker]}: {ln.text}" for ln in lines)

    def _scene_specs(self, script: ShowScript) -> list[_SceneSpec]:
        def scene(type_: str, lines: list[Line], **kw) -> _SceneSpec:
            return _SceneSpec(Scene(type=type_, start_frame=0, duration_in_frames=0,
                                    narration=self._transcript(lines), **kw), lines)

        n = len(script.stories)
        specs = []
        if script.cold_open:
            top = script.stories[0] if script.stories else None
            specs.append(scene("coldopen", script.cold_open,
                               headline=top.headline if top else self.settings.show_name,
                               category=top.category if top else None))
        specs += [
            scene("intro", script.intro, headline=self.settings.show_name),
            scene("market", script.market.lines, headline=script.market.headline,
                  bullets=script.market.bullets),
        ]
        for i, s in enumerate(script.stories, 1):
            specs.append(scene("news", s.lines, headline=s.headline, bullets=s.points,
                               source=s.source, category=s.category, follow_up=s.follow_up,
                               index=i, total=n))
            if script.explainer and i == min(2, n):
                ex = script.explainer
                specs.append(scene("explainer", ex.lines, headline=ex.title, bullets=ex.steps))
        if script.quiz:
            q = script.quiz
            specs.append(scene("quiz", q.reveal_lines + q.lines, headline=q.question,
                               options=q.options, reveal=q.reveal))
        outro = list(script.outro)
        closer = outro[-1].speaker if outro else "a"
        outro.append(Line(speaker=closer, text=DISCLAIMER))
        specs.append(scene("outro", outro))
        return specs

    @staticmethod
    def _alert_label(scene: Scene) -> str:
        if scene.type == "market":
            return "Market watch"
        if scene.type == "explainer":
            return "AI in 30 seconds"
        if scene.type == "quiz":
            return "Quiz time"
        if scene.type != "news":
            return ""
        if scene.follow_up:
            return "Follow-up"
        return {"AI": "AI alert", "Biotech": "Biotech alert"}.get(scene.category or "", "Tech alert")

    def build(self, script: ShowScript, snap: MarketSnapshot, show_date: date) -> Episode:
        fps, rate = self.settings.fps, self.tts.sample_rate
        audio: list[np.ndarray] = []
        cursor = 0.0
        captions: list[Caption] = []
        scenes: list[Scene] = []

        def silence(seconds: float) -> None:
            nonlocal cursor
            audio.append(np.zeros(int(seconds * rate), dtype=np.float32))
            cursor += seconds

        alert_clip = news_alert(rate)
        silence(LEAD_IN_S)
        for idx, spec in enumerate(self._scene_specs(script)):
            scene_start = 0.0 if idx == 0 else cursor
            alert = self._alert_label(spec.scene)
            if alert:
                audio.append(alert_clip)
                cursor += len(alert_clip) / rate
                silence(0.15)
            previous = None
            for line in spec.lines:
                if previous is not None and previous != line.speaker:
                    silence(TURN_GAP_S - SENTENCE_GAP_S)
                previous = line.speaker
                for sentence in split_sentences(line.text):
                    clip = self._speak(sentence, line.speaker)
                    start = cursor
                    audio.append(clip)
                    cursor += len(clip) / rate
                    captions.append(Caption(text=sentence, speaker=line.speaker,
                                            start_frame=round(start * fps),
                                            end_frame=round(cursor * fps)))
                    silence(SENTENCE_GAP_S)
            if spec.scene.type == "market" and cursor - scene_start < MARKET_MIN_S:
                silence(MARKET_MIN_S - (cursor - scene_start))
            silence(OUTRO_TAIL_S if spec.scene.type == "outro" else SCENE_GAP_S)
            start_f = round(scene_start * fps)
            scenes.append(spec.scene.model_copy(update={
                "start_frame": start_f, "duration_in_frames": round(cursor * fps) - start_f,
                "alert": alert, "alert_frames": round((ALERT_SECONDS + 0.15) * fps) if alert else 0,
            }))

        if cursor > self.settings.max_seconds:
            raise TooLong(cursor)
        self._audio = np.concatenate(audio)
        total_frames = scenes[-1].start_frame + scenes[-1].duration_in_frames
        silent = self.tts.name == "silent"

        return Episode(
            date=show_date.isoformat(),
            show_name=self.settings.show_name,
            fps=fps,
            duration_in_frames=total_frames,
            audio_file=None if silent else "narration.wav",
            market=EpMarket(
                as_of=snap.as_of,
                indices=[_ep_quote(q, with_series=True) for q in snap.indices],
                gainers=[_ep_quote(q) for q in snap.gainers()],
                losers=[_ep_quote(q) for q in snap.losers()],
                sample_data=snap.sample_data,
            ),
            ticker=[_ep_quote(q) for q in snap.indices + snap.watchlist],
            scenes=scenes,
            captions=captions,
            youtube=self.youtube_meta(script, snap, scenes, show_date),
            disclaimer=DISCLAIMER,
            anchors=[Anchor(id=k, name=v) for k, v in self.names.items()],
            short=self.short_spec(script, scenes, fps),
            mouths={} if silent else speaker_mouths(
                mouth_envelope(self._audio, rate, fps, total_frames), captions),
        )

    @staticmethod
    def short_spec(script: ShowScript, scenes: list[Scene], fps: int) -> ShortSpec | None:
        """A vertical Short: the cold open followed by the top story, capped at 58 seconds."""
        cold = next((s for s in scenes if s.type == "coldopen"), None)
        top = next((s for s in scenes if s.type == "news"), None)
        if not top:
            return None
        limit = SHORT_MAX_S * fps
        clips = []
        if cold:
            clips.append(ShortClip(start_frame=cold.start_frame,
                                   end_frame=cold.start_frame + cold.duration_in_frames))
        used = sum(c.end_frame - c.start_frame for c in clips)
        end = min(top.start_frame + top.duration_in_frames, top.start_frame + limit - used)
        clips.append(ShortClip(start_frame=top.start_frame, end_frame=end))
        total = sum(c.end_frame - c.start_frame for c in clips)
        title = f"{script.stories[0].headline} #Shorts"[:100]
        return ShortSpec(title=title, clips=clips, duration_in_frames=total)

    def youtube_meta(self, script: ShowScript, snap: MarketSnapshot, scenes: list[Scene],
                     show_date: date) -> YouTubeMeta:
        fps = self.settings.fps
        show = self.settings.show_name
        top = script.stories[0].headline if script.stories else "AI news"
        title = f"{script.market.headline} · {top} | {show} {show_date.strftime('%b %-d')}"
        if len(title) > 100:
            title = f"{top} | {show} {show_date.strftime('%b %-d, %Y')}"[:100]

        chapters = []
        for sc in scenes:
            if sc.type == "coldopen":
                continue
            label = {"intro": "Intro", "outro": "Wrap-up", "quiz": "Daily quiz"}.get(sc.type) or (
                f"Markets: {sc.headline}" if sc.type == "market" else
                f"AI in 30 seconds: {sc.headline}" if sc.type == "explainer" else sc.headline)
            start = 0 if not chapters else sc.start_frame / fps
            chapters.append(f"{_timestamp(start)} {label}")

        a, b = self.names["a"], self.names["b"]
        sources = "\n".join(f"• {s.headline} ({s.source}): {s.url}" for s in script.stories)
        description = (
            f"{show}: your daily three-minute briefing on the stock market and the biggest AI and "
            f"tech stories, for {show_date.strftime('%A, %B %-d, %Y')}, with {a} and {b}.\n\n"
            f"Chapters\n" + "\n".join(chapters) + "\n\n"
            f"Sources\n{sources}\n\n"
            f"Market data reflects the {snap.as_of} session close.\n"
            f"{DISCLAIMER}\n"
            f"{a} and {b} are AI-generated characters. Script, voices and animation are produced "
            "with AI tools and automated fact checks.\n\n"
            "#AI #StockMarket #TechNews"
        )
        tags = ["AI news", "stock market today", "tech news", "Nasdaq", "S&P 500",
                "artificial intelligence", "daily market update", show]
        tags += [q.name for q in snap.gainers(2) + snap.losers(1)]
        return YouTubeMeta(title=title, description=description, tags=list(dict.fromkeys(tags)))

    def write(self, episode: Episode, out_dir: Path) -> None:
        out_dir.mkdir(parents=True, exist_ok=True)
        if episode.audio_file:
            sf.write(out_dir / episode.audio_file, self._audio, self.tts.sample_rate,
                     subtype="PCM_16")
        (out_dir / "episode.json").write_text(episode.model_dump_json(by_alias=True, indent=2))
        (out_dir / "youtube.json").write_text(
            json.dumps(episode.youtube.model_dump(), indent=2, ensure_ascii=False))
        if episode.short:
            (out_dir / "short.json").write_text(json.dumps({
                "title": episode.short.title,
                "description": f"{episode.short.title}\nFull episode of {episode.show_name} on the "
                               f"channel.\n{DISCLAIMER}\n#AI #StockMarket #TechNews",
            }, indent=2, ensure_ascii=False))
        (out_dir / "captions.srt").write_text("\n".join(
            f"{i}\n{_srt_time(c.start_frame, episode.fps)} --> "
            f"{_srt_time(c.end_frame, episode.fps)}\n{self.names[c.speaker]}: {c.text}\n"
            for i, c in enumerate(episode.captions, 1)))
