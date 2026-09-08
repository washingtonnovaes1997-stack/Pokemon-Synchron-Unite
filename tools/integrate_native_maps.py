#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import struct
from pathlib import Path


def slug(text: str) -> str:
    text = text.replace(" ", "_")
    return re.sub(r"[^A-Za-z0-9_]", "", text)


def const(text: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", text.upper()).strip("_")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_bin(path: Path, values: list[int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"".join(struct.pack("<H", v & 0xFFFF) for v in values))


def native_value(code: int) -> int:
    # Elevation 3 + low metatile index. The visual tileset is intentionally
    # temporary until the Synchron master tileset is registered.
    return 0x3000 | max(1, min(code, 10))


def build_map_json(name: str, layout_id: str, kind: str, connections: list[dict]) -> dict:
    return {
        "id": f"MAP_{const(name)}",
        "name": name,
        "layout": layout_id,
        "music": "MUS_NONE",
        "region": "REGION_HOENN",
        # Hidden while Aurelis map-section constants are being generated.
        "region_map_section": "MAPSEC_LITTLEROOT_TOWN",
        "requires_flash": False,
        "weather": "WEATHER_NONE",
        "map_type": "MAP_TYPE_TOWN" if kind == "city" else "MAP_TYPE_ROUTE",
        "allow_cycling": True,
        "allow_escaping": False,
        "allow_running": True,
        "show_map_name": False,
        "battle_scene": "MAP_BATTLE_SCENE_NORMAL",
        "connections": connections or None,
        "object_events": [],
        "warp_events": [],
        "coord_events": [],
        "bg_events": [],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--engine", required=True)
    args = ap.parse_args()

    project = Path(args.project).resolve()
    engine = Path(args.engine).resolve()
    generated = project / "generated" / "maps"
    world = project / "game" / "world"

    index = load_json(generated / "map_build_index.json")
    routes_cfg = load_json(world / "routes.json")
    region_cfg = load_json(world / "region_01.json")

    city_blueprints = {}
    for fn in index["city_files"]:
        m = load_json(generated / fn)
        city_blueprints[m["name"]] = m

    route_blueprints = {}
    for fn in index["route_files"]:
        m = load_json(generated / fn)
        route_blueprints[m["id"]] = m

    # Stable native names. City names remain the actual Aurelis names.
    city_native = {name: slug(name) for name in city_blueprints}
    route_native = {rid: f"AurelisRoute_{rid}" for rid in route_blueprints}

    # Build reciprocal connection candidates. A city receives at most four
    # edge connections; excess routes remain registered and can later be
    # reached by gate/warp events without invalidating the native map table.
    dirs = ["up", "right", "down", "left"]
    opposite = {"up": "down", "down": "up", "left": "right", "right": "left"}
    city_conn = {name: [] for name in city_blueprints}
    route_conn = {rid: [] for rid in route_blueprints}
    used = {name: 0 for name in city_blueprints}

    for r in routes_cfg["routes"]:
        rid = r["id"]
        a, b = r["from"], r["to"]
        da = dirs[used[a] % 4]
        db = dirs[used[b] % 4]
        used[a] += 1
        used[b] += 1
        if len(city_conn[a]) < 4:
            city_conn[a].append({"map": f"MAP_{const(route_native[rid])}", "offset": 0, "direction": da})
            route_conn[rid].append({"map": f"MAP_{const(city_native[a])}", "offset": 0, "direction": opposite[da]})
        if len(city_conn[b]) < 4:
            city_conn[b].append({"map": f"MAP_{const(route_native[rid])}", "offset": 0, "direction": db})
            route_conn[rid].append({"map": f"MAP_{const(city_native[b])}", "offset": 0, "direction": opposite[db]})

    map_names = []
    layouts_to_add = []
    native_report = {"cities": [], "routes": [], "start_map": "Lunaris", "development_tileset": True}

    def emit(native_name: str, bp: dict, kind: str, connections: list[dict]):
        map_names.append(native_name)
        layout_id = f"LAYOUT_{const(native_name)}"
        layout_name = f"{native_name}_Layout"
        layout_dir = engine / "data" / "layouts" / native_name
        layout_dir.mkdir(parents=True, exist_ok=True)
        grid = bp["grid"]
        vals = [native_value(v) for row in grid for v in row]
        write_bin(layout_dir / "map.bin", vals)
        write_bin(layout_dir / "border.bin", [native_value(1)] * 4)
        layouts_to_add.append({
            "id": layout_id,
            "name": layout_name,
            "width": bp["width"],
            "height": bp["height"],
            "primary_tileset": "gTileset_General",
            "secondary_tileset": "gTileset_Petalburg",
            "border_filepath": f"data/layouts/{native_name}/border.bin",
            "blockdata_filepath": f"data/layouts/{native_name}/map.bin",
            "layout_version": "emerald"
        })
        mp = engine / "data" / "maps" / native_name
        mp.mkdir(parents=True, exist_ok=True)
        (mp / "map.json").write_text(json.dumps(build_map_json(native_name, layout_id, kind, connections), indent=2) + "\n", encoding="utf-8")
        (mp / "scripts.inc").write_text(f"{native_name}_MapScripts::\n\t.byte 0\n", encoding="utf-8")

    for city in region_cfg["cities"]:
        n = city["name"]
        native = city_native[n]
        emit(native, city_blueprints[n], "city", city_conn[n])
        native_report["cities"].append({"name": n, "native": native, "connections": len(city_conn[n])})

    for r in routes_cfg["routes"]:
        rid = r["id"]
        native = route_native[rid]
        emit(native, route_blueprints[rid], "route", route_conn[rid])
        native_report["routes"].append({"id": rid, "name": r["name"], "native": native, "connections": len(route_conn[rid])})

    # Register Aurelis map group.
    groups_path = engine / "data" / "maps" / "map_groups.json"
    groups = load_json(groups_path)
    group_name = "gMapGroup_Aurelis"
    if group_name not in groups["group_order"]:
        groups["group_order"].append(group_name)
    groups[group_name] = map_names
    groups_path.write_text(json.dumps(groups, indent=2) + "\n", encoding="utf-8")

    # Register layouts.
    layouts_path = engine / "data" / "layouts" / "layouts.json"
    layouts = load_json(layouts_path)
    existing = {x["id"] for x in layouts["layouts"]}
    layouts["layouts"].extend(x for x in layouts_to_add if x["id"] not in existing)
    layouts_path.write_text(json.dumps(layouts, indent=2) + "\n", encoding="utf-8")

    # Replace the truck start with direct spawn in Lunaris.
    new_game = engine / "src" / "new_game.c"
    text = new_game.read_text(encoding="utf-8")
    old = "SetWarpDestination(MAP_GROUP(MAP_INSIDE_OF_TRUCK), MAP_NUM(MAP_INSIDE_OF_TRUCK), WARP_ID_NONE, -1, -1);"
    new = "SetWarpDestination(MAP_GROUP(MAP_LUNARIS), MAP_NUM(MAP_LUNARIS), WARP_ID_NONE, 15, 13);"
    if old not in text:
        raise SystemExit("[native] expected Emerald truck start hook not found")
    text = text.replace(old, new, 1)
    new_game.write_text(text, encoding="utf-8")

    out = project / "generated" / "native_integration.json"
    out.write_text(json.dumps(native_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[native] Registered {len(native_report['cities'])} cities + {len(native_report['routes'])} routes")
    print("[native] New Game spawn redirected to MAP_LUNARIS at (15,13)")
    print("[native] Visual status: development tileset only; no inherited story/NPC events enabled")


if __name__ == "__main__":
    main()
