#!/usr/bin/env python3
"""L4D2 post-Step-9 polygon-budget decimation.

L4D2's renderer chokes on oversized survivor meshes: empirically a single bodygroup mesh
above ~30k triangles renders as an exploding spray of stretched triangles in game, and the
whole model is unstable much above the base-game ~15-20k-vert envelope. Working community
ports keep every bodygroup mesh well under that ceiling (the heaviest proven-safe single mesh
across a set of working ports was ~27.7k tris; total ~76k tris) while the broken model had a
32.7k-tri mesh and ~100k tris total.

This pass runs AFTER the Step 9 proportion export is finished and decimates the exported
bodygroup SMDs to a triangle budget (both a per-mesh cap and a whole-model total cap). It
NEVER touches a mesh that has a paired ``.vta`` (vertex animation / flex deltas) -- decimating
such a mesh would change its vertex count and invalidate the VTA morph indices -- and it never
runs for GMod (the caller only invokes it for L4D2), so the GMod pipeline is byte-identical.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy

# Data-derived L4D2 budget (triangles). Working ports: per-mesh <= ~27.7k, total <= ~76k.
DEFAULT_PER_MESH_TRIS = 25000
DEFAULT_TOTAL_TRIS = 70000
HELPER_MESH_NAMES = {"smd_bone_vis"}
# The Physics SMD is the collision hull, not a rendered bodygroup -- never decimate it (that would
# change collision) and never count it toward the render-triangle budget.
EXCLUDE_STEMS = {"physics"}


def log(message: str) -> None:
    print(f"[L4D2 Decimate] {message}", flush=True)


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
        bpy.ops.export_scene.smd.get_rna_type()
        bpy.ops.import_scene.smd.get_rna_type()
    except Exception as exc:
        log(f"Blender Source Tools operators are unavailable: {exc}")
        return False
    return True


def smd_triangle_count(path: Path) -> int:
    """Count triangles in an SMD by counting vertex lines (>=9 numeric tokens) / 3."""
    vertex_lines = 0
    in_tris = False
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        s = raw.strip()
        if not in_tris:
            if s == "triangles":
                in_tris = True
            continue
        if s == "end":
            break
        if not s:
            continue
        parts = s.split()
        if len(parts) >= 9:
            try:
                float(parts[0]); float(parts[8])
                vertex_lines += 1
            except ValueError:
                pass  # material-name line
    return vertex_lines // 3


def reset_scene() -> None:
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_smd(path: Path) -> list[bpy.types.Object]:
    before = set(bpy.data.objects)
    bpy.ops.import_scene.smd(filepath=str(path), append="NEW_ARMATURE", upAxis="Z")
    return [obj for obj in bpy.data.objects if obj not in before]


def decimate_object(obj: bpy.types.Object, ratio: float) -> int:
    """Collapse-decimate one mesh to `ratio` of its faces. Returns resulting tri count."""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    mod = obj.modifiers.new(name="L4D2Budget", type="DECIMATE")
    mod.decimate_type = "COLLAPSE"
    mod.ratio = max(0.01, min(1.0, ratio))
    mod.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return len(obj.data.polygons)


def limit_object_weights(obj: bpy.types.Object, max_influences: int = 3) -> int:
    """Re-impose Source's max-3-bones-per-vertex limit after decimation.

    Collapse-decimation merges vertices and unions their bone links, so a decimated vertex can
    end up with 4-5 influences -- the exact condition L4D2's studiomdl mishandles. Keep each
    vertex's strongest `max_influences` weights and renormalize to sum 1.0 (manual, deterministic;
    the SMD's groups are all real bones so no orphan-group pass is needed).
    """
    import math

    mesh = obj.data
    group_by_index = {vg.index: vg for vg in obj.vertex_groups}
    limited = 0
    for vertex in mesh.vertices:
        entries = [
            (a.group, float(a.weight))
            for a in vertex.groups
            if a.group in group_by_index and a.weight > 0.0
        ]
        if not entries:
            continue
        drop: list[int] = []
        keep = entries
        if len(entries) > max_influences:
            entries.sort(key=lambda it: it[1], reverse=True)
            keep = entries[:max_influences]
            drop = [gi for gi, _ in entries[max_influences:]]
            limited += 1
        total = sum(w for _, w in keep)
        if total <= 0.0:
            continue
        for gi in drop:
            group_by_index[gi].remove([vertex.index])
        if not math.isclose(total, 1.0, rel_tol=1e-6, abs_tol=1e-6):
            for gi, w in keep:
                group_by_index[gi].add([vertex.index], w / total, "REPLACE")
    if limited:
        mesh.update()
    return limited


def configure_export(export_dir: Path) -> None:
    scene = bpy.context.scene
    scene.vs.export_format = "SMD"
    scene.vs.smd_format = "SOURCE"
    scene.vs.qc_compile = False
    scene.vs.export_path = str(export_dir.resolve())
    for obj in scene.objects:
        try:
            obj.hide_set(False)
            obj.hide_viewport = False
            if obj.type == "MESH":
                obj.vs.export = obj.name not in HELPER_MESH_NAMES and not obj.name.startswith("VTA")
                obj.vs.subdir = "."
            elif obj.type == "ARMATURE":
                obj.vs.export = False
                obj.vs.subdir = "."
            else:
                obj.vs.export = False
        except Exception:
            pass
    try:
        from io_scene_valvesource.utils import State  # type: ignore

        State.update_scene(scene)
    except Exception:
        pass


def export_single_smd(target_smd: Path, scratch_dir: Path) -> None:
    """Export the (single decimated) mesh in the current scene back to target_smd."""
    if scratch_dir.exists():
        for f in scratch_dir.glob("*"):
            try:
                f.unlink()
            except Exception:
                pass
    scratch_dir.mkdir(parents=True, exist_ok=True)
    configure_export(scratch_dir)
    result = bpy.ops.export_scene.smd(export_scene=True)
    if result != {"FINISHED"}:
        raise RuntimeError(f"SMD re-export failed for {target_smd.name}: {result}")
    produced = sorted(scratch_dir.glob("*.smd"))
    if not produced:
        raise RuntimeError(f"SMD re-export produced no file for {target_smd.name}")
    # Prefer a same-stem match; otherwise the only/largest SMD.
    match = next((p for p in produced if p.stem.casefold() == target_smd.stem.casefold()), None)
    chosen = match or max(produced, key=lambda p: p.stat().st_size)
    target_smd.write_bytes(chosen.read_bytes())


def plan_ratios(meshes: dict[str, int], fixed_tris: int, per_mesh: int, total: int) -> dict[str, float]:
    """Compute per-mesh keep-ratios so each decimatable mesh <= per_mesh and the whole
    model (decimatable + fixed VTA meshes) <= total."""
    # Per-mesh cap first.
    capped = {name: min(tris, per_mesh) for name, tris in meshes.items()}
    budget_for_decimatable = max(1, total - fixed_tris)
    sum_capped = sum(capped.values())
    if sum_capped > budget_for_decimatable:
        scale = budget_for_decimatable / sum_capped
        capped = {name: max(1, int(t * scale)) for name, t in capped.items()}
    ratios: dict[str, float] = {}
    for name, orig in meshes.items():
        target = capped[name]
        ratios[name] = (target / orig) if orig > 0 else 1.0
    return ratios


def run(args: argparse.Namespace) -> dict[str, object]:
    export_dir = Path(args.export_dir).resolve()
    if not export_dir.exists():
        raise FileNotFoundError(export_dir)
    if not enable_source_tools():
        raise RuntimeError("Blender Source Tools is required for L4D2 decimation.")

    # Top-level bodygroup SMDs only (anims/ holds proportions/reference, not bodygroups).
    smds = sorted(p for p in export_dir.glob("*.smd"))
    vta_stems = {p.stem.casefold() for p in export_dir.glob("*.vta")}

    decimatable: dict[str, Path] = {}
    fixed: dict[str, Path] = {}
    for smd in smds:
        if smd.stem.casefold() in EXCLUDE_STEMS:
            log(f"  excluded (not a rendered bodygroup): {smd.stem}")
            continue
        if smd.stem.casefold() in vta_stems:
            fixed[smd.stem] = smd
        else:
            decimatable[smd.stem] = smd

    dec_tris = {stem: smd_triangle_count(p) for stem, p in decimatable.items()}
    fixed_tris_by = {stem: smd_triangle_count(p) for stem, p in fixed.items()}
    fixed_tris = sum(fixed_tris_by.values())
    total_before = sum(dec_tris.values()) + fixed_tris

    ratios = plan_ratios(dec_tris, fixed_tris, args.per_mesh_tris, args.total_tris)

    log(
        f"Budget per-mesh={args.per_mesh_tris} total={args.total_tris}; "
        f"{len(decimatable)} decimatable + {len(fixed)} VTA-locked mesh(es); total tris before={total_before}."
    )
    for stem in sorted(fixed_tris_by):
        log(f"  VTA-locked (kept): {stem} = {fixed_tris_by[stem]} tris")

    results: list[dict[str, object]] = []
    scratch = export_dir / "_decimate_scratch"
    for stem, smd in decimatable.items():
        orig = dec_tris[stem]
        ratio = ratios[stem]
        if ratio >= 0.999 or orig <= 0:
            results.append({"mesh": stem, "tris_before": orig, "tris_after": orig, "ratio": 1.0, "decimated": False})
            log(f"  keep (under budget): {stem} = {orig} tris")
            continue
        reset_scene()
        if not enable_source_tools():
            raise RuntimeError("Source Tools unavailable after scene reset.")
        objs = import_smd(smd)
        mesh_objs = [o for o in objs if o.type == "MESH" and o.name not in HELPER_MESH_NAMES]
        if not mesh_objs:
            log(f"  WARNING: no mesh imported from {smd.name}; skipping.")
            results.append({"mesh": stem, "tris_before": orig, "tris_after": orig, "ratio": 1.0, "decimated": False, "warning": "no mesh"})
            continue
        after_total = 0
        relimited = 0
        for mo in mesh_objs:
            after_total += decimate_object(mo, ratio)
            relimited += limit_object_weights(mo, max_influences=3)
        export_single_smd(smd, scratch)
        new_tris = smd_triangle_count(smd)
        results.append({"mesh": stem, "tris_before": orig, "tris_after": new_tris, "ratio": round(ratio, 4), "decimated": True, "reweighted_verts": relimited})
        log(f"  decimated: {stem} {orig} -> {new_tris} tris (ratio {ratio:.3f}); re-limited {relimited} vert(s) to <=3 bones")

    if scratch.exists():
        try:
            for f in scratch.glob("*"):
                f.unlink()
            scratch.rmdir()
        except Exception:
            pass

    total_after = sum(int(r["tris_after"]) for r in results) + fixed_tris
    report = {
        "export_dir": str(export_dir),
        "per_mesh_tris": args.per_mesh_tris,
        "total_tris_budget": args.total_tris,
        "total_tris_before": total_before,
        "total_tris_after": total_after,
        "fixed_vta_meshes": fixed_tris_by,
        "meshes": results,
        "ok": True,
    }
    log(f"Done. Total tris {total_before} -> {total_after} (budget {args.total_tris}).")
    if args.report_json:
        Path(args.report_json).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--export-dir", required=True)
    p.add_argument("--per-mesh-tris", type=int, default=DEFAULT_PER_MESH_TRIS)
    p.add_argument("--total-tris", type=int, default=DEFAULT_TOTAL_TRIS)
    p.add_argument("--report-json", default="")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        run(args)
    except Exception as exc:
        import traceback

        traceback.print_exc()
        if args.report_json:
            try:
                Path(args.report_json).write_text(
                    json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2), encoding="utf-8"
                )
            except Exception:
                pass
        return 1
    return 0


if __name__ == "__main__":
    args_after_dash = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    raise SystemExit(main(args_after_dash))
