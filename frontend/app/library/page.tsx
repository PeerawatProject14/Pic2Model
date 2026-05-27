"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type CatalogEntry } from "@/lib/api";

export default function LibraryPage() {
  const [entries, setEntries] = useState<CatalogEntry[]>([]);
  const [q, setQ] = useState("");
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    try {
      setEntries(await api.catalog(q || undefined));
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function del(id: string) {
    if (!confirm("Delete this model?")) return;
    await api.deleteEntry(id);
    load();
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <div className="flex items-center gap-3">
        <h1 className="text-xl font-semibold">Library</h1>
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && load()}
          placeholder="search by name…"
          className="ml-auto w-56 rounded bg-zinc-800 px-3 py-1.5 text-sm outline-none focus:ring-1 focus:ring-indigo-500"
        />
        <button onClick={load} className="rounded border border-zinc-700 px-3 py-1.5 text-sm hover:bg-zinc-900">
          Search
        </button>
        <Link href="/create" className="rounded bg-indigo-500 px-3 py-1.5 text-sm font-medium text-white hover:bg-indigo-400">
          + New
        </Link>
      </div>

      {loading ? (
        <p className="mt-10 text-zinc-500">Loading…</p>
      ) : entries.length === 0 ? (
        <p className="mt-10 text-zinc-500">No models yet. Create one →</p>
      ) : (
        <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
          {entries.map((e) => (
            <div key={e.id} className="group overflow-hidden rounded-lg border border-zinc-800 bg-zinc-900/40">
              <Link href={`/model/${e.id}`}>
                <div className="aspect-square bg-zinc-950">
                  {e.thumbnail_path ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={api.fileUrl("thumbnails", e.thumbnail_path)}
                      alt={e.name}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <div className="flex h-full items-center justify-center text-zinc-700">no preview</div>
                  )}
                </div>
              </Link>
              <div className="p-3">
                <div className="flex items-center justify-between">
                  <Link href={`/model/${e.id}`} className="truncate text-sm font-medium hover:text-indigo-400">
                    {e.name}
                  </Link>
                  <button onClick={() => del(e.id)} className="text-xs text-zinc-600 hover:text-red-400">✕</button>
                </div>
                <p className="mt-0.5 text-xs text-zinc-500">
                  {e.parts.length} parts · {e.faces.toLocaleString()}f
                </p>
                {e.tags.length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-1">
                    {e.tags.map((t) => (
                      <span key={t} className="rounded bg-zinc-800 px-1.5 py-0.5 text-[10px] text-zinc-400">{t}</span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
