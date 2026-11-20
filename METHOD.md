# Method

Method version 1. Every sheet prints the method version that made it. A change to any rule below bumps it.

## What a sheet says

A sheet is a picture of where your days went and who was in your party, drawn on your own machine from your own history.

- Points are **activity points**. One active day is one point.
- An **active day** is a day you or your party changed something in a project: a commit, or a file an agent edited. Unattended agents can make one, so the sheet says "you or your party".
- **Level** counts active days over all history. Class and radar cover a **season** you choose (default: all history).
- The sheet never claims skill, productivity, seniority, hours worked, or who did how much of the work.

Everything is deterministic. The same inputs and the same profile give the same sheet. No model scores anything, nothing is random, and ties break by the fixed stat order of the set.

## Inputs

Each reader turns one source into events. Readers keep timestamps, folders, file paths and counts. **No reader stores prompt text, message text or commit subjects.**

| Reader | Source | What it reads |
|---|---|---|
| git | the repos a profile lists, `log --all` | commit hash, author name and email, author time, changed paths, `Co-Authored-By` trailers |
| Claude Code | `~/.claude/projects/*/*.jsonl` | session id, timestamps, `cwd`, model, file paths of Edit, Write, MultiEdit and NotebookEdit calls |
| Codex | `~/.codex/sessions/**/rollout-*.jsonl` | `session_meta` (id, `cwd`, originator, time), model, file paths of applied patches when the log has them |
| Antigravity | `~/.gemini/antigravity-cli/conversation_summaries.db` | conversation id, workspace folder, time. Experimental, off by default |

Commits are matched to a profile by its identity patterns and deduplicated by hash across refs and clones. Bot authors (`[bot]` and a configurable list) never count. A commit with you as author or co-author counts.

## Events

Every reader emits the same record:

```
ts        ISO time with offset
source    git | claude | codex | agy
kind      commit | edit | session
path      file path, absolute (commit and edit), or the session folder
session   session id (harness events)
harness   claude | codex | agy (harness events)
model     model id when the source has one
actor     human | agent | bot
```

## Days

A day runs from the profile's rollover hour (default 04:00) to the next, in the profile's time zone. Work at 1am counts toward the day before.

## Projects

A profile lists project roots: folders or repos. A path belongs to the longest matching root. One repo can hold several **parts** (subfolder rules in the profile), and a project with parts counts as one project when a day is split. Paths outside every root are **unassigned** and listed, never guessed into a profile.

## Sets and stats

A set is a fixed list of eight stats in a fixed order. The profile picks the set. The tool may suggest one, the person picks.

**builder** (default):

| Stat | What earns it |
|---|---|
| Interface | views, components, styles, input handling |
| Logic | application and service code: domain rules, state, APIs, core libraries |
| Infra | CI, containers, deploys, infrastructure as code, service units, shell scripts |
| Tools | CLIs, editor and browser extensions, generators, converters, build plugins |
| Data | schemas, migrations, queries, notebooks, pipelines |
| Models | training, fine-tuning, evaluation and model-serving code |
| Tests | tests, fixtures, benchmarks, validation suites |
| Docs | guides, references, decision records, changelogs |

**tinkerer**: Systems, Tools, Interface, Art, Worlds, Lore, Community, Models. Systems, Tools, Interface and Models come from files like builder's (Logic and Infra both count as Systems; Data and Tests count with the project's main code stat). Art, Worlds, Lore and Community come **only from hand tags** in the profile, because no file can prove them.

## Classifying a day's files

Each changed file goes to one stat, by the first rule that matches:

