"""The built-in art pack: the colors, and which of the Keepsake art's named pieces each trade wears.

The drawings are code. A pack is plain JSON that recolors them and reassigns the named pieces.
"""
from ._colors import STAT_KEYS, WANDERER, ramp

# Each trade's held tool and its shelf trinket.
TOOLS = {
    'Interface': ('fan', 'frame'), 'Logic': ('orrery', 'runebook'),
    'Infra': ('pavise', 'helmlet'), 'Tools': ('spanner', 'hammer'),
    'Data': ('scope', 'map'), 'Models': ('lantern', 'flask'),
    'Tests': ('foil', 'hourglass'), 'Docs': ('nib', 'books'),
    'Systems': ('key', 'cog'), 'Art': ('washbrush', 'paints'),
    'Worlds': ('spade', 'sprout'), 'Lore': ('codex', 'candle'),
    'Community': ('teapot', 'mug'),
}

LOOKS = {stat: dict(hat=stat.lower() + '-head', body=stat.lower() + '-coat', item=item, trinket=trinket,
                    gear=stat.lower() + '-gear')
         for stat, (item, trinket) in TOOLS.items()}

PACK = {
    'version': 3, 'name': 'keepsake',
    'skin_colors': ramp('e<>L'),
    'stat_colors': {s: ramp(keys) for s, keys in STAT_KEYS.items()}, 'wanderer_colors': ramp(WANDERER),
    'sets': {
        'builder': dict(zip(('plate', 'floor', 'wall2'), ramp('?%/')), scene='ridge'),
        'tinkerer': dict(zip(('plate', 'floor', 'wall2'), ramp('}|O')), scene='vale'),
    },
    'looks': LOOKS,
    'generalist': dict(hat='traveler-head', body='traveler-coat', item='crook'),
    'icons': {
        'first-light': 'sunrise', 'founder': 'flag', 'thousandfold': 'coins', 'shipwright': 'ship',
        'long-road': 'signpost', 'swarm-day': 'mail', 'necromancer': 'skull', 'polyglot': 'bubbles',
        'full-party': 'pennants', 'seasons-turn': 'wheel', 'milestone': 'star',
    },
}
