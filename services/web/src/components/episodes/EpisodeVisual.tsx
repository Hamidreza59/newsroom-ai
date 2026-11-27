import { Logo } from "@newsroom/brand";
import { mediaUrl } from "@/lib/env";
import { siteConfig } from "@/site.config";

export function EpisodeVisual({ thumbnailUrl, date, className = "" }: { thumbnailUrl: string | null; date: string; className?: string }) {
  const src = mediaUrl(thumbnailUrl);
  return (
    <div className={`relative aspect-video overflow-hidden bg-surface-2 ${className}`}>
      {src ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={src} alt="" className="h-full w-full object-cover" loading="lazy" />
      ) : (
        <div
          className="flex h-full w-full flex-col items-center justify-center gap-3"
          style={{ background: "radial-gradient(600px 300px at 30% 20%, rgb(34 211 238 / 0.22), transparent 60%), radial-gradient(600px 300px at 80% 90%, rgb(167 139 250 / 0.22), transparent 60%), linear-gradient(160deg, #0d1533, #060a1a)" }}
        >
          <Logo name={siteConfig.name} size={16} fontFamily="var(--font-inter)" textColor="#f4f6ff" />
          <span className="num text-xs tracking-widest text-[#a3add3]">{date}</span>
        </div>
      )}
    </div>
  );
}
