"use client";

import { useRef, useState } from "react";
import type { PartSpec } from "@/lib/api";

interface Props {
  imageUrl: string;
  imageWidth: number;
  imageHeight: number;
  parts: PartSpec[];
  onChange: (parts: PartSpec[]) => void;
}

interface DragState {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

const COLORS = ["#6366f1", "#22c55e", "#f59e0b", "#ec4899", "#06b6d4", "#a855f7"];

// Lets the user draw bounding boxes over the image to define separate parts.
// Coordinates are stored in the image's native pixel space (not display space)
// so they line up with what the backend crops.
export default function PartMarker({
  imageUrl,
  imageWidth,
  imageHeight,
  parts,
  onChange,
}: Props) {
  const boxRef = useRef<HTMLDivElement>(null);
  const [drag, setDrag] = useState<DragState | null>(null);

  // map a pointer event to native image pixels
  function toImageCoords(e: React.PointerEvent) {
    const el = boxRef.current!;
    const rect = el.getBoundingClientRect();
    const sx = imageWidth / rect.width;
    const sy = imageHeight / rect.height;
    return {
      x: Math.max(0, Math.min(imageWidth, (e.clientX - rect.left) * sx)),
      y: Math.max(0, Math.min(imageHeight, (e.clientY - rect.top) * sy)),
    };
  }

  function onPointerDown(e: React.PointerEvent) {
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
    const { x, y } = toImageCoords(e);
    setDrag({ x0: x, y0: y, x1: x, y1: y });
  }
  function onPointerMove(e: React.PointerEvent) {
    if (!drag) return;
    const { x, y } = toImageCoords(e);
    setDrag({ ...drag, x1: x, y1: y });
  }
  function onPointerUp() {
    if (!drag) return;
    const x = Math.min(drag.x0, drag.x1);
    const y = Math.min(drag.y0, drag.y1);
    const w = Math.abs(drag.x1 - drag.x0);
    const h = Math.abs(drag.y1 - drag.y0);
    setDrag(null);
    if (w < 8 || h < 8) return; // ignore stray clicks
    onChange([
      ...parts,
      { name: `part_${parts.length + 1}`, bbox: [x, y, w, h], tags: [] },
    ]);
  }

  function updatePart(i: number, patch: Partial<PartSpec>) {
    onChange(parts.map((p, idx) => (idx === i ? { ...p, ...patch } : p)));
  }
  function removePart(i: number) {
    onChange(parts.filter((_, idx) => idx !== i));
  }

  // percentage helpers for absolute overlay positioning
  const pct = (v: number, total: number) => `${(v / total) * 100}%`;

  return (
    <div className="grid gap-4 md:grid-cols-[2fr_1fr]">
      <div
        ref={boxRef}
        className="relative max-h-[70vh] w-full select-none overflow-hidden rounded-lg border border-zinc-800 bg-zinc-950"
        style={{ aspectRatio: `${imageWidth} / ${imageHeight}`, touchAction: "none" }}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={imageUrl}
          alt="source"
          className="pointer-events-none absolute inset-0 h-full w-full object-contain"
          draggable={false}
        />
        {parts.map((p, i) =>
          p.bbox ? (
            <div
              key={i}
              className="absolute border-2"
              style={{
                left: pct(p.bbox[0], imageWidth),
                top: pct(p.bbox[1], imageHeight),
                width: pct(p.bbox[2], imageWidth),
                height: pct(p.bbox[3], imageHeight),
                borderColor: COLORS[i % COLORS.length],
                background: `${COLORS[i % COLORS.length]}22`,
              }}
            >
              <span
                className="absolute -top-5 left-0 whitespace-nowrap rounded px-1 text-[10px] font-medium text-white"
                style={{ background: COLORS[i % COLORS.length] }}
              >
                {p.name}
              </span>
            </div>
          ) : null
        )}
        {drag && (
          <div
            className="absolute border-2 border-dashed border-white/70 bg-white/10"
            style={{
              left: pct(Math.min(drag.x0, drag.x1), imageWidth),
              top: pct(Math.min(drag.y0, drag.y1), imageHeight),
              width: pct(Math.abs(drag.x1 - drag.x0), imageWidth),
              height: pct(Math.abs(drag.y1 - drag.y0), imageHeight),
            }}
          />
        )}
      </div>

      <div className="space-y-2">
        <p className="text-xs text-zinc-500">
          Drag on the image to add a part. No boxes = whole image as one mesh.
        </p>
        {parts.length === 0 && (
          <p className="rounded border border-dashed border-zinc-800 p-3 text-xs text-zinc-600">
            No parts yet.
          </p>
        )}
        {parts.map((p, i) => (
          <div
            key={i}
            className="flex items-center gap-2 rounded border border-zinc-800 bg-zinc-900/50 p-2"
          >
            <span
              className="h-3 w-3 shrink-0 rounded-full"
              style={{ background: COLORS[i % COLORS.length] }}
            />
            <input
              value={p.name}
              onChange={(e) => updatePart(i, { name: e.target.value })}
              className="w-full rounded bg-zinc-800 px-2 py-1 text-sm outline-none focus:ring-1 focus:ring-indigo-500"
            />
            <button
              onClick={() => removePart(i)}
              className="shrink-0 rounded px-2 py-1 text-xs text-zinc-400 hover:bg-zinc-800 hover:text-red-400"
            >
              ✕
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
