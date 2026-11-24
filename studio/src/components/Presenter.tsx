import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { lighten, type Outfit, outfitFor } from "./wardrobe";

export type PresenterId = "a" | "b";

type Look = {
  skin: string;
  skinShade: string;
  hair: string;
  hairLight: string;
  lips: string;
  iris: string;
  faceRx: number;
  faceRy: number;
  blinkOffset: number;
};

const LOOKS: Record<PresenterId, Look> = {
  a: {
    skin: "#C98B63", skinShade: "#AE6F4C", hair: "#24150F", hairLight: "#4A2C20",
    lips: "#9C4A4A", iris: "#3B2418",
    faceRx: 78, faceRy: 95, blinkOffset: 0,
  },
  b: {
    skin: "#F0C4A1", skinShade: "#D9A27E", hair: "#5A3722", hairLight: "#7A5034",
    lips: "#B0605A", iris: "#2F4A6B",
    faceRx: 84, faceRy: 98, blinkOffset: 53,
  },
};

const blinkAmount = (frame: number, offset: number) => {
  const cycle = 120;
  const jitter = [0, 41, 17, 67, 29][Math.floor((frame + offset) / cycle) % 5];
  const t = ((frame + offset) % cycle) - jitter;
  return t >= 0 && t < 7 ? Math.sin((t / 7) * Math.PI) : 0;
};

const MayaHairBack: React.FC<{ c: Look }> = ({ c }) => (
  <path d="M104 196 Q96 86 200 78 Q304 86 296 196 L304 300 Q276 318 246 300 L238 250 L162 250 L154 300
           Q124 318 96 300 Z" fill={c.hair} />
);

const MayaHairFront: React.FC<{ c: Look }> = ({ c }) => (
  <g>
    <path d="M112 186 Q112 96 200 90 Q290 94 292 186 Q282 132 236 116 Q196 150 132 160 Q118 170 112 186 Z"
          fill={c.hair} />
    <path d="M150 112 Q190 96 236 112" stroke={c.hairLight} strokeWidth="6" fill="none" strokeLinecap="round"
          opacity="0.7" />
  </g>
);

const LeoHair: React.FC<{ c: Look }> = ({ c }) => (
  <g>
    <path d="M116 176 Q108 92 200 82 Q294 88 286 172 Q282 130 254 118 Q236 92 194 100 Q150 106 132 132
             Q120 150 116 176 Z" fill={c.hair} />
    <path d="M168 102 Q200 82 240 100" stroke={c.hairLight} strokeWidth="7" fill="none" strokeLinecap="round"
          opacity="0.8" />
    <path d="M116 176 L114 214 L124 214 L126 172 Z" fill={c.hair} />
    <path d="M284 172 L286 214 L276 214 L274 168 Z" fill={c.hair} />
  </g>
);

const sleeveColor = (id: PresenterId, o: Outfit) =>
  o.style === "turtleneck" ? (id === "b" ? o.jacket : o.top) : o.jacket;

const UPPER_ARMS = {
  l: "M136 328 Q84 330 66 392 L46 548 Q48 572 76 574 L104 570 Q100 520 102 470 L108 404 Q116 362 142 350 Z",
  r: "M264 328 Q316 330 334 392 L354 548 Q352 572 324 574 L296 570 Q300 520 298 470 L292 404 Q284 362 258 350 Z",
};
const ARM_SEAMS = "M104 570 Q100 520 102 470 L108 404 Q116 362 142 350 M296 570 Q300 520 298 470 L292 404 Q284 362 258 350";

