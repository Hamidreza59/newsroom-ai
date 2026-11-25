import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { type Delivery, NO_DELIVERY } from "./Voice";
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

/** Every ~9s a listening anchor glances down at their notes for about a second. */
const glanceAmount = (frame: number, offset: number) => {
  const t = (frame + offset * 3) % 270;
  return t < 34 ? Math.sin((t / 34) * Math.PI) : 0;
};

/** An occasional smooth posture shift in the chair (about every 14s). */
const chairShift = (frame: number, offset: number) => {
  const cycle = 420;
  const t = ((frame + offset * 5) % cycle) / 40;
  const dir = Math.floor((frame + offset * 5) / cycle) % 2 === 0 ? 1 : -1;
  return t < 1 ? dir * Math.sin(t * Math.PI) : 0;
};

const blinkAmount = (frame: number, offset: number) => {
  const cycle = 120;
  const jitter = [0, 41, 17, 67, 29][Math.floor((frame + offset) / cycle) % 5];
  const t = ((frame + offset) % cycle) - jitter;
  return t >= 0 && t < 7 ? Math.sin((t / 7) * Math.PI) : 0;
};

const MayaHairBack: React.FC<{ c: Look }> = ({ c }) => (
  <g>
    <path d="M104 196 Q96 86 200 78 Q304 86 296 196 L304 300 Q276 318 246 300 L238 250 L162 250 L154 300
             Q124 318 96 300 Z" fill={c.hair} />
    <g stroke={c.hairLight} strokeWidth="2.5" fill="none" strokeLinecap="round" opacity="0.5">
      <path d="M108 214 Q102 256 110 298" />
      <path d="M120 236 Q116 270 124 304" />
      <path d="M292 214 Q298 256 290 298" />
      <path d="M280 236 Q284 270 276 304" />
    </g>
  </g>
);

const MayaHairFront: React.FC<{ c: Look }> = ({ c }) => (
  <g>
    <path d="M112 186 Q112 96 200 90 Q290 94 292 186 Q282 132 236 116 Q196 150 132 160 Q118 170 112 186 Z"
          fill={c.hair} />
    <path d="M150 112 Q190 96 236 112" stroke={c.hairLight} strokeWidth="6" fill="none" strokeLinecap="round"
          opacity="0.7" />
    <g stroke={c.hairLight} strokeWidth="2.5" fill="none" strokeLinecap="round" opacity="0.55">
      <path d="M140 150 Q170 114 214 106" />
      <path d="M126 176 Q138 132 180 112" />
      <path d="M250 116 Q282 140 286 184" />
      <path d="M236 112 Q266 128 278 168" />
      <path d="M160 140 Q190 120 228 116" />
    </g>
  </g>
);

const LeoHair: React.FC<{ c: Look }> = ({ c }) => (
  <g>
    <path d="M116 176 Q108 92 200 82 Q294 88 286 172 Q282 130 254 118 Q236 92 194 100 Q150 106 132 132
             Q120 150 116 176 Z" fill={c.hair} />
    <path d="M168 102 Q200 82 240 100" stroke={c.hairLight} strokeWidth="7" fill="none" strokeLinecap="round"
          opacity="0.8" />
    <g stroke={c.hairLight} strokeWidth="2.5" fill="none" strokeLinecap="round" opacity="0.55">
      <path d="M146 118 Q186 94 232 104" />
      <path d="M136 136 Q166 110 206 104" />
      <path d="M252 118 Q272 132 280 160" />
      <path d="M124 160 Q132 136 150 124" />
    </g>
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
  const folds = (
    <g stroke="#000000" strokeOpacity="0.08" strokeWidth="2.5" fill="none" strokeLinecap="round">
      <path d="M132 430 Q146 452 138 482" />
      <path d="M268 430 Q254 452 262 482" />
      <path d="M150 566 Q200 580 250 566" />
      <path d="M160 590 Q200 602 240 590" />
    </g>
  );
  const arms = (
    <g>
      <path d={UPPER_ARMS.l} fill={sleeve} />
      <path d={UPPER_ARMS.r} fill={sleeve} />
      <path d={ARM_SEAMS} stroke="#00000059" strokeWidth="6" fill="none" strokeLinecap="round" />
      <g stroke="#000000" strokeOpacity="0.1" strokeWidth="2.5" fill="none" strokeLinecap="round">
        <path d="M58 502 Q72 512 90 504 M60 524 Q74 532 92 526" />
        <path d="M342 502 Q328 512 310 504 M340 524 Q326 532 308 526" />
        <path d="M86 378 Q96 392 94 410 M314 378 Q304 392 306 410" />
      </g>
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
        {folds}
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
      {folds}
      {arms}
    </g>
  );
};

