"""Debug Step 8 collision vertex selection inside Blender.

Run from Blender with:

    blender --python tools/blender_debug_select_collision_vertices.py -- \
        --input-blend "path/to/model_flexes_sorted.blend" \
        --bone ValveBiped.Bip01_R_Forearm

The script creates one merged debug copy of all render bodygroups, then selects
the vertices that Step 8 would use for the requested collision bone. Original
bodygroup objects are left unchanged.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

import bpy
from mathutils import Vector

TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import blender_sort_collision as collision  # noqa: E402


DEBUG_PREFIX = "MCI_DebugCollisionMerged"
DEFAULT_BONE = "ValveBiped.Bip01_R_Forearm"


def parse_args() -> argparse.Namespace:
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description="Select Step 8 collision source vertices for one bone.")
    parser.add_argument("--input-blend", type=Path, help="Optional blend file to open before debugging.")
    parser.add_argument("--bone", default="", help=f"Collision target bone. Defaults to active bone or {DEFAULT_BONE}.")
    parser.add_argument("--output-blend", type=Path, help="Optional path to save the debug blend after selecting.")
    parser.add_argument(
        "--include-excluded-selection",
        action="store_true",
        help="Do not exclude hair/accessory/physics-like source object names during Step 8 selection.",
    )
    parser.add_argument(
        "--hide-originals",
        action="store_true",
        help="Hide original bodygroup meshes after the merged debug copy is created.",
    )
    parser.add_argument(
        "--keep-old-debug",
        action="store_true",
        help="Keep existing MCI debug merged objects instead of removing them first.",
    )
    return parser.parse_args(args)


def active_bone_name() -> str:
    pose_bone = getattr(bpy.context, "active_pose_bone", None)
    if pose_bone is not None:
        return str(pose_bone.name)
    active_bone = getattr(bpy.context, "active_bone", None)
    if active_bone is not None:
        return str(active_bone.name)
    return ""


def debug_log(message: str) -> None:
    print(f"[Collision Selection Debug] {message}", flush=True)


def remove_old_debug_objects() -> None:
    collision.ensure_object_mode()
    for obj in list(bpy.data.objects):
        if obj.name.startswith(DEBUG_PREFIX):
            mesh = obj.data if obj.type == "MESH" else None
            bpy.data.objects.remove(obj, do_unlink=True)
            if mesh is not None and mesh.users == 0:
                bpy.data.meshes.remove(mesh)


def source_mesh_objects() -> list[bpy.types.Object]:
    return [
        obj
        for obj in collision.mesh_objects(include_physics=False)
        if not obj.name.startswith(DEBUG_PREFIX)
    ]


def mesh_objects_for_selection(filtered_sources: bool) -> list[bpy.types.Object]:
    objects = []
    for obj in source_mesh_objects():
        if filtered_sources and not collision.is_collision_source_object(obj):
            continue
        objects.append(obj)
    return objects


def vertex_weight_any(
    obj: bpy.types.Object,
    vertex: bpy.types.MeshVertex,
    bone_names: Iterable[str],
    group_by_index: dict[int, str],
) -> float:
    return collision.vertex_group_weight_any(obj, vertex, bone_names, group_by_index)


def compute_fit(
    armature: bpy.types.Object,
    bone_name: str,
    filtered_sources: bool,
) -> dict[str, object]:
    shrink = collision.default_shrink(bone_name)
    clouds = collision.collect_weighted_vertex_cloud(armature, filtered_sources=filtered_sources)
    unfiltered_clouds = collision.collect_weighted_vertex_cloud(armature, filtered_sources=False)
    source_points = clouds.get(bone_name, [])
    if len(source_points) < collision.MIN_MULTI_HULL_POINTS and len(unfiltered_clouds.get(bone_name, [])) >= collision.MIN_MULTI_HULL_POINTS:
        debug_log(f"{bone_name}: filtered source was sparse; using unfiltered source points for fit, same as Step 8.")
        source_points = unfiltered_clouds.get(bone_name, [])
    scene_mins, scene_maxs = collision.scene_bounds_in_armature(armature, filtered_sources=filtered_sources)
    return collision.fit_part(armature, bone_name, source_points, shrink, scene_mins, scene_maxs)


def compute_selected_source_vertices(
    armature: bpy.types.Object,
    bone_name: str,
    fit: dict[str, object],
    filtered_sources: bool,
) -> dict[str, object]:
    armature_inv = armature.matrix_world.inverted()
    influence_bones = collision.collision_influence_bones(armature, bone_name)
    stats = collision.weight_threshold_for_bone(
        armature,
        bone_name,
        filtered_sources=filtered_sources,
        influence_bones=influence_bones,
    )
    threshold = float(stats.get("threshold", 0.0) or 0.0)
    selected_vertex_keys: set[tuple[str, int]] = set()
    source_objects: set[str] = set()
    selected_vertex_count = 0
    selected_face_count = 0
    child_face_count = 0

    child_names = collision.direct_target_children(armature, bone_name)
    child_influence_bones = {child: collision.collision_influence_bones(armature, child) for child in child_names}
    child_stats = {
        child: collision.weight_threshold_for_bone(
            armature,
            child,
            filtered_sources=filtered_sources,
            influence_bones=child_influence_bones[child],
        )
        for child in child_names
    }

    parent_center = fit.get("center")
    axes = fit.get("axes", (None, None, None))
    parent_axis = axes[2] if isinstance(axes, tuple) and len(axes) >= 3 else None
    parent_t_min = 0.0
    parent_t_max = 0.0
    parent_span = 0.0

    if isinstance(parent_center, Vector) and isinstance(parent_axis, Vector):
        source_points: list[Vector] = []
        for obj in mesh_objects_for_selection(filtered_sources):
            group_by_index = {group.index: group.name for group in obj.vertex_groups}
            for vertex in obj.data.vertices:
                if vertex_weight_any(obj, vertex, influence_bones, group_by_index) >= threshold > 0.0:
                    source_points.append(armature_inv @ (obj.matrix_world @ vertex.co))
        if source_points:
            ts = [(point - parent_center).dot(parent_axis) for point in source_points]
            parent_t_min = collision.percentile(ts, 0.04)
            parent_t_max = collision.percentile(ts, 0.96)
            parent_span = max(0.04, parent_t_max - parent_t_min)

    for obj in mesh_objects_for_selection(filtered_sources):
        group_by_index = {group.index: group.name for group in obj.vertex_groups}
        target_weights = [vertex_weight_any(obj, vertex, influence_bones, group_by_index) for vertex in obj.data.vertices]
        selected = [weight >= threshold > 0.0 for weight in target_weights]
        selected_vertex_count += sum(1 for flag in selected if flag)
        child_weights_by_name = {
            child: [
                vertex_weight_any(obj, vertex, child_influence_bones[child], group_by_index)
                for vertex in obj.data.vertices
            ]
            for child in child_names
        }

        for poly in obj.data.polygons:
            poly_vertices = [int(index) for index in poly.vertices]
            if len(poly_vertices) < 3:
                continue
            weights = [target_weights[index] for index in poly_vertices]
            selected_count = sum(1 for index in poly_vertices if selected[index])
            include = selected_count >= 2 or (max(weights) if weights else 0.0) >= max(0.20, threshold)
            include_child = False
            if not include and isinstance(parent_center, Vector) and isinstance(parent_axis, Vector) and parent_span > 0.0:
                current_overlap = (max(weights) if weights else 0.0) >= max(0.02, threshold * 0.20)
                centroid = sum(
                    (armature_inv @ (obj.matrix_world @ obj.data.vertices[index].co) for index in poly_vertices),
                    Vector((0.0, 0.0, 0.0)),
                ) / float(len(poly_vertices))
                t = (centroid - parent_center).dot(parent_axis)
                in_joint_span = parent_t_max - parent_span * 0.12 <= t <= parent_t_max + parent_span * 0.14
                if current_overlap and in_joint_span:
                    for child, child_weights in child_weights_by_name.items():
                        child_threshold = float(child_stats.get(child, {}).get("threshold", 0.0) or 0.0)
                        if child_threshold > 0.0 and max(child_weights[index] for index in poly_vertices) >= max(0.08, child_threshold):
                            include_child = True
                            break
            if not include and not include_child:
                continue
            source_objects.add(obj.name)
            if include_child:
                child_face_count += 1
            else:
                selected_face_count += 1
            for vertex_index in poly_vertices:
                selected_vertex_keys.add((obj.name, int(vertex_index)))

    return {
        "selected_vertex_keys": selected_vertex_keys,
        "stats": stats,
        "influence_bones": influence_bones,
        "source_objects": sorted(source_objects, key=collision.natural_key),
        "selected_vertex_count": selected_vertex_count,
        "selected_face_count": selected_face_count,
        "child_face_count": child_face_count,
        "filtered_sources": filtered_sources,
    }


def material_index_for(
    mesh: bpy.types.Mesh,
    material_slots: bpy.types.bpy_prop_collection,
    source_index: int,
    material_map: dict[str, int],
) -> int:
    material = None
    if 0 <= source_index < len(material_slots):
        material = material_slots[source_index].material
    if material is None:
        return 0
    key = material.name
    existing = material_map.get(key)
    if existing is not None:
        return existing
    mesh.materials.append(material)
    index = len(mesh.materials) - 1
    material_map[key] = index
    return index


def create_merged_debug_object(
    armature: bpy.types.Object,
    selected_vertex_keys: set[tuple[str, int]],
    bone_name: str,
    hide_originals: bool,
) -> bpy.types.Object:
    armature_inv = armature.matrix_world.inverted()
    vertices: list[tuple[float, float, float]] = []
    faces: list[list[int]] = []
    face_material_indices: list[int] = []
    source_to_debug_vertex: dict[tuple[str, int], int] = {}
    assignments: dict[str, list[tuple[int, float]]] = {}
    material_map: dict[str, int] = {}

    mesh = bpy.data.meshes.new(f"{DEBUG_PREFIX}_{collision.safe_fragment(bone_name)}_Mesh")
    source_objects = source_mesh_objects()
    for obj in source_objects:
        group_by_index = {group.index: group.name for group in obj.vertex_groups}
        object_vertex_map: dict[int, int] = {}
        for vertex in obj.data.vertices:
            debug_index = len(vertices)
            object_vertex_map[int(vertex.index)] = debug_index
            source_to_debug_vertex[(obj.name, int(vertex.index))] = debug_index
            co = armature_inv @ (obj.matrix_world @ vertex.co)
            vertices.append((float(co.x), float(co.y), float(co.z)))
            for group_ref in vertex.groups:
                group_name = group_by_index.get(group_ref.group)
                if group_name:
                    assignments.setdefault(group_name, []).append((debug_index, float(group_ref.weight)))
        for poly in obj.data.polygons:
            poly_vertices = [object_vertex_map[int(index)] for index in poly.vertices if int(index) in object_vertex_map]
            if len(poly_vertices) >= 3:
                faces.append(poly_vertices)
                face_material_indices.append(material_index_for(mesh, obj.material_slots, int(poly.material_index), material_map))
        if hide_originals:
            obj.hide_set(True)
            obj.hide_viewport = True

    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    for index, material_index in enumerate(face_material_indices):
        if index < len(mesh.polygons):
            mesh.polygons[index].material_index = material_index

    debug_obj = bpy.data.objects.new(f"{DEBUG_PREFIX}_{collision.safe_fragment(bone_name)}", mesh)
    bpy.context.collection.objects.link(debug_obj)
    debug_obj.matrix_world = armature.matrix_world.copy()

    for group_name, weighted_indices in assignments.items():
        group = debug_obj.vertex_groups.new(name=group_name)
        for vertex_index, weight in weighted_indices:
            group.add([vertex_index], weight, "ADD")

    selected_debug_indices = [
        source_to_debug_vertex[key]
        for key in selected_vertex_keys
        if key in source_to_debug_vertex
    ]
    selected_group = debug_obj.vertex_groups.new(name=f"MCI_Selected_{collision.safe_fragment(bone_name)}")
    if selected_debug_indices:
        selected_group.add(selected_debug_indices, 1.0, "ADD")

    modifier = debug_obj.modifiers.new("Armature", "ARMATURE")
    modifier.object = armature

    for vertex in mesh.vertices:
        vertex.select = False
    for vertex_index in selected_debug_indices:
        mesh.vertices[vertex_index].select = True
    mesh.update()

    bpy.ops.object.select_all(action="DESELECT")
    debug_obj.select_set(True)
    bpy.context.view_layer.objects.active = debug_obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_mode(type="VERT")
    return debug_obj


def main() -> int:
    args = parse_args()
    if args.input_blend:
        debug_log(f"Opening blend: {args.input_blend}")
        bpy.ops.wm.open_mainfile(filepath=str(args.input_blend))
    collision.ensure_object_mode()
    if not args.keep_old_debug:
        remove_old_debug_objects()

    armature = collision.main_armature()
    if armature is None:
        raise SystemExit("No armature found in the scene.")

    bone_name = args.bone.strip() or active_bone_name() or DEFAULT_BONE
    if bone_name not in armature.data.bones:
        raise SystemExit(f"Bone not found on main armature: {bone_name}")

    filtered_sources = not bool(args.include_excluded_selection)
    influence_bones = collision.collision_influence_bones(armature, bone_name)
    debug_log(f"Target bone: {bone_name}")
    debug_log(f"Influence bones: {', '.join(influence_bones)}")
    debug_log(f"Selection source filtering: {'enabled' if filtered_sources else 'disabled'}")

    fit = compute_fit(armature, bone_name, filtered_sources=filtered_sources)
    selection = compute_selected_source_vertices(armature, bone_name, fit, filtered_sources=filtered_sources)
    selected_vertex_keys = selection["selected_vertex_keys"]
    if not selected_vertex_keys and filtered_sources:
        debug_log("Filtered selection produced no vertices; retrying with excluded source objects included.")
        filtered_sources = False
        fit = compute_fit(armature, bone_name, filtered_sources=filtered_sources)
        selection = compute_selected_source_vertices(armature, bone_name, fit, filtered_sources=filtered_sources)
        selected_vertex_keys = selection["selected_vertex_keys"]

    debug_obj = create_merged_debug_object(
        armature,
        selected_vertex_keys,
        bone_name=bone_name,
        hide_originals=bool(args.hide_originals),
    )

    stats = selection.get("stats", {})
    debug_log(
        "Selected {selected:,} vertices on merged debug mesh from {objects:,} source object(s); "
        "threshold={threshold:.4f}, mean={mean:.4f}, stdev={stdev:.4f}, max={max_weight:.4f}, "
        "method={method}, faces={faces:,}, child_faces={child_faces:,}.".format(
            selected=len(selected_vertex_keys),
            objects=len(selection.get("source_objects", [])),
            threshold=float(stats.get("threshold", 0.0) or 0.0),
            mean=float(stats.get("mean", 0.0) or 0.0),
            stdev=float(stats.get("stdev", 0.0) or 0.0),
            max_weight=float(stats.get("max", 0.0) or 0.0),
            method=str(stats.get("threshold_method") or ""),
            faces=int(selection.get("selected_face_count", 0) or 0),
            child_faces=int(selection.get("child_face_count", 0) or 0),
        )
    )
    debug_log(f"Created merged debug object: {debug_obj.name}")
    debug_log("Blender is now in edit mode with the Step 8 collision source vertices selected.")

    if args.output_blend:
        bpy.ops.wm.save_as_mainfile(filepath=str(args.output_blend))
        debug_log(f"Saved debug blend: {args.output_blend}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
