# Changelog

Newest first. Every release gets a version, an entry here and a GitHub release.

## Unreleased

- Pixel art, made in code from a pack of parts: a woodland guild with one animal per trade, by lantern light. A portrait beside your class shows your top stat's animal and costume, with your runner-up's tool, sleeve and shoulder piece, and a cape for a multiclass. On a close call it changes into the other costume.
- A workshop banner on top of the sheet, looking out on a moonlit viaduct (builder) or a lake (tinkerer). Its shelves hold trinkets for your strongest stats and your party's familiars stand beside you.
- Familiars for each harness, icons for each achievement, trinkets on the stat cards.
- A chronicle on the sheet: one chapter per quarter with that quarter's class. Quiet stretches rest at camp. `sheet.json` gains a `chronicle` list.
- The share card shows the portrait, drawn from its allowlisted fields only. `build` writes `portrait.png` when the card is on.
- `tinkerprint gallery` writes one page with every portrait, familiar and icon. `--art-pack` on `build` and `gallery` draws with your own pack. See docs/ART.md.

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
