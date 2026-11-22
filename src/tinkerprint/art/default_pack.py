"""The Woodland Guild. Hand-edited sprites and two panoramic workshops, exported as plain JSON."""
from . import _coats, _heads, _kit, _tokens, _workshop
from ._colors import EDGES, INK, STAT_KEYS, WANDERER, ramp
from ._landscape import valley
from ._companions import PARTS as COMPANIONS

TOOLS = {
    'Interface': ('fan', 'frame'), 'Logic': ('orrery', 'runebook'),
    'Infra': ('pavise', 'helmlet'), 'Tools': ('spanner', 'hammer'),
    'Data': ('scope', 'map'), 'Models': ('lantern', 'flask'),
    'Tests': ('foil', 'hourglass'), 'Docs': ('nib', 'books'),
    'Systems': ('key', 'cog'), 'Art': ('washbrush', 'paints'),
    'Worlds': ('spade', 'sprout'), 'Lore': ('codex', 'candle'),
    'Community': ('teapot', 'mug'),
}

LOOKS = {}
for stat,(item,trinket) in TOOLS.items():
    grip, shoulder = _coats.POSES[stat]
    LOOKS[stat] = dict(hat=stat.lower()+'-head', body=stat.lower()+'-coat', item=item,
                       trinket=trinket, gear=stat.lower()+'-gear', grip=list(grip), shoulder=list(shoulder))

PARTS = {**_heads.PARTS, **_coats.PARTS, **_kit.ITEMS, **_kit.GEAR, **_kit.SLEEVES, **_tokens.PARTS, **COMPANIONS, **_workshop.PARTS}
PARTS.update({
    'cape': _kit.CAPE, 'pack': _kit.PACK, 'hand': _kit.HAND,
    'ridge': valley('builder'), 'vale': valley('tinkerer'),
})

PACK = {
    'version': 2, 'name': 'woodland-guild', 'canvas': [48,48], 'hand': [32,29],
    'mixed_gear_only': True, 'skin_colors': ramp('e<>L'), 'presentations': _heads.PRESENTATIONS,
    'ink': INK, 'outline': INK['k'], 'edges': EDGES,
    'stat_colors': {s:ramp(keys) for s,keys in STAT_KEYS.items()}, 'wanderer_colors': ramp(WANDERER),
    'sets': {
        'builder': dict(zip(('plate','floor','wall','wall2','mortar','board','board2'), ramp('?%!/?OL')),
                        scene='ridge', studio='blue-studio'),
        'tinkerer': dict(zip(('plate','floor','wall','wall2','mortar','board','board2'), ramp('}|LOLlP')),
                         scene='vale', studio='amber-studio'),
    },
    'looks': LOOKS,
    'generalist': dict(hat='traveler-head',body='traveler-coat',item='crook',back='pack',grip=[32,30]),
    'familiars': {'claude':'nightlight','codex':'typewriter','agy':'orrery-mobile','default':'gramophone'},
    'icons': {
        'first-light':'sunrise','founder':'flag','thousandfold':'coins','shipwright':'ship',
        'long-road':'signpost','swarm-day':'mail','necromancer':'skull','polyglot':'bubbles',
        'full-party':'pennants','seasons-turn':'wheel','milestone':'star',
    }, 'parts': PARTS,
}
