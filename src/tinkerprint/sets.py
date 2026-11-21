"""Stat sets: eight stats in a fixed order, and the class names that belong to each set."""
from __future__ import annotations

from itertools import combinations

BUILDER_STATS = ("Interface", "Logic", "Infra", "Tools", "Data", "Models", "Tests", "Docs")
TINKERER_STATS = ("Systems", "Tools", "Interface", "Art", "Worlds", "Lore", "Community", "Models")

# Builder stats a tinkerer profile maps from. None means "the project's main code stat".
# Docs has no tinkerer stat, so it stays unclassified.
TINKERER_FROM_BUILDER = {
    "Interface": "Interface",
    "Logic": "Systems",
    "Infra": "Systems",
    "Tools": "Tools",
    "Models": "Models",
    "Data": None,
    "Tests": None,
    "Docs": "",
}
TINKERER_CODE_STATS = ("Systems", "Tools", "Interface", "Models")
TINKERER_HAND_ONLY = ("Art", "Worlds", "Lore", "Community")

DESCRIPTIONS = {
    "builder": {
        "Interface": "Views, components, styles, input handling.",
        "Logic": "Application and service code: domain rules, state, APIs, core libraries.",
        "Infra": "CI, containers, deploys, infrastructure as code, service units, shell scripts.",
        "Tools": "CLIs, editor and browser extensions, generators, converters, build plugins.",
        "Data": "Schemas, migrations, queries, notebooks, pipelines.",
        "Models": "Training, fine-tuning, evaluation and model-serving code.",
        "Tests": "Tests, fixtures, benchmarks, validation suites.",
        "Docs": "Guides, references, decision records, changelogs.",
    },
    "tinkerer": {
        "Systems": "Application code and the machinery that runs it.",
        "Tools": "CLIs, extensions, generators, converters.",
        "Interface": "Views, components, styles, input handling.",
        "Art": "Pictures, sprites, shaders, visual work. Hand tags only.",
        "Worlds": "Levels, maps, scenes, settings. Hand tags only.",
        "Lore": "Stories, characters, writing. Hand tags only.",
        "Community": "Bots, servers and spaces for other people. Hand tags only.",
        "Models": "Training, fine-tuning, evaluation and model-serving code.",
    },
}

SPECIALIST = {
    "builder": {
        "Interface": "Illusionist",
        "Logic": "Sage",
        "Infra": "Warden",
        "Tools": "Artificer",
        "Data": "Cartographer",
        "Models": "Summoner",
        "Tests": "Inquisitor",
        "Docs": "Scribe",
    },
    "tinkerer": {
        "Systems": "Mechanist",
        "Tools": "Artificer",
        "Interface": "Illusionist",
        "Art": "Painter",
        "Worlds": "Worldsmith",
        "Lore": "Lorekeeper",
        "Community": "Innkeeper",
        "Models": "Summoner",
    },
}

GENERALIST = {"builder": "Adventurer", "tinkerer": "Wanderer"}

PAIR = {
    "builder": {
        ("Interface", "Logic"): "Spellblade",
        ("Interface", "Infra"): "Lamplighter",
        ("Interface", "Tools"): "Tinker",
        ("Interface", "Data"): "Seer",
        ("Interface", "Models"): "Dreamweaver",
        ("Interface", "Tests"): "Duelist",
        ("Interface", "Docs"): "Bard",
        ("Logic", "Infra"): "Paladin",
        ("Logic", "Tools"): "Engineer",
        ("Logic", "Data"): "Alchemist",
        ("Logic", "Models"): "Archmage",
        ("Logic", "Tests"): "Templar",
        ("Logic", "Docs"): "Loremaster",
        ("Infra", "Tools"): "Siegewright",
        ("Infra", "Data"): "Quartermaster",
        ("Infra", "Models"): "Beastmaster",
        ("Infra", "Tests"): "Sentinel",
        ("Infra", "Docs"): "Herald",
        ("Tools", "Data"): "Prospector",
        ("Tools", "Models"): "Golemancer",
        ("Tools", "Tests"): "Trapsmith",
        ("Tools", "Docs"): "Runesmith",
        ("Data", "Models"): "Oracle",
        ("Data", "Tests"): "Assayer",
        ("Data", "Docs"): "Chronicler",
        ("Models", "Tests"): "Augur",
        ("Models", "Docs"): "Mystic",
        ("Tests", "Docs"): "Arbiter",
    },
    "tinkerer": {
        ("Systems", "Tools"): "Engineer",
        ("Systems", "Interface"): "Spellblade",
        ("Systems", "Art"): "Clockmaker",
        ("Systems", "Worlds"): "Architect",
        ("Systems", "Lore"): "Sage",
        ("Systems", "Community"): "Steward",
        ("Systems", "Models"): "Archmage",
        ("Tools", "Interface"): "Tinker",
        ("Tools", "Art"): "Toymaker",
        ("Tools", "Worlds"): "Mapwright",
        ("Tools", "Lore"): "Runesmith",
        ("Tools", "Community"): "Quartermaster",
        ("Tools", "Models"): "Golemancer",
        ("Interface", "Art"): "Enchanter",
        ("Interface", "Worlds"): "Stagewright",
        ("Interface", "Lore"): "Bard",
        ("Interface", "Community"): "Herald",
        ("Interface", "Models"): "Dreamweaver",
        ("Art", "Worlds"): "Worldpainter",
        ("Art", "Lore"): "Illuminator",
        ("Art", "Community"): "Minstrel",
        ("Art", "Models"): "Conjurer",
        ("Worlds", "Lore"): "Mythmaker",
        ("Worlds", "Community"): "Gamekeeper",
        ("Worlds", "Models"): "Druid",
        ("Lore", "Community"): "Storyteller",
        ("Lore", "Models"): "Oracle",
        ("Community", "Models"): "Beastmaster",
    },
}

SETS = {"builder": BUILDER_STATS, "tinkerer": TINKERER_STATS}


def stats_of(set_name: str) -> tuple:
    return SETS[set_name]


def pair_name(set_name: str, a: str, b: str) -> str:
    order = SETS[set_name]
    x, y = sorted((a, b), key=order.index)
    return PAIR[set_name][(x, y)]


def _check() -> None:
    for name, stats in SETS.items():
        assert len(stats) == 8
        assert set(SPECIALIST[name]) == set(stats)
        assert set(PAIR[name]) == set(combinations(stats, 2)), name
        assert len(set(PAIR[name].values())) == 28


_check()
