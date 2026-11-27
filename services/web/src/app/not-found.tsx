import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto mt-16 max-w-md text-center">
      <p className="num text-5xl font-bold text-gold">404</p>
      <h1 className="mt-4 text-xl font-semibold">Page not found</h1>
      <p className="mt-2 text-sm text-muted">The page you are looking for does not exist or has moved.</p>
      <Link href="/" className="mt-6 inline-block rounded-lg border border-line-strong px-4 py-2 text-sm font-medium hover:bg-surface-2">Back to home</Link>
    </div>
  );
}
