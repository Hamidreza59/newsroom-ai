import React, { useMemo } from "react";
import { Easing, interpolate, useCurrentFrame } from "remotion";
import { body, color, layout } from "../theme";
import type { Episode } from "../types";
import { Logo } from "./Chrome";
import { Presenter } from "./Presenter";
import { useVoice } from "./Voice";

/* ---------- world geometry (set is drawn in a 1920x1080 world, the camera moves over it) ---------- */

export const WORLD = { w: 1920, h: 1080, floorY: 700 } as const;
export const TV = { x: 1000, y: 150, w: 760 } as const;
const TV_H = (layout.contentH * TV.w) / layout.contentW;
const DESK = { left: 80, right: 980, back: 722, front: 790, edge: 812, bottom: 1008 } as const;
const PRESENTER_SIZE = 360;
const PRESENTER_SCALE = PRESENTER_SIZE / 400;
export const SEAT = { a: 360, b: 690 } as const;
const PRESENTER_TOP = 770 - 592 * PRESENTER_SCALE;

/* ---------- camera ---------- */

export type ShotName = "wide" | "desk" | "singleA" | "singleB" | "tv" | "tvSide";
type Shot = { start: number; name: ShotName; opening?: boolean };

const SHOTS: Record<ShotName, { x: number; y: number; z: number }> = {
  wide: { x: 960, y: 540, z: 1 },
  desk: { x: 530, y: 600, z: 1.7 },
  singleA: { x: SEAT.a + 20, y: 565, z: 1.95 },
  singleB: { x: SEAT.b - 90, y: 565, z: 1.95 },
  tv: { x: TV.x + TV.w / 2, y: 400, z: 2 },
  tvSide: { x: 1060, y: 470, z: 1.25 },
};

const MIN_SHOT = 45;

export const buildShots = (episode: Episode): Shot[] => {
  const shots: Shot[] = [];
  const push = (start: number, name: ShotName, force = false, opening = false) => {
    const last = shots[shots.length - 1];
    if (last && last.name === name) return;
    if (last && !force && start - last.start < MIN_SHOT) return;
    shots.push({ start: Math.max(0, start), name, opening });
  };
  const single = (s: "a" | "b"): ShotName => (s === "a" ? "singleA" : "singleB");

  for (const scene of episode.scenes) {
    const end = scene.startFrame + scene.durationInFrames;
    const caps = episode.captions.filter((c) => c.startFrame >= scene.startFrame && c.startFrame < end);
    if (scene.type === "coldopen") {
      push(scene.startFrame, "tv", true);
      continue;
    }
    if (scene.type === "intro") {
      push(scene.startFrame, "wide", true, true);
      caps.forEach((c, i) => i > 0 && push(c.startFrame, i === caps.length - 1 ? "desk" : single(c.speaker)));
      continue;
    }
    if (scene.type === "outro") {
      push(scene.startFrame, "desk", true);
      caps.forEach((c, i) => i > 0 && i < caps.length - 1 && push(c.startFrame, single(c.speaker)));
      push(end - 80, "wide", true);
      continue;
    }
    if (scene.alertFrames > 0) push(scene.startFrame, "tv", true);
    const count = { a: 0, b: 0 };
    caps.forEach((c) => count[c.speaker]++);
    const lead = count.b > count.a ? "b" : "a";
    const cycle: ShotName[] = ["tvSide", "tv", "tv", single(lead)];
    let leadLines = 0;
    caps.forEach((c) => {
      if (c.speaker === lead) {
        push(c.startFrame, cycle[leadLines % cycle.length], leadLines === 0 && !scene.alertFrames);
        leadLines++;
      } else {
        push(c.startFrame, single(c.speaker));
      }
    });
  }
  return shots;
};

