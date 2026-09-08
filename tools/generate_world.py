#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORLD = ROOT / "game" / "world"
OVERLAY = ROOT / "overlay"
GENERATED = ROOT / "generated"


def load(name: str):
    return json.loads((WORLD / name).read_text(encoding="utf-8"))


def c_id(text: str) -> str:
    text = text.upper()
    text = re.sub(r"[^A-Z0-9]+", "_", text).strip("_")
    return text


def main() -> None:
    region = load("region_01.json")
    routes = load("routes.json")
    gyms = load("gyms.json")
    cast = load("cast.json")
    npcs = load("npc_roster.json")
    maps = load("map_manifest.json")

    GENERATED.mkdir(parents=True, exist_ok=True)
    out_include = OVERLAY / "include" / "constants"
    out_include.mkdir(parents=True, exist_ok=True)

    index = {
        "region": region["name"],
        "region_id": region["region_id"],
        "cities": region["cities"],
        "gyms": gyms["gyms"],
        "routes": routes["routes"],
        "special_areas": routes["special_areas"],
        "protagonists": cast["protagonists"],
        "rivals": cast["rivals"],
        "enemy_team": cast["enemy_team"],
        "city_npcs": npcs["city_npcs"],
        "map_specs": maps["city_map_specs"],
    }
    (GENERATED / "world_index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "#ifndef GUARD_CONSTANTS_SYNCHRON_UNITE_WORLD_H",
        "#define GUARD_CONSTANTS_SYNCHRON_UNITE_WORLD_H",
        "",
        f"#define SYNCHRON_REGION_NAME \"{region['name']}\"",
        f"#define SYNCHRON_CITY_COUNT {len(region['cities'])}",
        f"#define SYNCHRON_GYM_COUNT {len(gyms['gyms'])}",
        f"#define SYNCHRON_ROUTE_COUNT {len(routes['routes'])}",
        f"#define SYNCHRON_SPECIAL_AREA_COUNT {len(routes['special_areas'])}",
        "",
    ]
    for city in region["cities"]:
        lines.append(f"#define SYNCHRON_CITY_{city['id']} \"{city['name']}\"")
    lines.append("")
    for gym in gyms["gyms"]:
        lines.append(f"#define SYNCHRON_GYM_{gym['number']}_LEADER \"{gym['leader']}\"")
        lines.append(f"#define SYNCHRON_GYM_{gym['number']}_CITY \"{gym['city']}\"")
        lines.append(f"#define SYNCHRON_GYM_{gym['number']}_LEVEL_CAP {gym['level_cap']}")
    lines += ["", "#endif // GUARD_CONSTANTS_SYNCHRON_UNITE_WORLD_H", ""]
    (out_include / "synchron_unite_world.h").write_text("\n".join(lines), encoding="utf-8")

    report = [
        "Pokemon Synchron Unite - generated world summary",
        f"Region: {region['name']}",
        f"Cities: {len(region['cities'])}",
        f"Gyms: {len(gyms['gyms'])}",
        f"Routes: {len(routes['routes'])}",
        f"Special areas: {len(routes['special_areas'])}",
        f"City NPC pairs: {len(npcs['city_npcs'])}",
        f"Map specs: {len(maps['city_map_specs'])}",
        "",
        "Generated automatically from game/world JSON manifests.",
    ]
    (GENERATED / "world_summary.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"[worldgen] Generated {GENERATED / 'world_index.json'}")
    print(f"[worldgen] Generated {out_include / 'synchron_unite_world.h'}")
    print(f"[worldgen] Cities={len(region['cities'])} Gyms={len(gyms['gyms'])} Routes={len(routes['routes'])}")


if __name__ == "__main__":
    main()
