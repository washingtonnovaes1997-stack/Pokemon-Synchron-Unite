#!/usr/bin/env python3
from __future__ import annotations
import json
from collections import deque
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; MAPS=ROOT/"generated"/"maps"; WORLD=ROOT/"game"/"world"
def fail(x): raise SystemExit("[mapvalidate] ERROR: "+x)
def walkable(v): return v not in {3,4,5,9}
def connected(m):
 g=m["grid"]; h=len(g); w=len(g[0]); starts=[(e["x"],e["y"]) for e in m.get("entrances",[])];
 if not starts:return True
 q=deque([starts[0]]); seen={starts[0]}
 while q:
  x,y=q.popleft()
  for nx,ny in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
   if 0<=nx<w and 0<=ny<h and (nx,ny) not in seen and walkable(g[ny][nx]):seen.add((nx,ny));q.append((nx,ny))
 return all(s in seen for s in starts) and all((f["x"],f["y"]) in seen for f in m.get("features",[]))
def main():
 manifest=json.loads((WORLD/"map_manifest.json").read_text()); routes=json.loads((WORLD/"routes.json").read_text()); region=json.loads((WORLD/"region_01.json").read_text()); gyms={g["city"] for g in region["gyms"]}
 city_files=list(MAPS.glob("city_*.json")); route_files=list(MAPS.glob("route_*.json"))
 if len(city_files)!=34:fail(f"expected 34 city blueprints, found {len(city_files)}")
 if len(route_files)!=len(routes["routes"]):fail(f"expected {len(routes['routes'])} route blueprints, found {len(route_files)}")
 required={"pokemon_center","shop","landmark","residential_a","residential_b","npc_plaza","fly_point"}
 for p in city_files:
  m=json.loads(p.read_text()); kinds={f["kind"] for f in m["features"]}
  if not required<=kinds:fail(f"{m['name']} missing features: {sorted(required-kinds)}")
  if m["name"] in gyms and "gym" not in kinds:fail(f"gym city {m['name']} has no gym anchor")
  if len(m["npc_slots"])<8:fail(f"{m['name']} needs at least 8 NPC slots")
  if not connected(m):fail(f"{m['name']} has unreachable entrance or feature")
 interiors=json.loads((MAPS/"interiors.json").read_text()); expected=34*4+16
 if len(interiors)!=expected:fail(f"expected {expected} interiors, found {len(interiors)}")
 corpus=" ".join(p.read_text().lower() for p in city_files+route_files)
 for bad in ("littleroot","petalburg","rustboro","slateport","mauville","hoenn"):
  if bad in corpus:fail(f"Emerald reference found in generated maps: {bad}")
 print(f"[mapvalidate] PASS cities=34 routes={len(route_files)} interiors={len(interiors)}")
if __name__=="__main__":main()