const SKIN_TONES: Record<PresenterId, string> = { a: "#C98B63", b: "#F0C4A1" };

/** A relaxed hand resting on the desk, fingers pointing toward the body's centre line. */
const Hand: React.FC<{ x: number; y: number; flip: boolean; skin: string; open: number }> = ({ x, y, flip, skin, open }) => {
  return (
    <g transform={`translate(${x} ${y}) scale(${flip ? -1 : 1} 1)`}>
      <path d="M-24 -8 Q-12 -16 6 -13 L14 -8 Q18 2 12 10 L-16 12 Q-28 8 -24 -8 Z" fill={skin} />
      {[-9, -3, 3, 9].map((fy, i) => (
        <rect key={i} x={8 + Math.abs(fy) * -0.3} y={fy - 3 + open * (fy * 0.35)} width={18 - Math.abs(fy) * 0.5 + open * 4}
              height="6.5" rx="3.2" fill={skin} transform={`rotate(${fy * 2 * open} 8 ${fy})`} />
      ))}
      <path d="M-10 -12 Q4 -24 16 -20 Q20 -17 16 -14 Q6 -14 -2 -8 Z" fill={skin} />
      <g stroke="#000000" strokeOpacity="0.16" strokeWidth="1.6" fill="none" strokeLinecap="round">
        <path d="M8 -9 L10 -9 M8 -3 L11 -3 M8 3 L11 3 M8 9 L10 9" />
        <path d="M-20 4 Q-8 8 6 6" />
      </g>
    </g>
  );
};

