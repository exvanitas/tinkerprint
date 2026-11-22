"""The guild palette. Material ramps borrow adjacent hues, especially at either end."""
# Charcoal, umber, russet, biscuit, vellum
INK = {
    'k': '#1b1a2b', 'd': '#302b41', 'P': '#493446', 'L': '#70505a',
    'O': '#925f52', 'l': '#b87a56', 'o': '#d69b68', 'a': '#e9ba85',
    'e': '#f6dba5', 'w': '#fff0c9',
    # Blue-steel, pewter and ivory
    'f': '#38485b', 'n': '#526479', 'N': '#70869a', 'M': '#96a8ab',
    's': '#b8c2b9', 'm': '#dbe0c8', 'c': '#e9d4ab', 'S': '#aa9c89',
    # Old brass, marigold, vermilion
    'G': '#a06a42', 'g': '#dfaa54', 'y': '#ffda80', 'h': '#ef9250',
    'r': '#cf5653', 'R': '#913e50', 'i': '#ffae80',
    # Pine, fern, reed, blue spruce, celadon
    'J': '#345456', 'j': '#50806d', 't': '#83aa7a', 'v': '#b3ce90',
    'u': '#317c86', 'b': '#61bfba', 'z': '#b6e5cb',
    # Blue, iris, violet, rose
    '1': '#414c77', '2': '#536caa', '3': '#85abdc', '4': '#d6e4e6',
    '5': '#534368', '6': '#866293', '7': '#b49cd4', '8': '#f4d2df',
    '9': '#673a57', 'p': '#aa456e', 'q': '#e17197', 'Q': '#ffc3c0',
    # Mineral surfaces and atmospheric colors
    'I': '#a4beb3', 'E': '#748e8c', 'D': '#536c71', 'K': '#3c535b',
    'x': '#c79b83', '0': '#dfb48f',
    # Midnight ridge and plum lake, arranged in close values behind the characters.
    '!': '#192b38', '?': '#263e50', '%': '#314c60', '/': '#466575',
    '{': '#30293a', '}': '#49374b', '|': '#594256', ';': '#735766',
    '<': '#f2ba97', '>': '#c3816e', '(': '#a48692', ')': '#746a7d', '=': '#807674',
}
STAT_KEYS = {
    'Interface': 'Qqp9', 'Logic': '4321', 'Infra': 'mMnf', 'Tools': 'yhlL',
    'Data': 'zbuJ', 'Models': '8765', 'Tests': 'irRP', 'Docs': 'weaL',
    'Systems': '4MNf', 'Art': 'QirR', 'Worlds': 'vtjJ',
    'Lore': '8qp9', 'Community': 'eygG',
}
WANDERER = 'eaol'
SKIN_KEYS = '@+:~'


def ramp(keys):
    return [INK[k] for k in keys]


# Nearest cool edge on a lit side, and the edge in shadow. Each color is in the master table.
EDGE_GROUPS = (
    ('PLOloaewcSGgyhirR0x<>', 'O', 'P'),
    ('fnNMsmIEDK=', 'n', 'f'),
    ('Jjtvubz', 'j', 'J'), ('1234', '2', '1'), ('5678()', '6', '5'),
    ('9pqQ', 'p', '9'), ('kd', 'P', 'k'),
)
EDGES = {INK[k]: [INK[light], INK[dark]] for keys, light, dark in EDGE_GROUPS for k in keys}