export const useCamera = (episode: Episode, anchorsOnly = false) => {
  const frame = useCurrentFrame();
  const shots = useMemo(() => {
    const all = buildShots(episode);
    return anchorsOnly
      ? all.map((s) => (s.name === "tv" || s.name === "tvSide" ? { ...s, name: "desk" as ShotName } : s))
      : all;
  }, [episode, anchorsOnly]);
  let i = 0;
  while (i + 1 < shots.length && shots[i + 1].start <= frame) i++;
  const shot = shots[i] ?? { start: 0, name: "wide" as ShotName };
  const next = shots[i + 1]?.start ?? episode.durationInFrames;
  const t = interpolate(frame, [shot.start, next], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const base = SHOTS[shot.name];
  const opening = !!shot.opening;
  const z = base.z * (opening ? interpolate(t, [0, 1], [1, 1.12], { easing: Easing.inOut(Easing.sin) }) : 1 + 0.035 * t);
  const halfW = WORLD.w / 2 / z;
  const halfH = WORLD.h / 2 / z;
  const drift = (shot.name.startsWith("single") ? 6 : 14) * (t - 0.5);
  const cx = Math.min(WORLD.w - halfW, Math.max(halfW, base.x + drift));
  const cy = Math.min(WORLD.h - halfH, Math.max(halfH, base.y));
  return {
    shot: shot.name,
    transform: `scale(${z}) translate(${WORLD.w / 2 / z - cx}px, ${WORLD.h / 2 / z - cy}px)`,
  };
};

/* ---------- set pieces ---------- */

const rand = (i: number) => {
  const x = Math.sin(i * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
};

const Skyline: React.FC = () => {
  const frame = useCurrentFrame();
  const buildings = useMemo(() => {
    const out: { x: number; w: number; h: number; seed: number }[] = [];
    let x = -20;
    let i = 0;
    while (x < WORLD.w) {
      const w = 60 + rand(i) * 110;
      out.push({ x, w, h: 140 + rand(i + 99) * 300, seed: i });
      x += w + 6;
      i++;
    }
    return out;
  }, []);
  const base = 620;
  return (
    <svg width={WORLD.w} height={WORLD.h} style={{ position: "absolute", inset: 0 }}>
      <defs>
        <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#0A1236" />
          <stop offset="0.7" stopColor="#1B2A63" />
          <stop offset="1" stopColor="#3A3A78" />
        </linearGradient>
      </defs>
      <rect x="0" y="60" width={WORLD.w} height={base - 60} fill="url(#sky)" />
      <circle cx="1560" cy="150" r="34" fill="#F6F1D5" opacity="0.8" />
      {buildings.map((b) => (
        <g key={b.seed}>
          <rect x={b.x} y={base - b.h} width={b.w} height={b.h} fill={rand(b.seed + 7) > 0.5 ? "#0E1638" : "#121C46"} />
          {Array.from({ length: Math.floor((b.h - 30) / 26) }).flatMap((_, r) =>
            Array.from({ length: Math.floor((b.w - 14) / 20) }).map((__, c) => {
              const k = b.seed * 1000 + r * 37 + c;
              const lit = rand(k) > 0.55;
              if (!lit) return null;
              const flicker = rand(k + Math.floor(frame / 90)) > 0.04 ? 1 : 0.2;
              return <rect key={`${r}-${c}`} x={b.x + 10 + c * 20} y={base - b.h + 18 + r * 26} width="9" height="12"
                           fill={rand(k + 3) > 0.8 ? "#9FD8FF" : "#FFD98A"} opacity={0.55 * flicker} />;
            }),
          )}
        </g>
      ))}
    </svg>
  );
};

const BackWall: React.FC = () => (
  <>
    <Skyline />
    <svg width={WORLD.w} height={WORLD.h} style={{ position: "absolute", inset: 0 }}>
      <defs>
        <linearGradient id="glass" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="#FFFFFF" stopOpacity="0.06" />
          <stop offset="0.5" stopColor="#FFFFFF" stopOpacity="0" />
          <stop offset="1" stopColor="#FFFFFF" stopOpacity="0.05" />
        </linearGradient>
      </defs>
      <rect x="0" y="60" width={WORLD.w} height="560" fill="url(#glass)" />
      {Array.from({ length: 9 }).map((_, i) => (
        <rect key={i} x={i * 240 - 6} y="60" width="12" height="560" fill="#070B1F" />
      ))}
      <rect x="0" y="0" width={WORLD.w} height="64" fill="#070B1F" />
      <rect x="0" y="612" width={WORLD.w} height={WORLD.floorY - 612} fill="#0B1128" />
      <rect x="0" y="612" width={WORLD.w} height="5" fill={color.ai} opacity="0.55" />
      {[200, 560, 960, 1360, 1720].map((x) => (
        <g key={x}>
          <rect x={x - 40} y="8" width="80" height="22" rx="6" fill="#1A2350" />
          <polygon points={`${x - 30},30 ${x + 30},30 ${x + 160},${WORLD.floorY} ${x - 160},${WORLD.floorY}`}
                   fill="#FFFFFF" opacity="0.025" />
        </g>
      ))}
    </svg>
  </>
);

const MonitorWall: React.FC = () => {
  const frame = useCurrentFrame();
  const tones = [color.ai, color.gold, color.up, color.tech, color.down, color.ai];
  return (
    <div style={{ position: "absolute", left: 96, top: 86, display: "grid", gridTemplateColumns: "repeat(3, 150px)", gap: 12 }}>
      {tones.map((tone, i) => (
        <div key={i} style={{ height: 86, borderRadius: 6, border: "3px solid #1C2552", overflow: "hidden",
                              background: `linear-gradient(135deg, #0A1030, ${tone}40)` }}>
          <svg width="150" height="86">
            <polyline fill="none" stroke={tone} strokeWidth="3" opacity="0.8"
                      points={Array.from({ length: 12 }, (_, k) =>
                        `${k * 14},${50 + 22 * Math.sin(k * 0.9 + i * 2 + frame / 40) * rand(i + k)}`).join(" ")} />
            <rect x="8" y="8" width={40 + 30 * rand(i)} height="8" rx="4" fill="#FFFFFF" opacity="0.35" />
          </svg>
        </div>
      ))}
    </div>
  );
};

const Floor: React.FC = () => (
  <svg width={WORLD.w} height={WORLD.h} style={{ position: "absolute", inset: 0 }}>
    <defs>
      <linearGradient id="floor" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stopColor="#141C42" />
        <stop offset="1" stopColor="#05081A" />
      </linearGradient>
    </defs>
    <rect x="0" y={WORLD.floorY} width={WORLD.w} height={WORLD.h - WORLD.floorY} fill="url(#floor)" />
    {Array.from({ length: 17 }).map((_, i) => {
      const x = -400 + i * 170;
      return <line key={i} x1={960 + (x - 960) * 0.35} y1={WORLD.floorY} x2={x} y2={WORLD.h} stroke="#FFFFFF" strokeOpacity="0.04" strokeWidth="2" />;
    })}
    <ellipse cx="530" cy="1012" rx="500" ry="34" fill="#000" opacity="0.5" />
    <ellipse cx={TV.x + TV.w / 2} cy="940" rx="170" ry="20" fill="#000" opacity="0.5" />
  </svg>
);

export const BigTV: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const scale = TV.w / layout.contentW;
  const cx = TV.x + TV.w / 2;
  return (
    <>
      <svg width={WORLD.w} height={WORLD.h} style={{ position: "absolute", inset: 0 }}>
        <rect x={cx - 14} y={TV.y + TV_H + 10} width="28" height={930 - TV.y - TV_H} fill="#2A3366" />
        <rect x={cx - 6} y={TV.y + TV_H + 10} width="6" height={930 - TV.y - TV_H} fill="#FFFFFF" opacity="0.12" />
        <ellipse cx={cx} cy="932" rx="140" ry="16" fill="#2A3366" />
        <ellipse cx={cx} cy="928" rx="140" ry="12" fill="#39448A" />
      </svg>
      <div style={{ position: "absolute", left: TV.x - 16, top: TV.y - 16, width: TV.w + 32, height: TV_H + 32,
                    borderRadius: 18, background: "#0B0F22", border: "3px solid #2A3366",
                    boxShadow: `0 0 80px ${color.ai}33, 0 30px 60px rgba(0,0,0,0.6)` }}>
        <div style={{ position: "absolute", left: 16, top: 16, width: TV.w, height: TV_H, overflow: "hidden",
                      borderRadius: 6, background: color.bg0 }}>
          <div style={{ position: "absolute", inset: 0,
                        background: `radial-gradient(800px 500px at 30% 20%, ${color.bg2}, ${color.bg0})` }} />
          <div style={{ position: "absolute", left: 0, top: 0, width: layout.contentW, height: layout.contentH,
                        transform: `scale(${scale})`, transformOrigin: "0 0" }}>
            {children}
          </div>
          <div style={{ position: "absolute", inset: 0, pointerEvents: "none",
                        background: "linear-gradient(120deg, rgba(255,255,255,0.07), transparent 35%)" }} />
        </div>
      </div>
    </>
  );
};

const Spotlights: React.FC = () => {
  const { speaker } = useVoice();
  return (
    <>
      {(["a", "b"] as const).map((id) => (
        <div key={id} style={{
          position: "absolute", left: SEAT[id] - 260, top: 360, width: 520, height: 520,
          background: `radial-gradient(closest-side, rgba(255,240,215,${speaker === id ? 0.16 : 0.07}), transparent 72%)`,
        }} />
      ))}
    </>
  );
};

const Presenters: React.FC<{ seed: string; part: "body" | "hands" }> = ({ seed, part }) => {
  const voice = useVoice();
  const look = (id: "a" | "b") => {
    const toward = id === "a" ? 1 : -1;
    if (voice.speaker && voice.speaker !== id) return toward * 0.9;
    return toward * 0.3;
  };
  return (
    <>
      {(["a", "b"] as const).map((id) => (
        <div key={id} style={{ position: "absolute", left: SEAT[id] - PRESENTER_SIZE / 2, top: PRESENTER_TOP }}>
          <Presenter id={id} mouth={voice[id]} look={look(id)} speaking={voice.speaker === id}
                     size={PRESENTER_SIZE} seed={seed} part={part} delivery={voice.delivery[id]} />
        </div>
      ))}
    </>
  );
};

const deskTopPath = () => {
  const { left, right, back, front } = DESK;
  const mid = (left + right) / 2;
  const inset = 46;
  return `M${left + inset} ${back} Q${mid} ${back - 14} ${right - inset} ${back} L${right} ${front}
          Q${mid} ${front + 18} ${left} ${front} Z`;
};

const DeskTop: React.FC = () => {
  const { left, right, back } = DESK;
  const mid = (left + right) / 2;
  return (
    <svg width={WORLD.w} height={WORLD.h} style={{ position: "absolute", inset: 0 }}>
      <defs>
        <linearGradient id="slabTop" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#2C3670" />
          <stop offset="1" stopColor="#47549A" />
        </linearGradient>
        <linearGradient id="slabSheen" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0" stopColor="#FFFFFF" stopOpacity="0" />
          <stop offset="0.45" stopColor="#FFFFFF" stopOpacity="0.55" />
          <stop offset="0.6" stopColor="#FFFFFF" stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={deskTopPath()} fill="url(#slabTop)" />
      <path d={deskTopPath()} fill="url(#slabSheen)" opacity="0.35" />
      <path d={`M${left + 46} ${back} Q${mid} ${back - 14} ${right - 46} ${back}`} stroke="#5B68B0" strokeWidth="2" fill="none" />
    </svg>
  );
};

const DeskProps: React.FC = () => {
  const { back } = DESK;
  return (
    <svg width={WORLD.w} height={WORLD.h} style={{ position: "absolute", inset: 0 }}>
      <g transform={`translate(${SEAT.a + 150} ${back + 22}) rotate(-5)`}>
        <rect width="70" height="44" rx="2" fill="#FFFFFF" />
        <rect x="6" y="4" width="70" height="44" rx="2" fill="#F1F3FA" transform="rotate(6)" />
        {[10, 18, 26, 34].map((y) => <rect key={y} x="10" y={y} width="44" height="3" fill="#C4CADB" />)}
      </g>
      <g transform={`translate(${SEAT.b + 128} ${back - 6})`}>
        <ellipse cx="17" cy="44" rx="20" ry="5" fill="#000" opacity="0.2" />
        <rect width="34" height="42" rx="6" fill="#F4F6FF" />
        <path d="M34 10 q15 0 15 12 q0 12 -15 12" stroke="#F4F6FF" strokeWidth="5" fill="none" />
        <rect x="6" y="14" width="22" height="9" rx="3" fill={color.gold} />
      </g>
    </svg>
  );
};

const DeskFront: React.FC<{ showName: string }> = ({ showName }) => {
  const { left, right, front, edge, bottom } = DESK;
  const mid = (left + right) / 2;
  return (
    <>
      <svg width={WORLD.w} height={WORLD.h} style={{ position: "absolute", inset: 0 }}>
        <defs>
          <linearGradient id="slabEdge" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#FFFFFF" />
            <stop offset="1" stopColor="#B4BCD6" />
          </linearGradient>
          <linearGradient id="panel" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#0B1233" />
            <stop offset="1" stopColor="#1A2560" />
          </linearGradient>
          <linearGradient id="pedestal" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0" stopColor="#25336F" />
            <stop offset="1" stopColor="#1A2558" />
          </linearGradient>
          <linearGradient id="reflect" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#1A2560" stopOpacity="0.55" />
            <stop offset="1" stopColor="#1A2560" stopOpacity="0" />
          </linearGradient>
          <radialGradient id="logoGlow" cx="0.5" cy="0.5" r="0.5">
            <stop offset="0" stopColor={color.ai} stopOpacity="0.35" />
            <stop offset="1" stopColor={color.ai} stopOpacity="0" />
          </radialGradient>
        </defs>
        <path d={`M${left + 40} ${bottom} Q${mid} ${bottom + 26} ${right - 40} ${bottom} L${right - 70} ${WORLD.h}
                 L${left + 70} ${WORLD.h} Z`} fill="url(#reflect)" />
        <path d={`M${left + 44} ${edge} Q${mid} ${edge + 20} ${right - 44} ${edge} L${right - 50} ${bottom}
                 Q${mid} ${bottom + 22} ${left + 50} ${bottom} Z`} fill="url(#panel)" />
        <path d={`M${left + 60} ${bottom - 22} Q${mid} ${bottom - 2} ${right - 60} ${bottom - 22}`} stroke={color.ai}
              strokeWidth="5" fill="none" opacity="0.85" />
        <path d={`M${left + 60} ${bottom - 22} Q${mid} ${bottom - 2} ${right - 60} ${bottom - 22}`} stroke={color.ai}
              strokeWidth="18" fill="none" opacity="0.15" />
        {[left + 210, right - 210].map((x) => (
          <line key={x} x1={x} y1={edge + 16} x2={x} y2={bottom - 30} stroke="#FFFFFF" strokeOpacity="0.07" strokeWidth="3" />
        ))}
        <ellipse cx={mid} cy={(edge + bottom) / 2 + 4} rx="230" ry="80" fill="url(#logoGlow)" />
        <rect x={mid - 190} y={edge + 50} width="380" height="92" rx="16" fill="#060A1E" stroke={color.ai}
              strokeOpacity="0.5" strokeWidth="2" />
        <path d={`M${left} ${front} L${left + 44} ${edge} L${left + 50} ${bottom} L${left + 6} ${bottom - 8} Z`}
              fill="url(#pedestal)" />
        <path d={`M${right} ${front} L${right - 44} ${edge} L${right - 50} ${bottom} L${right - 6} ${bottom - 8} Z`}
              fill="url(#pedestal)" />
        <path d={`M${left} ${front} Q${mid} ${front + 18} ${right} ${front} L${right - 6} ${edge + 2}
                 Q${mid} ${edge + 22} ${left + 6} ${edge + 2} Z`} fill="url(#slabEdge)" />
        <path d={`M${left} ${front} Q${mid} ${front + 18} ${right} ${front}`} stroke="#FFFFFF" strokeWidth="2" fill="none" />
        <path d={`M${left + 6} ${edge + 2} Q${mid} ${edge + 22} ${right - 6} ${edge + 2}`} stroke={color.gold}
              strokeWidth="3" fill="none" opacity="0.9" />
      </svg>
      <div style={{ position: "absolute", left: mid - 190, top: DESK.edge + 50, width: 380, height: 92,
                    display: "flex", alignItems: "center", justifyContent: "center" }}>
        <Logo name={showName} size={32} />
      </div>
    </>
  );
};

export const NewsroomSet: React.FC<{ episode: Episode; tv: React.ReactNode }> = ({ episode, tv }) => (
  <div style={{ position: "absolute", left: 0, top: 0, width: WORLD.w, height: WORLD.h, fontFamily: body }}>
    <BackWall />
    <MonitorWall />
    <Floor />
    <BigTV>{tv}</BigTV>
    <Spotlights />
    <Presenters seed={episode.date} part="body" />
    <DeskTop />
    <DeskProps />
    <Presenters seed={episode.date} part="hands" />
    <DeskFront showName={episode.showName} />
  </div>
);

