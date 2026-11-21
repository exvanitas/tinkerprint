# Changelog

Newest first. Every release gets a version, an entry here and a GitHub release.

## Unreleased

- Readers declare the record shapes they accept and drop the rest. A model id must look like one, so a path or a sentence never shows as a model. Codex change records link through their call id.
- Manifest priors come from the git commit at the as-of date, not the checkout. Roots outside git still read the files on disk.
- Files are keyed by repository and path inside it, so clones at any depth count a file once. A complete clone wins over a shallow one.
- History is written last, so a failed build never becomes a comparison. A sheet saved without `--as-of` never holds events after its date.
- `audit` parses `card.svg` as XML and reports a file that does not parse. It works with `--out` alone.
- What changed treats a first class as new and still compares points after a set change.
- Shares add up exactly. Only equal shares tie. Stats under 5% stay off the card.
- Paths compare with the platform's own rules, after symlinks.
- Unassigned totals match between `sheet.json` and the terminal.
- Card class lines fit instead of being cut. Necromancer, Polyglot and Season's turn match their wording.
- README lists known limits.
- Method version 2. `sheet.json` now depends on the logs and the profile alone. The 2-point class hold is gone. When the runner-up is within 2 points of share, the sheet names both: "Artificer, close to Alchemist". The multiclass works the same way.
- What changed moves to `changes.json`. It compares with the newest saved sheet from an earlier as-of date and names that date. A build with an earlier `--as-of` never compares with a later sheet. A failed build is never saved.
- History and default output folders are keyed by the profile file's real path. The `id` key in a profile is no longer used.
- `audit` reads `card.svg` itself and prints its text strings in order. Without `--out` it reads the profile's last build.
- The New class achievement is gone. A new class now shows in what changed.
- Shipwright counts only annotated version tags you made, once per tag across clones.
- Readers check the type of every field and pass a fuzz test each. A Claude edit needs an error flag that is absent or false. Models attach only to records that name them.
- Symlinked roots keep their activity. Clones that share history count a file once, shallow clones included.
- Unassigned folders and sessions are listed from every event, by season. Bulk imports count the whole commit.
- The card's chart follows its rounded shares. Fixed time zone offsets must be whole quarter hours. Weights must be finite.
- Warnings name projects, never their folders. Odd file names stay distinct.
- The data folder is refused inside bare repositories and when a subfolder links into a repo.
- Agent edits count only when the log confirms them. Codex edits come from completed change records, never from tool call text. A Claude edit counts when its result returns without an error.
- Presence keeps every profile day and every model, in any time zone.
- A relative path joins the folder the session was in at that moment. Without a folder it stays unassigned.
- Manifest priors now come right after overrides, as METHOD.md says. A Tools prior takes all of a project's code. A Models or Data prior takes its Python, tests included.
- Bulk imports are judged per commit and keep their unclassified share.
- Merge commits count the files that differ from every parent, such as conflict resolutions.
- Two roots of one project no longer merge their files. Clones of one repo still count once.
- The party counts only days and models inside the profile's roots and season.
- Profile switches must be true or false. A quoted "false" is an error.
- A rebuild of the same inputs gives the same `sheet.json`.
- The data folder is refused inside a git repo or a profile root.
- git never fetches. A partial clone is read without line counts, with a warning.
- The share card draws bars when the sheet does. Radars use one square-root scale on every sheet.
- `build` lists folders of unassigned edits too.
- The cache is checked against file contents.
- First build of tinkerprint. Python 3.11, standard library only.
- Commands: `build`, `audit`, `init` and `demo`.
- Readers for git, Claude Code, Codex and Antigravity. They keep times, folders, paths and counts. They never keep prompt, message or commit text.
- Scoring follows METHOD.md: one point per active day, log splits by project and stat, level, classes, party and achievements.
- Builder and tinkerer sets with 28 pair names, 8 specialist names and one generalist name each.
- `sheet.html`: one file with a content policy that blocks every request. Light and dark themes. Works on a phone.
- `card.svg`: a share card built from an allowlist. `audit` prints every string it holds.
- History and a cache under the user's data folder. The sheet opens with what changed since an earlier sheet.
- An example profile and two invented people for the demo.
- Repository started: README, license, this changelog.
