import React from "react";
import { color } from "./tokens";

export interface LogoProps {
  name: string;
  size?: number;
  fontFamily?: string;
  textColor?: string;
  markOnly?: boolean;
}

export const Logo: React.FC<LogoProps> = ({
  name,
  size = 40,
  fontFamily,
  textColor = color.text,
  markOnly = false,
}) => {
  const [first, second] = name.includes("&") ? name.split("&").map((s) => s.trim()) : [name, ""];
  return (
    <div style={{ display: "flex", alignItems: "center", gap: size * 0.35 }}>
      <svg width={size * 1.3} height={size * 1.3} viewBox="0 0 52 52" aria-hidden="true">
        <rect x="2" y="2" width="48" height="48" rx="14" fill={color.gold} />
        <path
          d="M12 34 L20 24 L27 29 L38 15"
          stroke={color.bg0}
          strokeWidth="5"
          fill="none"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle cx="38" cy="15" r="4" fill={color.bg0} />
      </svg>
      {!markOnly && (
        <div
          style={{
            fontFamily,
            fontWeight: 700,
            fontSize: size,
            color: textColor,
            letterSpacing: size * 0.04,
            lineHeight: 1,
          }}
        >
          {first.toUpperCase()}
          {second && (
            <>
              <span style={{ color: color.gold }}> &amp; </span>
              {second.toUpperCase()}
            </>
          )}
        </div>
      )}
    </div>
  );
};
