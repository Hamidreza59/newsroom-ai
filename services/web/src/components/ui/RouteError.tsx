"use client";

import { RotateCcw } from "lucide-react";

export default function RouteError({ reset }: { error: Error; reset: () => void }) {
  return (
    <div className="card mx-auto mt-10 flex max-w-lg flex-col items-center gap-3 px-6 py-14 text-center" role="alert">
      <h1 className="text-xl font-semibold">Something went wrong</h1>
      <p className="text-sm text-muted">We hit an unexpected error while loading this page.</p>
      <button
        type="button"
        onClick={reset}
        className="mt-2 inline-flex items-center gap-2 rounded-lg border border-line-strong px-4 py-2 text-sm font-medium hover:bg-surface-2"
      >
        <RotateCcw size={14} aria-hidden="true" /> Try again
      </button>
    </div>
  );
}
