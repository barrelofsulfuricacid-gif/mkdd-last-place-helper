# Kart size (USA GM4E01 revision 0)

Enable **Kart size** for a multiplier from **0 to 100**, in 0.1 increments. **Reset to 1×** restores normal size. The setting applies to human and CPU karts in every mode using the native kart display routine. It starts off and composes with both item modes and every other generator option.

The visual patch runs the native `KartDisp::MakeScaleMatrix`, then scales the body and twelve wheel/suspension display matrices about the body center. Scaling the wheel translations as well as their axes keeps the assembly together. Body and driver models receive the scaled matrix; shadows receive the same multiplier. Zero collapses the meshes without dividing by the selected visual size. Particles, equipped items, camera distance and culling distances are not resized. Extreme sizes can obscure the track or exhibit clipping.

## Optional physics and collisions

**Scale physics and collisions** is a separate checkbox, off by default, available when kart size is enabled. It is experimental. With physical multiplier `p = max(0.01, size)` it changes:

- Kart-to-kart collision radius: native body field `0x3A8`, multiplied by `p` after initialization.
- Wall-search radius: the second float in each distinct native `BodyOpData` record, multiplied by `p`.
- Course-object collision radius: all 21 entries of the GeographyObjManager radius table, multiplied by `p`.
- Ground-contact vertices: the body matrix used by the next physics pass carries `p` on its axes.
- Body dimensions, mass and rotational inertia: dimensions scale by `p`, mass by `p³`, and inertia by `p⁵`. These follow constant-density uniform scaling of the native rigid body. They are applied once after each native initialization, not repeatedly each frame.

At 0× the meshes collapse, but physics uses 0.01× so mass and inertia remain positive. At 1× these multipliers are identity. Suspension travel/springs, tire contact geometry, camera, AI, item hitboxes, object collision-center offsets and special roof checks retain their native tuning. This is **not** a complete geometrically rescaled vehicle simulation. Large or tiny settings can be undriveable; no full race or handling claim is made.

The game reuses its body display matrix for ground-contact checks. Before applying visual scaling, the patch saves the native matrix in the caller's no-longer-used `0x50–0x7F` local scratch space. After the final driver matrix copy, it restores that matrix with the physical multiplier (1 when the physics option is off). Visual zero therefore never has to be inverted to recover the collision matrix. Existing lightning/native size effects remain in the original matrix and are not used to fake permanent lightning status.

Changing or removing any option requires replacing the previous code and fully restarting emulation. Do not load an old save state. Patches using the same addresses are incompatible.

## Retail addresses

| Address | Stock word / meaning | Change |
| --- | --- | --- |
| `802D3DC4` | `4BFFF89D`, call native display scaling | Call visual wrapper |
| `802D3EB0` | `807E0020`, load first driver model | Scale shadow, replay load |
| `802D3EC4` | `4BEAFD45`, final driver matrix copy | Copy, then restore physical body matrix |
| `8029D6C0` | `BB810020`, initialization epilogue | Optional physical field scaling, replay epilogue |
| `80003F20–800041D7` | Verified zero padding | Instructions and two independent multipliers |
| `803636D4` | 21 pointers to 13 distinct `BodyOpData` records | Read-only reference for wall radii |
| `803635A0` through `803636C0`, stride `0x18` | 13 wall-radius floats (130–170) | Optional absolute scaled writes |
| `80353A74–80353AC7` | 21 object-radius floats (65–100) | Optional absolute scaled writes |

The new cave and writes are disjoint from the item, lap, banana, fog and speed patches. `tools/assemble_size.py` reproduces the instructions with `keystone-engine`.

## Prior art

[Ralf's USA codes](https://www.gc-forever.com/forums/viewtopic.php?t=2435) include a lightning-specific size modifier; it affects a temporary status and does not supply a persistent 0–100× size control. [doldecomp/mkdd](https://github.com/doldecomp/mkdd) supplies the display, ground-contact, rigid-body and collision semantics. Its debug/PAL addresses were not used as retail USA addresses: hook instructions, tables and the cave were checked against an unmodified USA revision 0 disc. MKDD Extender/track-patcher modify discs and do not provide a compatible slider patch to reuse. The target repository had no open issue, PR or fork implementing this feature.

## Validation

```sh
node tests/kart-size.cjs /tmp/kart-size.json
python tests/kart_size_ppc.py /path/to/GM4E01.iso /tmp/kart-size.json
```

The portable test covers all 1,001 slider values with physical scaling both off and on, invalid inputs, unchanged defaults, and 1,512 combinations with existing options. It checks that every write address is unique.

The read-only native test requires `unicorn`. It runs the actual retail display routine and patch code: 2,044 matrix/shadow cases across all eight kart slots, 1,061 injected physical-initialization cases, 147 native initializations covering every one of the 21 kart types, and 12,012 native kart-to-kart collision broad-phase threshold cases. It checks endpoints, physical positivity at zero, matrix restoration, register/stack preservation, original hook signatures, stock radius values and patch memory guards. The final model-copy call is stubbed to capture its matrix; collision-status filtering is stubbed to allow testing the size threshold. Contact response after the broad phase, suspension integration, GPU rasterization and live Dolphin gameplay remain untested.

Browser QA uses desktop 1440px and mobile 390px/320px. It covers keyboard endpoints and 0.1 steps, reset, physical zero handling, regeneration, both item modes, all options together, copy/download, toggling/removing options, invalid mixes and offline use. No browser console errors were observed.