/** Forearms and hands, drawn on top of the desk surface so they rest on it. */
const Forearms: React.FC<{ id: PresenterId; outfit: Outfit; lift: number; open: number }> = ({ id, outfit, lift, open }) => {
  const sleeve = sleeveColor(id, outfit);
  const cuff = outfit.style === "blazer" || outfit.style === "tie" || outfit.style === "open-collar"
    ? outfit.top : lighten(sleeve, 0.15);
  const skin = SKIN_TONES[id];
  return (
    <g>
      <g>
        <path d="M46 546 Q52 594 100 602 L150 604 L154 580 L112 574 Q102 566 104 548 Z" fill={sleeve} />
        <path d="M142 576 L156 576 L158 604 L144 604 Z" fill={cuff} />
        <Hand x={174} y={592} flip={false} skin={skin} open={0} />
      </g>
      <g transform={`rotate(${-lift} 320 556)`}>
        <path d="M354 546 Q348 594 300 602 L250 604 L246 580 L288 574 Q298 566 296 548 Z" fill={sleeve} />
        <path d="M258 576 L244 576 L242 604 L256 604 Z" fill={cuff} />
        <Hand x={226} y={592} flip skin={skin} open={open} />
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
  delivery?: Delivery;
}> = ({ id, mouth, look, speaking, size = 430, frameOverride, seed = "default", part = "body", delivery = NO_DELIVERY }) => {
  const current = useCurrentFrame();
  const frame = frameOverride ?? current;
  const c = LOOKS[id];
  const outfit = outfitFor(id, seed);
  const d = delivery;
  const blink = blinkAmount(frame, c.blinkOffset);
  const breathe = Math.sin(frame / 22 + c.blinkOffset) * 1.5;
  const glance = speaking ? 0 : glanceAmount(frame, c.blinkOffset);
  const seat = Math.sin(frame / 170 + c.blinkOffset) * 2.5 + chairShift(frame, c.blinkOffset) * 5;
  const nod = speaking ? Math.sin(frame / 7) * 1.6 * (0.4 + mouth) + d.emphasis * 4 : 0;
  const tilt = look * 4 + Math.sin(frame / 53 + c.blinkOffset) * 1.2 + nod * 0.5
    + d.question * 6 * (id === "a" ? 1 : -1) + (speaking ? 0 : Math.sin(frame / 90 + c.blinkOffset) * 1.5);
  const shift = look * 9;
  const eyeOpen = interpolate(blink, [0, 1], [1, 0.08]) * (1 - 0.4 * glance) * (1 + 0.12 * d.exclaim);
  const smile = Math.min(1, 0.3 + (speaking ? 0.1 : 0.3) + d.exclaim * 0.5 + d.emphasis * 0.15);
  const brow = -(d.question * 8 + d.emphasis * 4 + d.exclaim * 4) + glance * 2;
  const mouthOpen = mouth * 26;
  const mouthW = 40 + mouth * 6 + smile * 6;
  const mx = 200 + shift * 0.9;
  const my = 252;
  const corner = smile * 4;

  return (
    <svg width={size} height={(size * PRESENTER_VIEW.h) / PRESENTER_VIEW.w}
         viewBox={`0 0 ${PRESENTER_VIEW.w} ${PRESENTER_VIEW.h}`} style={{ overflow: "visible" }}>
      {part === "hands" ? (
        <g transform={`translate(0 ${breathe * 0.5})`}>
          <g transform={`translate(${seat * 0.4} 0)`}>
            <Forearms id={id} outfit={outfit} open={d.emphasis}
                      lift={speaking ? Math.max(0, Math.sin(frame / 11)) * 6 * (0.4 + mouth) + d.emphasis * 16 : 0} />
          </g>
        </g>
      ) : (
      <>
      <g transform={`translate(${seat * 0.6} ${breathe})`}>
        <Torso id={id} outfit={outfit} />
      </g>

      <g transform={`translate(${seat} ${breathe * 0.6 + nod + glance * 6}) rotate(${tilt} 200 300)`}>
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
            <path d={`M150 ${160 + brow * 0.8} Q166 ${150 + brow} 184 ${157 + brow - d.question * 3}`} />
            <path d={`M216 ${157 + brow - d.question * 3} Q234 ${150 + brow} 250 ${160 + brow * 0.8}`} />
          </g>
          {[167, 233].map((ex) => (
            <g key={ex} transform={`translate(${ex} 190) scale(1 ${eyeOpen})`}>
              <ellipse cx="0" cy="0" rx="15" ry="11" fill="#FFFFFF" />
              <circle cx={look * 3} cy={1 + glance * 5} r="8" fill={c.iris} />
              <circle cx={look * 3} cy={1 + glance * 5} r="4" fill="#0B0B12" />
              <circle cx={look * 3 + 3} cy={-2 + glance * 5} r="2.4" fill="#FFFFFF" />
            </g>
          ))}
          {id === "a" &&
            [167, 233].map((ex) => (
              <path key={ex} d={`M${ex - 16} ${185 - 9 * eyeOpen} Q${ex} ${175 - 10 * eyeOpen} ${ex + 17} ${184 - 9 * eyeOpen}`}
                    stroke="#120A08" strokeWidth="3.5" fill="none" strokeLinecap="round" />
            ))}
          {smile > 0.45 && [167, 233].map((ex) => (
            <path key={ex} d={`M${ex - 13} 201 Q${ex} ${196 - smile * 3} ${ex + 13} 201`} stroke={c.skinShade}
                  strokeWidth="3" fill="none" strokeLinecap="round" opacity={(smile - 0.45) * 1.6} />
          ))}
          <path d="M197 205 Q192 224 200 228 Q207 229 210 225" stroke={c.skinShade} strokeWidth="4"
                fill="none" strokeLinecap="round" />
          <ellipse cx="146" cy="226" rx="14" ry="8" fill="#E0757A" opacity="0.28" />
          <ellipse cx="254" cy="226" rx="14" ry="8" fill="#E0757A" opacity="0.28" />
        </g>

        {mouth > 0.06 ? (
          <g>
            <path d={`M${mx - mouthW / 2} ${my - corner} Q${mx} ${my - 4} ${mx + mouthW / 2} ${my - corner}
                      Q${mx} ${my + 8 + mouthOpen} ${mx - mouthW / 2} ${my - corner} Z`}
                  fill="#4A1620" stroke={c.lips} strokeWidth="4" strokeLinejoin="round" />
            <path d={`M${mx - mouthW / 2 + 6} ${my + 1} Q${mx} ${my + 2 + mouthOpen * 0.18} ${mx + mouthW / 2 - 6} ${my + 1}`}
                  stroke="#FFFFFF" strokeWidth={Math.min(6, 2 + mouthOpen * 0.25)} fill="none" strokeLinecap="round" />
            <ellipse cx={mx} cy={my + 4 + mouthOpen * 0.62} rx={mouthW * 0.24} ry={Math.max(1, mouthOpen * 0.16)}
                     fill="#D9707A" />
          </g>
        ) : (
          <path d={`M${mx - 22 - smile * 5} ${my - 2 - corner} Q${mx} ${my + 8 + smile * 9} ${mx + 22 + smile * 5} ${my - 2 - corner}`}
                stroke={c.lips} strokeWidth="5" fill="none" strokeLinecap="round" />
        )}
      </g>
      </>
      )}
    </svg>
  );
};
