# charsheet

Turn your git history and your coding-agent logs into an RPG character sheet.

Stats on a radar, a class from your two strongest stats, a level, a few dated achievements, and a party: the agents that worked beside you. It runs on your machine and reads only what is already there. Nothing is uploaded.

> Not released yet. The method is still being worked out in the open. The first version will be 0.1.0.

## What it reads

- **git**: commits in the repos you point it at, matched to you by name and email.
- **Claude Code**: session transcripts under `~/.claude/projects/`. Timestamps, folders and the files a session edited. Never your prompts.
- **Codex CLI**: session logs under `~/.codex/sessions/`. When and where a session ran, and its model.
- **Antigravity**: session summaries (experimental, off by default).

## How it scores

Every day you changed something earns one point. That point splits across the projects you worked on that day, and each project feeds the stats its files and dependencies point to. Your level is the square root of your points. Agent sessions that edited nothing do not earn points. They show up in your party.

## Profiles

One person can keep several sheets. A profile says which folders, remotes and identities belong to it, and what to hide. A day-job profile next to a personal one makes a good comparison.

## What it will not do

- Upload anything, or call any server.
- Read or store prompt text.
- Rank people, or say anything about skill, productivity or seniority. A sheet shows where your recorded time went, nothing more.

## License

MIT
