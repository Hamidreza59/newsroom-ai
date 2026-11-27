import { color } from "./tokens";

export type TabSlug = "markets" | "ai" | "ai-finance" | "tech" | "biotech";

export interface Category {
  slug: TabSlug;
  label: string;
  color: string;
  description: string;
}

export const categories: Record<TabSlug, Category> = {
  markets: {
    slug: "markets",
    label: "Markets",
    color: color.gold,
    description: "Indices, sectors and the stories moving prices.",
  },
  ai: {
    slug: "ai",
    label: "AI",
    color: color.ai,
    description: "Models, chips, research and policy shaping artificial intelligence.",
  },
  "ai-finance": {
    slug: "ai-finance",
    label: "AI in Finance",
    color: color.teal,
    description: "Where machine learning meets banks, trading desks and fintech.",
  },
  tech: {
    slug: "tech",
    label: "Tech",
    color: color.tech,
    description: "Platforms, hardware, software and the business of technology.",
  },
  biotech: {
    slug: "biotech",
    label: "Biotech",
    color: color.bio,
    description: "Trials, approvals and the science behind the next generation of medicine.",
  },
};

export const tabs: Category[] = Object.values(categories);

export const isTabSlug = (s: string): s is TabSlug => s in categories;
