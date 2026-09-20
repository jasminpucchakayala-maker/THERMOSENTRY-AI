// C:/Users/jasmi/OneDrive/Desktop/THERMOSENTRY-AI/frontend/src/lib/api.ts
export const API_BASE = process.env.NEXT_PUBLIC_API_BASE || '';
export const ws = typeof window !== 'undefined' ? new WebSocket(`${API_BASE.replace('http', 'ws')}/events`) : null;

export async function fetchJSON(path: string) {
  const res = await fetch(`${API_BASE}/${path}`);
  if (!res.ok) throw new Error(`API error ${res.status}`);
  return res.json();
}
