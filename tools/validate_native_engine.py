#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

def fail(msg): raise SystemExit('[native-validate] ERROR: '+msg)

def main():
 p=argparse.ArgumentParser(); p.add_argument('--engine',required=True); a=p.parse_args(); e=Path(a.engine)
 groups=json.loads((e/'data/maps/map_groups.json').read_text())
 maps=groups.get('gMapGroup_Aurelis',[])
 if len(maps)!=74: fail(f'expected 74 Aurelis maps, found {len(maps)}')
 if len(set(maps))!=74: fail('duplicate native map names')
 if 'Lunaris' not in maps: fail('Lunaris not registered')
 layouts=json.loads((e/'data/layouts/layouts.json').read_text())['layouts']
 aurelis=[x for x in layouts if x['id'].startswith('LAYOUT_AURELIS') or x['id']=='LAYOUT_LUNARIS' or any(x['name'].startswith(n+'_') for n in maps)]
 if len(aurelis)<74: fail(f'expected at least 74 Aurelis layouts, found {len(aurelis)}')
 for n in maps:
  d=e/'data/maps'/n
  if not (d/'map.json').exists(): fail(f'missing map.json for {n}')
  if not (d/'scripts.inc').exists(): fail(f'missing scripts.inc for {n}')
  m=json.loads((d/'map.json').read_text())
  if m.get('show_map_name') is not False: fail(f'{n} must hide inherited map-section popup during development')
 ng=(e/'src/new_game.c').read_text()
 if 'MAP_LUNARIS' not in ng: fail('New Game does not point to Lunaris')
 if 'MAP_INSIDE_OF_TRUCK), MAP_NUM(MAP_INSIDE_OF_TRUCK), WARP_ID_NONE, -1, -1' in ng: fail('Emerald truck start still active')
 print(f'[native-validate] PASS Aurelis maps={len(maps)} layouts>={len(aurelis)} NewGame=Lunaris')
if __name__=='__main__': main()
