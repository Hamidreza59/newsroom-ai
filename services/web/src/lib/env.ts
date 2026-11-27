export const SERVER_API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";
export const PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export const mediaUrl = (path: string | null) => (path ? `${PUBLIC_API_URL}${path}` : null);