const Torso: React.FC<{ id: PresenterId; outfit: Outfit }> = ({ id, outfit }) => {
  const { style, jacket, top, accent, pattern } = outfit;
  const sheen = lighten(jacket, 0.16);
  const body = "M102 620 L96 470 Q90 360 136 328 L200 314 L264 328 Q310 360 304 470 L298 620 Z";
  const sleeve = sleeveColor(id, outfit);
  const arms = (
    <g>
      <path d={UPPER_ARMS.l} fill={sleeve} />
      <path d={UPPER_ARMS.r} fill={sleeve} />
      <path d={ARM_SEAMS} stroke="#00000059" strokeWidth="6" fill="none" strokeLinecap="round" />
      <path d="M70 400 Q60 470 52 540 M330 400 Q340 470 348 540" stroke="#FFFFFF" strokeOpacity="0.12" strokeWidth="5" fill="none" />
    </g>
  );

  if (style === "blouse" || style === "turtleneck") {
    const fill = style === "blouse" ? jacket : top;
    return (
      <g>
        <path d={body} fill={fill} />
        <path d="M136 328 Q200 304 264 328 Q290 360 286 470 L280 620 L120 620 L114 470 Q110 360 136 328 Z"
              fill="#FFFFFF" opacity="0.07" />
        {style === "blouse" ? (
          <g>
            <path d="M166 318 Q200 366 234 318 Q218 326 200 326 Q182 326 166 318 Z" fill="#00000022" />
            <path d="M200 366 L200 600" stroke="#00000018" strokeWidth="3" />
            {[420, 480, 540].map((y) => <circle key={y} cx="200" cy={y} r="4" fill="#00000026" />)}
            {id === "a" && (
              <g>
                <path d="M172 330 Q200 362 228 330" stroke={accent} strokeWidth="3.5" fill="none" />
                <circle cx="200" cy="356" r="6" fill={accent} />
              </g>
            )}
          </g>
        ) : (
          <g>
            <rect x="166" y="298" width="68" height="44" rx="18" fill={top} />
            <path d="M170 312 Q200 322 230 312 M170 326 Q200 336 230 326" stroke="#00000026" strokeWidth="3" fill="none" />
            {id === "b" && (
              <path d="M102 620 L96 470 Q90 360 136 328 L152 332 L164 460 L156 620 Z M298 620 L304 470 Q310 360 264 328 L248 332 L236 460 L244 620 Z"
                    fill={jacket} />
            )}
          </g>
        )}
        {arms}
      </g>
    );
  }

  const isTie = style === "tie" || style === "open-collar";
  return (
    <g>
      <path d={body} fill={jacket} />
      <path d="M136 328 Q200 304 264 328 Q290 360 286 470 L280 620 L120 620 L114 470 Q110 360 136 328 Z"
            fill={sheen} opacity="0.3" />
      <path d={isTie ? "M166 316 L200 330 L234 316 L212 476 L188 476 Z" : "M162 318 L200 330 L238 318 L216 520 L184 520 Z"}
            fill={top} />
      {isTie && <path d="M166 316 L186 346 L200 328 Z M234 316 L214 346 L200 328 Z" fill={lighten(top, 0.4)} />}
      {style === "tie" && (
        <g>
          <path d="M193 330 L207 330 L213 440 L200 462 L187 440 Z" fill={accent} />
          {pattern && (
            <path d="M190 352 L210 344 M189 372 L211 364 M189 392 L212 384 M189 412 L212 404 M190 432 L211 424"
                  stroke="#FFFFFF" strokeOpacity="0.45" strokeWidth="3" />
          )}
          <path d="M193 330 L207 330 L204 342 L196 342 Z" fill="#00000030" />
        </g>
      )}
      {style === "open-collar" && <path d="M190 326 L200 354 L210 326 Z" fill="#D9A27E" opacity="0.9" />}
      {style === "blazer" && (
        <g>
          <path d="M178 330 Q200 354 222 330" stroke={accent} strokeWidth="3" fill="none" />
          <circle cx="200" cy="352" r="5" fill={accent} />
        </g>
      )}
      <path d={isTie ? "M156 318 L200 402 L188 480 L118 384 Z" : "M154 320 L200 410 L186 520 L112 384 Z"} fill={sheen} opacity="0.55" />
      <path d={isTie ? "M244 318 L200 402 L212 480 L282 384 Z" : "M246 320 L200 410 L214 520 L288 384 Z"} fill={sheen} opacity="0.55" />
      <path d={isTie ? "M188 476 L200 470 L212 476 L206 620 L194 620 Z" : "M184 520 L200 516 L216 520 L210 620 L190 620 Z"}
            fill={jacket} />
      <circle cx="200" cy={isTie ? 512 : 556} r="6" fill="#00000040" />
      {id === "b" && style === "tie" && !pattern && (
        <path d="M262 380 L284 376 L286 384 L264 388 Z" fill={lighten(accent, 0.5)} opacity="0.9" />
      )}
      {arms}
    </g>
  );
};

