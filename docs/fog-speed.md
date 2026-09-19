# Particle mist and speed (USA GM4E01 revision 0)

Both options are off by default and compose with both item modes, Maximum Bananas, Baby Park laps, skip intro, kart size and first-person view. Replace the old generated code and fully restart emulation after changing options. Do not load a previous save state: removing AR lines does not restore patched memory.

## Particle mist

The 0–100 slider controls the opacity of **native mist particles in the 3D scene**, in Grand Prix and VS. Zero adds no mist. The patch creates short-lived particle bursts near each active race camera's look point. It reuses the global `mk_koura_smoke` resource (`08CF`), enlarges its billboard particles and reduces their opacity. This is particle-based mist, not a physically volumetric renderer. Normal course/material fog is unchanged; there is no HUD hook or fullscreen overlay. Particles can intersect geometry and nearby cameras' clouds can overlap.

Every 20 race updates, each of up to four cameras gets a one-frame emitter burst, with rate 2 and particle lifetime 180 updates. The native engine fades and retires particles and emitters. Only the new emitter instance is modified; the shared resource and ordinary shell smoke are untouched. Null managers/cameras, invalid camera counts and allocation failure are handled; existing native particle calculation always runs. The native particle pool remains finite, so heavy effects can reduce available mist and split-screen may cost performance. No emitter pointers survive a race transition.

Density controls primary alpha `round(80 * density / 100)`, from 1 through 80; the particle rate and lifetime stay fixed. Tuning values are game units, not meters: volume radius 1800, vertical volume scale 0.25, camera-look height offset 300, particle scale 180. A camera moving faster than normal can outrun the clouds; this patch does not retune particles for extreme speed or kart sizes.

**Upgrade from old fog:** disable/delete the previous AR code, paste the newly generated replacement, stop and restart Dolphin, then start a fresh race without a save state. Old releases patched surface fog and one also used a white overlay; neither is part of this patch.

| Address | Original | Purpose |
| --- | --- | --- |
| `80189EA8` | `48073BA9` | Race call to native particle calculation; new linked branch `4BE7B0F9` |
| `80004FA0–800050FF` | zero padding | 88-word mist routine |
| `80005180–800051A3` | zero padding | Nine configuration words |
| `800051BC` | zero padding | Mutable frame counter; deliberately absent from AR writes |
| `801FD680` | native function | Create emitter by resource ID |
| `801FDA50` | native function | Original particle calculation |

Positive density adds 98 AR lines; zero adds none. `tools/assemble_fog.py` reproduces the instruction array using `keystone-engine` and `capstone`. External PPC branch displacements are encoded explicitly to avoid Keystone's numeric-target/label relocation issue. The scratch space is disjoint from the per-position tables ending at `80004F9F`, kart-size routines below `800041D8`, the relocated first-person routine at `80005220–800052E3`, and lap routines starting at `80005320`.

## Speed

[Ralf's USA class multiplier and overall speed-cap codes](https://www.gc-forever.com/forums/viewtopic.php?t=2435) identify the stock parameters. Their addresses and values were independently checked against the user's unmodified retail disc; no PAL addresses are used.

| Address | Original float | Custom value |
| --- | ---: | ---: |
| `80361D44` (50cc class) | 0.90 | `1.15 * cc / 150` |
| `80361D48` (100cc class) | 1.00 | `1.15 * cc / 150` |
| `80361D4C` (150cc/Mirror class) | 1.15 | `1.15 * cc / 150` |
| `803D1894` (global cap) | 200 | `200 * cc / 150` |

All values are encoded as IEEE-754 single-precision floats. The scalar entries are consumed by native `KartBody::InitBodySetting` for the four engine parameters at offsets `3F0â€“3FC`; both human and CPU karts use that setup. The slider does not add engine classes to the game menu, alter the simulation clock, or claim a calibrated physical displacement/speed relationship. It preserves kart-specific parameter differences while applying the selected multiplier. The global cap and class values also affect other game modes; track layout, AI strategy, and projectile parameters are not retuned for high speeds.

## Sources and validation

The implementation follows [MKDD's native particle manager](https://github.com/doldecomp/mkdd/blob/main/src/Sato/JPEffectMgr.cpp) and [JPA emitter allocation](https://github.com/doldecomp/mkdd/blob/main/libs/JSystem/JParticle/JPAEmitterManager.cpp). Addresses, call signatures and the available global particle resource were independently verified against the user's USA revision 0 ISO. Debug/PAL symbol addresses are not interchangeable with USA retail addresses. No game executable, texture, or particle asset is distributed.

```sh
node tests/generator.cjs
node tests/positions.cjs
node tests/race-options.cjs /tmp/race-options.json
node tests/kart-size.cjs
python tests/race_options_ppc.py /path/to/GM4E01.iso /tmp/race-options.json
```

The native suite executes the actual injected PPC instructions from the website output. Particle creation and calculation use call fixtures, while the speed initializer executes retail instructions. It checks all 101 density settings, nine modes, 0–5 cameras, all 20 cadence states, allocation success/failure, null pointers, unchanged neighboring memory, and stack/nonvolatile-register preservation. GPU rendering is not simulated. Portable checks also cover every speed slider value and combined options, including kart size.

Live visual validation used a separate Dolphin 5.0-20347 profile, Direct3D 11 and the user's unchanged USA ISO: translucent mist appeared around the kart and track in a single-player Luigi Circuit GP race, with the HUD clear. A multi-minute run retained free emitters and particles. Live split-screen validation is not complete; up to four camera pointers are covered by the native hook fixtures. This is not an all-course, all-camera or all-modifier gameplay qualification. Browser checks cover enabling, density changes, regeneration, copy/download, both item modes and desktop/mobile layouts. The browser preview is illustrative.
