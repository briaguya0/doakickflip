# The Skate-Tricks (Skatetris) goal

How the stock goal works and what we learned driving it from script. The
mod no longer uses the goal (see [high-combo-mode.md](high-combo-mode.md)),
but its UI pieces are reused and these engine details still apply.

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

## Update loop and the old live mode

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
