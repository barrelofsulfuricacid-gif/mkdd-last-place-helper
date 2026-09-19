# First-person race camera

The **First-person view** checkbox defaults to off. It adds a kart-mounted forward camera to normal GP, VS and Time Trial driving, using the target kart of each viewport. It works with either item-chance mode and updates generated/copied/downloaded codes immediately. Replace the old code and fully restart emulation after changing it.

This is a front-of-kart viewpoint, slightly ahead of the driver, not a character-specific eye/bone attachment. It uses the kart's orientation, including pitch and roll. Other karts and drivers remain visible. Rescue, launch, pipe, rear-view and cinematic camera paths retain native behavior. Battle is excluded. Item-chance restrictions are unchanged.

## Retail USA revision 0 patch

- Hook: `0x802b7484`, the `addi r3,r31,0x80` immediately before the normal `KartCam::OutView` look-at arguments. Original instruction: `387F0080`. Replacement: `4BD4DD9C`.
- Routine: `0x80004fa0–0x80005053` (180 bytes); constants: `0x800050b0–0x800050bf`. Both are checked zero padding in the retail executable, separate from particle mist ending below `0x800051e4` and lap routines starting at `0x80005320`. This relocation allows mist and first-person view to be enabled together.
- RaceMgr and RaceInfo are null-checked; race modes 1–3 are allowed. The hook is in the normal driving camera path, not the common dispatcher, so special camera paths are not overridden.
- Each camera's target body comes from `r31+0`, not a hardcoded player slot. The body player-position matrix at `+0x140` provides translation, up and forward vectors. Native size at `+0x568` and the selected visual size determine camera offset.
- `eye = translation + (90 × up + 120 × forward) × nativeSize × max(0.01, visualSize)`. With size disabled, visualSize is 1. `target = eye + 1000 × forward`. The up vector follows the kart.
- Stores only camera eye/target fields (`+0x1e8/+0x1f4`) and the native stack-local up vector (`sp+0x80`). Replays the replaced instruction and resumes at `0x802b7488`, retaining the original look-at call and subsequent audio-camera update. No model visibility, physics or collision data is altered.
- `tools/assemble_camera.py` reproduces the instruction words with Keystone. No game image or assets are distributed.

## Validation and limits

`node tests/first-person.cjs` checks default-off parity, invalid values, 2,376 combinations with existing options, and distinct write addresses. The optional retail ISO check executes the generated PowerPC hook in Unicorn: 4,392 cases across four distinct camera targets, arbitrary yaw/pitch/roll and positions, native shrink/grow factors, visual sizes from 0 to 100, race modes and null guards. It verifies the computed geometry, memory boundaries, native look-at arguments and preserved registers.

```sh
node tests/first-person.cjs /tmp/camera.json
python tests/first_person_ppc.py /path/to/GM4E01.iso /tmp/camera.json
```

Browser checks cover desktop and mobile (1440, 390 and 320 pixels), keyboard access, both item modes, combined options, regeneration, copy/download, disabling and offline HTML use.

**Experimental: no live Dolphin race or GPU-rendered camera test has been performed.** Head/model occlusion, near-plane clipping, screen shake and course behavior need gameplay validation. Extreme kart sizes can put the camera above, below or through track scenery. Zero visual size uses a tiny nonzero camera offset; the projection near plane is unchanged. Disable other patches that change the same camera hook or use its cave.

Prior-art review: [Ralf's USA Driver Camera code](https://www.gc-forever.com/forums/viewtopic.php?t=2435) changes follow-camera parameters at a different point; it is not reused or relabeled as this view. [doldecomp/mkdd](https://github.com/doldecomp/mkdd) provides camera dispatch, matrix and body semantics. PAL/debug addresses were not copied: the hook, arguments and cave were checked directly against the unmodified USA revision 0 executable.