const SKIN_TONES: Record<PresenterId, string> = { a: "#C98B63", b: "#F0C4A1" };

/** Forearms and hands, drawn on top of the desk surface so they rest on it. */
const Forearms: React.FC<{ id: PresenterId; outfit: Outfit; lift: number }> = ({ id, outfit, lift }) => {
  const sleeve = sleeveColor(id, outfit);
  const cuff = outfit.style === "blazer" || outfit.style === "tie" || outfit.style === "open-collar"
    ? outfit.top : lighten(sleeve, 0.15);
  const skin = SKIN_TONES[id];
  return (
    <g>
      <g>
        <path d="M46 546 Q52 594 100 602 L150 604 L154 580 L112 574 Q102 566 104 548 Z" fill={sleeve} />
        <path d="M142 576 L156 576 L158 604 L144 604 Z" fill={cuff} />
        <ellipse cx="172" cy="592" rx="24" ry="14" fill={skin} />
        <ellipse cx="164" cy="582" rx="9" ry="6" fill={skin} />
      </g>
      <g transform={`rotate(${-lift} 320 556)`}>
        <path d="M354 546 Q348 594 300 602 L250 604 L246 580 L288 574 Q298 566 296 548 Z" fill={sleeve} />
        <path d="M258 576 L244 576 L242 604 L256 604 Z" fill={cuff} />
        <ellipse cx="228" cy="592" rx="24" ry="14" fill={skin} />
        <ellipse cx="236" cy="582" rx="9" ry="6" fill={skin} />
      </g>
    </g>
  );
};

export const PRESENTER_VIEW = { w: 400, h: 620, deskY: 570 } as const;

