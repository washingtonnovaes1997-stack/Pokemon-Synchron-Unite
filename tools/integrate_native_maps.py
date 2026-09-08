#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, re, struct
from pathlib import Path

def slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]", "", text.replace(" ", "_"))
def const(text: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", text.upper()).strip("_")
def load_json(path: Path): return json.loads(path.read_text(encoding="utf-8"))
def write_bin(path: Path, values: list[int]):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"".join(struct.pack("<H", v & 0xFFFF) for v in values))
def native_value(code: int) -> int: return 0x3000 | max(1, min(code, 10))

def build_map_json(name, layout_id, kind, connections=None, warps=None):
    map_type = "MAP_TYPE_TOWN" if kind == "city" else ("MAP_TYPE_INDOOR" if kind == "interior" else "MAP_TYPE_ROUTE")
    return {
        "id": f"MAP_{const(name)}", "name": name, "layout": layout_id, "music": "MUS_NONE",
        "region": "REGION_HOENN", "region_map_section": "MAPSEC_LITTLEROOT_TOWN",
        "requires_flash": False, "weather": "WEATHER_NONE", "map_type": map_type,
        "allow_cycling": kind != "interior", "allow_escaping": False, "allow_running": True,
        "show_map_name": False, "battle_scene": "MAP_BATTLE_SCENE_NORMAL",
        "connections": connections or None, "object_events": [], "warp_events": warps or [],
        "coord_events": [], "bg_events": []
    }

