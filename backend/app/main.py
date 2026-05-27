from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .routers import catalog, files, generate, upload

settings = get_settings()

app = FastAPI(title="Pic2Model", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(generate.router)
app.include_router(catalog.router)
app.include_router(files.router)


@app.get("/api/health")
def health() -> dict:
    return {
        "status": "ok",
        "backends": {
            "generator": settings.generator_backend,
            "bg": settings.bg_backend,
            "segmenter": settings.segmenter_backend,
            "device": settings.device,
        },
    }
