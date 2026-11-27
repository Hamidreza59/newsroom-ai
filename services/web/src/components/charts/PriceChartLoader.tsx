"use client";

import dynamic from "next/dynamic";
import { Skeleton } from "@/components/ui/Skeleton";

export const PriceChartLoader = dynamic(() => import("./PriceChart"), {
  ssr: false,
  loading: () => <Skeleton className="h-[420px] w-full" />,
});
