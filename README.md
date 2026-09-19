# mkdd-last-place-helper
Le meilleur ami de mat

## Item chance mixer

**[Open the website](https://barrelofsulfuricacid-gif.github.io/mkdd-last-place-helper/)**

Choose relative weights for all 19 Mario Kart: Double Dash!! race items, including character specials, and generate a Dolphin Action Replay code for the last-place kart or independently for each race position, 1st through 8th.

- Live percentages, a catch-up preset, equal weights, and clear controls.
- Choose **Each race position (1st–8th)**, select a position, and enable **Custom chances** to edit its mix. Unchecked positions keep normal game odds. Presets and Clear affect only the selected mix; **Use this mix for all 8 positions** copies it to every position, which you can then edit independently.
- One generated code includes all configured positions. The preview shows the selected position. Enabled mixes must each contain at least one positive weight; errors identify the affected position even when another position is selected.
- **Last place only** retains the original behavior and a separate mix. In per-position mode, 8th means 8th: a four-kart race uses positions 1–4. Positions 1–7 initially retain normal odds and 8th starts with the catch-up preset.
- Set any item's weight to zero to exclude it; use whole-number weights from 0 to 1,000.
- Copy the generated code or download it as a text file.
- Check **Maximum Bananas** to append the banana-limit patch to both copied and downloaded code. It starts unchecked; toggling it updates an already generated code immediately.
- Enable **Fog / visibility**, then use the **0–100%** slider: 0% clears course fog; 100% gives dense distance fog with a clear foreground around the player. Distant fog-enabled scenery fades into pale fog. No screen overlay is added; the sky and materials without native fog may stay clear.
- Enable **Kart speed**, then choose a **150–10,000cc equivalent**. All human and CPU karts use the selected scale regardless of the selected class. 150cc is the normal 150cc baseline; 10,000cc multiplies the class-speed parameters and cap by 10000/150 (66.67×). These are modded equivalents, not new native engine classes. Speed affects all modes using these class parameters.
- Enable **Kart size** for **0–100×** visual scaling of human and CPU karts, with 0.1 steps and a **Reset to 1×** button. Zero collapses the models; 1× is normal. Optionally check **Scale physics and collisions** to also scale kart/wall/course-object collision radii, ground-contact vertices, mass and rotational inertia. At zero, physical size uses a 0.01× minimum. Physical scaling is experimental: suspension, AI, camera and item hitboxes retain their stock tuning, and extreme sizes can be undriveable. Both options start off. See [kart-size patch notes and validation](docs/kart-size.md).
- Fog and speed start disabled, preserving normal game settings. Moving either slider updates an already-generated code, including in per-position mode. Copy the replacement code and fully restart emulation; do not use an old save state. The small fog preview is illustrative, not a game screenshot.
- Entirely client-side, with no uploads, tracking, external dependencies, or installation.
- Download `index.html` and open it in a browser to use the tool offline.

### Game compatibility

This patch targets **USA GM4E01 revision 0**. It applies to **multiplayer Grand Prix and VS with at least two human karts**. Positions include CPU racers, and custom chances apply to whichever kart holds that position. Unconfigured positions, single-player races, and battle modes retain their normal item selection.

The position check happens when the item roulette finishes. Specials can be selected for any character. Fireball colors and Yoshi/Birdo eggs each share a game item ID. Golden Mushrooms retain their normal timed duration.

Default weights:

| Item | Weight | Chance |
| --- | ---: | ---: |
| Golden Mushroom | 10 | 33⅓% |
| Star | 10 | 33⅓% |
| Blue Shell | 3 | 10% |
| Triple Red Shells | 3 | 10% |
| Triple Mushrooms | 4 | 13⅓% |

### Use with Dolphin

1. Choose **Last place only** or **Each race position (1st–8th)**, configure your mixes, click **Generate AR code**, and copy the code. Per-position mode exports all enabled mixes together.
2. Right-click the game in Dolphin, open **Properties → AR Codes → Add**, name the code, paste it, save, and enable it.
3. Enable **Config → General → Enable Cheats**. Disable any previous last-place/item-replacement code before enabling this one.
4. Stop emulation and restart the game, then begin a multiplayer GP or VS race.

### Validation and limits

**Skip intro** adds five AR lines that skip the Nintendo/Dolby logo waits and opening movie, then automatically follow the title screen's normal Start-button path into the main menu. Normal loading, display-mode prompts, and memory-card checks still run. The setting defaults to off; toggling it adds or removes the lines in an already-generated code. Replace the old code and fully restart Dolphin. The target instructions were checked against the USA revision 0 ISO, and a separate Dolphin test profile reached the title menu (native state 4) without controller input, with all five patches confirmed active in memory. This checks startup, not gameplay interaction. The logo-wait patches and movie-exit delay come from [Ralf's USA startup codes](https://www.gc-forever.com/forums/viewtopic.php?start=150&t=2435); the movie-state bypass follows [MKDD Extender](https://github.com/cristian64/mkdd-extender/blob/main/code_patcher.py). The final line bypasses only the title screen's Start-button condition, preserving the native card-check/menu transition.

**Fog and speed** passed retail-executable checks in PowerPC emulation: 909 complete native fog material updates, 1,111 fog argument/scope cases, and 147,765 native speed-initialization cases. Regression checks cover a clear foreground at every fog intensity and prohibit the old screen-overlay writes. GPU rasterization and live Dolphin races were **not** tested. Portable checks cover every slider value and 600 option combinations; browser checks cover slider input, regeneration, copy/download and desktop/mobile layouts. After upgrading from the old fog code, replace it and fully restart Dolphin without loading a save state. See [fog and speed patch notes](docs/fog-speed.md).

**Baby Park laps** optionally sets 1–99 laps for every kart in Baby Park Grand Prix and VS races, including single-player GP. Leave the checkbox off to use the game's normal setting. Time Trials and other courses retain their normal lap rules. Changing the setting updates an already-generated code; copy the replacement code into Dolphin, disable the old code, and fully restart emulation.

**10–99 laps is experimental.** The generated code includes additional bounds fixes: the single-digit lap HUD is hidden for long races, only the first nine lap splits are retained in the results, later split popups are suppressed, and unavailable numbered Lakitu signs are skipped. The native final-lap signal and finish condition still use the actual lap count. This is not a two-digit HUD replacement. Native PowerPC checks covered all 99 settings, 456,192 course/mode initialization cases, 4,950 lap crossings through the native finish logic, and 792 native result-copy cases with memory guards. A complete long race in Dolphin has **not** been tested. See [patch notes](docs/baby-park-laps.md) for the hooks and validation scope.

**Maximum Bananas** raises the global track limits to 20 regular bananas and 6 giant bananas, with a 64-item overall ceiling. It allocates 28 regular and 8 giant banana objects. These are finite limits, not infinite items, and they apply globally rather than only to the last-place kart. Fully restart the game after enabling or disabling the code; do not load an old save state. The seven limit-patch lines come from [Ralf's USA item-limit codes](https://www.gc-forever.com/forums/viewtopic.php?start=25&t=2435). Their target addresses were checked against the USA revision 0 ISO; the patch and combined configuration have not been tested in a live race.

The game's executable, original hook, and unused patch regions were checked against a local USA revision 0 disc image. The original last-place routine passed 27,262 exhaustive ticket cases, 7,634 scope/register checks, and 120,000 draws through the game's original RNG under PowerPC emulation. The per-position routine separately passed **227,900 exhaustive ticket cases, 10,080 scope/register checks, and 120,000 native RNG draws**, including distinct position mixes, unconfigured positions, fewer racers, invalid rank guards, and unchanged memory outside the patch regions. Browser checks covered independent editing, cross-position validation, copying, downloads, both modes, Maximum Bananas, offline use, and widths of 1440, 390, and 320 pixels.

**Arbitrary special-item combinations have not been verified in live multiplayer.** The game retains its stock item pools unless Maximum Bananas is enabled; active-item limits can affect equipping or using a selected item. Avoid combining this code with other item/allocation patches or patches using the same memory space.

### Development

`index.html` is the complete website: HTML, CSS, item data, generation logic, and UI code. No build is required. Run the portable generator checks with Node.js 20 or newer:

```sh
node tests/generator.cjs
node tests/positions.cjs
node tests/race-options.cjs
node tests/kart-size.cjs
```

`tools/assemble_positions.py` reproduces the PowerPC instruction template using `keystone-engine`. The new routine uses the existing hook at `0x8020cbc8` and 132 bytes of the existing code cave at `0x80005420`. Its eight fixed-size 80-byte tables occupy verified zero padding at `0x80004d20–0x80004f9f`. A table starts with a 16-bit total followed by cumulative thresholds and item IDs; a zero total preserves the game's original selection. Both RNG calls preserve the table pointer in nonvolatile r28, and the original epilogue restores the saved registers. Full table writes clear unused slots when settings change. Disable other patches using either region.

To repeat native validation with your own unmodified USA revision 0 ISO (read-only), install the development-only `unicorn` Python package, then run:

```sh
node tests/positions.cjs /tmp/position-fixtures.json
python tests/positions_ppc.py /path/to/GM4E01.iso /tmp/position-fixtures.json
```

Prior-art review: the repository had no forks, releases, or existing issue/PR implementation to reuse. [doldecomp/mkdd](https://github.com/doldecomp/mkdd) documents position-based selection but targets the debug executable; [MKDD Extender](https://github.com/RenolY2/mkdd-extender) patches disc images, and [Ralf's position-based item codes](https://www.gc-forever.com/forums/viewtopic.php?start=100&t=1974) include PAL-specific addresses. This implementation extends the existing retail USA AR hook and offline workflow rather than importing incompatible addresses or adding a disc-patching dependency.

GitHub Pages serves the repository root from `main`; `.nojekyll` keeps this a plain static site. The generator checks also run on pushes and pull requests.

This unofficial fan tool contains no game image or game assets. Mario Kart and its characters belong to Nintendo.
