# Changelog

Newest first. Every release gets a version, an entry here and a GitHub release.

## Unreleased

- Agent edits count only when the log confirms them. Codex edits come from completed change records, never from tool call text. A Claude edit counts when its result returns without an error.
- Presence keeps every profile day and every model, in any time zone.
- A relative path joins the folder the session was in at that moment. Without a folder it stays unassigned.
- Manifest priors now come right after overrides, as METHOD.md says. A Tools prior takes all of a project's code. A Models or Data prior takes its Python, tests included.
- Bulk imports are judged per commit and keep their unclassified share.
- Merge commits count the files that differ from every parent, such as conflict resolutions.
- Two roots of one project no longer merge their files. Clones of one repo still count once.
- The party counts only days and models inside the profile's roots and season.
- The multiclass follows the same 2-point hold as the class.
- Profile switches must be true or false. A quoted "false" is an error.
- Each profile file gets its own snapshots. A rebuild of the same inputs gives the same `sheet.json`.
- The data folder is refused inside a git repo or a profile root.
- git never fetches. A partial clone is read without line counts, with a warning.
- The share card draws bars when the sheet does. Radars use one square-root scale on every sheet.
- `audit` reads the card of the last build, or the build in `--out`, and lists only what the card draws.
- `build` lists folders of unassigned edits too.
- The cache is checked against file contents.
- First build of tinkerprint. Python 3.11, standard library only.
- Commands: `build`, `audit`, `init` and `demo`.
- Readers for git, Claude Code, Codex and Antigravity. They keep times, folders, paths and counts. They never keep prompt, message or commit text.
- Scoring follows METHOD.md version 1: one point per active day, log splits by project and stat, level, classes with a 2-point hold, party and achievements.
- Builder and tinkerer sets with 28 pair names, 8 specialist names and one generalist name each.
- `sheet.html`: one file with a content policy that blocks every request. Light and dark themes. Works on a phone.
- `card.svg`: a share card built from an allowlist. `audit` prints every string it holds.
- Snapshots and a cache under the user's data folder. The sheet opens with what changed since the last one.
- An example profile and two invented people for the demo.
- Repository started: README, license, this changelog.
