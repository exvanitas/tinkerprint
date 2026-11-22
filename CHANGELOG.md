# Changelog

Newest first. Every release gets a version, an entry here and a GitHub release.

## 0.2.0 (2026-11-23)

Pixel art, a card you can post anywhere, and an easier first run.

### The new look

- Pixel art made in code. Your character stands half length at the counter of their own workshop, in your top stat's coat and hat, holding your runner-up's tool, with a cape for a multiclass.
- The sheet opens on that room, idling. The view, the light and the furnishings come from your name, the shelves hold trinkets for your strongest stats, and your party's instruments stand in the case. A nameplate with a level seal sits below. Viewers who ask for reduced motion see a still. On a phone the room crops to you and the case.
- A `[look]` table in the profile sets the presentation (neutral, man or woman), skin, hair, eyes and expression. Hair, eyes and expression left unset are picked from the name the card shows, exactly as it shows it, so characters clipped off a long name play no part. `build` prints the look and what it picked. See docs/ART.md.
- On a close call the figure changes into the other costume, and a button under your class tries it. The two costumes never show at once.
- A chronicle: a road of chapters, one per quarter, each with that quarter's class in your own look and room. Quiet quarters rest at camp. It opens on the latest chapter.
- A new reading order: the scene, then the build (radar beside the stat cards, strongest first), party, achievements, chronicle, what changed, projects and method. A link under your name jumps to what changed. Stats with no points share one line.
- A lantern palette for the light and dark themes. Stat cards, radar dots and the card's share bars wear each stat's colors. Party cards show each member's instrument, achievements wear pins, and stat cards hold trinkets.
- The top bar fits a phone: the title above, the buttons on their own row.
- `tinkerprint gallery` writes one page with every class, face, room, pin, trinket and party instrument. `--art-pack` on `build`, `gallery` and `audit` draws with your own pack.

### First run and setup

- `init` fills in your name and email from your git config.
- `build` and `audit` use `./tinkerprint.toml` when `--profile` is left out.
- A misspelled profile key, like `[[projects]]`, stops the build and names the right one. A wrong type or a missing profile ends with one plain line.
- After a build, a warning for each cause of an empty sheet it can see: a root that does not exist, a repo with commits by others but none by you (with up to five of their authors), a folder of repos given as a root, git missing, and a harness with no folder or no sessions.
- After each build, a `Readers` line per harness counts its files, records, sessions and edits, with the log versions seen, and warns when a log format looks changed. A malformed record, however deep or long, is skipped and counted there, and the build goes on.
- `--list-unassigned N` lists up to N folders outside every root. By default the build prints only their totals.
- The README covers install with pipx, uv or a venv, update, uninstall and Windows.

### Sharing and the card

- `card.png`, the file to post. Discord and most social sites preview it. It draws the same fields as `card.svg`. Its pixel font draws Latin letters, and `build` says when a name holds others: `card.png` shows them as "?" and `card.svg` keeps them.
- `portrait.png` and an idling `portrait.gif`: the card's portrait alone, your figure in front of your own room.
- A `[card]` table: `enabled` turns the card on or off on any profile, `name` puts a handle on the card while the sheet keeps your name, and `hide` leaves off any of the party, the level and the achievements.
- The card gains your portrait with a level seal, share bars, the party's instruments, a MULTICLASS label, and a footer naming tinkerprint, the method version, the build month (the `--as-of` month, else the month you build) and the active days the shares cover. A season build's footer names the season by month, or by day when `show` has `dates`.
- After each build, `shows` lists what the card holds and `alt` gives alt text to paste with it. The SVG carries the same alt text.
- A Share view button on the sheet leaves only what the card shows, ready for a screenshot. The browser tab shows the card's name, or a plain title when there is no card.
- `audit` checks `card.png`, `portrait.png` and `portrait.gif` as well as `card.svg`: each must be, byte for byte, what the card's fields draw. It lists the look tokens, and fails a card whose saved fields hold more than a card may show. With a profile, it also checks that the card follows the profile's current `[card]` and `[look]` settings and shows only project names the profile still has. An empty `--profile` is an error, never the same as leaving it out. It exits 1 unless every card file is there and certified.
- The sheet links `card.png` and `card.svg`.

### Your data and privacy

