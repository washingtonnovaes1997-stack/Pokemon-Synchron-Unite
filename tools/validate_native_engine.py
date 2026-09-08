#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

def fail(msg): raise SystemExit('[native-validate] ERROR: '+msg)

def main():
 p=argparse.ArgumentParser(); p.add_argument('--engine',required=True); a=p.parse_args(); e=Path(a.engine)
 groups=json.loads((e/'data/maps/map_groups.json').read_text())
 maps=groups.get('gMapGroup_Aurelis',[])
 expected=226
 if len(maps)!=expected: fail(f'expected {expected} Aurelis maps, found {len(maps)}')
 if len(set(maps))!=expected: fail('duplicate native map names')
 if 'Lunaris' not in maps: fail('Lunaris not registered')
 interior_count=sum(1 for n in maps if n.startswith('AurelisInterior_'))
 route_count=sum(1 for n in maps if n.startswith('AurelisRoute_'))
 city_count=expected-interior_count-route_count
 if (city_count,route_count,interior_count)!=(34,40,152): fail(f'wrong map composition: cities={city_count} routes={route_count} interiors={interior_count}')
 layouts=json.loads((e/'data/layouts/layouts.json').read_text())['layouts']
 ids={x['id'] for x in layouts}
 for n in maps:
  lid='LAYOUT_'+n.upper()
  if lid not in ids: fail(f'missing layout {lid}')
  d=e/'data/maps'/n
  if not (d/'map.json').exists(): fail(f'missing map.json for {n}')
  if not (d/'scripts.inc').exists(): fail(f'missing scripts.inc for {n}')
  m=json.loads((d/'map.json').read_text())
  if m.get('show_map_name') is not False: fail(f'{n} must hide inherited map-section popup during development')
 for n in maps:
  if not n.startswith('AurelisInterior_'): continue
  m=json.loads((e/'data/maps'/n/'map.json').read_text())
  if len(m.get('warp_events',[]))!=1: fail(f'{n} must have exactly one return warp')
 ng=(e/'src/new_game.c').read_text()
 if 'MAP_LUNARIS' not in ng: fail('New Game does not point to Lunaris')
 if 'MAP_INSIDE_OF_TRUCK), MAP_NUM(MAP_INSIDE_OF_TRUCK), WARP_ID_NONE, -1, -1' in ng: fail('Emerald truck start still active')
 print(f'[native-validate] PASS maps={expected} cities=34 routes=40 interiors=152 NewGame=Lunaris')
if __name__=='__main__': main()
