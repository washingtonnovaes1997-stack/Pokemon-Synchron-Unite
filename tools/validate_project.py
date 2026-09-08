#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "game" / "project.json"
WORLD = ROOT / "game" / "world" / "region_01.json"
CAST = ROOT / "game" / "world" / "cast.json"
MANIFEST = ROOT / "game" / "world" / "map_manifest.json"

FORBIDDEN = {
    "littleroot","oldale","petalburg","rustboro","dewford","slateport","mauville",
    "verdanturf","fallarbor","lavaridge","fortree","lilycove","mossdeep","sootopolis",
    "pacifidlog","ever grande","roxanne","brawly","wattson","flannery","norman",
    "winona","tate","liza","wallace","steven","archie","maxie","may","brendan"
}

def fail(message: str) -> None:
    raise SystemExit(f"[validate] ERROR: {message}")

def load(path: Path):
    if not path.exists(): fail(f"missing {path.relative_to(ROOT)}")
    try: return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc: fail(f"invalid JSON in {path}: {exc}")

def main() -> None:
    project, world, cast, manifest = map(load, [CONFIG, WORLD, CAST, MANIFEST])
    for key in ["project_name","engine","regions"]:
        if key not in project: fail(f"missing required project field: {key}")
    cities = world.get("cities", [])
    gyms = world.get("gyms", [])
    if len(cities) != 34: fail(f"expected 34 cities, found {len(cities)}")
    if len(gyms) != 16: fail(f"expected 16 gyms, found {len(gyms)}")
    city_names = [c["name"] for c in cities]
    if len(set(city_names)) != 34: fail("city names must be unique")
    leaders = [g["leader"] for g in gyms]
    if len(set(leaders)) != 16: fail("gym leaders must be unique")
    if len(manifest.get("city_map_specs", [])) != 34: fail("map manifest must define all 34 cities")
    corpus = " ".join([json.dumps(world), json.dumps(cast), json.dumps(manifest)]).lower()
    hits = sorted(x for x in FORBIDDEN if x in corpus)
    if hits: fail("forbidden Emerald player-facing names detected: " + ", ".join(hits))
    print(f"[validate] Project: {project['project_name']}")
    print(f"[validate] Region: {world['name']} | Cities: {len(cities)} | Gyms: {len(gyms)}")
    print(f"[validate] Original leaders: {len(leaders)} | Emerald-name guard: PASS")
    print("[validate] Large world-definition milestone passed.")

if __name__ == "__main__": main()
