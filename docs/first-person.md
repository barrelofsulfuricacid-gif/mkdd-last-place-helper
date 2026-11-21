# First-person race camera

The **First-person view** checkbox defaults to off. It adds a kart-mounted forward camera to normal GP, VS and Time Trial driving, using the target kart of each viewport. It works with either item-chance mode and updates generated/copied/downloaded codes immediately. Replace the old code and fully restart emulation after changing it.

At zero setback the viewpoint sits slightly ahead of the driver. **Move camera back** shifts the eye and target together along the kart’s forward axis. Height ranges from 0 to 160 game units and downward tilt ranges from 0° to 30°. Reset restores zero setback, a height of 90 and a level view. It uses the kart's orientation, including pitch and roll. Other karts and drivers remain visible. Rescue, launch, pipe, rear-view and cinematic camera paths retain native behavior. Battle is excluded. Item-chance restrictions are unchanged.

## Retail USA revision 0 patch

- Hook: `0x802b7484`, the `addi r3,r31,0x80` immediately before the normal `KartCam::OutView` look-at arguments. Original instruction: `387F0080`. Replacement: `4BD4DD9C`.
- Routine: `0x80005220–0x800052d3` (180 bytes); constants: `0x800052d4–0x800052e3`. Both are checked zero padding in the retail executable, separate from particle mist ending below `0x800051e4` and lap routines starting at `0x80005320`. This relocation allows mist and first-person view to be enabled together.
- RaceMgr and RaceInfo are null-checked; race modes 1–3 are allowed. The hook is in the normal driving camera path, not the common dispatcher, so special camera paths are not overridden.
- Each camera's target body comes from `r31+0`, not a hardcoded player slot. The body player-position matrix at `+0x140` provides translation, up and forward vectors. Native size at `+0x568` and the selected visual size determine camera offset.
- `eye = translation + (height × up + (120 − setback) × forward) × nativeSize × max(0.01, visualSize)`. With size disabled, visualSize is 1. `target = eye + 1000 × (forward − tan(tilt) × up)`. The up vector follows the kart. A nonzero tilt uses the additional routine at `0x80004c70` and slope at `0x80004c68`.
- Stores only camera eye/target fields (`+0x1e8/+0x1f4`) and the native stack-local up vector (`sp+0x80`). Replays the replaced instruction and resumes at `0x802b7488`, retaining the original look-at call and subsequent audio-camera update. No model visibility, physics or collision data is altered.
- `tools/assemble_camera.py` reproduces the instruction words with Keystone. No game image or assets are distributed.

## First-person drift indicator

The race HUD draws a bar in the lower center of each drifting kart’s normal driving viewport. Its three fill widths and colors follow the same status bits and mini-turbo charge byte as the retail wheel effects. Releasing the drift removes the bar. **Show drift charge** can be turned off independently of camera placement.

The hook at `0x80145dc8` runs after the race HUD installs its projection. It reads each camera’s target, mode and viewport, maps the bar into HUD coordinates, draws the background and charge with the game’s `J2DFillBox`, then resumes the displaced `GXClearVtxDesc` call. The routine and data start at `0x80004a20` and `0x80004c20`.

## Instant respawn by race place

Enable the checkbox and select any combination of 1st through 8th. Each fall samples the kart’s one-based race rank from its own race checker. A kart falling in a selected place uses the native recovery point and heading. Ordinary terrain falls, including water and voids, skip the wipe and 100-tick wait. Course-object captures such as the antlion keep their usual behavior.

The hook at `0x802bfce0` runs after rescue initialization has registered the checkpoint warp. A selected fall uses the next simulation tick for relocation, giving the lap checker time to record the departure sector. Hooks at `0x802c0024`, `0x802becf4` and `0x802c0598` enter the native warp and landing paths, remove the 1,800-unit lift, leave 30 units of clearance, and bypass the drop timer. Wheel contact and normal rescue cleanup release control. The byte mask lives at `0x800042dc`. All hook words are reproducible with `tools/assemble_driving.py`.

## Validation and limits

`node tests/first-person.cjs` checks default-off parity, invalid values, 2,376 combinations with existing options, and distinct write addresses. The optional retail ISO check executes the generated PowerPC hook in Unicorn: 13,176 cases across four distinct camera targets, arbitrary yaw/pitch/roll and positions, setbacks of 0, 90 and 200 units, native shrink/grow factors, visual sizes from 0 to 100, race modes and null guards. It verifies the computed geometry, memory boundaries, native look-at arguments and preserved registers.

```sh
node tests/first-person.cjs /tmp/camera.json
python tests/first_person_ppc.py /path/to/GM4E01.iso /tmp/camera.json
```

The driving option suite checks all 256 rank masks and all 201 camera setbacks, 161 heights and 31 angles in both item modes. The retail hook tests exercise 420 rank, mode and rescue-type combinations, the selected and ordinary timer/height paths, and 112 HUD cases across four viewport counts. The HUD tests inspect native draw-call colors and geometry.

```sh
node tests/driving.cjs driving.json
python tests/driving_ppc.py /path/to/GM4E01.iso driving.json
```

Browser checks cover desktop and mobile (1440, 390 and 320 pixels), keyboard access, both item modes, combined options, regeneration, copy/download, disabling and offline HTML use.

In a recorded single-player GP race on Rainbow Road with USA revision 0, Dolphin rendered all three drift colors. An eighth-place fall entered rescue on race frame 1,313, reached the course checkpoint on frame 1,314, and returned to normal driving by frame 1,321. Split-screen indicator routing was tested at the native draw-call boundary. Kart and driver models vary, and far-back camera positions can put the view inside the driver. Extreme kart sizes can put the camera through scenery.

Prior-art review: [Ralf's USA Driver Camera code](https://www.gc-forever.com/forums/viewtopic.php?t=2435) changes follow-camera parameters at a different point; it is not reused or relabeled as this view. [doldecomp/mkdd](https://github.com/doldecomp/mkdd) provides camera dispatch, matrix and body semantics. PAL/debug addresses were not copied: the hook, arguments and cave were checked directly against the unmodified USA revision 0 executable.
