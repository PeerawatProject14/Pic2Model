// Typed client for the Pic2Model backend. All calls go through Next's /api proxy.

export interface PartSpec {
  name: string;
  bbox?: [number, number, number, number]; // x, y, w, h
  polygon?: [number, number][];
  tags?: string[];
}

export interface Job {
  id: string;
  kind: string;
  status: "queued" | "running" | "done" | "error";
  progress: number;
  message: string;
  result_id: string | null;
  error: string | null;
}

export interface CatalogPart {
  name: string;
  node: string;
  faces: number;
  tags: string[];
}

export interface CatalogEntry {
  id: string;
  name: string;
  source_image_id: string | null;
  glb_path: string;
  thumbnail_path: string | null;
  parts: CatalogPart[];
  faces: number;
  tags: string[];
  backend: string;
  created_at: string;
}

export interface UploadResponse {
  image_id: string;
  url: string;
  width: number;
  height: number;
}

async function jsonFetch<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

export const api = {
  health: () => jsonFetch<{ status: string; backends: Record<string, string> }>("/api/health"),

  async upload(file: File): Promise<UploadResponse> {
    const fd = new FormData();
    fd.append("file", file);
    const res = await fetch("/api/upload", { method: "POST", body: fd });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  segment: (image_id: string, points: number[][] = []) =>
    jsonFetch<{ image_id: string; parts: PartSpec[] }>("/api/segment", {
      method: "POST",
      body: JSON.stringify({ image_id, points }),
    }),

  generate: (body: {
    image_id: string;
    parts: PartSpec[];
    remove_bg: boolean;
    target_faces?: number;
    name?: string;
    tags?: string[];
  }) => jsonFetch<Job>("/api/generate", { method: "POST", body: JSON.stringify(body) }),

  job: (id: string) => jsonFetch<Job>(`/api/jobs/${id}`),

  catalog: (q?: string, tag?: string) => {
    const p = new URLSearchParams();
    if (q) p.set("q", q);
    if (tag) p.set("tag", tag);
    const qs = p.toString();
    return jsonFetch<CatalogEntry[]>(`/api/catalog${qs ? `?${qs}` : ""}`);
  },

  entry: (id: string) => jsonFetch<CatalogEntry>(`/api/catalog/${id}`),

  deleteEntry: (id: string) =>
    fetch(`/api/catalog/${id}`, { method: "DELETE" }).then((r) => r.ok),

  fileUrl: (subdir: "inputs" | "models" | "thumbnails", filename: string) =>
    `/api/files/${subdir}/${filename}`,
};
