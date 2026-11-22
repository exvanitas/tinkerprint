# Art

The art is Keepsake: pixel art made in code, with no image files. A person stands at the counter of their own workshop, half length, 64 × 64 pixels. Run `tinkerprint gallery --out art` to see every class, face, room, pin, trinket, party instrument and camp on one page. Add `--png` to save each picture.

## What a picture is drawn from

Five things, and nothing else:

- **Class.** The top stat picks the coat and hat. The runner-up picks the held tool and the gear on the far shoulder. A specialist with one rounded stat holds their own trade's tool. The generalist wears a traveling cloak and carries a crook. Unclassed has a bare head and no trade tool.
- **Pair order.** A pair wears its top stat's outfit and holds its runner-up's tool, so the same two stats in the other order look different.
- **Multiclass.** A cape in the first multiclass stat's colors, with a hem in the second.
- **Set.** The builder and tinkerer sets differ in wall color and in their camp's landscape.
- **The look and the seed.** The `[look]` tokens below, and the seed: the name the card shows (the `[card]` handle when set, else the profile name), exactly as it shows it. A name longer than 22 characters is clipped, and the characters cut off play no part in the art.

Stat shares are rounded to 5% and ranked highest first, ties in the set's order. Level, points, dates and projects never reach a picture. The same inputs give the same bytes, GIFs included.

## [look]

```
[look]
presentation = "neutral"    # neutral, man or woman
skin = "medium"             # light, medium or deep
hair = "curtains"           # neutral: bob, curtains, shag. man: crop, curls, side part. woman: braid, waves, chignon
eyes = "moss"               # honey, moss, slate, chestnut, plum, lagoon
expression = "calm"         # smile, grin, calm, determined, joy, curious
```

Every key is optional.

- **Presentation and skin** are never random. Presentation defaults to neutral. Skin left unset uses the art pack's own skin colors, which are the light skin in the built-in pack.
- **Hair, eyes and expression** left unset are picked from the seed, so they follow a name already on the card and never change with class or stats. `build` prints the look and says which parts it picked, so you can set them to keep them.
- A hair must belong to the presentation. A misspelled value stops the build and suggests the right one.

The card keeps the five look tokens, and `audit` lists them.

## Rooms

The sheet's banner is a 252 × 72 room: a workbench and a window on the left, the figure at a counter in the middle, a display case on the right.

- **From the seed:** the view through the window (harbor, viaduct, windmill or peaks), its light (amber dawn, blue hour, rose dusk or overcast), the drapery, the wall finish, the plant and its pot, the rug's weave and wool, the hanging over the bench, and which cubbies hold stock.
- **From the class:** the workbench's fixture and the objects on its tray. A pair keeps its top stat's fixture and borrows its runner-up's tray.
- **From the stats:** the case's cubbies hold a trinket for each stat with a rounded share, more for the larger shares, 18 at most.
- **From the party:** up to three party instruments stand in the bottom of the case.

The card portrait and `portrait.png` crop the same room behind the figure, at the window, and show no party or stock.

## The idle animation

Everything moves on one 2.88-second clock of 16 frames: the figure breathes and blinks, a wisp crosses the window, the plant's leaves bend, a candle or ember flickers and one party instrument works. The sheet's banner stacks two GIFs at a whole-number scale: the room, then the figure with the counter, hands and tools in front. A close call adds the other costume as a third layer, which swaps with the first every few seconds, on hover, or with the button under the class. `portrait.gif` is the card portrait's loop at 384 × 384.

Viewers who ask their system for reduced motion get frame zero of each layer as a still PNG, and no automatic costume swap. The sheet needs no script for this.

## Pins, trinkets and party instruments

- **Pins:** an enamel pin for each achievement, and one for milestones written by hand.
- **Trinkets:** a miniature for each stat in its own colors, on the stat cards and the room's shelves.
- **Party instruments:** each harness is a wind-up instrument. Claude Code is a wick lantern, Codex a typewriter, Antigravity an orrery. Gemini CLI, OpenCode, Cline, Roo Code, Copilot CLI, Cursor and Aider have their own, and any other harness gets a gramophone.

A party member is presence only. Its drawing depends on the harness name alone: never on how much it was used, its models or its dates.

The art draws no animals.

## Quiet quarters

A chronicle chapter with no activity rests at camp: a bedroll and pack by a fire under the night sky, in the set's landscape. The seed places the moon, the hearth and the blanket.

## Art packs

```
tinkerprint gallery --export-pack mypack.json
tinkerprint gallery --art-pack mypack.json --out preview
tinkerprint build --art-pack mypack.json
tinkerprint audit --art-pack mypack.json
```

The drawings themselves are code. A pack is JSON data that changes:

| Key | What it changes |
|---|---|
| `stat_colors` | Each stat's four colors, highlight to shadow: coats, tools, trinkets, capes and the sheet's stat tints |
| `wanderer_colors` | The generalist's and the unclassed figure's clothes |
| `skin_colors` | The skin used when `[look]` sets none |
| `sets` | Each set's `plate`, `floor` and `wall2` colors, and its camp `scene`: `ridge` or `vale` |
| `looks` | For each stat, which built-in `hat`, `body`, `item`, `gear` and `trinket` its trade wears |
| `generalist` | The generalist's `hat`, `body` and `item` |
| `icons` | Which built-in pin each achievement wears |

Every color must be `#rrggbb`, and every name must be one the built-in art draws. The loader checks both, so a pack can change how a sheet looks and nothing else. Pack names never reach an output. Keys from older packs, such as `parts` and `familiars`, are ignored.

Build and audit a card with the same pack: `audit` re-draws the card and portraits to check them.

## Size budgets

The art tests keep both demo sheets under 104,000 bytes, cards under 30,000 bytes, `portrait.png` under 4,800 bytes, `portrait.gif` under 24,000 bytes and the gallery under 360,000 bytes.
