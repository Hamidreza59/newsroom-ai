import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Logo, Panel, Pill } from "../components/Chrome";
import { body, categoryColor, color, display } from "../theme";
import type { Episode, Scene } from "../types";
import { reveal, SceneFrame, useSceneDuration } from "./SceneFrame";

/** Cold open: the top story slammed on screen in the first seconds. */
export const ColdOpenScene: React.FC<{ scene: Scene; episode: Episode }> = ({ scene, episode }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const tone = categoryColor(scene.category);
  const slam = spring({ frame: frame - 3, fps, config: { damping: 10, stiffness: 180 } });
  const flash = interpolate(frame, [0, 4, 12], [1, 0.6, 0], { extrapolateRight: "clamp" });
  const blink = Math.floor(frame / 8) % 2 === 0;
  const biggest = [...episode.market.gainers, ...episode.market.losers]
    .sort((a, b) => Math.abs(b.changePct) - Math.abs(a.changePct))[0];
  return (
    <SceneFrame>
      <div style={{ position: "absolute", inset: 0, borderRadius: 28, overflow: "hidden",
                    background: `radial-gradient(900px 600px at 50% 40%, ${tone}33, ${color.bg0} 70%)` }}>
        <div style={{ position: "absolute", inset: 0, background: "#FFFFFF", opacity: flash }} />
        <div style={{ position: "absolute", top: 70, left: 0, right: 0, display: "flex", justifyContent: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 16, padding: "12px 30px", borderRadius: 999,
                        background: "#E5303F", color: "#fff", fontFamily: body, fontWeight: 800, fontSize: 30,
                        letterSpacing: 6 }}>
            <div style={{ width: 16, height: 16, borderRadius: 8, background: "#fff", opacity: blink ? 1 : 0.3 }} />
            TOP STORY
          </div>
        </div>
        <div style={{ position: "absolute", top: 190, left: 80, right: 80, textAlign: "center", fontFamily: display,
                      fontWeight: 700, fontSize: 92, lineHeight: 1.05, color: color.text,
                      transform: `scale(${1.4 - 0.4 * slam})`, opacity: slam,
                      textShadow: `0 0 40px ${tone}88` }}>
          {scene.headline}
        </div>
        {biggest && (
          <div style={{ position: "absolute", bottom: 90, left: 0, right: 0, textAlign: "center", fontFamily: body,
                        fontSize: 40, fontWeight: 700, color: biggest.changePct >= 0 ? color.up : color.down,
                        opacity: reveal(frame, 40) }}>
            {biggest.name} {biggest.changePct >= 0 ? "▲" : "▼"} {Math.abs(biggest.changePct).toFixed(1)}%
          </div>
        )}
        <div style={{ position: "absolute", bottom: 26, right: 34, opacity: 0.8 }}>
          <Logo name={episode.showName} size={24} />
        </div>
      </div>
    </SceneFrame>
  );
};

const StepIcon: React.FC<{ n: number; tone: string; on: number }> = ({ n, tone, on }) => (
  <div style={{ width: 70, height: 70, borderRadius: 20, background: `${tone}22`, border: `3px solid ${tone}`,
                display: "flex", alignItems: "center", justifyContent: "center", fontFamily: display,
                fontWeight: 700, fontSize: 36, color: tone, transform: `scale(${0.6 + 0.4 * on})`, flexShrink: 0 }}>
    {n}
  </div>
);