- `tinkerprint forget` shows what tinkerprint keeps and where: the data folder and its size, and for a profile its history, last-build file and sheets folder. It deletes nothing.
- `tinkerprint forget --all --yes` deletes the whole data folder, when it holds only what tinkerprint keeps. Your repos, agent logs, profiles and `--out` folders are never in it.
- The README's Trust section says what tinkerprint promises and what it assumes.
- Sessions from agent logs that are gone still count. Claude Code deletes old transcripts after about a month, and your sheet no longer loses those days. That includes logs 0.1 read that are gone by your first 0.2 build.
- Two builds at once, or a build and `forget --all`, take turns with the data folder, so neither loses the other's sessions or profiles. A run that has to wait says so and keeps waiting.
- A build moves into a `--data-dir` only when it is new, empty or a tinkerprint data folder, and writes `--out` only outside the data folder. A 0.1 data folder at the default location is adopted as it is. To adopt one you chose with `--data-dir`, create `tinkerprint-data.txt` in it: the build says how.
- History follows a profile file you move. A copy of a profile starts its own. A profile whose name or identity changed at the same path keeps its history, and `build` says how to start afresh.
- "What changed" says when the profile's projects, roots, identity, harnesses or day settings changed in between, and says when an update changed the method instead of comparing.
- A build reads your repos without starting any program their git config names, such as a signature checker or a diff filter, and without fetching, whatever the repo or your `GIT_` variables say.
- `demo` writes its repos only inside its own temporary folder, even when `GIT_DIR` or `GIT_WORK_TREE` is set.
- The sheet runs only its own small script, for the theme, the costume button and the chronicle. A browser refuses any other script on the page.
- A saved sheet that was damaged or edited by hand no longer stops a build. "What changed" shows only the numbers and names it can trust.
- The card files (`card.svg`, `card.png`, `portrait.png`, `portrait.gif`) are readable by others, so a web server or a copy can serve them, and only you can change them. The sheet (`sheet.html`, `sheet.json`, `changes.json`), the cache and history stay private to you.

### Accuracy and achievements

- Full party needs any three harnesses on one day, so a fourth harness seen once no longer takes it away.
- Shipwright counts lightweight tags on your commits, dated by the commit, and reads a prefixed tag like `cli/v1.2.0` by its last part.
- Commit and tag achievements count only commits that change a file inside one of the profile's roots.
- A shallow clone's oldest commits, whose changes it cannot show, earn no achievement and add no lines, and a shallow clone never earns Founder. The build warns when a project's history is shallow.
- Party labels say only what the logs recorded: "No edits recorded" replaces "Mostly reviews", and Antigravity says "Presence only". Past six models a party card shows "+N more".
- The sheet says how many active days the class rests on: "Based on N of M active days".
- The sheet's footer gives the build's as-of date, not the clock time, so the same inputs make the same `sheet.html`.

### Windows

- Paths, roots and time zones work on Windows. `init` writes your clock's UTC offset when it cannot read a time zone name.
- Antigravity's `file:///C:/` paths and its database work on Windows.
- On Windows, a path from an agent log reaches the disk only when it is inside one of your roots by name, so a log can never send a build to another machine. Work on a network share counts when a root is on that share. A device path or a file stream is left out.
- A build on Windows passes its own audit: text outputs are written with `\n` line ends there too.
- `tzdata` installs on Windows only, since Windows Python ships no time-zone data.
- The demo runs on Windows.

### For maintainers

- `tools/` holds the scripts that regenerate the README images. They are not part of the package.
- Tests tie the version in `pyproject.toml`, `__init__.py` and this changelog together, and METHOD.md's method version to the code's.

### Changes that need attention

- The method is now version 3. METHOD.md lists what changed. "What changed" does not compare a 0.1 sheet with a 0.2 one.
- The sheet format is `tinkerprint.sheet/3`. Party members lose `review_sessions` and `other_sessions`, and season totals gain `classified_days`. `sheet.json` also gains `chronicle`, `look` and the card's build month.
- The first build after the update re-reads every agent log that is still there, once.
- `audit` exits 1 when a card is not certified.
- The art pack is version 3. Version-1 packs are refused, and the sprite parts of a version-2 pack are ignored.
- Unknown profile keys are errors.
- `build` refuses a `--data-dir` that is neither empty nor a tinkerprint data folder, and an `--out` inside the data folder. A 0.1 data folder is taken as it is.
- A `[[project.part]]` path must be a folder inside its project's root. A part like `../other` is an error, and a part linked to a folder outside the root gives it no manifest prior.
- `[card] allow = false` now turns the card off on personal profiles too. `enabled` is the new name for `allow`.

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
