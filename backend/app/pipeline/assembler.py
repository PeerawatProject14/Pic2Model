"""Assemble per-part meshes into one GLB with a named scene graph.

Each part becomes a named node so the frontend (Three.js / R3F) can select and
highlight individual components — the core digital-twin requirement.
"""
from __future__ import annotations

import re

import numpy as np
import trimesh


def _safe_node_name(name: str, used: set[str]) -> str:
    base = re.sub(r"[^A-Za-z0-9_]", "_", name).strip("_") or "part"
    node = base
    i = 1
    while node in used:
        i += 1
        node = f"{base}_{i}"
    used.add(node)
    return node


def normalize_and_place(mesh: trimesh.Trimesh, anchor_2d: tuple[float, float] | None = None,
                        image_size: tuple[int, int] | None = None) -> trimesh.Trimesh:
    """Center a part at origin and (optionally) offset it using its 2D anchor so
    multi-part assemblies start roughly aligned. The user fine-tunes in the UI.
    """
    mesh = mesh.copy()
    mesh.apply_translation(-mesh.centroid)
    # Scale to unit-ish so different parts are comparable.
    scale = float(np.max(mesh.extents)) or 1.0
    mesh.apply_scale(1.0 / scale)

    if anchor_2d and image_size:
        w, h = image_size
        ax, ay = anchor_2d
        # Map image coords -> world XY (origin at image center, y up).
        ox = (ax / w - 0.5) * 2.0
        oy = (0.5 - ay / h) * 2.0
        mesh.apply_translation([ox, oy, 0.0])
    return mesh


def assemble_glb(
    parts: list[dict],
    out_path: str,
) -> dict:
    """parts: list of {name, mesh, anchor_2d?, image_size?, tags?}

    Returns metadata: {faces, parts: [{name, node, faces, tags}]}
    """
    scene = trimesh.Scene()
    used: set[str] = set()
    meta_parts = []
    total_faces = 0

    for part in parts:
        mesh: trimesh.Trimesh = part["mesh"]
        placed = normalize_and_place(
            mesh, part.get("anchor_2d"), part.get("image_size")
        )
        # Smooth shading: averaged per-vertex normals so the surface shades
        # continuously instead of showing flat triangle facets in the viewer.
        try:
            placed.fix_normals()
            _ = placed.vertex_normals  # force compute + cache smooth normals
        except Exception:
            pass
        node = _safe_node_name(part["name"], used)
        scene.add_geometry(placed, node_name=node, geom_name=node)
        faces = int(len(placed.faces))
        total_faces += faces
        meta_parts.append(
            {"name": part["name"], "node": node, "faces": faces, "tags": part.get("tags", [])}
        )

    scene.export(out_path)  # .glb inferred from extension
    return {"faces": total_faces, "parts": meta_parts}