1. **Overrides** in the profile: a path glob or a whole project, with stat weights.
2. **Project priors from manifests**: an extension manifest or a `bin` entry makes the project's code Tools. Training dependencies (torch, transformers, peft, jax) make its Python Models. Data dependencies (dbt, pandas, polars, duckdb, sqlalchemy migrations) make its scripts Data.
3. **Paths**: `test/`, `tests/`, `__tests__/`, `*.test.*`, `*.spec.*` are Tests. `.github/`, `deploy/`, `infra/`, `k8s/`, `Dockerfile` are Infra. `migrations/`, `schema/` are Data. `docs/` is Docs. `components/`, `views/`, `pages/`, `styles/` are Interface. `bin/`, `cli/`, `scripts/`, `tools/` are Tools.
4. **Extensions**: `.tsx .jsx .vue .svelte .css .scss .html` are Interface. `.sql .ipynb` are Data. `.md .mdx .rst` are Docs. `.sh .ps1 .tf` are Infra. Other source code is Logic.
5. Anything else (images, data dumps, lockfiles, generated output, agent notes like `CLAUDE.md`, `AGENTS.md`, briefs and plans) is **unclassified**.

Generated and vendored paths (`node_modules/`, `dist/`, `build/`, `vendor/`, `target/`, lockfiles, `*.min.*`, `*.map`) are skipped. A commit that adds more than 200 non-code files counts those files once as a bulk import.

## Scoring

1. Every active day is one point.
2. The point splits across the day's projects by `log(1 + files changed)` per project.
3. Inside a project, its share splits across stats by `log(1 + files)` per stat. Unclassified files keep their share out of every stat, and the sheet shows the unclassified total.
4. Points per stat are summed over the season. Shares are each stat's points over the classified total.
5. Level is `floor(sqrt(points over all history))`, with a bar to the next level.

Days with no commit but with agent edits count. Harness sessions with no file change earn no points and show in the party.

## Class

Within the season:

- The top stat holds 50% or more: a **specialist** class of that stat.
- No stat holds more than 20%: a **generalist** class.
- Otherwise the **pair** of the top two, if the runner-up holds 10% or more. If not, the specialist class.
- A **multiclass** shows only when the third and fourth stats each hold 10% or more.
- With a previous sheet, a class changes only when the new class leads by more than 2 points of share. Exact ties go to the earlier stat in the set's order.

Class names belong to the set: 28 pair names, 8 specialist names and one generalist name.

## Radar

Eight spokes in the set's order, the same for every profile, so two profiles overlay. Fewer than three stats with points: ranked bars instead of a radar.

## Party

One member per harness: days together, sessions, models used, and whether its sessions mostly edit or mostly review (`exec` originator, no file changes). The party shows presence. It never shows a share of the work, and token counts never become a score. Usage limits and plan data are never read.

## Achievements

Generic rules over events and git, the same for everyone. Each states its rule and the dated event that earned it.

| Achievement | Rule |
|---|---|
| First light | your first active day |
| Founder | you made the first commit of a repo |
| Thousandfold | a repo reaches its 1,000th commit by you |
| Shipwright | you pushed a version tag (`v1.0.0` and up counts as a 1.0) |
| Long road | a streak of 30 active days |
| Swarm day | 100 or more of your commits in one day |
| Necromancer | you returned to a repo after 180 quiet days |
| Polyglot | 5 or more languages past 1,000 added lines |
| Full party | three harnesses on the same day |
| New class | your class changed since the last sheet |
| Season's turn | four seasons with at least 10 active days each |

A profile may add a milestones file (one dated line per milestone) for releases, launches or anything else the person keeps. Milestones show as the person wrote them and need no rule.

## Outputs

- `sheet.json`: versioned, everything the pages draw. Saved as a snapshot per run.
- `sheet.html`: the private sheet. One file, no network: fonts inlined, a content policy that blocks every request.
- `card.svg`: the share card, built from an allowlist only: name, set, class, level, stat shares rounded to 5%, achievement titles with month dates, and the party's harness names. Hours, weekdays, exact dates, streak ranges, project names and token totals stay off unless the profile turns them on. A profile marked `work = true` never goes on a card unless it says so.
- `audit`: prints every string a card would contain.
- **What changed**: with a previous snapshot, the sheet opens with points since then, level-ups, class drift and party changes.

## Privacy

Local only. The tool makes no network calls and has no telemetry. Redaction happens before data reaches any output: a profile's aliases replace project and repo names, and paths never leave the cache. The cache lives in the user's data folder, outside every repo.
