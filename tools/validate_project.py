#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "game" / "project.json"
WORLD = ROOT / "game" / "world" / "region_01.json"
CAST = ROOT / "game" / "world" / "cast.json"
MANIFEST = ROOT / "game" / "world" / "map_manifest.json"
ROUTES = ROOT / "game" / "world" / "routes.json"
GYMS = ROOT / "game" / "world" / "gyms.json"
NPCS = ROOT / "game" / "world" / "npc_roster.json"

FORBIDDEN_LOCATIONS = {
    "littleroot","oldale","petalburg","rustboro","dewford","slateport","mauville",
    "verdanturf","fallarbor","lavaridge","fortree","lilycove","mossdeep","sootopolis",
    "pacifidlog","ever grande","hoenn"
}
FORBIDDEN_CHARACTERS = {
    "roxanne","brawly","wattson","flannery","norman","winona","tate","liza",
    "wallace","steven","archie","maxie","may","brendan"
}
FORBIDDEN_TEAMS = {"team aqua","team magma"}

def fail(message: str) -> None:
    raise SystemExit(f"[validate] ERROR: {message}")

def load(path: Path):
    if not path.exists(): fail(f"missing {path.relative_to(ROOT)}")
    try: return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc: fail(f"invalid JSON in {path}: {exc}")

def named_characters(cast, gyms_data, npcs):
    names = []
    names += [p["name"] for p in cast.get("protagonists", [])]
    names += [r["name"] for r in cast.get("rivals", [])]
    professor = cast.get("professor", {}).get("name")
    if professor: names.append(professor)
    enemy = cast.get("enemy_team", {})
    if enemy.get("leader"): names.append(enemy["leader"])
    names += enemy.get("admins", [])
    league = cast.get("league", {})
    if league.get("champion"): names.append(league["champion"])
    names += league.get("council", [])
    names += [x["name"] for x in cast.get("supporting_cast", [])]
    names += [g["leader"] for g in gyms_data.get("gyms", [])]
    for entry in npcs.get("city_npcs", []):
        names += [entry["civic"]["name"], entry["specialist"]["name"]]
    names += [x["name"] for x in npcs.get("team_vesper_field_commanders", [])]
    return names

def main() -> None:
    project, world, cast, manifest, routes, gyms_data, npcs = map(load, [CONFIG, WORLD, CAST, MANIFEST, ROUTES, GYMS, NPCS])
    for key in ["project_name","engine","regions"]:
        if key not in project: fail(f"missing required project field: {key}")

    cities = world.get("cities", [])
    gyms = world.get("gyms", [])
    route_list = routes.get("routes", [])
    specials = routes.get("special_areas", [])
    detailed_gyms = gyms_data.get("gyms", [])
    city_npcs = npcs.get("city_npcs", [])

    if len(cities) != 34: fail(f"expected 34 cities, found {len(cities)}")
    if len(gyms) != 16: fail(f"expected 16 gyms in region, found {len(gyms)}")
    if len(detailed_gyms) != 16: fail(f"expected 16 detailed gym definitions, found {len(detailed_gyms)}")
    if len(route_list) < 40: fail(f"expected at least 40 routes, found {len(route_list)}")
    if len(specials) < 7: fail(f"expected at least 7 special areas, found {len(specials)}")
    if len(city_npcs) != 34: fail(f"expected NPC definitions for 34 cities, found {len(city_npcs)}")
    if len(manifest.get("city_map_specs", [])) != 34: fail("map manifest must define all 34 cities")

    city_names = [c["name"] for c in cities]
    city_set = set(city_names)
    if len(city_set) != 34: fail("city names must be unique")
    bad_locations = sorted(name for name in city_names if name.lower() in FORBIDDEN_LOCATIONS)
    route_names = [r["name"] for r in route_list] + [x["name"] for x in specials]
    bad_locations += sorted(name for name in route_names if name.lower() in FORBIDDEN_LOCATIONS)
    if bad_locations: fail("forbidden Emerald location names detected: " + ", ".join(bad_locations))

    leaders = [g["leader"] for g in gyms]
    if len(set(leaders)) != 16: fail("gym leaders must be unique")
    detailed_leaders = [g["leader"] for g in detailed_gyms]
    if leaders != detailed_leaders: fail("region gym leader order and detailed gym leader order must match")

    for r in route_list:
        if r["from"] not in city_set or r["to"] not in city_set:
            fail(f"route {r['id']} points to unknown city: {r['from']} -> {r['to']}")
        if r["from"] == r["to"]:
            fail(f"route {r['id']} cannot connect a city to itself")

    npc_cities = [x["city"] for x in city_npcs]
    if set(npc_cities) != city_set: fail("NPC roster must cover every city exactly once")
    if len(npc_cities) != len(set(npc_cities)): fail("NPC roster contains duplicate city entries")

    gym_numbers = [g["number"] for g in detailed_gyms]
    if gym_numbers != list(range(1, 17)): fail("gym numbers must be sequential from 1 to 16")
    caps = [g["level_cap"] for g in detailed_gyms]
    if caps != sorted(caps): fail("gym level caps must be non-decreasing")

    character_names = named_characters(cast, gyms_data, npcs)
    bad_characters = sorted(name for name in character_names if name.lower() in FORBIDDEN_CHARACTERS)
    if bad_characters: fail("forbidden Emerald character names detected: " + ", ".join(bad_characters))
    if len(character_names) != len(set(n.lower() for n in character_names)):
        fail("named character roster contains duplicate names")

    enemy_name = cast.get("enemy_team", {}).get("name", "").lower()
    if enemy_name in FORBIDDEN_TEAMS: fail("forbidden Emerald enemy team detected")

    print(f"[validate] Project: {project['project_name']}")
    print(f"[validate] Region: {world['name']} | Cities: {len(cities)} | Gyms: {len(gyms)}")
    print(f"[validate] Routes: {len(route_list)} | Special areas: {len(specials)} | City NPC sets: {len(city_npcs)}")
    print(f"[validate] Named original characters checked: {len(character_names)}")
    print("[validate] Emerald location/character/team guards: PASS")
    print("[validate] Extended Aurelis world-definition milestone passed.")

if __name__ == "__main__": main()
