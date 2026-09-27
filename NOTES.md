# Findings

Everything we've learned so far about THUG Pro's script data and the Skate-Tricks
(Skatetris) goal. The game data itself is never committed; run `tools/extract.py`
to regenerate `extracted/` locally and follow along.

Versions this was worked out against: THUG Pro 0.6.0.11 (`changelog.txt`) on a
retail PC THUG2 install.

## File formats

### PRE / PRX archives (`data/pre/*.prx`)

Little-endian, version 3:

```
header:  u32 total_file_size, u16 version (=3), u16 magic (=0xABCD), u32 file_count
entry:   u32 size, u32 compressed_size (0 = stored), u32 name_len, u32 name_checksum
         name (NUL-terminated, padded to name_len, name_len is a multiple of 4)
         data (compressed_size or size bytes), padded to 4
```

- `name_checksum` is the QB key of the lowercased path (e.g. `qb\thugpro\control_setup.qb`).
- Compression is Neversoft LZSS: 4096-byte ring buffer, initial write position
  4078 (N - F), max match 18, threshold 2, flag byte read LSB first, `1` = literal.
  Match = 2 bytes: `pos = b0 | (b1 & 0xF0) << 4`, `len = (b1 & 0x0F) + 3`.
- Stored (uncompressed) entries are accepted by the game, which is what
  `prx.replace()` writes. A no-op repack reproduces the original byte-for-byte.

### QB key (checksum)

`crc32(name.lower()) ^ 0xFFFFFFFF`, i.e. standard CRC-32 without the final XOR.

### QB bytecode (THUG2 / THUG Pro PC)

A flat token stream; each token is one opcode byte plus operands. Names are
checksums; each file ends with a name table of `0x2B` entries
(`0x2B, u32 checksum, NUL-terminated name`) then `0x00`. Harvest these tables
across all files for name resolution; accept an entry only if
`qbkey(name) == checksum` (matching raw `0x2B` bytes gives false hits).

| op | meaning | operands |
|----|---------|----------|
| 00 | end of file; **inside a script it is an alternate encoding of `begin`** (pairs with 21; ~200 occurrences) | |
| 01 | end of line | |
| 02 | end of line + line number (decompiled as a line starting with `@N`) | u32 |
| 03/04 | `{` / `}` | |
| 05/06 | `[` / `]` | |
| 07 `=`, 08 `.`, 09 `,`, 0A `-`, 0B `+`, 0C `/`, 0D `*`, 0E `(`, 0F `)` | | |
| 11 `==`, 12 `<`, 13 `<=`, 14 `>`, 15 `>=` | | |
| 16 | name | u32 checksum |
| 17 | int | i32 |
| 18 | hex int | u32 |
| 1A | float | f32 |
| 1B | string | u32 len (incl. NUL), bytes |
| 1C | local string | u32 len, bytes |
| 1E | vector | 3×f32 |
| 1F | pair | 2×f32 |
| 20 / 21 / 22 | begin / repeat / break | |
| 23 / 24 | script / endscript | |
| 25 / 26 / 28 | if / else / endif (old form, no offsets) | |
| 27 | elseif | u16, u16 |
| 29 | return | |
| 2B | name table entry | u32 checksum, C string |
| 2C | `<...>` (all args) | |
| 2D | argument prefix, followed by 16 → `<name>` | |
| 2E | jump | u32 |
| 2F / 37 / 40 / 41 | Random / Random2 / RandomNoRepeat / RandomPermute | u32 n, n×u16 weights, n×u32 offsets (**all four** have weights) |
| 30 / 38 | RandomRange / RandomRange2 | |
| 32 `\|\|`, 33 `&&`, 39 `NOT`, 42 `:` | | |
| 3C / 3D / 3E / 3F | switch / endswitch / case / default | |
| 47 | fast if | u16 offset |
| 48 | fast else | u16 offset |
| 49 | short jump (switch/case) | u16 |

Fast if/else offsets are measured **from the u16 field itself**. `if` jumps to
just past the matching `else`'s u16 (or just past `endif`); `else` jumps to
just past `endif`.

Tooling status: `qbdec.py` decompiles all 810 script files from both games.
`qbc.py` compiles the same syntax. `roundtrip.py` decompiles and recompiles
every file and compares the code bytes: 527 are byte-identical, 0 mismatch, and
283 are skipped because the compiler doesn't yet support
`switch`/`elseif`/`Random*`.

