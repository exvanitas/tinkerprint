# tinkerprint

Turn your git history and your coding-agent logs into an RPG stat sheet.

Stats on a radar, a class from your two strongest stats with a pixel portrait to match, a level, a few dated achievements, a chronicle of your classes by quarter, and a party: the agents that worked beside you. It runs on your machine and reads only what is already there. Nothing is uploaded.

![An invented tinkerer's workshop, idling: an engineer in goggles holds a spanner at the counter, a windmill stands beyond the window, and a lantern, a typewriter and an orrery stand in the case](docs/idle.gif)

## What it makes

A private sheet, one HTML file per profile. Here are the demo's two invented people, a developer on the builder set and a tinkerer on the tinkerer set:

![Sheet for Tobi Marsh, an invented developer: an alchemist in a blue hood at the counter of a workshop, with a telescope on the bench, a viaduct through the window, and a wick lantern and a typewriter, the party's instruments, in the case; below, a nameplate with level seal, then the build](docs/tobi.png)

![Sheet for Wren Aldous, an invented tinkerer, in the dark theme: an engineer in goggles holding a spanner, a windmill through the window, and three party instruments in the case](docs/wren.png)

And a share card, `card.png`, that carries only what you allow:

![Share card for Tobi Marsh, an invented developer: Alchemist with Duelist as multiclass, level 15, a pixel portrait at a workshop window, top stats Logic 35%, Data 20%, Interface 15% and Tests 10%, four achievements by month, a radar, Claude Code and Codex in the party, and a footer naming tinkerprint](docs/card.png)

## Install

Python 3.11 or newer. It needs no other packages, apart from `tzdata` on Windows.

```
git clone --branch v0.2.0 https://github.com/exvanitas/tinkerprint
cd tinkerprint
pipx install .
```

`uv tool install .` works the same way. `pipx install git+https://github.com/exvanitas/tinkerprint@v0.2.0` installs without keeping a clone. Or use a virtual environment:

```
python3 -m venv .venv
. .venv/bin/activate
pip install .
```

A bare `pip install .` outside a virtual environment is refused on current Debian, Ubuntu and Homebrew Python ("externally managed environment"). Use pipx, uv or a venv.

**Update:** in the clone, `git fetch --tags` and `git checkout` the newest tag, then `pipx install --force .`, `uv tool install --reinstall .`, or `pip install .` in the venv. Read [CHANGELOG.md](CHANGELOG.md) for changes that need attention.

**Uninstall:** run `tinkerprint forget --all --yes` first if you want the data folder gone (see [What stays on disk](#what-stays-on-disk)). Then `pipx uninstall tinkerprint`, `uv tool uninstall tinkerprint`, or delete the venv.

**Windows:** install the same way from PowerShell, for example `py -m pipx install .`, or a venv activated with `.venv\Scripts\activate`. pip adds `tzdata`, because Windows Python ships no time-zone data. `init` cannot read a time zone name on Windows, so it writes your clock's UTC offset: replace it with an IANA name like `"Europe/Berlin"` so daylight saving is right. Windows support is new and less tested than Linux and macOS.

## Try it

```
tinkerprint demo --out tinkerprint-demo
```

The demo builds sheets for two invented people: a tinkerer with games, a bot and art tools, and a backend and web developer on the builder set. Open `sheet.html` in each folder.

For your own sheet:

```
tinkerprint init      # writes tinkerprint.toml, with your name and email from git config
                      # then edit it: your other emails, and one [[project]] per project
tinkerprint build     # sheet.html and sheet.json, plus the card files
tinkerprint audit     # what the built card holds, before you share it
```

`build` and `audit` use `./tinkerprint.toml` when `--profile` is left out. Keep the profile outside your repos: it lists your folders and emails. A misspelled key, like `[[projects]]`, stops the build and names the right one.

The portrait is yours to set. Under `[look]` in the profile:

```
[look]
presentation = "neutral"   # neutral, man or woman
skin = "medium"            # light, medium or deep. Unset is the art pack's own.
hair = "bob"               # neutral: bob, curtains, shag. man: crop, curls, side part. woman: braid, waves, chignon
eyes = "honey"             # honey, moss, slate, chestnut, plum or lagoon
expression = "smile"       # smile, grin, calm, determined, joy or curious
```

Presentation is neutral unless you set it. Hair, eyes and expression left out are picked from the name the card shows, and `build` prints what it picked so you can keep it. Your coat, hat and tool come from your class.

`tinkerprint gallery --out art` writes one page with every class of both sets, the faces, a room for each set, and every pin, trinket and party instrument. The art is pixel art made in code. An art pack recolors it, and `--art-pack` swaps the pack. See [docs/ART.md](docs/ART.md).

`build` takes `--season FROM:TO` to set the season and `--as-of DATE` to ignore anything later. Without `--out`, sheets go to a folder under `~/.local/share/tinkerprint/sheets/` named for the profile file. Each build writes `sheet.json`, `changes.json` and `sheet.html`, plus `card.png`, `card.svg`, `portrait.png` and `portrait.gif` when the card is on. `python -m tinkerprint` works too. See `examples/profile.example.toml` for every profile option.

## Sharing

Post `card.png`. Discord and most social sites show it as a preview, and they do not preview SVG. `card.svg` draws the same thing. `portrait.png` is the portrait alone, for an avatar, and `portrait.gif` is the same portrait idling.

After each build, `shows` lists exactly what the card holds, and `alt` is a line of alt text to paste with it. Run `tinkerprint audit` before you share: it prints every string in `card.svg`, and checks that `card.png` and both portraits hold image data only and are, byte for byte, what the card's fields draw. With a profile, it also checks that the card follows the profile's current `[card]` and `[look]` settings, so change one and build again before you share. It exits 1 when a card file is missing, broken or not certified, so a script can stop on it.

What a card reveals:

- **Your name**, or a handle you choose.
- **Your class and multiclass**, from the season's shares rounded to 5%.
- **Your level**, a band of active days over all history: level 15 means 225 to 255 days. The footer gives the exact count of active days in the season.
- **Achievement months.** The earliest ones show roughly when you started.
- **Your party**: which coding agents you used, never how much.
- **Your portrait**: drawn from your class, multiclass and top stats, the name on the card and your `[look]`. It holds no text.
- **The season** of a season build, by month unless `show` adds dates, the month it was built, and the method version.

Nothing else: no project names, exact dates, hours, repos, paths or emails, unless `show` adds dates or project names.

The `[card]` table in the profile:

```
[card]
enabled = true                # on by default, off by default when work = true
name = "quillwork"            # a handle for the card. The sheet keeps your name.
hide = ["party", "level", "achievements"]  # any of these stay off the card
show = ["dates", "projects"]  # exact dates and up to three project names go on the card
```

Hiding the level also hides the day counts, since they give the same band away. `allow` is the older name for `enabled` and works the same way on every profile.

People often screenshot the sheet instead. The sheet's **Share view** button hides everything the card would not show and leaves the room, with only the party the card shows, the card's name, class, level and top stats. It works without script, with the keyboard and by touch.

## If your sheet is empty

A build that finds nothing still makes a sheet: level 0, Unclassed. It prints a warning for each cause it can see:

- **A root does not exist.** Fix `roots` in that `[[project]]`.
- **No commits match you.** The warning lists up to five authors seen in that repo, with their commit counts. Add yours to `emails` or `names` under `[identity]`. Commits made on GitHub's website use a noreply address like `12345+you@users.noreply.github.com`.
- **A root is a folder of repos.** Commits are read only from the repo a root is in. List each repo as a root.
- **A harness is on, but its folder is missing or has no sessions.** Set it to `false` under `[harnesses]`, or point `claude_dir`, `codex_dir` or `agy_db` at its logs.
- **git is not on PATH.** No commits can be read.
- **A harness changed its log format.** After each build, a line per harness under `Readers` counts its files, records, sessions and edits, with the log versions seen and any malformed records it skipped. It warns when logs hold no record it recognises, or many tool calls but no edit it knows. Update tinkerprint, and if that does not help, report that line. It holds counts and version numbers only.

Agent sessions in folders outside every root are unassigned and not scored. The build prints their totals. `--list-unassigned 20` lists up to 20 of the folders, so you can find roots you missed. Folder names stay off the screen unless you ask.

## What it reads

- **git**: commits in the repos your profile lists, matched to you by name and email. Co-authored commits count. Bot authors never do.
- **Claude Code**: session transcripts under `~/.claude/projects/`. Timestamps, folders, models and the files a session edited.
- **Codex CLI**: session logs under `~/.codex/sessions/`. When and where a session ran, its model, and the files its patches touched when the log records them.
- **Antigravity**: session summaries (experimental, off by default). Presence only.

The Claude Code and Codex readers parse each log line, prompts included, on your machine. They keep none of the prompt or message text. The git reader never reads commit subjects or bodies.

## How it scores

Every day you changed something earns one point. That point splits across the projects you worked on that day, and each project feeds the stats its files and dependencies point to. Your level is the square root of your points. Agent sessions that edited nothing do not earn points. They show up in your party.

The full rules are in [METHOD.md](METHOD.md). Every sheet prints the method version that made it.

## Profiles

One person can keep several sheets. A profile says which folders and identities belong to it, and what names the sheet shows. A day-job profile next to a personal one makes a good comparison. Mark it `work = true` and it makes no share card unless you turn one on.

Each build saves its sheet outside every repo, under `~/.local/share/tinkerprint/`. The next build compares with the newest saved sheet from an earlier date and writes `changes.json`. The sheet shows what changed since then, with a link to it under your name. When you changed the profile's projects, roots or identity in between, it says so, since the difference then includes history you added or removed. After an update that changes the method, it says the two sheets are not compared. `sheet.json` never depends on that history: the same logs, the same kept sessions from deleted logs and the same profile give the same file, apart from the month the card says it was built.

## What stays on disk

Everything tinkerprint keeps goes in its data folder: `~/.local/share/tinkerprint/`, or `$XDG_DATA_HOME/tinkerprint`, or `--data-dir`. A `--data-dir` must be new or empty the first time, or a data folder from tinkerprint 0.1.

- `cache/`: what the readers kept from each agent log (times, folders, file paths, models), so the next build skips logs that have not changed. Shared by all profiles. When a log is deleted, as Claude Code does with transcripts after about a month, its entry stays here, marked gone, so its days still count. This is the only copy of those sessions.
- `history/`: each build's sheet, per profile and season, for "what changed".
- `last-build/`: one small file per profile naming its last output folder, for `audit`.
- `sheets/`: builds made without `--out`. An `--out` folder goes outside the data folder.
- `profiles.json`: which profile file each saved history belongs to, so history follows a profile file you move. Move it, then build before you edit it. The path is what a profile is: a file edited or replaced at the same path keeps its history, and `build` says so when its name or identity changed. To start afresh, delete that profile's `history/` folder.
- `tinkerprint-data.txt`: says this is tinkerprint's data folder.
- `tinkerprint.lock`: lets one run at a time update the cache, `profiles.json` and history. A second run waits for the first, and says so after five seconds.

The cache, history, last-build files, `profiles.json` and the sheet itself (`sheet.html`, `sheet.json`, `changes.json`) are private to you (mode 0600), since the sheet names your projects, models and exact dates. The card files (`card.svg`, `card.png`, `portrait.png`, `portrait.gif`) are made to pass on: others can read them (0644, less what your umask takes away), and only you can change them. Text files are UTF-8 with `\n` line ends on every system.

`tinkerprint forget` deletes nothing. It shows the data folder and its size, and with `--profile` that profile's history folder, last-build file and sheets folder. To remove one profile's data, delete those yourself. The cache is shared by every profile.

`tinkerprint forget --all --yes` deletes the whole data folder. It does so only when the folder is not a link, holds `tinkerprint-data.txt`, and holds nothing at its top but the entries above. Otherwise it deletes nothing and names what is in the way. Without `--yes` it lists what it would delete. Deleting the cache loses the sessions kept from deleted logs. Your repos, agent logs, profiles and `--out` folders are outside the data folder, so it never touches them.

## What it will not do

- Upload anything, or call any server. Git reads your repos as they are on disk, and never fetches.
- Run a program your repo's git config names, such as a signature checker, a diff filter or a pager.
- Keep prompt or message text.
- Rank people, or say anything about skill, productivity or seniority. A sheet shows where your recorded time went, nothing more.

## Known limits

- Two builds that write to the same output folder at the same time can leave a mix of their files. Run one build per folder at a time.
- `audit` without `--out` reads the folder of the profile's last build. If another profile built into that folder later, it shows that card. Pass `--out` to audit a folder directly. That works without a profile, but a `--profile` that cannot be read fails the audit.
- Where a daylight-saving change crosses the rollover hour, as in `Pacific/Chatham`, the edge of a day can move during that hour. Work near the change may land on the next or previous day.
- Two Codex records of one change that share no call id or item id count as two changes.
- Roots outside git take manifest priors from the files on disk, so their sheets can change with the checkout.
- On Windows, a path from an agent log counts only when it is inside one of your roots as written, like `C:\code\kite`, so a log never makes tinkerprint open a folder outside them. A root reached through a link under another name misses that work. Work on a network share (`\\server\share`) counts only when a root is on that share. A device path or a file stream is left out.

## Tests

```
python -m unittest discover -s tests
```

[tools/README.md](tools/README.md) says how to regenerate the README images.

## License

MIT
