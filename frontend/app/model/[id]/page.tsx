"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { api, type CatalogEntry } from "@/lib/api";

// R3F must be client-only (no SSR).
const ModelViewer = dynamic(() => import("@/components/ModelViewer"), { ssr: false });

export default function ModelPage() {
  const { id } = useParams<{ id: string }>();
  const [entry, setEntry] = useState<CatalogEntry | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [hidden, setHidden] = useState<Set<string>>(new Set());
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    api.entry(id).then(setEntry).catch((e) => setErr(String(e)));
  }, [id]);

  if (err) return <div className="p-8 text-red-400">Failed to load: {err}</div>;
  if (!entry) return <div className="p-8 text-zinc-500">Loading…</div>;

  const glbUrl = api.fileUrl("models", entry.glb_path);

  function toggleHidden(node: string) {
    setHidden((prev) => {
      const next = new Set(prev);
      next.has(node) ? next.delete(node) : next.add(node);
      return next;
    });
  }

  return (
    <div className="flex h-[calc(100vh-49px)]">
      <div className="relative flex-1">
        <ModelViewer
          url={glbUrl}
          selectedNode={selected}
          hiddenNodes={hidden}
          onSelect={setSelected}
        />
        <div className="pointer-events-none absolute left-4 top-4 text-xs text-zinc-500">
          click a part to select • drag to orbit
        </div>
      </div>

      <aside className="w-80 shrink-0 overflow-y-auto border-l border-zinc-800 p-4">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="font-semibold">{entry.name}</h1>
            <p className="text-xs text-zinc-500">
              {entry.parts.length} part{entry.parts.length === 1 ? "" : "s"} ·{" "}
              {entry.faces.toLocaleString()} faces · {entry.backend}
            </p>
          </div>
        </div>

        {entry.tags.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1">
            {entry.tags.map((t) => (
              <span key={t} className="rounded bg-zinc-800 px-2 py-0.5 text-xs text-zinc-300">
                {t}
              </span>
            ))}
          </div>
        )}

        <h2 className="mt-5 mb-2 text-xs font-medium uppercase tracking-wide text-zinc-500">
          Parts
        </h2>
        <ul className="space-y-1">
          {entry.parts.map((p) => {
            const isSel = selected === p.node;
            const isHidden = hidden.has(p.node);
            return (
              <li
                key={p.node}
                className={`flex items-center gap-2 rounded px-2 py-1.5 text-sm ${
                  isSel ? "bg-indigo-500/20 ring-1 ring-indigo-500" : "hover:bg-zinc-900"
                }`}
              >
                <button
                  className="flex-1 text-left"
                  onClick={() => setSelected(isSel ? null : p.node)}
                >
                  <span className={isHidden ? "text-zinc-600 line-through" : ""}>{p.name}</span>
                  <span className="ml-2 text-xs text-zinc-600">{p.faces}f</span>
                </button>
                <button
                  title={isHidden ? "show" : "hide"}
                  onClick={() => toggleHidden(p.node)}
                  className="rounded px-1 text-xs text-zinc-500 hover:text-zinc-200"
                >
                  {isHidden ? "🙈" : "👁"}
                </button>
              </li>
            );
          })}
        </ul>

        <div className="mt-6 flex flex-col gap-2">
          <a
            href={glbUrl}
            download={`${entry.name}.glb`}
            className="rounded-md bg-indigo-500 px-3 py-2 text-center text-sm font-medium text-white hover:bg-indigo-400"
          >
            Download GLB
          </a>
          <Link
            href="/library"
            className="rounded-md border border-zinc-700 px-3 py-2 text-center text-sm text-zinc-200 hover:bg-zinc-900"
          >
            Back to library
          </Link>
        </div>
      </aside>
    </div>
  );
}
