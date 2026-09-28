# High combo mode ("Do a Kickflip!")

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
- **Cap and warning:** `max_pending` comes from `doakickflip_inbox_settings`
  in the inbox (re-read every poll, default 8). More than that pending is an
  overflow. The entries turn red (`goal_tetris_turn_trick_red`) from 75% of
  the cap, matching the stock Skate-Tricks stack, which reds at
  `count >= 0.75 * max_tricks` (factor at `0x64e918`) and fails the goal when
  an add would go past `max_tricks` (`0x56fa30`). Stock `max_tricks` is 15.
- **Overflow:** `MakeSkaterGoto YawBail` (the generic bail; vehicle bails use
  it too), then every entry turns red and is removed (under discussion, see
  [todo.md](todo.md)).
- **Inbox v2:** `doakickflip_inbox = [ { seq = N trick = "Kickflip" user = "name" } ... ]`
  plus `doakickflip_inbox_settings = { max_pending = N }`, polled every 6
  frames; all new requests are added at once.
