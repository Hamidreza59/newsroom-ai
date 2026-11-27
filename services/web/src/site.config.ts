export const siteConfig = {
  name: "Newsroom",
  tagline: "Markets, AI, tech & biotech — explained daily",
  description:
    "Daily markets, AI, tech and biotech news, an AI-produced video show and weekly explainers.",
  nav: [
    { href: "/", label: "Home" },
    { href: "/markets", label: "Markets" },
    { href: "/ai", label: "AI" },
    { href: "/ai-finance", label: "AI in Finance" },
    { href: "/tech", label: "Tech" },
    { href: "/biotech", label: "Biotech" },
    { href: "/innovation", label: "AI Innovation" },
    { href: "/episodes", label: "Episodes" },
  ],
  social: [
    { label: "YouTube", href: "#" },
    { label: "X", href: "#" },
    { label: "LinkedIn", href: "#" },
  ],
  footerLinks: [
    { label: "About", href: "#" },
    { label: "Methodology", href: "#" },
    { label: "Contact", href: "#" },
  ],
} as const;
