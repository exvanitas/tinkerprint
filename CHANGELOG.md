# Changelog

Newest first. Every release gets a version, an entry here and a GitHub release.

## Unreleased

- Pixel art made in code: your character, half length, at the counter of their own workshop. They wear your top stat's coat and hat and hold your runner-up's tool, with a cape for a multiclass. On a close call they change into the other costume.
- A `[look]` table in the profile sets the presentation (neutral, man or woman), skin, hair, eyes and expression. Hair, eyes and expression left unset are picked from the name the card shows. See docs/ART.md.
- The sheet opens on your room, idling, with a nameplate and level seal below. The view, light and furnishings come from your name, its shelves hold trinkets for your strongest stats, and your party's instruments stand in the case. Viewers who ask for reduced motion see a still. On a phone the room crops to you and the case.
- Party instruments on the party cards, a pin on each achievement, a trinket on each stat card, each at a whole multiple of its pixels.
- A new reading order: the scene, then the build (radar beside the stat cards, strongest first), party, achievements, chronicle, what changed, projects and method. A link under your name jumps to what changed. Stats with no points share one line instead of empty cards.
- On a close call, a button under your class tries the other costume. The two costumes never show at once.
- The chronicle opens on its latest chapter.
- A lantern palette for the light and dark themes. Stat cards, radar dots and the card's share bars wear each stat's colors.
- A chronicle on the sheet: a road of chapters, one per quarter, with that quarter's class. Quiet stretches rest at camp. `sheet.json` gains a `chronicle` list.
- The share card shows a larger portrait with a level seal, share bars and the party's instruments, all drawn from its allowlisted fields only. `build` writes `portrait.png` and an idling `portrait.gif` when the card is on.
- `audit` checks both portraits as it checks `card.png`, and exits 1 unless every card file is there and certified.
- `tinkerprint gallery` writes one page with every class, face, room, pin, trinket and party instrument. `--art-pack` on `build` and `gallery` draws with your own pack. See docs/ART.md.

## 0.1.0 (2026-11-21)

First release.

- Reads git, Claude Code and Codex logs on your own machine. Antigravity is experimental and off by default. Readers keep times, folders, file paths, models and counts. They never keep prompts, messages or commit subjects.
- One activity point per active day. The point splits across the day's projects, then across stats, by the log of files changed. Level is the square root of all-history points.
- Two sets of eight stats: builder (Interface, Logic, Infra, Tools, Data, Models, Tests, Docs) and tinkerer. A file's stat comes from your overrides, then the project's dependencies, then its path, then its extension.
- Classes: a specialist, a generalist or a pair, with a multiclass. A class within 2 points of the winner is named beside it.
- Profiles in TOML. Keep several, each with its own folders, identities, aliases and time zone. A profile marked `work = true` makes no share card unless you allow it.
- `sheet.html`: one file that makes no network requests. Light and dark, works on a phone. `card.svg`: a share card built from an allowlist. `audit` prints every string in it.
- What changed since an earlier sheet, kept apart from the sheet, so the same logs and profile always give the same `sheet.json`.
- Achievements anyone can earn, each with its rule and its date.
- `demo` builds sheets for two invented people.
- Python 3.11 or newer, standard library only.
- The method is in METHOD.md (method version 2). Known limits are in the README.
