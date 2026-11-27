export const color = {
  bg0: "#060A1A",
  bg1: "#0D1533",
  bg2: "#16224D",
  panel: "rgba(255,255,255,0.055)",
  panelBorder: "rgba(255,255,255,0.12)",
  text: "#F4F6FF",
  muted: "#A3ADD3",
  up: "#2BD97C",
  down: "#FF5C70",
  ai: "#22D3EE",
  tech: "#A78BFA",
  gold: "#FFC53D",
  suit: "#1E2B5C",
  tie: "#FF5C70",
  bio: "#F472B6",
  teal: "#2DD4BF",
} as const;

export const lightColor = {
  bg: "#F6F7FB",
  panel: "#FFFFFF",
  text: "#0B1230",
  muted: "#53608A",
  up: "#0E9F57",
  down: "#D92D45",
} as const;

export const moveColor = (v: number) => (v >= 0 ? color.up : color.down);