## Script layout (paths inside `extracted/thugpro/`)

- `qb/game/goals/goal_tetris.q`: Skate-Tricks goal. Only a param struct
  (`goal_tetris_genericParams`), init/activate/etc. hooks, the on-screen trick
  list UI, and trick→button-text tables. **All trick selection, timing,
  stacking and completion checks are native code.**
- `qb/game/goal_editor/goal_editor.q`: Create-a-Goal param presets
  (`EditedGoal_ExtraParams_SkateTris`, `..._ComboSkateTris`, `..._TrickTris`)
  and the `cag_key_combos` trick sets.
- `qb/game/net/trick_attack.q`: "High Score Run" (TrickAttack), the pattern
  we copied for starting a goal from the pause menu (`GoalManager_AddGoal`, then
  `GoalManager_EditGoal`, then `GoalManager_ActivateGoal`).
- `qb/game/menu/gamemenu_pause.q`: pause menu. Free skate items live in
  `if GameModeEquals is_singlesession`.
- `qb/game/goal_utilities.q`: `goal_init`, `goal_start`,
  `goal_initialize_skater`.
- `qb/game/Levels.q`: level load adds TrickAttack then `init_goal_manager`
  (`GoalManager_InitializeAllGoals`). Our goal is added later and never
  initialized; that turned out not to matter.
- `qb/thugpro/command_parser.q` / `qb/game/game.q`: chat `/commands` are parsed
  locally before sending (`entered_chat_message`), but the on-screen chat
  keyboard is only offered `if InNetGame`. That's why we went with the pause
  menu.
- Other goal types: `goal_trick_beat.q` (Trick to the Beat).

THUG Pro also loads loose level scripts from
`User\data\levels\<name>\<name>_scripts.qb` (strings in `thugpro.dll`), which
might be another injection route. `THUGPro.exe` still contains the old
`runnow.qb` hook, but it's tied to the "THUG2 Viewer" remote debugger.

## Starting Skate-Tricks from free skate: what the engine needs

Worked out from two crashes (see `mod/doakickflip.q` for the result):

1. **Don't give it level node params.** `goal_tetris_genericParams` has
   `trigger_obj_id`, `start_pad_id`, `restart_node` pointing at career-level
   nodes. With `quick_start`, `goal_start` → `goal_initialize_skater` does
   `ResetSkaters node_name = <restart_node>` on a missing node. So we spell out
   the params without those three.
2. **The trick pool param is `goal_tetris_key_combos`**, not `key_combos`.
   - The Skate-Tricks updater in `THUGPro.exe` (function around `0x56fb2f`) does
     `GetArray(goal_tetris_key_combos)`. If absent it does
     `GetArray(goal_tetris_tricks)` and dereferences the result without a null
     check → access violation at `0x0056FBDD` reading address 4.
   - Elements: if the element's symbol type is `0x0D` (name) it's used directly as the trick;
     otherwise it's a struct read with `key_combo` (required), and optional
     `num_taps` and a couple of unidentified flags (`0x8c8abd19`, `0xedf5db70`).
   - Create-a-Goal builds this array in native code (function at `0x4e98f0`,
     called from `0x4e9dd1` and `0x4ea211`) from the global `cag_key_combos`
     sets. If none are selected it prints "No combo sets specified, using
     emergency_key_combos" and uses `emergency_key_combos`.
3. `quick_start` skips the goal intro. Without it, `goal_tetris_activate` waits
   for `goal_cam_anim_post_start_done` before adding tricks, and that event
   presumably never fires with no intro cam.
4. `unlimited_time`: the run only ends when the stack fills (`max_tricks`).

Tuning knobs (in the goal params): `trick_time` (ms between tricks),
`max_tricks`, `acceleration_interval`, `acceleration_percent`,
`time_to_stop_adding_tricks`.

Resolved checksums seen in native code: `0x7be1e689` goal_tetris_key_combos,
`0xeb79fb49` goal_tetris_tricks, `0x79704516` key_combos, `0xacfdb27a`
key_combo, `0xa4bee6a1` num_taps, `0xdf1451eb` cag_key_combos, `0x6d641bcb`
emergency_key_combos, `0x270f56e1` trick, `0x255ed86f` grind, `0xc4745838` text.

## THUG Pro file redirect and `User\Data`

