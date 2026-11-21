# statsheet

Turn your git history and your coding-agent logs into an RPG character sheet.

Stats on a radar, a class from your two strongest stats, a level, a few dated achievements, and a party: the agents that worked beside you. It runs on your machine and reads only what is already there. Nothing is uploaded.

> Not released yet. The method is still being worked out in the open. The first version will be 0.1.0.

## Try it

Python 3.11 or newer. No other packages.

```
pip install .
statsheet demo --out statsheet-demo
```

The demo builds sheets for two invented people: a tinkerer with games, a bot and art tools, and a backend and web developer on the builder set. Open `sheet.html` in each folder.

For your own sheet:

```
statsheet init --out me.toml        # a commented starter profile
statsheet build --profile me.toml   # sheet.html, card.svg, sheet.json
statsheet audit --profile me.toml   # every string the share card holds
```

`build` takes `--season FROM:TO` to set the season and `--as-of DATE` to ignore anything later. Without `--out`, sheets go to `~/.local/share/statsheet/sheets/<profile>/`. `python -m statsheet` works too. See `examples/profile.example.toml` for every profile option.

## What it reads

- **git**: commits in the repos your profile lists, matched to you by name and email. Co-authored commits count. Bot authors never do.
- **Claude Code**: session transcripts under `~/.claude/projects/`. Timestamps, folders, models and the files a session edited. Never your prompts.
- **Codex CLI**: session logs under `~/.codex/sessions/`. When and where a session ran, its model, and the files its patches touched when the log records them.
- **Antigravity**: session summaries (experimental, off by default). Presence only.

## How it scores

Every day you changed something earns one point. That point splits across the projects you worked on that day, and each project feeds the stats its files and dependencies point to. Your level is the square root of your points. Agent sessions that edited nothing do not earn points. They show up in your party.

The full rules are in [METHOD.md](METHOD.md). Every sheet prints the method version that made it.

## Profiles

One person can keep several sheets. A profile says which folders and identities belong to it, and what names the sheet shows. A day-job profile next to a personal one makes a good comparison. Mark it `work = true` and it never makes a share card unless you allow it.

Each build saves a snapshot outside every repo, under `~/.local/share/statsheet/`. The next sheet opens with what changed since then.

## What it will not do

- Upload anything, or call any server.
- Read or store prompt text.
- Rank people, or say anything about skill, productivity or seniority. A sheet shows where your recorded time went, nothing more.

## Tests

```
python -m unittest discover -s tests
```

## License

MIT
