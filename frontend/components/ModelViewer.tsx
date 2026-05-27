"use client";

import { Bounds, GizmoHelper, GizmoViewport, Grid, OrbitControls, useGLTF } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { Suspense, useEffect, useMemo, useState } from "react";
import * as THREE from "three";

interface Props {
  url: string;
  selectedNode: string | null;
  hiddenNodes: Set<string>;
  onSelect: (node: string | null) => void;
}

const HILITE = new THREE.Color("#6366f1");

function Model({ url, selectedNode, hiddenNodes, onSelect }: Props) {
  const { scene } = useGLTF(url);

  // Clone so multiple viewers / re-renders don't fight over one graph.
  const root = useMemo(() => scene.clone(true), [scene]);

  // Cache original materials so we can restore after highlight.
  const originals = useMemo(() => {
    const map = new Map<string, THREE.Material | THREE.Material[]>();
    root.traverse((o) => {
      const m = o as THREE.Mesh;
      if (m.isMesh) map.set(m.uuid, m.material);
    });
    return map;
  }, [root]);

  useEffect(() => {
    root.traverse((o) => {
      const m = o as THREE.Mesh;
      if (!m.isMesh) return;
      const nodeName = topLevelName(m, root);
      m.visible = !hiddenNodes.has(nodeName);

      const orig = originals.get(m.uuid);
      if (selectedNode && nodeName === selectedNode) {
        const hl = new THREE.MeshStandardMaterial({
          color: HILITE,
          emissive: HILITE.clone().multiplyScalar(0.4),
          metalness: 0.1,
          roughness: 0.6,
        });
        m.material = hl;
      } else if (orig) {
        m.material = orig;
      }
    });
  }, [root, selectedNode, hiddenNodes, originals]);

  return (
    <primitive
      object={root}
      onPointerDown={(e: any) => {
        e.stopPropagation();
        const node = topLevelName(e.object, root);
        onSelect(node || null);
      }}
    />
  );
}

// Walk up to the named child of the scene root (our per-part node).
function topLevelName(obj: THREE.Object3D, root: THREE.Object3D): string {
  let cur: THREE.Object3D | null = obj;
  let name = obj.name;
  while (cur && cur.parent && cur.parent !== root) {
    cur = cur.parent;
    if (cur.name) name = cur.name;
  }
  return name;
}

export default function ModelViewer(props: Props) {
  return (
    <Canvas camera={{ position: [2.5, 2, 2.5], fov: 45 }} dpr={[1, 2]}>
      <color attach="background" args={["#0a0a0b"]} />
      <ambientLight intensity={0.6} />
      <directionalLight position={[5, 8, 5]} intensity={1.2} />
      <directionalLight position={[-5, -2, -5]} intensity={0.3} />
      <Suspense fallback={null}>
        <Bounds fit clip observe margin={1.2}>
          <Model {...props} />
        </Bounds>
      </Suspense>
      <Grid
        args={[20, 20]}
        cellColor="#27272a"
        sectionColor="#3f3f46"
        fadeDistance={25}
        infiniteGrid
        position={[0, -1, 0]}
      />
      <OrbitControls makeDefault enableDamping />
      <GizmoHelper alignment="bottom-right" margin={[60, 60]}>
        <GizmoViewport axisColors={["#ef4444", "#22c55e", "#3b82f6"]} labelColor="white" />
      </GizmoHelper>
    </Canvas>
  );
}
