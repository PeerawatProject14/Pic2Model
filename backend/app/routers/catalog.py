from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from ..config import get_settings
from ..db import Catalog
from ..schemas import CatalogEntry

router = APIRouter(prefix="/api/catalog", tags=["catalog"])


def _catalog() -> Catalog:
    return Catalog(get_settings().db_path)


@router.get("", response_model=list[CatalogEntry])
def list_catalog(q: str | None = Query(None), tag: str | None = Query(None)) -> list[CatalogEntry]:
    return _catalog().list(query=q, tag=tag)


@router.get("/{entry_id}", response_model=CatalogEntry)
def get_entry(entry_id: str) -> CatalogEntry:
    entry = _catalog().get(entry_id)
    if not entry:
        raise HTTPException(404, "not found")
    return entry


@router.delete("/{entry_id}")
def delete_entry(entry_id: str) -> dict:
    ok = _catalog().delete(entry_id)
    if not ok:
        raise HTTPException(404, "not found")
    return {"deleted": entry_id}
