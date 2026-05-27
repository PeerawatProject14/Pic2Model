# Pic2Model

Turn product/equipment photos into **part-segmented 3D models (GLB)** for digital
twins. You mark which regions of the image are separate components; each becomes a
named node in the GLB so they're individually selectable in Three.js.

Runs entirely on your own machine, free. Designed to work **without** bleeding-edge
GPU setup — the segmentation is done on the 2D image (you mark parts), so no custom
CUDA kernels (no flash-attn, no PyTorch nightly) are required.

```
┌──────────┐   ┌───────────────┐   ┌───────────────┐   ┌────────────────┐
│  upload  │ → │ mark parts 2D │ → │ generate each │ → │ assemble GLB   │
│  image   │   │ (draw boxes)  │   │ part (TripoSR)│   │ w/ named nodes │
└──────────┘   └───────────────┘   └───────────────┘   └────────────────┘
                                                              ↓
                                                    viewer + part inspector
```

## Stack

| Layer        | Tech                                                        |
|--------------|-------------------------------------------------------------|
| Backend      | FastAPI + single-worker job queue + SQLite catalog          |
| Generation   | **mock** (default) or **TripoSR** (CPU or any CUDA GPU)     |
| BG removal   | **mock** (default) or **rembg**                             |
| Segmentation | manual 2D boxes (default) or **SAM2** auto-suggest          |
| Mesh         | trimesh (assembly/GLB) + pymeshlab (decimation/LOD)         |
| Frontend     | Next.js 15 (App Router) + Tailwind v4 + React Three Fiber   |

## Project layout

```
Pic2Model/
├── backend/            FastAPI app
│   ├── app/
│   │   ├── main.py             routes + CORS
│   │   ├── service.py          orchestration (upload→parts→assemble)
│   │   ├── jobs.py             background job queue
│   │   ├── db.py               SQLite catalog
│   │   ├── pipeline/           pluggable backends (mock / triposr / rembg / sam2)
│   │   └── routers/            upload, generate, catalog, files
│   ├── pyproject.toml
│   └── .env.example
├── frontend/           Next.js app
│   ├── app/            /create, /library, /model/[id]
│   ├── components/     PartMarker (box drawing), ModelViewer (R3F)
│   └── lib/api.ts      typed backend client
├── storage/            inputs / models (.glb) / thumbnails  + catalog.db
└── scripts/            dev + install helpers
```

## Quick start (mock pipeline — no ML, instant)

The default backends are mocks so you can drive the whole UI immediately.

**Terminal 1 — backend**
```bash
# Windows PowerShell
./scripts/dev-backend.ps1
# or Git Bash / WSL / mac / linux
bash scripts/dev-backend.sh
```

**Terminal 2 — frontend**
```bash
cd frontend
npm run dev
```

Open http://localhost:3000 → Create → drop an image → draw boxes → name parts →
Generate. You'll get a multi-part GLB you can inspect and download.

> The mock generator returns simple primitives (box/cylinder/sphere) per part —
> enough to verify the full upload→parts→assemble→view→download flow before you
> install the real models.

## Switch on the real models

Heavy download (~2.5GB for torch). Run once:

```bash
# Windows PowerShell
./scripts/install-ml.ps1
```

Then edit `backend/.env` (copy from `.env.example`):

```
PIC2MODEL_GENERATOR_BACKEND=triposr
PIC2MODEL_BG_BACKEND=rembg
PIC2MODEL_DEVICE=auto         # auto-detects CUDA, falls back to CPU
```

Restart the backend. First generation downloads the TripoSR weights from
Hugging Face (~1.5GB, cached afterward).

### RTX 5070 (Blackwell) note
TripoSR uses stock PyTorch — no custom CUDA kernels — so the cu124 wheel usually
works. If it fails to use the GPU on your driver, switch `install-ml.ps1` to the
nightly cu128 index (commented in the script), or set `PIC2MODEL_DEVICE=cpu` to
run on CPU (slower but always works).

## API summary

| Method | Path                     | Purpose                              |
|--------|--------------------------|--------------------------------------|
| POST   | `/api/upload`            | upload an image, returns `image_id`  |
| POST   | `/api/segment`           | auto-suggest 2D part boxes (optional)|
| POST   | `/api/generate`          | start a generation job               |
| GET    | `/api/jobs/{id}`         | poll job status/progress             |
| GET    | `/api/catalog`           | list models (`?q=` / `?tag=`)        |
| GET    | `/api/catalog/{id}`      | one model + its parts                |
| DELETE | `/api/catalog/{id}`      | delete                               |
| GET    | `/api/files/{kind}/{f}`  | serve inputs / models / thumbnails   |
| GET    | `/api/health`            | active backends                      |

## Tips for digital-twin assets
- **Reuse parts:** generate a common component (a specific motor/valve) once and
  keep it in the library; rebuild assemblies instead of regenerating.
- **Keep poly counts low:** the target-faces slider decimates for WebGL. 10–30k
  total is plenty for most twin scenes.
- **Name parts meaningfully** ("motor", "inlet_valve") — those names become the
  selectable node names in your Three.js scene.
