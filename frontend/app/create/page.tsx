"use client";

import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";
import PartMarker from "@/components/PartMarker";
import { api, type PartSpec, type UploadResponse } from "@/lib/api";

export default function CreatePage() {
  const router = useRouter();
  const [upload, setUpload] = useState<UploadResponse | null>(null);
  const [parts, setParts] = useState<PartSpec[]>([]);
  const [name, setName] = useState("");
  const [tags, setTags] = useState("");
  const [removeBg, setRemoveBg] = useState(true);
  const [targetFaces, setTargetFaces] = useState(30000);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<string>("");

  const onFile = useCallback(async (file: File) => {
    setBusy(true);
    setStatus("uploading...");
    try {
      const res = await api.upload(file);
      setUpload(res);
      setParts([]);
      if (!name) setName(file.name.replace(/\.[^.]+$/, ""));
    } catch (e) {
      setStatus(`upload failed: ${e}`);
    } finally {
      setBusy(false);
      setStatus("");
    }
  }, [name]);

  async function suggestParts() {
    if (!upload) return;
    setBusy(true);
    setStatus("segmenting...");
    try {
      const res = await api.segment(upload.image_id);
      setParts(res.parts);
    } catch (e) {
      setStatus(`segment failed: ${e}`);
    } finally {
      setBusy(false);
      setStatus("");
    }
  }

  async function generate() {
    if (!upload) return;
    setBusy(true);
    try {
      const job = await api.generate({
        image_id: upload.image_id,
        parts,
        remove_bg: removeBg,
        target_faces: targetFaces,
        name: name || upload.image_id,
        tags: tags.split(",").map((t) => t.trim()).filter(Boolean),
      });
      // poll
      let j = job;
      while (j.status === "queued" || j.status === "running") {
        setStatus(`${j.status} ${Math.round(j.progress * 100)}% ${j.message}`);
        await new Promise((r) => setTimeout(r, 800));
        j = await api.job(job.id);
      }
      if (j.status === "done" && j.result_id) {
        router.push(`/model/${j.result_id}`);
      } else {
        setStatus(`error: ${j.error ?? "unknown"}`);
        setBusy(false);
      }
    } catch (e) {
      setStatus(`generate failed: ${e}`);
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <h1 className="text-xl font-semibold">Create a 3D model</h1>

      {!upload ? (
        <Dropzone onFile={onFile} busy={busy} />
      ) : (
        <div className="mt-6 space-y-6">
          <PartMarker
            imageUrl={api.fileUrl("inputs", upload.url.split("/").pop()!)}
            imageWidth={upload.width}
            imageHeight={upload.height}
            parts={parts}
            onChange={setParts}
          />

          <div className="grid gap-4 rounded-lg border border-zinc-800 p-4 sm:grid-cols-2">
            <label className="text-sm">
              <span className="mb-1 block text-zinc-400">Name</span>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full rounded bg-zinc-800 px-2 py-1 outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </label>
            <label className="text-sm">
              <span className="mb-1 block text-zinc-400">Tags (comma separated)</span>
              <input
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder="pump, valve"
                className="w-full rounded bg-zinc-800 px-2 py-1 outline-none focus:ring-1 focus:ring-indigo-500"
              />
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={removeBg}
                onChange={(e) => setRemoveBg(e.target.checked)}
              />
              <span className="text-zinc-300">Remove background</span>
            </label>
            <label className="text-sm">
              <span className="mb-1 block text-zinc-400">
                Target faces (total): {targetFaces.toLocaleString()}
              </span>
              <input
                type="range"
                min={2000}
                max={150000}
                step={1000}
                value={targetFaces}
                onChange={(e) => setTargetFaces(Number(e.target.value))}
                className="w-full"
              />
            </label>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={generate}
              disabled={busy}
              className="rounded-md bg-indigo-500 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-400 disabled:opacity-50"
            >
              {busy ? "Working..." : `Generate (${parts.length || 1} part${parts.length === 1 ? "" : "s"})`}
            </button>
            <button
              onClick={suggestParts}
              disabled={busy}
              className="rounded-md border border-zinc-700 px-4 py-2 text-sm text-zinc-200 hover:bg-zinc-900 disabled:opacity-50"
            >
              Auto-suggest parts
            </button>
            <button
              onClick={() => { setUpload(null); setParts([]); }}
              className="rounded-md px-3 py-2 text-sm text-zinc-400 hover:text-zinc-100"
            >
              Start over
            </button>
            {status && <span className="text-sm text-zinc-400">{status}</span>}
          </div>
        </div>
      )}
    </div>
  );
}

function Dropzone({ onFile, busy }: { onFile: (f: File) => void; busy: boolean }) {
  const [over, setOver] = useState(false);
  return (
    <label
      onDragOver={(e) => { e.preventDefault(); setOver(true); }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setOver(false);
        const f = e.dataTransfer.files?.[0];
        if (f) onFile(f);
      }}
      className={`mt-6 flex h-64 cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed text-center transition ${
        over ? "border-indigo-400 bg-indigo-500/5" : "border-zinc-700 hover:border-zinc-500"
      }`}
    >
      <input
        type="file"
        accept="image/png,image/jpeg,image/webp"
        className="hidden"
        disabled={busy}
        onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])}
      />
      <p className="text-zinc-300">{busy ? "Uploading..." : "Drop an image here or click to browse"}</p>
      <p className="mt-1 text-xs text-zinc-600">PNG / JPG / WEBP</p>
    </label>
  );
}
