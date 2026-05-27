import Link from "next/link";

export default function Home() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-20">
      <h1 className="text-3xl font-semibold tracking-tight">
        Turn product photos into <span className="text-indigo-400">part-segmented</span> 3D
      </h1>
      <p className="mt-4 max-w-xl text-zinc-400">
        Upload a photo of equipment, mark which regions are separate components, and get a
        single GLB whose parts you can select individually in Three.js — built for digital
        twins.
      </p>
      <div className="mt-8 flex gap-3">
        <Link
          href="/create"
          className="rounded-md bg-indigo-500 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-400"
        >
          Create a model
        </Link>
        <Link
          href="/library"
          className="rounded-md border border-zinc-700 px-4 py-2 text-sm font-medium text-zinc-200 hover:bg-zinc-900"
        >
          Browse library
        </Link>
      </div>

      <ol className="mt-12 space-y-3 text-sm text-zinc-400">
        <li><span className="text-zinc-200">1.</span> Upload an image (optional background removal).</li>
        <li><span className="text-zinc-200">2.</span> Draw boxes around each part and name them.</li>
        <li><span className="text-zinc-200">3.</span> Generate → each part becomes a named node in the GLB.</li>
        <li><span className="text-zinc-200">4.</span> Inspect parts in the viewer; download for your scene.</li>
      </ol>
    </div>
  );
}