export const Presenter: React.FC<{
  id: PresenterId;
  mouth: number;
  look: number;
  speaking: boolean;
  size?: number;
  frameOverride?: number;
  seed?: string;
  part?: "body" | "hands";
}> = ({ id, mouth, look, speaking, size = 430, frameOverride, seed = "default", part = "body" }) => {
  const current = useCurrentFrame();
  const frame = frameOverride ?? current;
  const c = LOOKS[id];
  const outfit = outfitFor(id, seed);
  const blink = blinkAmount(frame, c.blinkOffset);
  const breathe = Math.sin(frame / 22 + c.blinkOffset) * 1.5;
  const nod = speaking ? Math.sin(frame / 7) * 1.6 * (0.4 + mouth) : 0;
  const tilt = look * 4 + Math.sin(frame / 53 + c.blinkOffset) * 1.2 + nod * 0.5;
  const shift = look * 9;
  const eyeOpen = interpolate(blink, [0, 1], [1, 0.08]);
  const brow = speaking ? -mouth * 4 : 0;
  const mouthOpen = mouth * 26;
  const mouthW = 40 + mouth * 6;
  const mx = 200 + shift * 0.9;
  const my = 252;

  return (
    <svg width={size} height={(size * PRESENTER_VIEW.h) / PRESENTER_VIEW.w}
         viewBox={`0 0 ${PRESENTER_VIEW.w} ${PRESENTER_VIEW.h}`} style={{ overflow: "visible" }}>
      {part === "hands" ? (
        <g transform={`translate(0 ${breathe * 0.5})`}>
          <Forearms id={id} outfit={outfit} lift={speaking ? Math.max(0, Math.sin(frame / 11)) * 7 * (0.4 + mouth) : 0} />
        </g>
      ) : (
      <>
      <g transform={`translate(0 ${breathe})`}>
        <Torso id={id} outfit={outfit} />
      </g>

      <g transform={`translate(0 ${breathe * 0.6 + nod}) rotate(${tilt} 200 300)`}>
        {id === "a" && <MayaHairBack c={c} />}
        <rect x="174" y="250" width="52" height="76" rx="22" fill={c.skinShade} />
        <ellipse cx={200 - c.faceRx - shift * 0.3} cy="200" rx="13" ry="20" fill={c.skinShade} />
        <ellipse cx={200 + c.faceRx - shift * 0.3} cy="200" rx="13" ry="20" fill={c.skinShade} />
        <ellipse cx="200" cy="190" rx={c.faceRx} ry={c.faceRy} fill={c.skin} />
        <ellipse cx={200 + shift * 0.6} cy="268" rx={c.faceRx * 0.55} ry="14" fill={c.skinShade} opacity="0.18" />

        {id === "a" ? <MayaHairFront c={c} /> : <LeoHair c={c} />}
        {id === "a" && (
          <g fill="none" stroke={outfit.accent} strokeWidth="4">
            <circle cx={200 - c.faceRx - shift * 0.3} cy="226" r="9" />
            <circle cx={200 + c.faceRx - shift * 0.3} cy="226" r="9" />
          </g>
        )}

        <g transform={`translate(${shift} 0)`}>
          <g stroke={c.hair} strokeWidth={id === "b" ? 8 : 6} strokeLinecap="round" fill="none">
            <path d={`M150 ${160 + brow} Q166 ${150 + brow} 184 ${157 + brow}`} />
            <path d={`M216 ${157 + brow} Q234 ${150 + brow} 250 ${160 + brow}`} />
          </g>
          {[167, 233].map((ex) => (
            <g key={ex} transform={`translate(${ex} 190) scale(1 ${eyeOpen})`}>
              <ellipse cx="0" cy="0" rx="15" ry="11" fill="#FFFFFF" />
              <circle cx={look * 3} cy="1" r="8" fill={c.iris} />
              <circle cx={look * 3} cy="1" r="4" fill="#0B0B12" />
              <circle cx={look * 3 + 3} cy="-2" r="2.4" fill="#FFFFFF" />
            </g>
          ))}
          {id === "a" &&
            [167, 233].map((ex) => (
              <path key={ex} d={`M${ex - 16} ${185 - 9 * eyeOpen} Q${ex} ${175 - 10 * eyeOpen} ${ex + 17} ${184 - 9 * eyeOpen}`}
                    stroke="#120A08" strokeWidth="3.5" fill="none" strokeLinecap="round" />
            ))}
          <path d="M197 205 Q192 224 200 228 Q207 229 210 225" stroke={c.skinShade} strokeWidth="4"
                fill="none" strokeLinecap="round" />
          <ellipse cx="146" cy="226" rx="14" ry="8" fill="#E0757A" opacity="0.28" />
          <ellipse cx="254" cy="226" rx="14" ry="8" fill="#E0757A" opacity="0.28" />
        </g>

        {mouth > 0.06 ? (
          <g>
            <path d={`M${mx - mouthW / 2} ${my} Q${mx} ${my - 4} ${mx + mouthW / 2} ${my}
                      Q${mx} ${my + 8 + mouthOpen} ${mx - mouthW / 2} ${my} Z`}
                  fill="#4A1620" stroke={c.lips} strokeWidth="4" strokeLinejoin="round" />
            <path d={`M${mx - mouthW / 2 + 6} ${my + 1} Q${mx} ${my + 2 + mouthOpen * 0.18} ${mx + mouthW / 2 - 6} ${my + 1}`}
                  stroke="#FFFFFF" strokeWidth={Math.min(6, 2 + mouthOpen * 0.25)} fill="none" strokeLinecap="round" />
            <ellipse cx={mx} cy={my + 4 + mouthOpen * 0.62} rx={mouthW * 0.24} ry={Math.max(1, mouthOpen * 0.16)}
                     fill="#D9707A" />
          </g>
        ) : (
          <path d={`M${mx - 22} ${my - 2} Q${mx} ${my + 12} ${mx + 22} ${my - 2}`} stroke={c.lips}
                strokeWidth="5" fill="none" strokeLinecap="round" />
        )}
      </g>
      </>
      )}
    </svg>
  );
};
