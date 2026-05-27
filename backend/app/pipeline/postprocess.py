"""Mesh post-processing: decimation for WebGL-friendly poly counts.

Uses pymeshlab if available (best quality); otherwise falls back to trimesh's
quadric decimation, which is fine for the mock path and CPU-only setups.
"""
from __future__ import annotations

import trimesh


def decimate(mesh: trimesh.Trimesh, target_faces: int) -> trimesh.Trimesh:
    if target_faces <= 0 or len(mesh.faces) <= target_faces:
        return mesh

    # Try pymeshlab first.
    try:
        import numpy as np
        import pymeshlab  # type: ignore

        ms = pymeshlab.MeshSet()
        ms.add_mesh(pymeshlab.Mesh(np.asarray(mesh.vertices), np.asarray(mesh.faces)))
        ms.meshing_decimation_quadric_edge_collapse(targetfacenum=int(target_faces))
        m = ms.current_mesh()
        out = trimesh.Trimesh(
            vertices=m.vertex_matrix(), faces=m.face_matrix(), process=False
        )
        if hasattr(mesh.visual, "vertex_colors"):
            # colors don't survive decimation cleanly; keep a flat color
            out.visual.vertex_colors = mesh.visual.vertex_colors[0] if len(
                mesh.visual.vertex_colors
            ) else [180, 180, 180, 255]
        return out
    except Exception:
        pass

    # Fallback: trimesh quadric decimation (requires fast-simplification or open3d
    # in some versions; guard it).
    try:
        return mesh.simplify_quadric_decimation(face_count=int(target_faces))
    except Exception:
        return mesh
