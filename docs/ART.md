# Art

Every picture tinkerprint draws is pixel art made in code from a pack of parts. The same sheet always gives the same pixels. Nothing is fetched, and nothing is random except a stream seeded from sheet fields.

Run `tinkerprint gallery --out art` to see every part at once.

## What it draws

| Picture | Where | Made from |
|---|---|---|
| Portrait | sheet hero, card, `portrait.png` | the class |
| Close-call costume | sheet hero | the class within 2 points |
| Banner | top of the sheet | the stat mix, the class, the party |
| Familiar | party cards, banner | the harness |
| Icon | achievements, milestones | the achievement rule |
| Trinket | stat cards, banner shelves | the stat |
| Chronicle | sheet | one portrait per quarter, a campfire for a quiet stretch |

## How a portrait composes

A portrait is a 32 by 32 grid. Layers go down in this order, then every clear pixel next to a drawn one becomes outline:

1. **Cape**, only for a multiclass: the cloth takes the multiclass's first stat, the hem its second.
2. **Pack**, only for a generalist: a bedroll in the top stat's colors.
3. **Base**: the shadowed face, eyes, body, legs and boots.
4. **Body**: robe, armor, apron, smock, coat or tunic, by the top stat.
5. **Hat**, by the top stat.
6. **Held item**, by the runner-up. A specialist holds the next stat down, or its own stat's item when it has nothing else.
7. **Hand** over the grip, unless the item covers it (shield, tome).

A pair wears its top stat and holds its runner-up, so a Spellblade heavy on Logic looks different from one heavy on Interface. The generalist wears a traveler's hat and tunic and carries a walking staff.

Looks follow class shape only. Level, points, streaks and days never change a picture, so a portrait is never a status marker.

The sheet and the card rank stats the same way: by share rounded to 5%, ties in the set's order. So the card's portrait always matches the sheet's.

### Grid keys

`.` is clear. Upper-case keys are ramps filled in per drawing:

| Keys | Ramp |
|---|---|
| `A B C` | outfit: the top stat, light to dark |
| `X Y Z` | item: the runner-up |
| `T U` | cape: the multiclass's first stat |
| `V W` | hem: the multiclass's second stat |

Every other key is a fixed color from the pack's `ink`. A part may add its own `palette` for keys only it uses, like a familiar's fur.

## How many

Per set, a portrait varies by kind, top stat, item stat and cape:

| Kind | Looks |
|---|---|
| Specialist | 8 outfits, 8 items, 31 capes (none, or 30 ordered pairs of the other stats) |
| Pair | 28 pairs, 2 orders, 31 capes |
| Generalist | 8 pack colors |
| Unclassed | 1 |

That is about 3,500 portraits per set and 7,000 across both, from 14 hats, 6 bodies, 14 held items and one cape. Add 4 familiars, 11 icons, 13 trinkets and a campfire. The banner arranges trinkets by share and seed, so banners rarely repeat.

## Size budget

Pictures are inline SVG: one `<path>` per color, built from runs merged into rectangles, with `shape-rendering: crispEdges`.

| Output | Before art | With art | Budget (tested) |
|---|---|---|---|
| `sheet.html`, demo | 23 to 24 KB | 84 to 93 KB | under 160 KB |
| `card.svg` | 6 KB | 9 to 10 KB | under 24 KB |
| `portrait.png`, 256 px | none | under 2 KB | under 4 KB |
| `gallery.html` | none | about 400 KB | under 640 KB |

The banner is the largest piece, about 25 KB. A portrait is 3 to 4 KB. Chronicle chapters that share a look draw it once and reuse it.

PNGs come from a small writer on `zlib` and `struct`: RGBA, filter 0, fixed compression. `build` writes `portrait.png` only when the card is on, from the card's fields alone. `gallery --png` writes every picture.

## The card stays allowlisted

The card's portrait reads only `set`, `class`, `multiclass` and the rounded `stats`. It draws `<path>` elements with `fill` and `d` and nothing else, so `audit` lists no new strings. The test suite checks that the card's portrait matches the sheet's and ignores every other field.

## Replace the art

A pack is one JSON file. Start from the built-in one:

```
tinkerprint gallery --export-pack mypack.json
```

Edit grids and colors, then look at the result and build with it:

```
tinkerprint gallery --art-pack mypack.json --out preview
tinkerprint build --profile me.toml --art-pack mypack.json
```

What a pack holds:

- `ink`: fixed colors, one character each.
- `stat_colors`: light, mid and dark for each of the 13 stats.
- `sets`: plate, floor, wall and board colors for each set.
- `looks`: the hat, body, item and trinket each stat uses.
- `generalist`, `familiars`, `icons`: which part draws each.
- `parts`: grids. Each has `at` (its corner on the canvas), `rows`, and optional `palette` and `cover`.

The loader refuses a pack with a color that is not `#rrggbb`, a key no palette defines, rows of uneven width, or a missing part. A pack can change pixels and nothing else. It never adds text to a sheet or card.

## The alternative: a pre-made art pack

A hand-drawn or AI-made set of images could ship in place of the generator.

What it would improve:

- Faces, hands and fabric at a detail 32 pixels cannot hold.
- A distinct silhouette per class, where today pairs share an outfit and differ by item and accent.
- Poses, a banner with depth and lighting, familiars with personality.

What it would cost:

- **Combinations.** 7,000 portraits cannot each be drawn. A pack would cover 37 classes per set and drop the item and cape variation, or ship layered parts that still need composing.
- **Size.** Even small PNGs add up to megabytes in the package, against kilobytes of grids today. A sheet that embeds them grows too.
- **License and provenance.** Every image needs a clear license for an MIT repo. AI output needs a model whose terms allow it, and a record of how it was made.
- **Consistency.** Hand art for 74 classes drifts in style unless one person draws all of it.

The middle path fits the pack format as it is: draw or generate the parts at 32 pixels, quantize them to a palette, and write them as grids. The composer, the tests and the allowlist stay the same.
