#!/usr/bin/env python3
from __future__ import annotations
import json, re
from collections import deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORLD = ROOT / "game" / "world"
OUT = ROOT / "generated" / "maps"

def load(name): return json.loads((WORLD/name).read_text(encoding="utf-8"))
def slug(s): return re.sub(r"[^a-z0-9]+","_",s.lower()).strip("_")

def carve_rect(grid,x0,y0,x1,y1,v):
    h,w=len(grid),len(grid[0])
    for y in range(max(0,y0),min(h,y1)):
        for x in range(max(0,x0),min(w,x1)): grid[y][x]=v

def generate_city(name,w,h,biome,rules,gym=False):
    arch=rules["city_archetypes"][biome]; codes=rules["terrain_codes"]
    ground=codes[arch["ground"]]; path=codes[arch["path"]]
    g=[[ground for _ in range(w)] for _ in range(h)]
    cx,cy=w//2,h//2
    # Strong central pedestrian spine and cross-axis guarantee connected traversal.
    carve_rect(g,3,cy-1,w-3,cy+2,path); carve_rect(g,cx-1,3,cx+2,h-3,path)
    if arch["water"]:
        carve_rect(g,2,2,max(5,w//5),h-2,codes["water"])
        carve_rect(g,2,cy-1,max(5,w//5),cy+2,path)
    # Distinct silhouettes are deterministic by archetype pattern.
    p=arch["pattern"]
    if p in {"crescent","spiral","forest_ring","oasis_ring","cliff_ring"}:
        for r in range(4,min(w,h)//3,4):
            for x in range(cx-r,cx+r+1):
                for y in (cy-r,cy+r):
                    if 2<=x<w-2 and 2<=y<h-2: g[y][x]=path
    elif p in {"grid","mega_grid","rail_grid","ruin_grid"}:
        for x in range(5,w-4,7): carve_rect(g,x,3,x+2,h-3,path)
        for y in range(5,h-4,7): carve_rect(g,3,y,w-3,y+2,path)
    elif p in {"terraces","switchback","ridge"}:
        for y in range(5,h-4,6): carve_rect(g,4,y,w-4,y+2,path)
    elif p in {"sunburst","constellation","snowflake","radial"}:
        for d in range(-min(cx,cy)+4,min(cx,cy)-4):
            x=cx+d; y=cy+d
            if 2<=x<w-2 and 2<=y<h-2: g[y][x]=path
            y=cy-d
            if 2<=x<w-2 and 2<=y<h-2: g[y][x]=path
    # Feature anchors use coordinates, not Emerald map objects.
    features=[]
    anchors=[("pokemon_center",cx-7,cy-6),("shop",cx+5,cy-6),("landmark",cx,cy),("residential_a",cx-10,cy+6),("residential_b",cx+8,cy+6),("npc_plaza",cx,cy+3),("fly_point",cx+3,cy+3)]
    if gym: anchors += [("gym",cx+8,cy-12),("badge_gate",cx+8,cy-8)]
    for kind,x,y in anchors:
        x=max(3,min(w-4,x)); y=max(3,min(h-4,y)); g[y][x]=codes["landmark"]; features.append({"kind":kind,"x":x,"y":y})
    entrances=[{"direction":"north","x":cx,"y":2},{"direction":"south","x":cx,"y":h-3},{"direction":"west","x":2,"y":cy},{"direction":"east","x":w-3,"y":cy}]
    for e in entrances: g[e["y"]][e["x"]]=path
    return {"name":name,"id":slug(name),"kind":"city","biome":biome,"width":w,"height":h,"pattern":p,"landmark":arch["landmark"],"grid":g,"features":features,"entrances":entrances,"npc_slots":[{"id":i+1,"x":max(3,min(w-4,cx+(i%4)*2-3)),"y":max(3,min(h-4,cy+(i//4)*2+4))} for i in range(8)]}

def route_blueprint(r,idx,rules):
    w=rules["route_rules"]["min_width"]+(idx%4)*4; h=rules["route_rules"]["min_height"]+(idx%3)*4
    codes=rules["terrain_codes"]; g=[[codes["grass"] for _ in range(w)] for _ in range(h)]; cy=h//2
    carve_rect(g,1,cy-1,w-1,cy+2,codes["path"])
    return {"id":r["id"],"kind":"route","from":r["from"],"to":r["to"],"width":w,"height":h,"grid":g,"trainer_slots":[{"id":i+1,"x":4+i*3,"y":cy+(1 if i%2 else -2)} for i in range(rules["route_rules"]["trainer_slots"])],"item_slots":[{"id":i+1,"x":6+i*4,"y":max(2,cy-5+(i%3)*4)} for i in range(rules["route_rules"]["item_slots"])],"encounter_zones":rules["route_rules"]["encounter_zones"]}

def main():
    manifest=load("map_manifest.json"); region=load("region_01.json"); routes=load("routes.json"); rules=load("map_generation_rules.json")
    gyms={g["city"] for g in region["gyms"]}; OUT.mkdir(parents=True,exist_ok=True)
    maps=[]
    for name,w,h,biome in manifest["city_map_specs"]:
        m=generate_city(name,w,h,biome,rules,name in gyms); maps.append(m); (OUT/f"city_{slug(name)}.json").write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    route_maps=[]
    for i,r in enumerate(routes["routes"]):
        m=route_blueprint(r,i,rules); route_maps.append(m); (OUT/f"route_{slug(r['id'])}.json").write_text(json.dumps(m,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    interiors=[]
    for name,_,_,_ in manifest["city_map_specs"]:
        for kind in ("pokemon_center","shop","house_small","house_large"):
            spec=rules["interior_templates"][kind]; interiors.append({"id":f"{slug(name)}_{kind}","city":name,"kind":kind,"size":spec["size"],"rooms":spec["rooms"]})
        if name in gyms:
            spec=rules["interior_templates"]["gym"]; interiors.append({"id":f"{slug(name)}_gym","city":name,"kind":"gym","size":spec["size"],"rooms":spec["rooms"]})
    (OUT/"interiors.json").write_text(json.dumps(interiors,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    index={"cities":len(maps),"routes":len(route_maps),"interiors":len(interiors),"city_files":[f"city_{m['id']}.json" for m in maps],"route_files":[f"route_{slug(m['id'])}.json" for m in route_maps]}
    (OUT/"map_build_index.json").write_text(json.dumps(index,indent=2)+"\n",encoding="utf-8")
    print(f"[mapgen] cities={len(maps)} routes={len(route_maps)} interiors={len(interiors)}")
if __name__=="__main__": main()
