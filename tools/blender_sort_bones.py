#!/usr/bin/env python3
"""Blender-side step 4 bone sorting and merge helper."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import bpy


DEFAULT_LIMIT = 254
VALVEBIPED_PREFIX = "ValveBiped"
HEAD = "ValveBiped.Bip01_Head1"
PELVIS = "ValveBiped.Bip01_Pelvis"
SPINE = "ValveBiped.Bip01_Spine"
SPINE1 = "ValveBiped.Bip01_Spine1"
SPINE2 = "ValveBiped.Bip01_Spine2"
SPINE4 = "ValveBiped.Bip01_Spine4"
NECK = "ValveBiped.Bip01_Neck1"
R_CLAVICLE = "ValveBiped.Bip01_R_Clavicle"
L_CLAVICLE = "ValveBiped.Bip01_L_Clavicle"
R_THIGH = "ValveBiped.Bip01_R_Thigh"
L_THIGH = "ValveBiped.Bip01_L_Thigh"
SPINE_CHAIN = [PELVIS, SPINE, SPINE1, SPINE2, SPINE4]
SPINE_ATTACHMENTS = [NECK, R_CLAVICLE, L_CLAVICLE]
SPINE_TARGET_PARENTS = {
    PELVIS: None,
    SPINE: PELVIS,
    SPINE1: SPINE,
    SPINE2: SPINE1,
    SPINE4: SPINE2,
    NECK: SPINE4,
    R_CLAVICLE: SPINE4,
    L_CLAVICLE: SPINE4,
}
BASE_PROTECTED_BONES = {
    "ZArmTwist_L",
    "ZArmTwist_R",
    "ZHandTwist_L",
    "ZHandTwist_R",
    "Eye_L",
    "Eye_R",
}
FACE_ROOT_HINTS = {
    "face_head",
    "facehead",
    "face",
}
FACE_NAME_HINTS = (
    "face",
    "nose",
    "tongue",
    "jaw",
    "tooth",
    "teeth",
    "mouth",
    "lip",
    "brow",
    "eyebrow",
    "eyelid",
    "cheek",
    "beak",
)
SAFE_BONE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")
SOURCE_BONE_NAME_PATTERN = re.compile(r"^ValveBiped\.Bip01_[A-Za-z0-9_]+$")


def parse_args() -> argparse.Namespace:
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1 :]
    else:
        argv = []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("analyze", "apply"), required=True)
    parser.add_argument("--input-blend", type=Path, required=True)
    parser.add_argument("--analysis-json", type=Path)
    parser.add_argument("--plan-json", type=Path, required=True)
    parser.add_argument("--output-blend", type=Path)
    parser.add_argument("--report-json", type=Path)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    return parser.parse_args(argv)


def ensure_object_mode() -> None:
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode="OBJECT")


def armatures() -> list[bpy.types.Object]:
    return [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]


def mesh_objects() -> list[bpy.types.Object]:
    return [obj for obj in bpy.data.objects if obj.type == "MESH"]


def active_armature() -> bpy.types.Object:
    candidates = armatures()
    if not candidates:
        raise RuntimeError("No armature found in the spine-fixed blend file.")
    candidates.sort(key=lambda obj: len(obj.data.bones), reverse=True)
    armature = candidates[0]
    ensure_object_mode()
    bpy.ops.object.select_all(action="DESELECT")
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    return armature


def associated_meshes(armature: bpy.types.Object) -> list[bpy.types.Object]:
    meshes: list[bpy.types.Object] = []
    for obj in mesh_objects():
        for modifier in obj.modifiers:
            if isinstance(modifier, bpy.types.ArmatureModifier) and modifier.object == armature and modifier.use_vertex_groups:
                meshes.append(obj)
                break
    return meshes or mesh_objects()


def v3(value: Iterable[float]) -> list[float]:
    vector = list(value)
    return [round(float(vector[0]), 6), round(float(vector[1]), 6), round(float(vector[2]), 6)]


def parent_map(armature: bpy.types.Object) -> dict[str, str | None]:
    return {bone.name: bone.parent.name if bone.parent else None for bone in armature.data.bones}


def children_map_from_parents(parents: dict[str, str | None], existing: set[str] | None = None) -> dict[str | None, list[str]]:
    existing = existing or set(parents)
    children: dict[str | None, list[str]] = defaultdict(list)
    for name, parent in parents.items():
        if name not in existing:
            continue
        children[parent if parent in existing else None].append(name)
    for values in children.values():
        values.sort(key=natural_key)
    return children


def depth_map_from_parents(parents: dict[str, str | None], existing: set[str] | None = None) -> dict[str, int]:
    existing = existing or set(parents)
    cache: dict[str, int] = {}

    def depth(name: str) -> int:
        if name in cache:
            return cache[name]
        parent = parents.get(name)
        if not parent or parent not in existing or parent == name:
            cache[name] = 0
            return 0
        cache[name] = depth(parent) + 1
        return cache[name]

    for name in existing:
        depth(name)
    return cache


def ancestors(name: str, parents: dict[str, str | None]) -> list[str]:
    out: list[str] = []
    current: str | None = name
    seen: set[str] = set()
    while current and current not in seen:
        out.append(current)
        seen.add(current)
        current = parents.get(current)
    return out


def descendant_names(root: str, children: dict[str | None, list[str]]) -> list[str]:
    out: list[str] = []

    def visit(name: str) -> None:
        for child in children.get(name, []):
            out.append(child)
            visit(child)

    visit(root)
    return out


def normalized_name(name: str) -> str:
    return name.lower().replace(" ", "").replace("-", "_").replace(".", "_")


def natural_key(name: str) -> tuple[object, ...]:
    parts = re.split(r"(\d+)", name.lower())
    return tuple(int(part) if part.isdigit() else part for part in parts)


def is_source_bone(name: str) -> bool:
    return name.startswith(VALVEBIPED_PREFIX)


def is_protected_bone(name: str, extra: set[str] | None = None) -> bool:
    return is_source_bone(name) or name in BASE_PROTECTED_BONES or bool(extra and name in extra)


def is_safe_bone_name(name: str) -> bool:
    return bool(SAFE_BONE_NAME_PATTERN.fullmatch(name) or SOURCE_BONE_NAME_PATTERN.fullmatch(name))


def vertex_group_weight_totals() -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for obj in mesh_objects():
        index_to_name = {group.index: group.name for group in obj.vertex_groups}
        for vertex in obj.data.vertices:
            for group in vertex.groups:
                if group.weight <= 0.000001:
                    continue
                name = index_to_name.get(group.group)
                if name:
                    totals[name] += float(group.weight)
    return dict(totals)


def collect_bones(armature: bpy.types.Object, weight_totals: dict[str, float]) -> list[dict[str, object]]:
    parents = parent_map(armature)
    depths = depth_map_from_parents(parents)
    bones: list[dict[str, object]] = []
    for index, bone in enumerate(armature.data.bones):
        bones.append(
            {
                "index": index,
                "name": bone.name,
                "parent": bone.parent.name if bone.parent else None,
                "children": [child.name for child in bone.children],
                "head": v3(bone.head_local),
                "tail": v3(bone.tail_local),
                "depth": depths.get(bone.name, 0),
                "use_connect": bool(bone.use_connect),
                "use_deform": bool(bone.use_deform),
                "has_weights": weight_totals.get(bone.name, 0.0) > 0.000001,
                "weight_total": round(float(weight_totals.get(bone.name, 0.0)), 6),
                "protected": is_protected_bone(bone.name),
            }
        )
    return bones


def collect_model_preview(armature: bpy.types.Object, max_vertices: int = 7000, max_edges: int = 8000) -> dict[str, object]:
    vertices: list[list[float]] = []
    edges: list[tuple[int, int]] = []
    to_armature = armature.matrix_world.inverted()
    for obj in mesh_objects():
        offset = len(vertices)
        transform = to_armature @ obj.matrix_world
        for vertex in obj.data.vertices:
            vertices.append(v3(transform @ vertex.co))
        for edge in obj.data.edges:
            a, b = edge.vertices[:]
            edges.append((offset + int(a), offset + int(b)))

    if not vertices:
        return {"vertices": [], "edges": [], "source_vertex_count": 0, "source_edge_count": 0, "sample_stride": 1}

    sampled_vertices: list[list[float]] = []
    index_map: dict[int, int] = {}

    def add_vertex(index: int) -> int | None:
        if index in index_map:
            return index_map[index]
        if len(sampled_vertices) >= max_vertices:
            return None
        index_map[index] = len(sampled_vertices)
        sampled_vertices.append(vertices[index])
        return index_map[index]

    edge_stride = max(1, math.ceil(len(edges) / max(1, max_edges)))
    sampled_edges: list[list[int]] = []
    for a, b in edges[::edge_stride]:
        mapped_a = add_vertex(a)
        mapped_b = add_vertex(b)
        if mapped_a is None or mapped_b is None or mapped_a == mapped_b:
            continue
        sampled_edges.append([mapped_a, mapped_b])
        if len(sampled_edges) >= max_edges:
            break

    point_stride = max(1, math.ceil(len(vertices) / max(1, max_vertices)))
    for index in range(0, len(vertices), point_stride):
        if len(sampled_vertices) >= max_vertices:
            break
        add_vertex(index)

    return {
        "vertices": sampled_vertices,
        "edges": sampled_edges,
        "source_vertex_count": len(vertices),
        "source_edge_count": len(edges),
        "sample_stride": point_stride,
        "edge_sample_stride": edge_stride,
    }


def face_source_names(parents: dict[str, str | None], existing: set[str], protected: set[str]) -> set[str]:
    if HEAD not in existing:
        return set()
    head_descendants = set(ancestors(name, parents)[0] for name in existing if HEAD in ancestors(name, parents)[1:])
    roots: set[str] = set()
    children = children_map_from_parents(parents, existing)
    for child in children.get(HEAD, []):
        if child in protected:
            continue
        normalized = normalized_name(child)
        if any(hint in normalized for hint in FACE_ROOT_HINTS):
            roots.add(child)
        elif any(hint in normalized for hint in FACE_NAME_HINTS):
            roots.add(child)
    out: set[str] = set()
    for root in roots:
        out.add(root)
        out.update(descendant_names(root, children))
    for name in head_descendants:
        if name in protected:
            continue
        normalized = normalized_name(name)
        if any(hint in normalized for hint in FACE_NAME_HINTS):
            out.add(name)
    return {name for name in out if name in existing and name not in protected}


def chain_roots(parents: dict[str, str | None], existing: set[str], protected: set[str]) -> list[str]:
    roots: list[str] = []
    for name in sorted(existing, key=natural_key):
        if name in protected:
            continue
        parent = parents.get(name)
        if parent is None or parent not in existing or parent in protected:
            roots.append(name)
    return roots


def linear_chain_from(root: str, children: dict[str | None, list[str]], protected: set[str], excluded: set[str]) -> list[str]:
    chain = [root]
    current = root
    while True:
        candidates = [child for child in children.get(current, []) if child not in protected and child not in excluded]
        if len(candidates) != 1:
            break
        current = candidates[0]
        chain.append(current)
    return chain


def collect_linear_chains(
    parents: dict[str, str | None],
    existing: set[str],
    protected: set[str],
    excluded: set[str],
) -> list[list[str]]:
    children = children_map_from_parents(parents, existing)
    chains: list[list[str]] = []
    visited: set[str] = set()

    def walk(node: str) -> None:
        if node in visited or node in protected or node in excluded or node not in existing:
            return
        chain = linear_chain_from(node, children, protected, excluded)
        visited.update(chain)
        if len(chain) >= 3:
            chains.append(chain)
        tail = chain[-1]
        for child in children.get(tail, []):
            if child not in visited:
                walk(child)
        if len(chain) == 1:
            for child in children.get(node, []):
                if child not in visited:
                    walk(child)

    for root in chain_roots(parents, existing, protected):
        walk(root)
    return chains


def operation(
    round_index: int,
    order: int,
    source: str,
    target: str,
    branch: str,
    reason: str,
    depth: int,
) -> dict[str, object]:
    return {
        "round": round_index,
        "order": order,
        "source": source,
        "target": target,
        "branch": branch,
        "reason": reason,
        "depth": depth,
        "enabled": True,
        "warnings": [],
    }


def simulate_operations(
    parents: dict[str, str | None],
    existing: set[str],
    operations: list[dict[str, object]],
) -> None:
    children = children_map_from_parents(parents, existing)
    for raw in operations:
        source = str(raw.get("source") or "")
        target = str(raw.get("target") or "")
        if source not in existing or target not in existing or source == target:
            continue
        for child in list(children.get(source, [])):
            if child in existing and child != target:
                parents[child] = target
        parents.pop(source, None)
        existing.remove(source)
        children = children_map_from_parents(parents, existing)


def automatic_plan(armature: bpy.types.Object, limit: int) -> dict[str, object]:
    original_parents = parent_map(armature)
    simulated_parents = dict(original_parents)
    existing = set(simulated_parents)
    extra_protected: set[str] = set()
    protected = {name for name in existing if is_protected_bone(name, extra_protected)}
    original_depths = depth_map_from_parents(original_parents, existing)
    weight_totals = vertex_group_weight_totals()
    operations: list[dict[str, object]] = []
    rounds: list[dict[str, object]] = []
    warnings: list[str] = []
    max_rounds = 20
    round_index = 1

    while len(existing) > limit and round_index <= max_rounds:
        round_ops: list[dict[str, object]] = []
        used_sources: set[str] = set()
        order = 0
        protected = {name for name in existing if is_protected_bone(name, extra_protected)}

        face_sources = face_source_names(simulated_parents, existing, protected)
        if face_sources:
            depths = depth_map_from_parents(simulated_parents, existing)
            for source in sorted(face_sources, key=lambda name: (-depths.get(name, 0), natural_key(name))):
                if source in used_sources or source not in existing or HEAD not in existing:
                    continue
                round_ops.append(operation(round_index, order, source, HEAD, "Head face detail", "merge nonessential face/head detail into Head1", depths.get(source, 0)))
                used_sources.add(source)
                order += 1

        excluded = set(face_sources)
        chains = collect_linear_chains(simulated_parents, existing, protected, excluded)
        for chain in chains:
            if len(existing) - len(round_ops) <= limit and operations:
                break
            branch = chain[0]
            for index in range(1, len(chain), 2):
                source = chain[index]
                target = chain[index - 1]
                if source in used_sources or source not in existing or target not in existing:
                    continue
                reason = "alternating accessory-chain decimation"
                if round_index > 1:
                    reason = f"round {round_index} accessory-chain decimation"
                round_ops.append(operation(round_index, order, source, target, branch, reason, original_depths.get(source, 0)))
                used_sources.add(source)
                order += 1

        if not round_ops:
            fallback_ops = fallback_leaf_operations(simulated_parents, existing, protected, round_index, limit, original_depths)
            round_ops.extend(fallback_ops)

        if not round_ops:
            warnings.append("No safe merge candidates remain before reaching the requested bone limit.")
            break

        before = len(existing)
        simulate_operations(simulated_parents, existing, round_ops)
        after = len(existing)
        operations.extend(round_ops)
        rounds.append(
            {
                "round": round_index,
                "operation_count": len(round_ops),
                "before_count": before,
                "after_count": after,
            }
        )
        if after >= before:
            warnings.append("Merge planning stopped because a simulated round did not reduce bone count.")
            break
        round_index += 1

    if len(existing) > limit:
        warnings.append(f"Estimated final bone count {len(existing)} remains above limit {limit}.")

    return {
        "version": 1,
        "kind": "sort_bones",
        "armature": armature.name,
        "bone_limit": limit,
        "initial_bone_count": len(original_parents),
        "estimated_final_bone_count": len(existing),
        "protected_bones": sorted(protected),
        "base_protected_bones": sorted(BASE_PROTECTED_BONES),
        "protected_prefixes": [VALVEBIPED_PREFIX],
        "operations": operations,
        "rounds": rounds,
        "warnings": warnings,
        "weight_totals_before": {name: round(value, 6) for name, value in sorted(weight_totals.items())},
    }


def fallback_leaf_operations(
    parents: dict[str, str | None],
    existing: set[str],
    protected: set[str],
    round_index: int,
    limit: int,
    depths: dict[str, int],
) -> list[dict[str, object]]:
    children = children_map_from_parents(parents, existing)
    leaves = [
        name
        for name in existing
        if name not in protected
        and parents.get(name) in existing
        and name not in children
        and parents.get(name) != name
    ]
    leaves.sort(key=lambda name: (-depths.get(name, 0), natural_key(name)))
    ops: list[dict[str, object]] = []
    order = 0
    for source in leaves:
        if len(existing) - len(ops) <= limit:
            break
        target = parents.get(source)
        if not target or target not in existing:
            continue
        ops.append(operation(round_index, order, source, target, target, "limit pressure fallback leaf merge", depths.get(source, 0)))
        order += 1
    return ops


def spine_validation(armature: bpy.types.Object) -> dict[str, object]:
    bones = {bone.name: bone for bone in armature.data.bones}
    names = [bone.name for bone in armature.data.bones]
    indexes = {name: index for index, name in enumerate(names)}
    errors: list[str] = []
    warnings: list[str] = []
    for target in SPINE_CHAIN + SPINE_ATTACHMENTS:
        if target not in bones:
            errors.append(f"Missing required spine/source bone: {target}")
    for target, parent in SPINE_TARGET_PARENTS.items():
        if target not in bones or parent is None:
            continue
        actual = bones[target].parent.name if bones[target].parent else None
        if actual != parent:
            errors.append(f"{target} must be parented to {parent}; current parent is {actual or '<none>'}.")
        if parent in indexes and indexes[parent] > indexes[target]:
            errors.append(f"{parent} appears after child {target} in armature.data.bones order.")

    def side_check(right: str, left: str, label: str) -> None:
        if right not in bones or left not in bones:
            warnings.append(f"Could not validate {label} side because a landmark is missing.")
            return
        if float(bones[right].head_local.x) >= float(bones[left].head_local.x):
            errors.append(f"{label} side appears swapped: expected {right} on negative X and {left} on positive X.")

    side_check(R_CLAVICLE, L_CLAVICLE, "clavicle")
    side_check(R_THIGH, L_THIGH, "leg")
    return {"ok": not errors, "errors": errors, "warnings": warnings}


def current_validation(armature: bpy.types.Object, limit: int, protected: set[str] | None = None) -> dict[str, object]:
    protected = protected or {bone.name for bone in armature.data.bones if is_protected_bone(bone.name)}
    names = {bone.name for bone in armature.data.bones}
    errors: list[str] = []
    warnings: list[str] = []
    if len(names) > limit:
        errors.append(f"Bone count {len(names)} is above Source limit {limit}.")
    missing = sorted(name for name in protected if name not in names)
    if missing:
        errors.append("Protected bones are missing: " + ", ".join(missing[:16]))
    unsafe = [name for name in names if not is_safe_bone_name(name)]
    if unsafe:
        errors.append("Unsafe bone names remain: " + ", ".join(sorted(unsafe)[:16]))
    spine = spine_validation(armature)
    errors.extend(str(error) for error in spine["errors"])
    warnings.extend(str(warning) for warning in spine["warnings"])
    return {"ok": not errors, "errors": errors, "warnings": warnings}


def analyze_current_file(input_blend: Path, limit: int) -> tuple[dict[str, object], dict[str, object]]:
    armature = active_armature()
    weights = vertex_group_weight_totals()
    plan = automatic_plan(armature, limit)
    protected = set(str(name) for name in plan.get("protected_bones", []) if name)
    validation = current_validation(armature, limit, protected)
    bones = collect_bones(armature, weights)
    analysis = {
        "version": 1,
        "kind": "sort_bones",
        "input_blend": str(input_blend),
        "armature": armature.name,
        "object_count": len(bpy.data.objects),
        "mesh_object_count": len(mesh_objects()),
        "bone_count": len(armature.data.bones),
        "bone_limit": limit,
        "weighted_bone_count": sum(1 for value in weights.values() if value > 0.000001),
        "unsafe_bone_names": [bone.name for bone in armature.data.bones if not is_safe_bone_name(bone.name)],
        "bones": bones,
        "model_preview": collect_model_preview(armature),
        "current_validation": validation,
        "proposal": plan,
    }
    plan["input_blend"] = str(input_blend)
    return analysis, plan


def load_plan(path: Path) -> dict[str, object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError("Bone merge plan JSON must be an object.")
    return data


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def enabled_operations(plan: dict[str, object]) -> list[dict[str, object]]:
    raw = plan.get("operations", [])
    if not isinstance(raw, list):
        raise RuntimeError("Invalid bone merge plan: operations must be a list.")
    operations = [entry for entry in raw if isinstance(entry, dict) and entry.get("enabled", True)]
    operations.sort(key=lambda entry: (int(entry.get("round", 0)), int(entry.get("order", 0)), -int(entry.get("depth", 0))))
    return operations


def protected_from_plan(plan: dict[str, object], armature: bpy.types.Object) -> set[str]:
    raw = plan.get("protected_bones", [])
    protected = {bone.name for bone in armature.data.bones if is_protected_bone(bone.name)}
    if isinstance(raw, list):
        protected.update(str(name) for name in raw if name)
    return protected


def ensure_target_vertex_groups(armature: bpy.types.Object, target: str) -> None:
    for obj in associated_meshes(armature):
        if target not in obj.vertex_groups:
            obj.vertex_groups.new(name=target)


def transfer_vertex_groups(armature: bpy.types.Object, source: str, target: str) -> dict[str, float]:
    transferred: dict[str, float] = {}
    ensure_object_mode()
    for obj in associated_meshes(armature):
        if source not in obj.vertex_groups:
            continue
        if target not in obj.vertex_groups:
            obj.vertex_groups.new(name=target)
        source_group = obj.vertex_groups[source]
        target_group = obj.vertex_groups[target]
        source_index = source_group.index
        total = 0.0
        cached: list[tuple[int, float]] = []
        for vertex in obj.data.vertices:
            for group in vertex.groups:
                if group.group == source_index and group.weight > 0.000001:
                    cached.append((vertex.index, float(group.weight)))
                    total += float(group.weight)
                    break
        for vertex_index, weight in cached:
            target_group.add([vertex_index], weight, "ADD")
        obj.vertex_groups.remove(source_group)
        transferred[obj.name] = round(total, 6)
    return transferred


def delete_bone_internal(armature: bpy.types.Object, source: str, target: str) -> None:
    ensure_object_mode()
    bpy.ops.object.select_all(action="DESELECT")
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.mode_set(mode="EDIT")
    try:
        edit_bones = armature.data.edit_bones
        source_bone = edit_bones.get(source)
        target_bone = edit_bones.get(target)
        if source_bone is None or target_bone is None:
            return
        for child in list(source_bone.children):
            child.parent = target_bone
            child.use_connect = False
        edit_bones.remove(source_bone)
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")


def deselect_all_edit_bones(edit_bones) -> None:
    for bone in edit_bones:
        bone.select = False
        bone.select_head = False
        bone.select_tail = False


def addon_merge_bone(armature: bpy.types.Object, source: str, target: str) -> bool:
    try:
        bpy.ops.armature.voyage_vrsns_merge_bones.get_rna_type()
    except Exception:
        return False
    ensure_target_vertex_groups(armature, target)
    ensure_object_mode()
    bpy.ops.object.select_all(action="DESELECT")
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    old_mirror = bool(getattr(armature.data, "use_mirror_x", False))
    armature.data.use_mirror_x = False
    bpy.ops.object.mode_set(mode="EDIT")
    try:
        edit_bones = armature.data.edit_bones
        source_bone = edit_bones.get(source)
        target_bone = edit_bones.get(target)
        if source_bone is None or target_bone is None:
            return False
        deselect_all_edit_bones(edit_bones)
        target_bone.select = True
        target_bone.select_head = True
        target_bone.select_tail = True
        source_bone.select = True
        source_bone.select_head = True
        source_bone.select_tail = True
        edit_bones.active = target_bone
        result = bpy.ops.armature.voyage_vrsns_merge_bones()
        return "FINISHED" in result and source not in armature.data.edit_bones
    except Exception as exc:
        print(f"Blender Bones Merger failed for {source} -> {target}: {exc}")
        return False
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")
        armature.data.use_mirror_x = old_mirror


def merge_bone(armature: bpy.types.Object, source: str, target: str, protected: set[str]) -> dict[str, object]:
    if source == target:
        return {"source": source, "target": target, "status": "skipped", "reason": "source equals target"}
    bones = {bone.name for bone in armature.data.bones}
    if source not in bones:
        return {"source": source, "target": target, "status": "skipped", "reason": "source missing"}
    if target not in bones:
        return {"source": source, "target": target, "status": "error", "reason": "target missing"}
    if source in protected:
        return {"source": source, "target": target, "status": "error", "reason": "source is protected"}

    before_weights = vertex_group_weight_totals()
    method = "addon"
    if not addon_merge_bone(armature, source, target):
        method = "internal"
        transferred = transfer_vertex_groups(armature, source, target)
        delete_bone_internal(armature, source, target)
    else:
        transferred = {}
    after_bones = {bone.name for bone in armature.data.bones}
    if source in after_bones:
        return {"source": source, "target": target, "status": "error", "reason": "source bone still exists after merge", "method": method}
    after_weights = vertex_group_weight_totals()
    return {
        "source": source,
        "target": target,
        "status": "merged",
        "method": method,
        "source_weight_before": round(float(before_weights.get(source, 0.0)), 6),
        "target_weight_before": round(float(before_weights.get(target, 0.0)), 6),
        "target_weight_after": round(float(after_weights.get(target, 0.0)), 6),
        "internal_transferred_by_mesh": transferred,
    }


def validate_after_apply(
    armature: bpy.types.Object,
    plan: dict[str, object],
    applied: list[dict[str, object]],
    limit: int,
    protected: set[str],
    before_weights: dict[str, float],
) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    names = {bone.name for bone in armature.data.bones}
    if len(names) > limit:
        errors.append(f"Final bone count {len(names)} is above Source limit {limit}.")
    missing = sorted(name for name in protected if name not in names)
    if missing:
        errors.append("Protected bones are missing after merge: " + ", ".join(missing[:16]))

    for result in applied:
        if result.get("status") == "error":
            errors.append(f"{result.get('source')} -> {result.get('target')}: {result.get('reason')}")
    for obj in mesh_objects():
        existing_groups = {group.name for group in obj.vertex_groups}
        for result in applied:
            source = str(result.get("source") or "")
            if result.get("status") == "merged" and source in existing_groups:
                errors.append(f"Removed source vertex group remains on {obj.name}: {source}")

    merged_edges: dict[str, str] = {}
    for result in applied:
        if result.get("status") != "merged":
            continue
        source = str(result.get("source") or "")
        target = str(result.get("target") or "")
        if source and target:
            merged_edges[source] = target

    def final_merge_target(name: str) -> str:
        seen: set[str] = set()
        current = name
        while current in merged_edges:
            if current in seen:
                cycle = " -> ".join(list(seen) + [current])
                errors.append(f"Bone merge plan contains a cycle: {cycle}")
                return current
            seen.add(current)
            current = merged_edges[current]
        return current

    expected_source_by_final: dict[str, float] = defaultdict(float)
    expected_total_by_final: dict[str, float] = defaultdict(float)
    involved_names = set(merged_edges.keys()) | set(merged_edges.values())
    for name in involved_names:
        final_target = final_merge_target(name)
        expected_total_by_final[final_target] += float(before_weights.get(name, 0.0))
    for source in merged_edges:
        final_target = final_merge_target(source)
        expected_source_by_final[final_target] += float(before_weights.get(source, 0.0))

    after_weights = vertex_group_weight_totals()
    for target, source_total in expected_source_by_final.items():
        if source_total <= 0.000001:
            warnings.append(f"{target} received only unweighted or zero-weight source bones.")
            continue
        expected_total = expected_total_by_final[target]
        if target not in after_weights:
            errors.append(f"Target vertex group was not created after weighted merge: {target}")
        elif after_weights[target] + 0.0001 < expected_total:
            errors.append(f"Target vertex group did not receive expected merged weights: {target}")

    unsafe = [name for name in names if not is_safe_bone_name(name)]
    if unsafe:
        errors.append("Unsafe bone names remain: " + ", ".join(sorted(unsafe)[:16]))

    spine = spine_validation(armature)
    errors.extend(str(error) for error in spine["errors"])
    warnings.extend(str(warning) for warning in spine["warnings"])
    return {"ok": not errors, "errors": errors, "warnings": warnings}


def apply_plan(armature: bpy.types.Object, plan: dict[str, object], limit: int) -> dict[str, object]:
    protected = protected_from_plan(plan, armature)
    operations = enabled_operations(plan)
    before_count = len(armature.data.bones)
    before_weights = vertex_group_weight_totals()
    applied: list[dict[str, object]] = []
    print(f"Applying {len(operations)} enabled bone merge operation(s).")
    for index, raw in enumerate(operations, start=1):
        source = str(raw.get("source") or "")
        target = str(raw.get("target") or "")
        if not source or not target:
            applied.append({"source": source, "target": target, "status": "error", "reason": "missing source or target"})
            continue
        print(f"Merge {index}/{len(operations)}: {source} -> {target}")
        result = merge_bone(armature, source, target, protected)
        result.update({"round": raw.get("round"), "order": raw.get("order"), "reason": raw.get("reason")})
        applied.append(result)
    validation = validate_after_apply(armature, plan, applied, limit, protected, before_weights)
    return {
        "before_bone_count": before_count,
        "after_bone_count": len(armature.data.bones),
        "limit": limit,
        "operation_count": len(operations),
        "merged_count": sum(1 for result in applied if result.get("status") == "merged"),
        "applied_operations": applied,
        "validation": validation,
    }


def main() -> int:
    args = parse_args()
    if not args.input_blend.exists():
        raise FileNotFoundError(args.input_blend)
    limit = max(1, int(args.limit or DEFAULT_LIMIT))
    started = time.monotonic()
    print("Starting MMD Character Importer Blender step 4.")
    print(f"Opening spine-fixed blend: {args.input_blend}")
    bpy.ops.wm.open_mainfile(filepath=str(args.input_blend))

    if args.mode == "analyze":
        if not args.analysis_json:
            raise RuntimeError("--analysis-json is required for analyze mode")
        analysis, plan = analyze_current_file(args.input_blend, limit)
        write_json(args.analysis_json, analysis)
        write_json(args.plan_json, plan)
        print(f"Wrote bone merge analysis: {args.analysis_json}")
        print(f"Wrote bone merge plan: {args.plan_json}")
        print(f"Blender sort bones analysis finished in {time.monotonic() - started:.1f}s")
        return 0

    if not args.output_blend:
        raise RuntimeError("--output-blend is required for apply mode")
    if not args.report_json:
        raise RuntimeError("--report-json is required for apply mode")
    plan = load_plan(args.plan_json)
    before_analysis, _before_plan = analyze_current_file(args.input_blend, limit)
    armature = active_armature()
    result = apply_plan(armature, plan, limit)
    if not result["validation"]["ok"]:
        print("Validation failed after bone sorting.")
        for error in result["validation"]["errors"]:
            print(f"Error: {error}")
        raise RuntimeError("Bone sorting validation failed after apply.")
    args.output_blend.parent.mkdir(parents=True, exist_ok=True)
    print(f"Saving bone-sorted blend file: {args.output_blend}")
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output_blend))
    after_analysis, _after_plan = analyze_current_file(args.output_blend, limit)
    report = {
        "version": 1,
        "input_blend": str(args.input_blend),
        "output_blend": str(args.output_blend),
        "plan_json": str(args.plan_json),
        "elapsed_seconds": round(time.monotonic() - started, 3),
        "before": before_analysis,
        "after": after_analysis,
        "applied": result,
    }
    write_json(args.report_json, report)
    print(f"Wrote bone sorting report: {args.report_json}")
    print(f"Blender sort bones step finished in {time.monotonic() - started:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