def simple_interior_bp(size):
    w,h=size; grid=[[2 for _ in range(w)] for _ in range(h)]
    for x in range(w): grid[0][x]=5; grid[h-1][x]=5
    for y in range(h): grid[y][0]=5; grid[y][w-1]=5
    grid[h-1][w//2]=2
    return {"width":w,"height":h,"grid":grid}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--project",default="."); ap.add_argument("--engine",required=True); args=ap.parse_args()
    project=Path(args.project).resolve(); engine=Path(args.engine).resolve(); generated=project/"generated"/"maps"; world=project/"game"/"world"
    index=load_json(generated/"map_build_index.json"); routes_cfg=load_json(world/"routes.json"); region_cfg=load_json(world/"region_01.json"); interiors_cfg=load_json(generated/"interiors.json")
    city_blueprints={}; route_blueprints={}
    for fn in index["city_files"]:
        m=load_json(generated/fn); city_blueprints[m["name"]]=m
    for fn in index["route_files"]:
        m=load_json(generated/fn); route_blueprints[m["id"]]=m
    city_native={n:slug(n) for n in city_blueprints}; route_native={rid:f"AurelisRoute_{rid}" for rid in route_blueprints}
    interior_native={i["id"]: "AurelisInterior_"+slug(i["id"]) for i in interiors_cfg}

    dirs=["up","right","down","left"]; opposite={"up":"down","down":"up","left":"right","right":"left"}
    city_conn={n:[] for n in city_blueprints}; route_conn={rid:[] for rid in route_blueprints}; used={n:0 for n in city_blueprints}
    for r in routes_cfg["routes"]:
        rid=r["id"]; a,b=r["from"],r["to"]; da=dirs[used[a]%4]; db=dirs[used[b]%4]; used[a]+=1; used[b]+=1
        if len(city_conn[a])<4:
            city_conn[a].append({"map":f"MAP_{const(route_native[rid])}","offset":0,"direction":da}); route_conn[rid].append({"map":f"MAP_{const(city_native[a])}","offset":0,"direction":opposite[da]})
        if len(city_conn[b])<4:
            city_conn[b].append({"map":f"MAP_{const(route_native[rid])}","offset":0,"direction":db}); route_conn[rid].append({"map":f"MAP_{const(city_native[b])}","offset":0,"direction":opposite[db]})

    by_city={n:[] for n in city_blueprints}
    for i in interiors_cfg: by_city[i["city"]].append(i)
    map_names=[]; layouts_to_add=[]
    report={"cities":[],"routes":[],"interiors":[],"start_map":"Lunaris","development_tileset":True}

    def emit(native_name,bp,kind,connections=None,warps=None,primary="gTileset_General",secondary="gTileset_Petalburg"):
        map_names.append(native_name); layout_id=f"LAYOUT_{const(native_name)}"; ld=engine/"data/layouts"/native_name; ld.mkdir(parents=True,exist_ok=True)
        write_bin(ld/"map.bin",[native_value(v) for row in bp["grid"] for v in row]); write_bin(ld/"border.bin",[native_value(1)]*4)
        layouts_to_add.append({"id":layout_id,"name":f"{native_name}_Layout","width":bp["width"],"height":bp["height"],"primary_tileset":primary,"secondary_tileset":secondary,"border_filepath":f"data/layouts/{native_name}/border.bin","blockdata_filepath":f"data/layouts/{native_name}/map.bin","layout_version":"emerald"})
        mp=engine/"data/maps"/native_name; mp.mkdir(parents=True,exist_ok=True)
        (mp/"map.json").write_text(json.dumps(build_map_json(native_name,layout_id,kind,connections,warps),indent=2)+"\n",encoding="utf-8")
        (mp/"scripts.inc").write_text(f"{native_name}_MapScripts::\n\t.byte 0\n",encoding="utf-8")

    # Cities with native warps into all planned interiors.
    for city in region_cfg["cities"]:
        n=city["name"]; bp=city_blueprints[n]; feature_by_kind={f["kind"]:f for f in bp.get("features",[])}; warps=[]
        kind_anchor={"pokemon_center":"pokemon_center","shop":"shop","house_small":"residential_a","house_large":"residential_b","gym":"gym"}
        city_interiors=by_city[n]
        for idx,i in enumerate(city_interiors):
            anchor=feature_by_kind.get(kind_anchor.get(i["kind"],"npc_plaza"),{"x":bp["width"]//2,"y":bp["height"]//2})
            warps.append({"x":anchor["x"],"y":anchor["y"],"elevation":0,"dest_map":f"MAP_{const(interior_native[i['id']])}","dest_warp_id":"0"})
        emit(city_native[n],bp,"city",city_conn[n],warps)
        report["cities"].append({"name":n,"native":city_native[n],"connections":len(city_conn[n]),"interior_warps":len(warps)})

    for r in routes_cfg["routes"]:
        rid=r["id"]; emit(route_native[rid],route_blueprints[rid],"route",route_conn[rid]); report["routes"].append({"id":rid,"name":r["name"],"native":route_native[rid],"connections":len(route_conn[rid])})

    # 152 new interiors. Return warp targets the city's matching exterior warp index.
    for i in interiors_cfg:
        n=i["city"]; siblings=by_city[n]; exterior_warp_index=next(j for j,x in enumerate(siblings) if x["id"]==i["id"])
        bp=simple_interior_bp(i["size"]); return_x=i["size"][0]//2; return_y=i["size"][1]-1
        warps=[{"x":return_x,"y":return_y,"elevation":0,"dest_map":f"MAP_{const(city_native[n])}","dest_warp_id":str(exterior_warp_index)}]
        secondary="gTileset_PokemonCenter" if i["kind"]=="pokemon_center" else ("gTileset_Shop" if i["kind"]=="shop" else "gTileset_GenericBuilding")
        emit(interior_native[i["id"]],bp,"interior",None,warps,"gTileset_Building",secondary)
        report["interiors"].append({"id":i["id"],"city":n,"kind":i["kind"],"native":interior_native[i["id"]]})

    groups_path=engine/"data/maps/map_groups.json"; groups=load_json(groups_path); group="gMapGroup_Aurelis"
    if group not in groups["group_order"]: groups["group_order"].append(group)
    groups[group]=map_names; groups_path.write_text(json.dumps(groups,indent=2)+"\n",encoding="utf-8")
    layouts_path=engine/"data/layouts/layouts.json"; layouts=load_json(layouts_path); existing={x["id"] for x in layouts["layouts"]}; layouts["layouts"].extend(x for x in layouts_to_add if x["id"] not in existing); layouts_path.write_text(json.dumps(layouts,indent=2)+"\n",encoding="utf-8")

    ng=engine/"src/new_game.c"; text=ng.read_text(encoding="utf-8"); old="SetWarpDestination(MAP_GROUP(MAP_INSIDE_OF_TRUCK), MAP_NUM(MAP_INSIDE_OF_TRUCK), WARP_ID_NONE, -1, -1);"; new="SetWarpDestination(MAP_GROUP(MAP_LUNARIS), MAP_NUM(MAP_LUNARIS), WARP_ID_NONE, 15, 13);"
    if old not in text: raise SystemExit("[native] expected Emerald truck start hook not found")
    ng.write_text(text.replace(old,new,1),encoding="utf-8")
    (project/"generated/native_integration.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"[native] Registered cities={len(report['cities'])} routes={len(report['routes'])} interiors={len(report['interiors'])} total={len(map_names)}")
    print("[native] New Game -> MAP_LUNARIS (15,13); inherited story/NPC events remain disabled")
if __name__=="__main__": main()
