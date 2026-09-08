#!/usr/bin/env python3
from __future__ import annotations
import json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
WORLD=ROOT/'game'/'world'; MAPS=ROOT/'generated'/'maps'; OUT=ROOT/'generated'/'events'

def load(p): return json.loads(p.read_text(encoding='utf-8'))
def slug(s): return re.sub(r'[^a-z0-9]+','_',s.lower()).strip('_')

def dialogue(name, role, city):
    return [
        f"Eu sou {name}. Aqui em {city}, trabalho como {role}.",
        f"Aurelis muda muito de uma região para outra. Observe o ambiente e seus Pokémon.",
    ]

def main():
    roster=load(WORLD/'npc_roster.json'); cast=load(WORLD/'cast.json'); story=load(WORLD/'story_arc.json')
    OUT.mkdir(parents=True,exist_ok=True)
    city_plans=[]
    for entry in roster['city_npcs']:
        city=entry['city']; bp=load(MAPS/f"city_{slug(city)}.json"); slots=bp['npc_slots']
        people=[]
        for idx,key in enumerate(('civic','specialist')):
            p=entry[key]; pos=slots[idx]
            people.append({
                'id':f"NPC_{slug(city).upper()}_{idx+1}", 'name':p['name'], 'role':p['role'],
                'x':pos['x'],'y':pos['y'],'movement':'wander_small','sprite_status':'original_sprite_required',
                'dialogue':dialogue(p['name'],p['role'],city)
            })
        city_plans.append({'city':city,'enabled_in_engine':False,'activation_gate':'original_overworld_sprites_ready','npcs':people})
    (OUT/'city_npc_events.json').write_text(json.dumps(city_plans,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    key_cast=[]
    for p in cast['protagonists']: key_cast.append({'name':p['name'],'role':'protagonist'})
    for p in cast['rivals']: key_cast.append({'name':p['name'],'role':'rival'})
    key_cast += [
        {'name':cast['professor']['name'],'role':'professor'},
        {'name':cast['enemy_team']['leader'],'role':'enemy_leader'},
        *({'name':n,'role':'enemy_admin'} for n in cast['enemy_team']['admins']),
        {'name':cast['league']['champion'],'role':'champion'},
        *({'name':n,'role':'league_council'} for n in cast['league']['council'])
    ]
    (OUT/'key_character_events.json').write_text(json.dumps({'characters':key_cast,'enabled_in_engine':False,'reason':'original character sprites required before activation'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    hooks=[]
    acts=story.get('acts',story.get('story_acts',[]))
    for i,act in enumerate(acts,1):
        hooks.append({'hook_id':f'STORY_ACT_{i:02d}','act':i,'title':act.get('title',act.get('name',f'Act {i}')),'status':'script_hook_reserved'})
    (OUT/'story_hooks.json').write_text(json.dumps({'hooks':hooks},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f"[eventgen] city NPC plans={len(city_plans)} named civic/specialist NPCs={sum(len(x['npcs']) for x in city_plans)} key characters={len(key_cast)}")
    print('[eventgen] Visual activation remains gated on original sprites.')
if __name__=='__main__': main()