`thugpro.dll` hooks `CreateFileA` (hook entry `0x10014bb0`). For any path
containing `Data\` (matched with `StrStrIA`, so case-insensitive; the engine
uses lowercase `data\`) and not `thugpro.exe`:

1. Look the path up in a cache of earlier redirects (`0x10015350`, FNV hash map;
   filled at `0x10015211` after a successful search). It isn't an override
   mechanism.
2. Rewrite `.pre` to `.prx` (plus a similar swap on a `...tex` extension), then try
   these roots in order, taking the first that opens (observed with `+file`):
   1. the THUG Pro folder (stock install)
   2. `<THUG Pro>\..\output\`
   3. the THUG2 install folder (e.g. `C:\Program Files (x86)\Activision\Tony Hawk's Underground 2\Game\`)
   4. `<THUG Pro>\User\`
3. A missing-image fallback substitutes a placeholder texture.

So `User\Data\...` can only **add** files the stock install lacks; it can't
override `data\pre\thugpro_qb.prx`. A `+file` trace of startup, loading a level,
and free skate showed the only files probed under `User\` and not found are
`manifest_levels.dat` and `manifest_soundtracks.dat` (custom level / soundtrack
manifests). No stray script loads, so there's no zero-patch hook. Custom
levels load `User\data\levels\<name>\<name>_scripts.qb`, which would only
work inside that level.

`LoadQB "doakickflip\\tricks.qb"` from script does go through the redirect and
reads a loose `User\Data\doakickflip\tricks.qb` (verified). The mod uses this
for the trick list: the file is compiled QB (from `mod/tricks.txt` via
`tools/tricks.py`) and reloaded every time the goal starts, so it can change
without restarting the game.

## Trick order

The engine picks each new trick at random from `goal_tetris_key_combos`, re-read
from the goal params on every add, and runs `goal_tetris_add_trick` (looked up
by name) on each new trick's screen element. The mod patches
`goal_tetris_add_trick` to call `doakickflip_on_trick_added`, which sets the
list to the next single trick via `GoalManager_EditGoal`. At the end of the list
it sets `wait_to_add_tricks = 1` (read by the engine) to stop adding. Verified in
game: tricks appear in file order and stop after the last one.

Other native tetris script hooks the engine calls by name:
`goal_tetris_add_red_trick`, `goal_tetris_remove_trick`,
`goal_tetris_turn_trick_red`, `goal_tetris_turn_trick_white`,
`goal_tetris_reset_trick_container`, `goal_tetris_play_trick_removed_sound`.

## Skate-Tricks update loop and live mode

The Skate-Tricks update (`THUGPro.exe` `0x570c40`), reverse engineered while
building live mode:

- If goal param `wait_to_add_tricks` is non-zero it runs only the generic goal
  update and returns. That skips **everything** tetris-specific: adding tricks,
  fading tricks done in the current combo (`0x56f3b0`, alpha from
  `goal_tetris_faded_trick_alpha` / `goal_tetris_unfaded_trick_alpha`), and the
  "stack nearly full" red warning (`goal_tetris_turn_trick_red`, when the count
  reaches a fraction of `max_tricks`). Clearing tricks when a combo lands is a
  separate handler, so it still works.
- Adding is timer driven. An internal counter (`goal+0x434`, ms since the last
  add) is compared against goal param **`#648d8d2a`** (no known name). When it
  exceeds that value the engine adds one trick (`0x56fa30`; `combo_size` for
  combo variants) and resets the counter. `#648d8d2a` is copied from `trick_time`
  when the goal activates (`0x56f2e0`, which also zeroes `#8d958f01`, the
  cleared-trick count). Every `acceleration_interval` cleared tricks,
  `#648d8d2a *= (1 - acceleration_percent)` (`0x56f954`).
- Each stack slot stores the key combo it was added for (`slot+0x78`). Fading
  asks the skater's current combo whether it contains that trick.
- `Trick_Flag` is an optional goal param read by the fade function.

**Live mode** ("Do a Kickflip!" in the free skate pause menu) uses this:
`#648d8d2a = 2000000000` keeps the goal idle with the update still running (so
fading and the red warning work). A request sets the pool to one trick and
`#648d8d2a = 100`. The counter has been running while idle, so the trick is
added on the next frame. The `goal_tetris_add_trick` hook then sets it huge
again. The 100 ms (not 0) leaves the hook time to run before a duplicate could
be added. In-game test: tricks appear quickly (not instant, plenty fast),
exactly once each, and fade when done mid-combo.

