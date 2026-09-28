# Next steps

**To discuss: what happens on overflow.** The bail rule stays (more than
`max_pending` pending makes you bail). Open question: should the list also
clear?
- If we keep clearing, it needs cleanup: the request that causes the overflow
  (e.g. the 9th with a cap of 8) shows up at the bottom *while* the list is
  being cleared, and it isn't red. Probably: don't add the overflowing
  request at all, or add it red and clear it with the rest.
- If we don't clear, decide what happens instead (e.g. drop the oldest
  request, or keep the list and just bail each time it's exceeded).

**Done (tested in game):** `max_pending` is configurable (sent in the inbox
as `doakickflip_inbox_settings`, `--max-pending` on `call_trick.py` /
`fake_chat.py`, default 8, changes apply live), and the list turns red from
75% of it like the stock Skate-Tricks stack (6 of 8, 12 of 15).

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
