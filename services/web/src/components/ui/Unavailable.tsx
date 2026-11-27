import { CloudOff } from "lucide-react";

export function Unavailable({ what = "This content" }: { what?: string }) {
  return (
    <div className="card flex flex-col items-center gap-2 px-6 py-14 text-center" role="status">
      <CloudOff size={28} className="text-muted" aria-hidden="true" />
      <h2 className="text-lg font-semibold">Data temporarily unavailable</h2>
      <p className="max-w-md text-sm text-muted">
        {what} could not be loaded right now. Please try again in a few minutes.
      </p>
    </div>
  );
}
