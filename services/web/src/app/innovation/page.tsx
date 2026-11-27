import type { Metadata } from "next";
import { categories } from "@newsroom/brand";
import { FeatureCard } from "@/components/innovation/FeatureCard";
import { PageHeader } from "@/components/ui/Section";
import { Unavailable } from "@/components/ui/Unavailable";
import { getFeatures } from "@/lib/api";

export const metadata: Metadata = {
  title: "AI Innovation",
  description: "Weekly plain-language features on the ideas shaping AI.",
  openGraph: { title: "AI Innovation" },
};

export default async function InnovationPage() {
  const features = await getFeatures();
  return (
    <>
      <PageHeader
        title="AI Innovation"
        eyebrow="Weekly features"
        accent={categories.ai.color}
        description="One idea, explained clearly each week, with the week's related headlines and sources."
      />
      {!features ? (
        <Unavailable what="The feature archive" />
      ) : features.length === 0 ? (
        <p className="card p-10 text-center text-muted">No features published yet.</p>
      ) : (
        <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {features.map((f) => <FeatureCard key={f.slug} feature={f} />)}
        </div>
      )}
    </>
  );
}
