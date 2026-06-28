#!/usr/bin/env python3
"""Step 10 Blender automation: sort c_arms SMD files."""

from __future__ import annotations

import argparse
import colorsys
import json
import math
import shutil
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WEIGHT_THRESHOLD = 0.12
MAX_PREVIEW_TRIANGLES = 500000
HELPER_MESH_NAMES = {"smd_bone_vis"}
EXCLUDED_IMPORT_NAMES = {"physics.smd"}
FOREARM_ROOTS = {"ValveBiped.Bip01_R_Forearm", "ValveBiped.Bip01_L_Forearm"}


def log(message: str) -> None:
    print(f"[Step10 CArms] {message}", flush=True)


def write_json(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_object_mode() -> None:
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")


def set_active_only(obj: bpy.types.Object) -> None:
    ensure_object_mode()
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def prepare_output_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for child in list(path.iterdir()):
        if child.name == "blender_sort_carms.log":
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def clear_startup_scene() -> None:
    ensure_object_mode()
    for obj in list(bpy.context.scene.objects):
        obj.select_set(True)
    bpy.ops.object.delete()


def enable_source_tools() -> bool:
    try:
        bpy.ops.preferences.addon_enable(module="io_scene_valvesource")
    except Exception:
        blender_root = Path(bpy.app.binary_path).resolve().parent
        addon_dirs = [blender_root / "4.5" / "scripts" / "addons"]
        user_addon_dir = bpy.utils.user_resource("SCRIPTS", path="addons", create=False)
        if user_addon_dir:
            addon_dirs.append(Path(user_addon_dir))
        for addon_dir in addon_dirs:
            if addon_dir.exists() and str(addon_dir) not in sys.path:
                sys.path.insert(0, str(addon_dir))
        try:
            import io_scene_valvesource  # type: ignore

            io_scene_valvesource.register()
        except Exception as exc:
            log(f"Blender Source Tools could not be enabled: {exc}")
            return False
    try:
        bpy.ops.import_scene.smd.get_rna_type()
        bpy.ops.export_scene.smd.get_rna_type()
    except Exception as exc:
        log(f"Blender Source Tools operators are unavailable: {exc}")
        return False
    return True


def source_tools_state_update() -> None:
    try:
        from io_scene_valvesource.utils import State  # type: ignore

        State.update_scene(bpy.context.scene)
    except Exception as exc:
        log(f"Source Tools export list refresh warning: {exc}")


def v3(value: Vector) -> list[float]:
    return [round(float(value.x), 6), round(float(value.y), 6), round(float(value.z), 6)]


def natural_key(value: object) -> list[object]:
    import re

    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", str(value))]


def safe_fragment(value: str) -> str:
    import re

    text = re.sub(r"[^A-Za-z0-9_]+", "_", str(value or "")).strip("_").lower()
    return text or "item"


def input_smd_files(input_dir: Path) -> list[Path]:
    files = []
    for path in sorted(input_dir.glob("*.smd"), key=lambda item: natural_key(item.name)):
        if path.name.lower() in EXCLUDED_IMPORT_NAMES:
            continue
        files.append(path)
    if not files:
        raise RuntimeError(f"No top-level SMD files were found in {input_dir}")
    body = [path for path in files if path.name.lower() == "body.smd"]
    if body:
        return body + [path for path in files if path not in body]
    return files


def import_smds(input_dir: Path) -> dict[str, object]:
    smd_files = input_smd_files(input_dir)
    first = smd_files[0]
    log(f"Importing base c_arms source SMD: {first.name}")
    bpy.ops.import_scene.smd(filepath=str(first), append="NEW_ARMATURE", upAxis="Z")
    armatures = [
        obj
        for obj in bpy.data.objects
        if obj.type == "ARMATURE" and obj.name not in {"proportions", "reference_female", "reference_male"}
    ]
    if not armatures:
        armatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    if not armatures:
        raise RuntimeError(f"{first.name} did not import an armature.")
    armature = armatures[0]
    imported = [first.name]
    for path in smd_files[1:]:
        log(f"Importing additional c_arms source SMD: {path.name}")
        set_active_only(armature)
        bpy.ops.import_scene.smd(filepath=str(path), append="VALIDATE", upAxis="Z")
        imported.append(path.name)
    return {"armature": armature.name, "imported_smds": imported, "skipped_smds": sorted(EXCLUDED_IMPORT_NAMES)}


def main_armature() -> bpy.types.Object:
    armatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    if not armatures:
        raise RuntimeError("No armature was imported from the SMD files.")
    armatures.sort(key=lambda obj: len(obj.data.bones), reverse=True)
    return armatures[0]


def child_bone_names(armature: bpy.types.Object, roots: set[str]) -> set[str]:
    bones = armature.data.bones
    out = set()
    for root in roots:
        if root in bones:
            out.add(root)
    for bone in bones:
        parent = bone.parent
        while parent is not None:
            if parent.name in roots:
                out.add(bone.name)
                break
            parent = parent.parent
    return out


def mesh_objects() -> list[bpy.types.Object]:
    return sorted(
        [obj for obj in bpy.data.objects if obj.type == "MESH" and obj.name not in HELPER_MESH_NAMES and not obj.name.startswith("VTA vertices")],
        key=lambda obj: natural_key(obj.name),
    )


def vertex_keep_mask(obj: bpy.types.Object, target_bones: set[str], threshold: float) -> tuple[list[bool], int]:
    target_indices = {
        group.index
        for group in obj.vertex_groups
        if group.name in target_bones
    }
    weighted: list[bool] = []
    for vertex in obj.data.vertices:
        matched = False
        for ref in vertex.groups:
            if ref.group in target_indices and float(ref.weight) > threshold:
                matched = True
                break
        weighted.append(matched)
    keep = list(weighted)
    # Keep complete triangles around every qualifying weighted vertex. Deleting only
    # below-threshold vertices can otherwise leave no complete c_arms faces.
    for poly in obj.data.polygons:
        if any(weighted[int(vertex_index)] for vertex_index in poly.vertices):
            for vertex_index in poly.vertices:
                keep[int(vertex_index)] = True
    return keep, sum(1 for value in weighted if value)


def prune_mesh_to_carms(obj: bpy.types.Object, target_bones: set[str], threshold: float) -> dict[str, object]:
    before_vertices = len(obj.data.vertices)
    before_faces = len(obj.data.polygons)
    keep, weighted_vertices_before_expand = vertex_keep_mask(obj, target_bones, threshold)
    kept_vertices_before_delete = sum(1 for value in keep if value)
    log(
        f"{obj.name}: {weighted_vertices_before_expand:,} vertices exceed c_arms weight threshold; "
        f"{kept_vertices_before_delete:,} vertices kept after triangle expansion."
    )
    if weighted_vertices_before_expand <= 0:
        return {
            "object": obj.name,
            "removed": True,
            "before_vertices": before_vertices,
            "before_faces": before_faces,
            "after_vertices": 0,
            "after_faces": 0,
            "kept_weighted_vertices": weighted_vertices_before_expand,
            "kept_expanded_vertices": 0,
            "reason": "no vertices exceeded the c_arms weight threshold",
        }

    set_active_only(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_mode(type="VERT")
    bpy.ops.mesh.select_all(action="DESELECT")
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    for vertex in bm.verts:
        vertex.select_set(not keep[vertex.index])
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.mesh.delete(type="VERT")
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.data.update()

    after_vertices = len(obj.data.vertices)
    after_faces = len(obj.data.polygons)
    removed = after_vertices <= 0 or after_faces <= 0
    return {
        "object": obj.name,
        "removed": removed,
        "before_vertices": before_vertices,
        "before_faces": before_faces,
        "after_vertices": after_vertices,
        "after_faces": after_faces,
        "kept_weighted_vertices": weighted_vertices_before_expand,
        "kept_expanded_vertices": kept_vertices_before_delete,
        "reason": "empty after deleting non-c_arms vertices" if removed else "",
    }


def prune_all_meshes(target_bones: set[str], threshold: float) -> list[dict[str, object]]:
    reports = []
    for obj in list(mesh_objects()):
        report = prune_mesh_to_carms(obj, target_bones, threshold)
        reports.append(report)
        if report.get("removed"):
            log(f"Removing empty c_arms bodygroup: {obj.name}")
            bpy.data.objects.remove(obj, do_unlink=True)
        else:
            log(
                f"Kept {obj.name}: {int(report.get('after_vertices', 0)):,} vertices, "
                f"{int(report.get('after_faces', 0)):,} faces."
            )
    if not mesh_objects():
        raise RuntimeError("No c_arms bodygroup retained any faces after weight filtering.")
    return reports


def material_texture_map(input_dir: Path) -> dict[str, str]:
    workspace_root = input_dir.parent.parent if input_dir.parent.name == "9_export_proportion_trick" else input_dir.parent
    material_json = workspace_root / "5_sort_materials" / "materials.json"
    if not material_json.exists():
        return {}
    try:
        data = json.loads(material_json.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out: dict[str, str] = {}

    def visit(value: object) -> None:
        if isinstance(value, dict):
            path = str(value.get("base_color_path") or "")
            if path and Path(path).exists():
                for key_name in ("material_name", "proposed_name", "final_name", "combined_material", "name"):
                    name = str(value.get(key_name) or "")
                    if name:
                        out.setdefault(name.casefold(), path)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(data)
    return out


def material_texture_path(mat: bpy.types.Material | None, texture_by_name: dict[str, str]) -> str:
    if mat is None:
        return ""
    mapped = texture_by_name.get(mat.name.casefold())
    if mapped:
        return mapped
    if mat.node_tree is None:
        return ""
    for node in mat.node_tree.nodes:
        if getattr(node, "type", "") == "TEX_IMAGE" and getattr(node, "image", None) is not None:
            image = node.image
            if image.packed_file:
                return ""
            path = bpy.path.abspath(image.filepath or "")
            if path and Path(path).exists():
                return path
    return ""


def preview_color(uid: str, index: int) -> list[float]:
    seed = sum((offset + 1) * ord(char) for offset, char in enumerate(uid)) + index * 41
    hue = (seed % 360) / 360.0
    red, green, blue = colorsys.hsv_to_rgb(hue, 0.42, 0.88)
    return [round(red, 4), round(green, 4), round(blue, 4), 1.0]


def collect_preview(texture_by_name: dict[str, str], max_triangles: int = MAX_PREVIEW_TRIANGLES) -> dict[str, object]:
    objects = mesh_objects()
    total_triangles = sum(max(0, len(poly.vertices) - 2) for obj in objects for poly in obj.data.polygons)
    stride = max(1, math.ceil(total_triangles / max_triangles)) if total_triangles else 1
    triangles: list[dict[str, object]] = []
    materials_by_uid: dict[str, dict[str, object]] = {}
    points: list[list[float]] = []
    triangle_index = 0
    for object_index, obj in enumerate(objects, start=1):
        uv_layer = obj.data.uv_layers.active
        for poly in obj.data.polygons:
            mat = obj.data.materials[int(poly.material_index)] if 0 <= int(poly.material_index) < len(obj.data.materials) else None
            mat_name = mat.name if mat is not None else "No_Material"
            material_uid = f"{safe_fragment(obj.name)}__{int(poly.material_index):03d}_{safe_fragment(mat_name)}"
            texture_path = material_texture_path(mat, texture_by_name)
            if material_uid not in materials_by_uid:
                materials_by_uid[material_uid] = {
                    "uid": material_uid,
                    "material_name": f"{obj.name} / {mat_name}",
                    "proposed_name": mat_name,
                    "bodygroup": obj.name,
                    "keep": True,
                    "preview_color": preview_color(material_uid, object_index),
                    "base_color_path": texture_path,
                    "base_color_file": Path(texture_path).name if texture_path else "",
                    "alpha": 1.0,
                }
            verts = list(poly.vertices)
            loops = list(poly.loop_indices)
            if len(verts) < 3:
                continue
            for offset in range(1, len(verts) - 1):
                if triangle_index % stride == 0:
                    vertex_indices = [verts[0], verts[offset], verts[offset + 1]]
                    loop_indices = [loops[0], loops[offset], loops[offset + 1]]
                    coords = [v3(obj.matrix_world @ obj.data.vertices[index].co) for index in vertex_indices]
                    uvs: list[list[float]] = []
                    for loop_index in loop_indices:
                        if uv_layer is not None and 0 <= loop_index < len(uv_layer.data):
                            uv = uv_layer.data[loop_index].uv
                            uvs.append([round(float(uv.x), 6), round(float(uv.y), 6)])
                        else:
                            uvs.append([0.0, 0.0])
                    points.extend(coords)
                    triangles.append(
                        {
                            "points": coords,
                            "uvs": uvs,
                            "material_uid": material_uid,
                            "texture_path": texture_path,
                            "object_name": obj.name,
                        }
                    )
                triangle_index += 1
    mins = [min(point[index] for point in points) for index in range(3)] if points else [0.0, 0.0, 0.0]
    maxs = [max(point[index] for point in points) for index in range(3)] if points else [1.0, 1.0, 1.0]
    return {
        "materials": sorted(materials_by_uid.values(), key=lambda item: natural_key(item.get("uid", ""))),
        "material_count": len(materials_by_uid),
        "model_preview": {
            "triangles": triangles,
            "source_triangle_count": total_triangles,
            "sampled_triangle_count": len(triangles),
            "sample_stride": stride,
            "mins": mins,
            "maxs": maxs,
        },
    }


def configure_source_export(output_dir: Path) -> None:
    if not enable_source_tools():
        raise RuntimeError("Blender Source Tools is required for Step 10 export.")
    scene = bpy.context.scene
    scene.vs.export_format = "SMD"
    scene.vs.smd_format = "SOURCE"
    scene.vs.qc_compile = False
    scene.vs.export_path = str(output_dir.resolve())
    for collection in bpy.data.collections:
        try:
            collection.vs.mute = True
        except Exception:
            pass
    for obj in scene.objects:
        try:
            if obj.type == "MESH":
                obj.vs.export = obj.name not in HELPER_MESH_NAMES and not obj.name.startswith("VTA vertices")
                obj.vs.subdir = "."
            elif obj.type == "ARMATURE":
                obj.vs.export = False
                obj.vs.subdir = "."
            else:
                obj.vs.export = False
        except Exception:
            pass
    source_tools_state_update()


def export_carms(output_dir: Path) -> list[Path]:
    configure_source_export(output_dir)
    log(f"Exporting c_arms SMD files to {output_dir}")
    result = bpy.ops.export_scene.smd(export_scene=True)
    if result != {"FINISHED"}:
        raise RuntimeError(f"Source export failed: {result}")
    files = sorted(path for path in output_dir.glob("*.smd") if path.is_file())
    if not files:
        raise RuntimeError(f"No c_arms SMD files were exported under {output_dir}")
    return files


def copy_anims(input_dir: Path, output_dir: Path) -> list[Path]:
    source = input_dir / "anims"
    target = output_dir / "anims"
    if not source.exists():
        return []
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)
    copied = sorted(path for path in target.rglob("*.smd") if path.is_file())
    log(f"Copied {len(copied)} animation SMD file(s) to {target}.")
    return copied


def file_inventory(output_dir: Path, exported: list[Path], copied_anims: list[Path], object_reports: list[dict[str, object]]) -> list[dict[str, object]]:
    by_stem = {str(report.get("object") or ""): report for report in object_reports if not report.get("removed")}
    files: list[dict[str, object]] = []
    for path in exported:
        report = by_stem.get(path.stem, {})
        files.append(
            {
                "name": path.name,
                "relative_path": str(path.relative_to(output_dir)),
                "path": str(path),
                "type": "SMD",
                "size": path.stat().st_size,
                "source_stage": "c_arms_export",
                "vertices": int(report.get("after_vertices", 0) or 0),
                "faces": int(report.get("after_faces", 0) or 0),
                "warnings": "",
            }
        )
    for path in copied_anims:
        files.append(
            {
                "name": path.name,
                "relative_path": str(path.relative_to(output_dir)),
                "path": str(path),
                "type": "SMD",
                "size": path.stat().st_size,
                "source_stage": "copied_anim",
                "vertices": 0,
                "faces": 0,
                "warnings": "",
            }
        )
    return files


# Bundled STANDARD GMod c_arms skeleton (vendored copy of the stock weapons/c_arms.mdl reference,
# arms-only, 41 ValveBiped bones at canonical proportions). Used as the conform TARGET so the
# exported c_arms carries standard arm lengths and bonemerges cleanly onto weapon viewmodels.
STD_CARMS_SKELETON_SMD = Path(__file__).resolve().parent / "assets" / "std_c_arms_skeleton" / "c_arms.smd"


def import_standard_carms_armature() -> bpy.types.Object:
    """Import the bundled standard GMod c_arms skeleton as a SEPARATE armature (the conform target
    rest pose). Raises if the vendored asset is missing or no armature is produced."""
    if not STD_CARMS_SKELETON_SMD.exists():
        raise RuntimeError(f"Standard c_arms skeleton asset is missing: {STD_CARMS_SKELETON_SMD}")
    before = set(bpy.data.objects)
    bpy.ops.import_scene.smd(filepath=str(STD_CARMS_SKELETON_SMD), append="NEW_ARMATURE", upAxis="Z")
    new_objects = [obj for obj in bpy.data.objects if obj not in before]
    armature = next((obj for obj in new_objects if obj.type == "ARMATURE"), None)
    # The skeleton SMD carries no real geometry; drop any dummy object it imported.
    for obj in new_objects:
        if obj.type != "ARMATURE":
            bpy.data.objects.remove(obj, do_unlink=True)
    if armature is None:
        raise RuntimeError(f"Standard c_arms skeleton import produced no armature: {STD_CARMS_SKELETON_SMD}")
    return armature


def _vertex_weight(vertex: bpy.types.MeshVertex, group_index: int) -> float:
    for g in vertex.groups:
        if g.group == group_index:
            return g.weight
    return 0.0


def prepare_ulna_weights(char_arm: bpy.types.Object, std_bone_names: set[str]) -> dict[str, object]:
    """Set up L/R Ulna (ValveBiped forearm-twist) vertex groups on the arm meshes BEFORE the conform.

    The standard c_arms uses Ulna bones (driven by $proceduralbones) so the lower forearm twists with
    the hand; the stock arm animations expect them. MMD rigs either carry a forearm-twist bone
    (Japanese 手捩 / a non-standard child of Forearm) or had it merged into Forearm by SCMI's earlier
    steps. So per side:
      - if a non-standard child-of-Forearm twist bone exists, MOVE its weights onto Ulna (merge the
        twist into the standard Ulna) and drop the source group;
      - otherwise SYNTHESIZE Ulna from a gradient over the lower half of the Forearm (midpoint->wrist,
        matching the stock distribution).
    Only vertex-group weight VALUES are created here; the Ulna BONE comes from the standard target
    skeleton, and the conform preserves these weights and binds them to it on export."""
    char_bones = {bone.name: bone for bone in char_arm.data.bones}
    report: dict[str, object] = {}
    meshes = mesh_objects()
    for side in ("L", "R"):
        forearm = f"ValveBiped.Bip01_{side}_Forearm"
        hand = f"ValveBiped.Bip01_{side}_Hand"
        ulna = f"ValveBiped.Bip01_{side}_Ulna"
        if forearm not in char_bones:
            continue
        if ulna in char_bones:
            report[side] = "rig-has-ulna"  # already present; the conform handles it directly
            continue
        twist_sources = [child.name for child in char_bones[forearm].children if child.name not in std_bone_names]
        forearm_head = char_bones[forearm].matrix_local.translation
        hand_head = char_bones[hand].matrix_local.translation if hand in char_bones else None
        for obj in meshes:
            ulna_group = obj.vertex_groups.get(ulna) or obj.vertex_groups.new(name=ulna)
            if twist_sources:
                for src_name in twist_sources:
                    src_group = obj.vertex_groups.get(src_name)
                    if src_group is None:
                        continue
                    for vertex in obj.data.vertices:
                        weight = _vertex_weight(vertex, src_group.index)
                        if weight > 0.0:
                            ulna_group.add([vertex.index], weight, "ADD")
                    obj.vertex_groups.remove(src_group)
            elif hand_head is not None:
                forearm_group = obj.vertex_groups.get(forearm)
                if forearm_group is None:
                    continue
                axis = hand_head - forearm_head
                length = axis.length
                if length < 1.0e-6:
                    continue
                axis_n = axis / length
                for vertex in obj.data.vertices:
                    weight = _vertex_weight(vertex, forearm_group.index)
                    if weight <= 0.0:
                        continue
                    frac = (vertex.co - forearm_head).dot(axis_n) / length  # 0 = elbow, 1 = wrist
                    share = max(0.0, min(0.75, (frac - 0.5) / 0.5 * 0.75))
                    if share <= 0.0:
                        continue
                    ulna_group.add([vertex.index], weight * share, "REPLACE")
                    forearm_group.add([vertex.index], weight * (1.0 - share), "REPLACE")
        report[side] = ("twist:" + ",".join(twist_sources)) if twist_sources else "synthesized"
    return report


def _np3(vec) -> "np.ndarray":
    return np.array((vec.x, vec.y, vec.z), dtype=float)


def _weighted_similarity(a: "np.ndarray", b: "np.ndarray", w: "np.ndarray") -> tuple[float, "np.ndarray"]:
    """Closed-form weighted Procrustes: the uniform scale s and rotation R (no translation) that
    minimize sum_i w_i |s R a_i - b_i|^2. Returns (s, R[3x3]); degenerate input -> (1.0, identity)."""
    if a.shape[0] == 0:
        return 1.0, np.eye(3)
    cross = (b * w[:, None]).T @ a  # 3x3 = sum_i w_i b_i a_i^T
    try:
        u, _s, vt = np.linalg.svd(cross)
    except np.linalg.LinAlgError:
        return 1.0, np.eye(3)
    correction = np.eye(3)
    if np.linalg.det(u @ vt) < 0.0:  # forbid reflections
        correction[2, 2] = -1.0
    rot = u @ correction @ vt
    den = float((w * np.einsum("ij,ij->i", a, a)).sum())
    if den < 1.0e-12:
        return 1.0, rot
    num = float((w * np.einsum("ij,ij->i", b, a @ rot.T)).sum())
    scale = num / den
    if not np.isfinite(scale) or scale <= 1.0e-4:
        return 1.0, rot
    return scale, rot


def compute_hierarchical_deform(char_bones: dict, std_bones: dict, matched: list[str], decay: float = 0.5) -> dict:
    """Per-bone LBS deform matrices from a TOP-DOWN hierarchical similarity fit.

    Walking from the root (Spine4) down every arm/finger chain, for each bone we SNAP its head to the
    standard head, then solve the uniform scale + rotation about that head that best aligns the bone's
    whole sub-tree of joints (head AND tail of every descendant) onto the standard skeleton in a
    least-squares (RMSD) sense. Each joint's weight DECAYS with how far it sits below the bone
    (decay ** levels), so the many finger bones never dominate the proximal arm fit. Every bone's
    transform is accumulated onto its parent's (A_bone = T_bone @ A_parent), so the scale + rotation
    flows smoothly down to the fingertips and the mesh -- which removes the per-finger scale
    discontinuities a per-bone-independent scale produced. Returns {bone_name: 4x4 numpy matrix}."""
    matched_set = set(matched)
    parent_of: dict[str, "str | None"] = {}
    children: dict[str, list[str]] = {name: [] for name in matched}
    for name in matched:
        parent = std_bones[name].parent
        pname = parent.name if (parent is not None and parent.name in matched_set) else None
        parent_of[name] = pname
        if pname is not None:
            children[pname].append(name)

    def depth_of(name: str) -> int:
        d = 0
        cur = parent_of[name]
        while cur is not None:
            d += 1
            cur = parent_of[cur]
        return d

    depth = {name: depth_of(name) for name in matched}
    topo = sorted(matched, key=lambda n: depth[n])  # parents before children
    subtree: dict[str, list[str]] = {}

    def build_subtree(name: str) -> list[str]:
        out = [name]
        for child in children[name]:
            out.extend(build_subtree(child))
        subtree[name] = out
        return out

    for name in matched:
        if name not in subtree:
            build_subtree(name)

    head0 = {name: _np3(char_bones[name].head_local) for name in matched}
    tail0 = {name: _np3(char_bones[name].tail_local) for name in matched}
    head_std = {name: _np3(std_bones[name].head_local) for name in matched}
    tail_std = {name: _np3(std_bones[name].tail_local) for name in matched}

    def apply4(matrix, point):
        result = matrix @ np.array((point[0], point[1], point[2], 1.0))
        return result[:3]

    accum: dict[str, "np.ndarray"] = {}
    for name in topo:
        pname = parent_of[name]
        parent_matrix = accum[pname] if pname is not None else np.eye(4)
        if not children[name] and pname is not None:
            # Leaf bone (e.g. a fingertip Finger*2): nothing below it to fit, and a single-point
            # Procrustes is rank-deficient -> an arbitrary/backward twist and a collapsed scale (the
            # malformed tips). Its head already sits at the shared joint, so inherit the parent's
            # scale+rotation verbatim: the tip then continues its finger uniformly.
            accum[name] = parent_matrix
            continue
        head_cur = apply4(parent_matrix, head0[name])
        a_pts: list = []
        b_pts: list = []
        weights: list = []
        for desc in subtree[name]:
            weight = decay ** (depth[desc] - depth[name])
            for mmd_pt, std_pt in ((head0[desc], head_std[desc]), (tail0[desc], tail_std[desc])):
                a_pts.append(apply4(parent_matrix, mmd_pt) - head_cur)
                b_pts.append(std_pt - head_std[name])
                weights.append(weight)
        scale, rot = _weighted_similarity(np.array(a_pts), np.array(b_pts), np.array(weights))
        scale_rot = np.eye(4)
        scale_rot[:3, :3] = scale * rot
        to_origin = np.eye(4)
        to_origin[:3, 3] = -head_cur
        to_std = np.eye(4)
        to_std[:3, 3] = head_std[name]
        transform = to_std @ scale_rot @ to_origin  # snap head to standard, scale+rotate about it
        accum[name] = transform @ parent_matrix
    return accum


def conform_meshes_to_standard(char_arm: bpy.types.Object, std_arm: bpy.types.Object) -> dict[str, object]:
    """Rest-pose-conform every arm mesh from ``char_arm``'s (MMD-proportion) rest onto ``std_arm``'s
    STANDARD c_arms rest, via a pure-data linear-blend-skinning bake, then re-bind the meshes to
    ``std_arm``.

    Skin-weight values and vertex-group memberships are never edited -- only vertex POSITIONS and the
    bind armature change. This places the arm geometry on the standard c_arms skeleton so the runtime
    weapon-viewmodel bonemerge (player_manager.AddValidHands) lands on standard-proportion bones and
    nothing distorts. Pure data (no GUI operators / mode switches) so it is deterministic in
    ``blender --background``. Raises on a no-op (a bone-name mismatch) rather than silently shipping a
    distorted arm.
    """
    char_bones = {bone.name: bone for bone in char_arm.data.bones}
    std_bones = {bone.name: bone for bone in std_arm.data.bones}
    matched = sorted(name for name in std_bones if name in char_bones)
    if not matched:
        raise RuntimeError(
            "c_arms conform: no shared bone names between the character rig and the standard c_arms "
            "skeleton -- refusing to ship a silently unconformed (distorted) arm."
        )
    matched_set = set(matched)
    # Per-bone deform via a TOP-DOWN hierarchical scale+rotate fit (depth-weighted RMSD over each
    # bone's sub-tree, head-snapped, accumulated down the chain). This resizes AND re-orients the mesh
    # onto the standard skeleton smoothly all the way to the fingertips -- fixing both the thin arm
    # and the per-finger scale discontinuities a per-bone-independent scale produced.
    deform = compute_hierarchical_deform(char_bones, std_bones, matched)
    for arm_bone in ("ValveBiped.Bip01_L_Forearm", "ValveBiped.Bip01_L_Hand", "ValveBiped.Bip01_L_Finger2"):
        if arm_bone in deform:
            cumulative_scale = float(np.cbrt(abs(np.linalg.det(deform[arm_bone][:3, :3]))))
            log(f"Conform cumulative scale {arm_bone.split('.')[-1]} = {cumulative_scale:.3f}")
    total_moved = 0
    meshes = mesh_objects()
    for obj in meshes:
        # A raw vertex-coordinate write desyncs shape keys; first-person arms never flex, so clear them.
        if obj.data.shape_keys:
            log(f"Conform: clearing shape keys on {obj.name} (first-person arms do not flex).")
            obj.shape_key_clear()
        group_name = {vg.index: vg.name for vg in obj.vertex_groups}
        for vertex in obj.data.vertices:
            weighted = [
                (group_name.get(g.group), g.weight)
                for g in vertex.groups
                if g.weight > 0.0 and group_name.get(g.group) in matched_set
            ]
            if not weighted:
                continue  # non-arm vertex: leave at identity (the Step-10 cut drops it anyway)
            wsum = sum(weight for _name, weight in weighted)
            if wsum <= 0.0:
                continue
            blended = np.zeros((4, 4))
            for name, weight in weighted:
                blended += deform[name] * (weight / wsum)
            homogeneous = np.array((vertex.co.x, vertex.co.y, vertex.co.z, 1.0))
            new_co = blended @ homogeneous
            new_vec = Vector((float(new_co[0]), float(new_co[1]), float(new_co[2])))
            if (new_vec - vertex.co).length > 1.0e-6:
                total_moved += 1
            vertex.co = new_vec
        obj.data.update()
        # Re-bind to the standard skeleton so the exported reference SMD carries STANDARD bone lengths.
        obj.parent = std_arm
        obj.matrix_parent_inverse = std_arm.matrix_world.inverted()
        for modifier in obj.modifiers:
            if modifier.type == "ARMATURE":
                modifier.object = std_arm
        # The position edit invalidates custom split normals; clear them so the exporter recomputes
        # clean normals on the conformed geometry (arm meshes rarely carry custom normals).
        try:
            if getattr(obj.data, "has_custom_normals", False):
                obj.data.normals_split_custom_clear()
        except Exception as exc:
            log(f"Conform: could not clear custom normals on {obj.name}: {exc}")
    if total_moved == 0:
        raise RuntimeError(
            "c_arms conform: no vertices moved -- the conform was a no-op (bone-name mismatch). "
            "Refusing to ship a silently unconformed (distorted) arm."
        )
    return {
        "applied": True,
        "standard_skeleton": STD_CARMS_SKELETON_SMD.name,
        "matched_bone_count": len(matched),
        "meshes_conformed": len(meshes),
        "vertices_moved": total_moved,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--workspace-blend", type=Path, required=True)
    parser.add_argument("--report-json", type=Path, required=True)
    parser.add_argument("--files-json", type=Path, required=True)
    parser.add_argument("--weight-threshold", type=float, default=DEFAULT_WEIGHT_THRESHOLD)
    parser.add_argument("--game", default="gmod")
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> dict[str, object]:
    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()
    workspace_blend = args.workspace_blend.resolve()
    report_json = args.report_json.resolve()
    files_json = args.files_json.resolve()
    threshold = float(args.weight_threshold)
    game = str(getattr(args, "game", "gmod") or "gmod").strip().lower()
    if not input_dir.exists():
        raise FileNotFoundError(input_dir)
    if threshold <= 0.0:
        raise RuntimeError("Weight threshold must be positive.")

    log(f"Opening a clean Blender scene for c_arms import from {input_dir}")
    clear_startup_scene()
    if not enable_source_tools():
        raise RuntimeError("Blender Source Tools is required for Step 10.")
    prepare_output_directory(output_dir)
    import_report = import_smds(input_dir)
    armature = main_armature()
    target_bones = child_bone_names(armature, FOREARM_ROOTS)
    missing_roots = sorted(root for root in FOREARM_ROOTS if root not in target_bones)
    if missing_roots:
        raise RuntimeError("Required forearm bone(s) missing from imported armature: " + ", ".join(missing_roots))
    log(f"c_arms target bone set contains {len(target_bones)} forearm/hand/finger bone(s).")
    object_reports = prune_all_meshes(target_bones, threshold)
    # GMod first-person c_arms: conform the cut arm mesh onto the STANDARD c_arms skeleton (rest-pose
    # retarget) so it bonemerges cleanly onto weapon viewmodels. NOT done for L4D2 (its v_arms keep
    # the full-body skeleton + proportion trick) or SFM (Step 10 is skipped). Runs after the cut on
    # the small arm-only mesh; the cut itself is unchanged.
    conform_report: dict[str, object] = {"applied": False, "game": game}
    if game == "gmod":
        log("Conforming c_arms mesh onto the standard GMod c_arms skeleton (rest-pose retarget).")
        std_arm = import_standard_carms_armature()
        std_bone_names = {bone.name for bone in std_arm.data.bones}
        ulna_report = prepare_ulna_weights(armature, std_bone_names)
        log(f"Ulna weights: {ulna_report}")
        conform_report = conform_meshes_to_standard(armature, std_arm)
        conform_report["game"] = game
        conform_report["ulna"] = ulna_report
        log(
            f"Conform applied: matched {conform_report['matched_bone_count']} bones, moved "
            f"{conform_report['vertices_moved']} vertices across {conform_report['meshes_conformed']} mesh(es)."
        )
        # The meshes are now bound to the standard armature; remove the original MMD-proportion rig so
        # the Source export writes the standard skeleton unambiguously.
        if armature.name in bpy.data.objects:
            bpy.data.objects.remove(armature, do_unlink=True)
    texture_by_name = material_texture_map(input_dir)
    preview = collect_preview(texture_by_name)

    workspace_blend.parent.mkdir(parents=True, exist_ok=True)
    log(f"Saving c_arms workspace blend: {workspace_blend}")
    bpy.ops.wm.save_as_mainfile(filepath=str(workspace_blend))

    exported = export_carms(output_dir)
    copied_anims = copy_anims(input_dir, output_dir)
    files = file_inventory(output_dir, exported, copied_anims, object_reports)
    files_json.parent.mkdir(parents=True, exist_ok=True)
    files_json.write_text(json.dumps({"files": files}, ensure_ascii=False, indent=2), encoding="utf-8")

    kept_reports = [report for report in object_reports if not report.get("removed")]
    report = {
        "version": 1,
        "kind": "sort_c_arms",
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "workspace_blend": str(workspace_blend),
        "weight_threshold": threshold,
        "forearm_roots": sorted(FOREARM_ROOTS),
        "target_bones": sorted(target_bones, key=natural_key),
        "import": import_report,
        "conform": conform_report,
        "bodygroups": object_reports,
        "kept_bodygroup_count": len(kept_reports),
        "removed_bodygroup_count": len(object_reports) - len(kept_reports),
        "exported_file_count": len(exported),
        "copied_anim_count": len(copied_anims),
        **preview,
        "files": files,
        "validation": {
            "ok": bool(exported) and bool(kept_reports),
            "errors": [],
            "warnings": [],
        },
    }
    write_json(report_json, report)
    log(f"Wrote c_arms report: {report_json}")
    log(f"Wrote c_arms file list: {files_json}")
    return report


def main(argv: list[str] | None = None) -> int:
    run(parse_args(argv))
    return 0


if __name__ == "__main__":
    args_after_dash = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else sys.argv[1:]
    raise SystemExit(main(args_after_dash))
