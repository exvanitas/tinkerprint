# Art

The Woodland Guild works the night shift. Its 48 × 48 pixel portraits show people from thirteen trades. The Artificer wears copper goggles on a leather band. The Sage wears a moon-stitched hood. The Mechanist carries a pressure tank with brass valves. Through the workshop arch, the builder sees a moonlit viaduct and the tinkerer sees a windmill above the lake.

Run `tinkerprint gallery --out art` to see all 74 classes, both workshops, multiclass capes and the small pieces. Add `--png` to save individual sprites.

## Dressing a figure

The top stat selects the stance, clothes and headgear. The runner-up selects a tool, a sleeve pose and gear for the far shoulder. A Sage with Data carries a brass spyglass and map case. With Infra the same Sage braces a kite shield and buckles on a steel pauldron. A specialist who only has one rounded stat uses the tool of their own trade.

The generalist wears a traveling cloak and carries a crook and bedroll. The unclassed traveler has a bare head and rests a hand at their side. A multiclass adds a cape with a contrasting woven border.

The layers run from cape or pack through coat, shoulder gear, sleeve and head to the held tool. Ordinary handles use a separate hand layer. The open book, lantern, shield, spyglass and teapot include fingers drawn against their particular grips. Light comes from the upper left. A narrow dark line separates overlapping materials. The outer contour takes the color of the material along the silhouette.

All default inks come from 63 swatches. Brass takes a yellow glint and an ochre shadow. Steel reflects ivory and blue-gray. Each stat has a four-color fabric ramp. Every face and hand uses the same four skin colors. Replacing `skin_colors` in the pack changes all of them together.

## Presentation

Every sheet, card and chronicle uses the neutral head. The gallery shows the Sage, Artificer and Lorekeeper in all three presentations. In the built-in pack, neutral has a tucked or cropped cut and a clean jaw. Man has a shorter cut, a heavier brow and facial hair. Woman has a bob, waves, braid or low tail fitted to the headgear, with a small change at the mouth.

`art.figure` and `art.portrait` take the same optional keywords. Pass `presentation="neutral"`, `"man"` or `"woman"`. Pass `skin` with four hex colors, light to dark, to recolor the face and hands for one drawing.

```python
from tinkerprint import art

pack = art.default_pack()
sage = art.look_for("builder", "specialist", ["Logic"], ["Logic"])
portrait = art.portrait(pack, sage, presentation="woman")
figure = art.figure(pack, sage, skin=("#d7a471", "#a76a48", "#714a40", "#49323a"))
```

## On the sheet and card

| Picture | At display size |
|---|---|
| Workshop | A 252 × 72 room with a lantern over a drafting bench, an open arch and a stocked cabinet. The figure stands on the rug. A phone crops the scene around the figure and the party. |
| Portrait | The card draws 4× pixels. The level seal sits at the lower right, clear of the tools. The stand-alone portrait PNG is 384 × 384. |
| Chronicle | Each quarter shows its costume at 2×. A kettle hangs above the fire in quiet stretches. Repeated portraits share SVG definitions. |
| Familiars | A brass storm lantern for Claude, a portable typewriter for Codex, an amethyst orrery for Antigravity and a crank gramophone for any other harness. Each stands on the studio floor and appears at 3× on its party card. |
| Pins | Each achievement has its own 3× pin. A packet of sealed letters marks Swarm day. Four enamel quadrants share the Season's turn wheel. |
| Trinkets | Each trade stocks a miniature in the cabinet. Folded maps, book stacks and hourglasses appear at 4× on stat cards and 2× in smaller slots. |

The sheet and card rank stat shares rounded to 5%, breaking ties in set order. The card portrait reads `set`, `class`, `multiclass` and the rounded stats. Card artwork contributes only SVG paths with `fill` and `d`. The sheet and gallery embed lossless PNGs. The chronicle uses reusable paths.

`banner(..., with_figure=False)` returns the furnished studio. `banner_figure_box` locates the figure layer for the close-call swap. The counter-mode SHA-256 stream places stock and companions deterministically. The sheet uses `stat_ramp` for the stat colors and deepens the bars as needed for the light theme.

## Replace the pack

```
tinkerprint gallery --export-pack mypack.json
tinkerprint gallery --art-pack mypack.json --out preview
tinkerprint build --profile me.toml --art-pack mypack.json
```

The built-in art uses character grids and hand-placed polygons. Export resolves both into plain JSON. Each part has an `at` coordinate, rectangular `rows` and an optional local `palette`. A dot is transparent. Other characters select a fixed ink or a palette channel.

| Keys | Meaning |
|---|---|
| `A B C F` | Outfit, highlight to shadow |
| `X Y Z H` | Equipment, highlight to shadow |
| `T U` | Cape fabric |
| `V W` | Cape border |
| `@ + : ~` | Skin, highlight to shadow, in version 2 packs with `skin_colors` |

A version 2 look references its body, head (`hat`), tool, trinket and shoulder gear. The gear origin follows the costume's `shoulder`. The sleeve registers against the costume's `grip` using the reference `hand`. The tool's `offset` locates the closed fingers and handle together. A part with `seam: true` inks its contact edge where it overlaps existing paint. The `edges` table supplies lit and shaded outlines. With `mixed_gear_only: true`, the far shoulder takes extra gear when the outfit and tool come from different trades.

The loader checks coordinates, colors, grid keys, flags and references. Pack names and part identifiers stay out of visible output. Earlier packs retain their original composition rules.

### Add a hair or face variant

In an exported pack, the `hat` part is the complete neutral head. A named entry in `presentations` maps each neutral head part to a replacement. The map covers every distinct `hat` used by the trades, the generalist's hat and the unclassed `base`. Packs without this table draw their original heads by default. Requesting an unknown presentation raises `PackError`.

For example, to give the Sage a shorter braid in the woman presentation, edit `parts["logic-head-woman"]["rows"]`. Dots clear pixels. Keep the hood and its registration at `at`, use `@ + : ~` for skin and carry the hair colors through the cut. The built-in beards use three local palette keys, `^` for light, `$` for midtone and `&` for shadow.

To add a separate choice, copy an existing presentation map under a new name such as `cropped`. Duplicate the head part you want to edit, point that entry in the new map at the copy, and draw its rows. Other entries can share existing parts. Load the JSON with `art.load_pack` and pass `presentation="cropped"` to draw it.

## Size budgets

The art tests keep both demo sheets under 104,000 bytes, cards under 30,000 bytes, portrait PNGs under 4,800 bytes and the gallery under 240,000 bytes.
