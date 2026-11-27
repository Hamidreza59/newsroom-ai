"use client";

import { useSyncExternalStore } from "react";

const NAMES = ["text", "muted", "border", "surface", "surface-2", "up", "down", "gold", "ai", "tech", "bio", "teal"] as const;
export type ThemeColors = Record<(typeof NAMES)[number], string>;

const FALLBACK = Object.fromEntries(NAMES.map((n) => [n, "#888888"])) as ThemeColors;
let cache: { theme: string; colors: ThemeColors } | null = null;

const read = (): ThemeColors => {
  const theme = document.documentElement.dataset.theme ?? "dark";
  if (cache?.theme === theme) return cache.colors;
  const style = getComputedStyle(document.documentElement);
  const colors = Object.fromEntries(
    NAMES.map((n) => [n, style.getPropertyValue(`--${n}`).trim() || FALLBACK[n]]),
  ) as ThemeColors;
  cache = { theme, colors };
  return colors;
};

const subscribe = (cb: () => void) => {
  const obs = new MutationObserver(cb);
  obs.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  return () => obs.disconnect();
};

export const useThemeColors = () => useSyncExternalStore(subscribe, read, () => FALLBACK);