Requests come from `data\doakickflip\inbox.qb` (→ `User\Data`), re-`LoadQB`'d
every 0.1 s while the goal is active and no request is in flight:
`doakickflip_inbox = [ { seq = N goal_tetris_key_combos = [ <combo> ] } ... ]`,
oldest first. The game remembers the last `seq` it handled, and at goal start
skips everything already in the file. `tools/call_trick.py` writes it: it keeps
the last 32 requests, keeps `seq` increasing across runs via `inbox.json`, and
replaces the file atomically (write `.tmp`, rename).

To encode an inbox from another language: it's a flat QB token stream. Key
bytes: `0x16 <u32 qbkey>` name, `0x07` `=`, `0x17 <i32>` int, `0x03`/`0x04`
struct braces, `0x05`/`0x06` array brackets, `0x01` newline, and the file ends
with `0x00`. The name table (`0x2B` entries) is optional.

## High combo mode ("Do a Kickflip!", current design)

Chat picks the tricks; your normal combo is the score. A request clears as soon
as you do the trick, mid-combo, and too many pending requests make you bail.
This no longer uses the Skate-Tricks goal at all. Its native logic only clears
tricks when the combo is banked, fails the goal on overflow, and offers no
script function to remove a single trick:

- Removal of done tricks (`0x570a70`) runs only from `ClearPanel_Landed`
  (`0x523560` member-function switch, case `0x11ca5c42`), which is also what
  banks the combo (`tricks.q`), so script can't trigger it mid-combo.