/** "AI in 30 seconds": a concept title with three numbered steps revealed as the anchors explain. */
export const ExplainerScene: React.FC<{ scene: Scene }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const duration = useSceneDuration();
  const tone = color.ai;
  const pop = spring({ frame: frame - 4, fps, config: { damping: 14 } });
  return (
    <SceneFrame>
      <Panel style={{ position: "absolute", inset: 0, padding: "48px 60px", boxSizing: "border-box", overflow: "hidden" }}>
        <svg width="420" height="420" viewBox="0 0 100 100" style={{ position: "absolute", right: -40, top: -30, opacity: 0.12 }}>
          {[[20, 30], [20, 70], [50, 20], [50, 50], [50, 80], [80, 40], [80, 65]].map(([x, y], i) => (
            <circle key={i} cx={x} cy={y} r={4 + Math.sin(frame / 10 + i) * 0.8} fill={tone} />
          ))}
          {[[20, 30, 50, 20], [20, 30, 50, 50], [20, 70, 50, 50], [20, 70, 50, 80], [50, 20, 80, 40],
            [50, 50, 80, 40], [50, 50, 80, 65], [50, 80, 80, 65]].map(([a, b, c, d], i) => (
            <line key={i} x1={a} y1={b} x2={c} y2={d} stroke={tone} strokeWidth="1" />
          ))}
        </svg>
        <Pill text="AI in 30 seconds" fg={tone} />
        <div style={{ marginTop: 28, fontFamily: display, fontSize: 74, fontWeight: 700, color: color.text,
                      lineHeight: 1.05, opacity: pop, transform: `translateY(${(1 - pop) * 24}px)` }}>
          {scene.headline}
        </div>
        <div style={{ marginTop: 40, display: "flex", flexDirection: "column", gap: 26 }}>
          {scene.bullets.map((step, i) => {
            const t = reveal(frame, Math.round(duration * (0.2 + i * 0.22)));
            return (
              <div key={i} style={{ display: "flex", alignItems: "center", gap: 26, opacity: t,
                                    transform: `translateX(${(1 - t) * 40}px)` }}>
                <StepIcon n={i + 1} tone={tone} on={t} />
                <div style={{ fontFamily: body, fontSize: 36, color: color.text, fontWeight: 500, lineHeight: 1.25 }}>
                  {step}
                </div>
              </div>
            );
          })}
        </div>
      </Panel>
    </SceneFrame>
  );
};

/** Daily quiz: yesterday's answer first (if any), then today's question with A/B/C options. */
export const QuizScene: React.FC<{ scene: Scene }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const duration = useSceneDuration();
  const tone = color.gold;
  const revealEnd = scene.reveal ? Math.round(duration * 0.38) : 0;
  const showReveal = scene.reveal && frame < revealEnd;
  const q = frame - revealEnd;
  return (
    <SceneFrame>
      <Panel style={{ position: "absolute", inset: 0, padding: "48px 60px", boxSizing: "border-box", overflow: "hidden" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 18 }}>
          <Pill text="Quiz time" fg={tone} />
          <div style={{ marginLeft: "auto", fontFamily: body, color: color.muted, fontSize: 24, fontWeight: 600,
                        letterSpacing: 2 }}>
            ANSWER ON TOMORROW'S SHOW
          </div>
        </div>
        {showReveal ? (
          <div style={{ marginTop: 70, textAlign: "center", opacity: reveal(frame, 4) }}>
            <div style={{ fontFamily: body, fontSize: 34, color: color.muted, fontWeight: 600 }}>Last show's answer</div>
            <div style={{ marginTop: 30, display: "inline-block", padding: "26px 56px", borderRadius: 26,
                          background: `${color.up}22`, border: `4px solid ${color.up}`, fontFamily: display,
                          fontSize: 80, fontWeight: 700, color: color.text,
                          transform: `scale(${spring({ frame: frame - 10, fps, config: { damping: 10 } })})` }}>
              ✓ {scene.reveal}
            </div>
          </div>
        ) : (
          <>
            <div style={{ marginTop: 34, fontFamily: display, fontSize: 60, fontWeight: 700, color: color.text,
                          lineHeight: 1.1, opacity: reveal(q, 2) }}>
              {scene.headline}
            </div>
            <div style={{ marginTop: 40, display: "flex", gap: 26 }}>
              {scene.options.map((opt, i) => {
                const s = spring({ frame: q - 14 - i * 8, fps, config: { damping: 12 } });
                return (
                  <div key={i} style={{ flex: 1, padding: "28px 26px", borderRadius: 24, background: color.panel,
                                        border: `3px solid ${tone}88`, transform: `scale(${0.6 + 0.4 * s})`, opacity: s }}>
                    <div style={{ width: 64, height: 64, borderRadius: 32, background: tone, color: color.bg0,
                                  fontFamily: display, fontWeight: 700, fontSize: 36, display: "flex",
                                  alignItems: "center", justifyContent: "center" }}>
                      {"ABC"[i]}
                    </div>
                    <div style={{ marginTop: 18, fontFamily: body, fontSize: 34, fontWeight: 600, color: color.text }}>
                      {opt}
                    </div>
                  </div>
                );
              })}
            </div>
            <div style={{ position: "absolute", left: 60, right: 60, bottom: 44, textAlign: "center", fontFamily: body,
                          fontSize: 28, fontWeight: 600, color: color.muted, opacity: reveal(q, 50) }}>
              Drop your answer in the comments ↓
            </div>
          </>
        )}
      </Panel>
    </SceneFrame>
  );
};
