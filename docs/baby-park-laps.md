# Baby Park lap override (USA revision 0)

The optional generator setting accepts integer lap counts from 1 to 99. It sets `RaceMgr::mTotalLapNumber` after the stock course/VS/LAN lap initialization, but before the kart checkers allocate their lap-time and split arrays. The override checks course ID `0x21` and GP/VS mode (`2`/`3`). Time Trials, battle modes, and other courses retain their original initialization.

This is a new raw AR patch, checked against the retail USA executable. Its code occupies verified unused padding `0x80005320..0x800053E3`, immediately between exception stubs. It does not overlap the item routine at `0x80005420` or the banana pool patches. It is incompatible with other cheats that use these addresses. Completely restart emulation when enabling, removing, or changing the code; AR writes are not undone simply by unchecking a cheat during a running game.

## Hooks

| Retail address | Original instruction | Purpose |
| --- | --- | --- |
| `80187BFC` | `7FE3FB78` | Set Baby Park GP/VS lap count and replay the overwritten instruction |
| `80144934` | `A863002E` | Bound constructor digit lookup to 9 |
| `80189AB4` | `A803002E` | Copy at most nine result splits per kart |
| `8014F658` | `A885002E` | Show at most nine result rows |
| `8014F3B0` | `91471588` | Bound live UI lap/split index to 8 |
| `8014638C` | `40820100` | Hide lap HUD for totals above 9, preserving minigame skip |
| `80250FB8` | `4BFFF351` | Skip unavailable non-final Lakitu sign frames; final-lap branch remains native |
| `8014F4CC` | `3C800001` | Suppress split popups after lap 9 |
| `8014F3EC` | `2C1E000A` | Prevent the tenth split row from overwriting the following UI-position array |

Only the first hook is needed for 1–9 laps (15 AR lines). Counts from 10 to 99 include all bounds fixes (58 lines). The lap immediate is at `80005348`. All helpers use local conditional branches and full-range unconditional branches to return to the original executable; the Lakitu helper preserves the native link-register return.

For longer races the lap HUD is hidden, results contain the first nine splits, and later split popups are suppressed. The code does not provide a two-digit counter. Native race completion and final-lap logic retain the selected total. Short races keep their native HUD. The bounds helpers are installed globally when a long Baby Park count is selected, but only the Baby Park GP/VS initialization receives a custom count.

## Validation boundary

The local ISO's DOL SHA-256 was `e96b8578451b9157e2b68fe5e918ebb572940c3ea54d6c8c7d45c24382bf12ae`. Every overwritten word, code-cave byte, and adjacent exception boundary was checked before assembly. No disc image or game assets are included here.

Local Unicorn PowerPC execution used the retail executable to check:

- 456,192 combinations across all 99 lap counts, all 256 course bytes, GP/VS/other modes, native overrides, and default course counts.
- 792 complete native result-copy calls, covering 1–8 karts at each lap count, with exact memory comparisons protecting adjacent fields.
- 4,950 native lap-increment/finish crossings: the goal flag first becomes true at the selected lap, with the last split used as the final time.
- 4,950 live UI index cases, result-row visibility bounds, the tenth-row write guard, HUD branch destinations, unavailable sign suppression, and late split-popup suppression.

`node tests/generator.cjs` checks all lap counts with every existing item fixture and both banana settings, exact hook words, code size, option validation, preserved probabilities, and non-overlapping writes. Browser checks cover copy/download output, toggles, keyboard operation, invalid counts, offline use, and desktop/mobile layout.

**A complete long race in Dolphin is not yet verified.** These checks validate the executed code paths with controlled inputs, not full-game rendering, audio, heap behavior, multiplayer synchronization, or all special-item combinations. The website labels the option experimental.

## Research references

- [Ralf's USA codes](https://www.gc-forever.com/forums/viewtopic.php?t=2435) document individual course lap overrides and the limitations of simple high-lap changes. The published code-cave layout conflicts with the item generator and is not copied into this patch.
- [MKDD decompilation](https://github.com/doldecomp/mkdd): `KartChecker.cpp` documents dynamic lap arrays; `RaceMgr.cpp` and `RaceInfo.h` describe fixed result storage; `Race2D.cpp` contains fixed lap-row resources. Retail addresses were independently verified because debug symbols differ.
- [MKDD Extender](https://github.com/cristian64/mkdd-extender/blob/main/data/code/lib.c): its section-course lap override clamps counts to nine because unmodified result handling can crash. This generator supplies bounds fixes instead of only raising the count.
