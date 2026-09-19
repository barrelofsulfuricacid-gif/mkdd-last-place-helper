# Fog and speed (USA GM4E01 revision 0)

Both options are off by default and compose with both item modes, Maximum Bananas, and all Baby Park lap settings. Their writes do not overlap the existing patches. A changed or removed option requires disabling the previous code and fully restarting emulation.

## Fog

The 0–100 slider controls **distance fog** in GP/VS, including single-player and split-screen. It intercepts `ExModel::setFogInfo` for materials already configured to use native fog. Zero selects no fog; other values select perspective linear fog in neutral `#f0f2f4`. Calls outside GP/VS or without a race manager retain their original arguments. Camera near/far projection values are preserved.

With `q = (1 - fog / 100)^2`, start is `1200 + 8000*q` and end is `3200 + 48000*q` game units. These are mod tuning parameters, not meters or stock course settings. At maximum density, the first 1,200 units from the camera are clear, objects at 2,200 units are halfway blended, and fog-enabled objects at 3,200 units are fully blended. This keeps a clear foreground instead of collapsing the fog range onto the player.

The previous version also painted a screen-sized white rectangle and reduced the fog end to 10 units. That caused the reported white characters. The corrected generator emits **no overlay routine and no HUD draw hook**. The sky and intentionally unfogged materials may remain visible; this uses the game's depth fog, not volumetric particles. The browser gradient is illustrative, not a game screenshot.

**Upgrading:** replace/disable the old generated code, fully stop and restart emulation, and start a fresh race. Do not load an old save state: removing AR lines does not undo code already written into memory.

| Address | Original word | Purpose |
| --- | --- | --- |
| `80182490` | `9421FFC0` | Native fog setter hook; replays original stack allocation |
| `800050CC–800050DB` | zero padding | Fog type, start, end and color |
| `800050E0–8000512B` | zero padding | Material argument override |

The 24-line option composes with existing item and lap patches. `tools/assemble_fog.py` reproduces its instruction template using `keystone-engine`.

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

[doldecomp/mkdd's native material setter](https://github.com/doldecomp/mkdd/blob/main/src/Kaneshige/ExModel.cpp) explains how fog-enabled materials receive their distances and color; [libogc's GX definitions](https://github.com/devkitPro/libogc/blob/master/gc/ogc/gx.h) define perspective linear fog. The retail hook and original instructions were independently verified against the user's USA revision 0 disc. Debug-build addresses are not interchangeable with retail addresses.

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

The native suite checks all 101 fog values across nine modes, null manager/info guards (1,111 argument/scope cases), and the complete retail setter writing two synthetic materials (909 cases). It checks actual fog type/distances/color, unchanged intentionally unfogged materials, original HUD instructions, stack and nonvolatile register restoration. The virtual material accessor is represented by a two-instruction fixture; the setter and floating-point save/restore routines execute from the user's ISO. All 351 speed values still pass the native initializer in three classes (5,265 cases).

Portable regression checks ensure a clear foreground at every slider value, increasing density, absence of overlay writes, and 600 combinations with other options. Browser checks cover slider keyboard controls, automatic regeneration, copy/download, both item modes and desktop/mobile layouts. These checks do not render game graphics: live Dolphin races, cinematic camera angles and GPU appearance remain unverified. The disc image and user's Dolphin settings are never modified by these checks.