- `Trick_Flag` (used by NY's burning-taxi goal) only gates the same on-land
  check. Per-trick removal (`0x574f00`) belongs to the Trick to the Beat class.

What's used instead, all from script (`mod/doakickflip.q`):

- **Detecting a done trick:** `GetNumberOfTrickOccurrences TrickText = "Kickflip"`
  returns `Number_Of_Occurrences` in the current combo (native `0x5b1610`: it
  checksums the text and asks the skater's combo). It's a **global** function.
  Called as `skater: GetNumberOfTrickOccurrences` the result never reaches the
  calling script. Each entry stores a baseline count taken at request time; the
  entry clears when the count exceeds it, and the baseline resets when counts
  drop (the combo ended). Grinds are stored with a direction (`BS 50-50`).
- **The list is the stock Skate-Tricks UI:** `create_tetris_menu`
  (`tetris_menu_anchor` / `tetris_tricks_menu`), and each entry is built like
  the engine builds one (`~0x570100`): a `ContainerElement` with
  `dims = (100, 20)`, child 0 = trick text in `newtrickfont`, child 1 = button
  glyphs from `goal_tetris_trick_text` / `goal_tetris_trick_text_double_tap`.
  The stock `goal_tetris_add_trick` / `goal_tetris_remove_trick` /
  `goal_tetris_turn_trick_red` / `_white` /
  `goal_tetris_play_trick_removed_sound` animate them (pass
  `Params = { id = <entry> }`; `no_key_combo` when there are no glyphs).
- **Layout:** a VMenu only lays children out when locked. Lock on then off
  (like `refresh_scrolling_menu` in `net_vault_menu.q`) after changes, or every
  entry is drawn at the menu origin. Done every poll.
- **Trick name to button glyphs:** loop the air/lip key combos and call
  `GoalManager_GetTrickFromKeyCombo key_combo = X`. The native code (`0x55a700`)
  returns `trick_string` (the slot trick's display name), `extra_trick_string`
  (its first `ExtraTricks` entry, i.e. the double tap, e.g. Method on the
  Melon slot), `trick_checksum` and `cat_num` (created tricks). Adding
  `special` searches the profile's `specials` (`trickSlot` / `trickName`,
  looping `max_specials`) and returns `trick_string` / `trick_checksum` /
  `current_index`. Compare names as checksums (`FormatText ChecksumName`):
  trick definitions use local strings (`'Kickflip'`), which don't compare
  equal to strings. Manuals and grinds aren't in slots, so they get no glyphs.
- **Overflow:** `MakeSkaterGoto YawBail` (the generic bail; vehicle bails use
  it too), then every entry turns red and is removed.
- **Inbox v2:** `doakickflip_inbox = [ { seq = N trick = "Kickflip" user = "name" } ... ]`,
  polled every 6 frames; all new requests are added at once.

QB gotchas found here:

- A bare global name in an expression is its checksum, not its value
  (`<x> = some_global` gives `some_global`). Parentheses evaluate it, but
  reading/writing global *strings* didn't work in either form. Keep strings in
  element tags (`SetTags` / `GetTags`) instead.
- Script `printf` is a no-op in this build (`Printf` → `0x5b9760`, a
  `return true` stub), and `ScriptAssert` formats and discards. For debugging,
  `doakickflip_debug = 1` shows an overlay with recent events and each entry's
  count, baseline and position. It uses `z_priority = 10000` so it draws over
  the pause menu, which also freezes it for screenshots.
- `"\n"` in `.q` source is needed for the game's newline escape; `"
"`
  compiles to a raw newline character.
- Keywords can't be used as parameter names (`script = ...`); `qbc.py`
  now rejects that.

## Channels for live input (towards "do a trick" on demand)

- **Chat commands**: `global_cmd_array` in `qb/thugpro/command_parser.q` maps
  `/COMMAND` strings to scripts. You can type chat yourself only
  `if InNetGame`. Incoming messages are parsed as commands only when the sender
  is in `whitelist_player_array` (`qb/engine/menu/consolemessage.q`). This is the
  likely network path.
- **Registry**: THUG Pro exposes `GetRegKeyValue` / `SetRegKeyValue` /
  `RegKeyExist` to scripts (it keeps its settings in `HKCU\Software\THUG Pro`).
  Rejected: messy for Windows users.
- **File inbox** (chosen next): poll `LoadQB` of a small `.qb` in `User\Data`.
- No script-level "read a text file" function exists in `THUGPro.exe` or
  `thugpro.dll`. THUG Pro's own script functions include `StripStringColorCodes`,
  `ResizeStringInPlace`, `LookupChecksumName`, `CastChecksumToInteger`,
  `SplitConsoleMessage`, `GetSaveDirectoryListing`, `FindSpawnedScriptWithID`.

## Running / debugging under Lutris + umu (GE-Proton)

- `lutris lutris:rungameid/N` hands off to a running Lutris GUI, so you don't
  get its output.
- `tools/run_thugpro.sh` runs `THUGPro.exe` directly via `umu-run` with
  `PROTON_LOG=1`, `WINEDEBUG=+seh,+debugstr`, and the log in
  `logs/steam-default.log`. Grep for `c0000005` / `Exception 0x` to find the
  faulting address, then `objdump -d -M intel --start-address=... THUGPro.exe`
  (image base 0x400000, no ASLR) and resolve pushed checksums against the
  harvested name table.
- On this machine the Lutris install has `drive_c/users/briaguya` symlinked to
  `steamuser`, and THUG Pro lives at
  `drive_c/users/steamuser/AppData/Local/THUG Pro`.
- Gamescope: Lutris wraps the launch as `gamescope <args> -- <umu cmd>` (game
  res → `-w/-h`, output res → `-W/-H`, window mode defaults to `-f`).
  `run_thugpro.sh` does the same when `GAMESCOPE` is set. Running fullscreen
  without it, the game minimizes when it loses focus.
- The game's own `thugpro.log` only had script-not-found warnings. It didn't
  show either crash.

## Ideas / next steps

**Next up: only accept tricks the skater can actually do** (decided: slots plus
an allowlist).
- Accept a request if `doakickflip_find_key_combo` finds it in a normal,
  double-tap or special slot, **or** it's on an allowlist of always-available
  moves: manuals, basic grinds, maybe reverts and wallrides. Drop anything
  else. Rejected requests are dropped silently for now; telling chat needs a
  channel out of the game, which doesn't exist yet.
- Open question: **glyphs for grinds.** Grind inputs are relative to the rail
  (and the stored names carry FS/BS, e.g. `BS 50-50`), so there's no single
  fixed button combo to show like there is for air tricks. Needs thought: show
  no glyphs, a generic grind hint, or work out direction-relative glyphs.
  Related: a "50-50" request should probably match both `FS 50-50` and
  `BS 50-50` (GetNumberOfTrickOccurrences matches exact names).

Later:
- Twitch bridge: a separate program that writes the inbox from Twitch chat
  (anonymous IRC read is enough), with name aliases and flood control
  (per-user cooldown, global rate, pending cap).
- Untested: the red "nearly full" warning in high combo mode.
- Triple taps (Triple Kickflip = Double Kickflip's own `ExtraTricks`) would
  need walking `ExtraTricks` by hand and a triple-tap glyph string.
- Compiler: add `switch`/`elseif`/`Random*` so any script can be recompiled.
