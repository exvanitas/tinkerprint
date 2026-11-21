# Art

The Woodland Guild is a set of original 48 × 48 pixel portraits. Each trade has its own character. The Warden is a broad badger behind a pavise, the Cartographer is a kingfisher with a telescope, and the Lorekeeper is a raven reading an open book. The builder stands above a moonlit viaduct. The tinkerer stands on a plum-colored lakeshore. The hills, sky and ground use closely spaced dark values so the faces and tools carry the light.

Run `tinkerprint gallery --out art` for the 74 classes, close-call costumes, multiclass capes, both workshops and the small sprites. Add `--png` to write individual PNGs.

## How a portrait composes

The top stat selects the animal, coat, stance and shoulder position. The runner-up supplies a handheld tool, a second piece of equipment worn on the opposite shoulder, and the pose of the working arm. For example, a mouse with Logic wears a blue mantle and leans on a staff. With Art it carries a paint palette and raises a brush. A specialist with a single rounded stat uses its own trade for both.

A multiclass adds a windblown cloak behind the figure. Its fabric and woven border use the two multiclass stats. The generalist is a tortoise with a walking crook and a rolled blanket dyed in the leading stat. The unclassed tortoise rests its hand at its side.

Layers are the cloak or pack, body, shoulder equipment, sleeve, head, and tool. The hand goes over the grip unless the tool covers it. A one-pixel material contour finishes the figure. The light comes from the upper left. All fixed inks, stat ramps and contours in the default pack come from 61 swatches. Steel has short ivory reflections, leather catches an ochre edge, and cloth uses larger uninterrupted folds.

Looks follow class shape alone. The sheet and card both rank shares rounded to 5%, breaking ties in the set's order. The card portrait reads only `set`, `class`, `multiclass` and the rounded stats. It contributes only paths with `fill` and `d` attributes to the card.

## Other pictures

| Picture | Composition |
|---|---|
| Workshop | A 252 × 72 studio with a lantern over a pressed fern, a distant aqueduct or windmill, and a rug for the figure. Active trades stock the cabinet. Party members bring their familiars. |
| Familiars | An owl, cat, jelly and fallback sprout slime. These also appear on the party cards. |
| Achievement pins | Each rule and the milestone fallback get their own silhouette. |
| Shelf miniatures | One object per stat, shared between the shelf and stat cards. |
| Chronicle | Each quarter shows its class portrait. A kettle hangs over the fire in quiet stretches. Repeated portraits reuse SVG definitions. |

The counter-mode SHA-256 stream places stock and companions from the same sheet seed on every build. PNGs use the standard library and fixed compression. The default `portrait.png` is an 8× integer enlargement, 384 × 384. The card and sheet hero use 3× pixels. The chronicle uses 2×. Inline SVG on the sheet and gallery carries lossless pixel art at its requested display resolution. The card and the chronicle’s reusable portrait definitions draw orthogonal paths. Each path joins same-color runs across rows, including stepped edges.

## Replace the pack

```
tinkerprint gallery --export-pack mypack.json
tinkerprint gallery --art-pack mypack.json --out preview
tinkerprint build --profile me.toml --art-pack mypack.json
```

The built-in heads, coats, tools, shoulder gear, pins and miniatures are literal character grids. Edit the corresponding row to move a highlight, change a sleeve or cut a notch in a feather. The landscape and workshop drawings are rasterized to the same grid format on export. A replacement pack contains only data. Each part has `at`, rectangular `rows`, and an optional local `palette`. A dot is clear. A grid key selects either a fixed ink or one of the following channels.

| Keys | Meaning |
|---|---|
| `A B C F` | Top stat, from highlight to deep shadow |
| `X Y Z H` | Equipment stat, in the same order |
| `T U` | Cloak fabric |
| `V W` | Cloak border |
| `@ + : ~` | Face and paw, from highlight to shadow, in a version 2 pack with `skin_colors` |

Every built-in head and exposed paw uses the same `skin_colors` array of four hex colors. Replacing that one array changes the skin ramp throughout the set. The feathers, fur markings, horns and eye details have their own inks. Older packs that omit the array keep their original grid keys.

A version 2 look references its body, head (`hat`), tool, trinket and shoulder gear. The gear's origin is relative to `shoulder`. The sleeve is registered to the costume's `grip` using the pack's reference `hand`. The tool and hand then move together by the tool's `offset`. The `edges` table maps an ink to its lit and shadow contour colors. Each set references its portrait scene and studio background.

The loader checks grid sizes, color values, keys, coordinates and part references. Pack metadata and part identifiers stay out of visible output. Earlier 32 × 32 version 1 packs retain their original composition rules.

## Size budgets

The art tests keep both invented demo sheets below 104,000 bytes, cards below 16,000 bytes and portrait PNGs below 4,800 bytes. The gallery limit is 240,000 bytes. The built-in gallery measures 215,843 bytes.
