# Fog and speed (USA GM4E01 revision 0)

Both options are off by default and compose with both item modes, Maximum Bananas, and all Baby Park lap settings. Their writes do not overlap the existing patches. A changed or removed option requires disabling the previous code and fully restarting emulation.

## Fog

The 0–100 slider uses two complementary changes in GP/VS (single-player or multiplayer):

1. Intercept `ExModel::setFogInfo` to give fog-enabled world materials linear distance fog in a neutral `#f0f2f4` color. Fog start/end move closer as intensity increases. Zero sets the native fog type to none. Other modes and calls without a race manager retain their original arguments.
2. Intercept `RaceDrawer::drawPostScene` immediately before the HUD draw. Restore the full-screen orthographic port and draw a fog-colored rectangle through native `J2DFillBox`, with alpha `round(255 * (fog / 100)^2)`. This covers sky, effects and materials that do not participate in distance fog. At 100%, alpha is 255; the native color routine chooses unblended replacement, leaving no world visibility. HUD and pause controls are drawn afterward.

The distance end is `10 + 50000 * (1 - fog / 100)^2` game units; start is one quarter of end. These are deliberately chosen mod parameters, not claimed stock settings or real-world meters. The whiteout is guaranteed by the final opaque rectangle, independently of distance-fog material coverage. The 0–1280 rectangle covers the game's full logical screen under its own orthographic port, including split-screen views.

| Address | Original word | Purpose |
| --- | --- | --- |
| `80182490` | `9421FFC0` | Entry to native material fog setter; replacement replays original stack allocation |
| `801A1E64` | `4BF824C5` | HUD draw call; replacement draws the fog veil then tail-calls original `80124328` |
| `80005000–80005073` | zero padding | Fog veil routine |
| `800050C0–800050DB` | zero padding | Rectangle size, alpha, fog type, distances and color |
| `800050E0–8000512B` | zero padding | Material argument override |

`tools/assemble_fog.py` reproduces the instruction templates using `keystone-engine`. The patch preserves the stack, link register, nonvolatile registers and original HUD receiver. It reuses native drawing routines rather than adding a second renderer. The browser's gradient preview only illustrates opacity; it is not a game rendering.

## Speed

[Ralf's USA class multiplier and overall speed-cap codes](https://www.gc-forever.com/forums/viewtopic.php?t=2435) identify the stock parameters. Their addresses and values were independently checked against the user's unmodified retail disc; no PAL addresses are used.

| Address | Original float | Custom value |
| --- | ---: | ---: |
| `80361D44` (50cc class) | 0.90 | `1.15 * cc / 150` |
| `80361D48` (100cc class) | 1.00 | `1.15 * cc / 150` |
| `80361D4C` (150cc/Mirror class) | 1.15 | `1.15 * cc / 150` |
| `803D1894` (global cap) | 200 | `200 * cc / 150` |

All values are encoded as IEEE-754 single-precision floats. The scalar entries are consumed by native `KartBody::InitBodySetting` for the four engine parameters at offsets `3F0–3FC`; both human and CPU karts use that setup. The slider does not add engine classes to the game menu, alter the simulation clock, or claim a calibrated physical displacement/speed relationship. It preserves kart-specific parameter differences while applying the selected multiplier. The global cap and class values also affect other game modes; track layout, AI strategy, and projectile parameters are not retuned for high speeds.

## Prior art and validation

The repository had no open fog/speed implementation or fork to reuse. Ralf's [fog-disable codes](https://www.gc-forever.com/forums/viewtopic.php?start=25&t=2435) only remove course fog and cannot provide the requested whiteout. [doldecomp/mkdd](https://github.com/doldecomp/mkdd) provides the material and draw-order semantics; its debug addresses cannot be used for the retail executable. The new hooks were located and verified in the retail USA disc. MKDD Extender's disc-patching workflow is unnecessary for this offline AR generator.

Run portable checks:

```sh
node tests/generator.cjs
node tests/positions.cjs
node tests/race-options.cjs
```

Run read-only retail verification with `unicorn` installed:

```sh
node tests/race-options.cjs /tmp/race-options.json
python tests/race_options_ppc.py /path/to/GM4E01.iso /tmp/race-options.json
```

The native suite checks all 101 fog values across nine modes, null manager/info guards, stack/register restoration, the real rectangle/color/vertex routines' FIFO output, and all 351 speed values through the native four-parameter initializer in three classes. GPU entry points, the orthographic-port receiver and paired-single matrix identity helper are stubbed; this verifies command generation rather than GPU rasterization. Live Dolphin races and high-speed handling have not been tested. The disc image and the user's Dolphin settings are never modified by these checks.
