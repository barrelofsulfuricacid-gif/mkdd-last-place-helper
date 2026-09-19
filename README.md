# mkdd-last-place-helper
Le meilleur ami de mat

## Last-place item mixer

**[Open the website](https://barrelofsulfuricacid-gif.github.io/mkdd-last-place-helper/)**

Choose relative weights for all 19 Mario Kart: Double Dash!! race items, including character specials, and generate a Dolphin Action Replay code for the last-place kart overall.

- Live percentages, a catch-up preset, equal weights, and clear controls.
- Set any item's weight to zero to exclude it; use whole-number weights from 0 to 1,000.
- Copy the generated code or download it as a text file.
- Check **Maximum Bananas** to append the banana-limit patch to both copied and downloaded code. It starts unchecked; toggling it updates an already generated code immediately.
- Entirely client-side, with no uploads, tracking, external dependencies, or installation.
- Download `index.html` and open it in a browser to use the tool offline.

### Game compatibility

This patch targets **USA GM4E01 revision 0**. It applies to **multiplayer Grand Prix and VS with at least two human karts**. Last place includes CPU racers; other positions, single-player races, and battle modes retain their normal item selection.

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

1. Choose weights, click **Generate AR code**, and copy the code.
2. Right-click the game in Dolphin, open **Properties → AR Codes → Add**, name the code, paste it, save, and enable it.
3. Enable **Config → General → Enable Cheats**. Disable any previous last-place/item-replacement code before enabling this one.
4. Stop emulation and restart the game, then begin a multiplayer GP or VS race.

### Validation and limits

**Baby Park laps** optionally sets 1–99 laps for every kart in Baby Park Grand Prix and VS races, including single-player GP. Leave the checkbox off to use the game's normal setting. Time Trials and other courses retain their normal lap rules. Changing the setting updates an already-generated code; copy the replacement code into Dolphin, disable the old code, and fully restart emulation.

**10–99 laps is experimental.** The generated code includes additional bounds fixes: the single-digit lap HUD is hidden for long races, only the first nine lap splits are retained in the results, later split popups are suppressed, and unavailable numbered Lakitu signs are skipped. The native final-lap signal and finish condition still use the actual lap count. This is not a two-digit HUD replacement. Native PowerPC checks covered all 99 settings, 456,192 course/mode initialization cases, 4,950 lap crossings through the native finish logic, and 792 native result-copy cases with memory guards. A complete long race in Dolphin has **not** been tested. See [patch notes](docs/baby-park-laps.md) for the hooks and validation scope.

**Maximum Bananas** raises the global track limits to 20 regular bananas and 6 giant bananas, with a 64-item overall ceiling. It allocates 28 regular and 8 giant banana objects. These are finite limits, not infinite items, and they apply globally rather than only to the last-place kart. Fully restart the game after enabling or disabling the code; do not load an old save state. The seven limit-patch lines come from [Ralf's USA item-limit codes](https://www.gc-forever.com/forums/viewtopic.php?start=25&t=2435). Their target addresses were checked against the USA revision 0 ISO; the patch and combined configuration have not been tested in a live race.

The game's executable, original hook, and 188-byte unused patch area were checked against a local USA revision 0 disc image. The selection routine passed 27,262 exhaustive ticket cases, 7,634 scope/register checks, and 120,000 draws through the game's original RNG under PowerPC emulation. The webpage was checked for generation, copying, downloads, offline use, invalid inputs, and responsive layouts.

**Arbitrary special-item combinations have not been verified in live multiplayer.** The game retains its stock item pools unless Maximum Bananas is enabled; active-item limits can affect equipping or using a selected item. Avoid combining this code with other item/allocation patches or patches using the same memory space.

### Development

`index.html` is the complete website: HTML, CSS, item data, generation logic, and UI code. No build is required. Run the portable generator checks with Node.js 20 or newer:

```sh
node tests/generator.cjs
```

GitHub Pages serves the repository root from `main`; `.nojekyll` keeps this a plain static site. The generator checks also run on pushes and pull requests.

This unofficial fan tool contains no game image or game assets. Mario Kart and its characters belong to Nintendo.
