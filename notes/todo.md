# Next steps

**App scaffold (2026-10-12):** the real app is being built in `app/` on the
`app-scaffold` branch (worktree `../doakickflip-app`), one small reviewed
commit at a time; decisions are in [architecture.md](architecture.md)
("App scaffold"). Done: template review, ZIP-only packaging, `app://`
protocol + fuse, TS 7, type-aware lint, React + compiler, Tailwind,
shadcn (Maia, Phosphor) + desktop-only sidebar, mount guard, TanStack
Router (file-based, hash history). Next: TanStack Query, Vitest + RTL,
commitlint; CSP (below); real pages instead of Page 1 / Page 2.

**Next session (left 2026-10-11):** architecture is settled (see
[architecture.md](architecture.md), "Open" has only one thing to check);
the prototype is reviewed except the rest of Settings. Fresh findings on
THUG Pro versions and its updater are in
[thugpro-versions.md](thugpro-versions.md); the items below on version
detection, the updater reverting the mod, and the `.bak` bug follow from
them. Lots of local commits on `file-read-discovery` aren't pushed.

**Current focus: the frontend.** Reviewing the static prototype page by page;
see [frontend.md](frontend.md) for where it stands and what's next.

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

**Discovery: what's possible, and what kinds of tricks exist** (for the
layered allowlist in [frontend.md](frontend.md)).
- Where THUG Pro keeps saves / created skaters, and whether the trick slot
  assignments (normal, double tap, special) can be read from them. Goal:
  fill the "possible" layer without the streamer listing tricks by hand and
  without reading game memory. Fallback: a config file.
- Sweep the trick definitions in the extracted QB for every kind of trick,
  not just normal / double tap / triple tap / special: **flips and rolls**
  (not accounted for yet), grinds, lips, manuals, reverts, anything else.
  For each: how the game names it, whether `GetNumberOfTrickOccurrences`
  counts it, and what glyphs it'd get. This fixes the kind list the
  per-trigger denylists use.
- Note the mod can already see slots live (`doakickflip_find_key_combo`), so
  the game could still drop impossible yells itself; the app-side list is
  so the app knows before sending (and could tell chat).

**Bug: build_mod.py after a THUG Pro update.** The build reads the original
archive from `thugpro_qb.prx.bak` whenever that exists. A THUG Pro update
overwrites `thugpro_qb.prx` but leaves our old `.bak`, so the next build
would patch the *old* scripts and install them over the update. Fix: notice
when the live file isn't the one we installed (e.g. keep a hash of what we
wrote) and treat it as the new original (refresh the backup from it).
Better: match the live file's CRC32 against THUG Pro's published manifest
CRCs (see [thugpro-versions.md](thugpro-versions.md)): an official CRC means
a fresh original.

**Does THUG Pro's launcher undo the mod?** Its updater validates every file
by CRC32 against the release manifest, so our patched `thugpro_qb.prx`
looks damaged. Test whether opening the launcher (or only Repair / an
update) re-downloads it. If it does on every start, the app needs to know
(and say so) and the mod may need re-installing after the launcher runs.

**Detecting the THUG Pro version.** Plan (details in
[thugpro-versions.md](thugpro-versions.md)): read the label from
`thugpro.dll` (the four pushes before its single `%d.%d.%d.%d` reference;
0.7.0.0 today), and decide tested/safe from a known-versions table of CRC32s
seeded from THUG Pro's `update/<release>/<version>/update.json` manifests.
`changelog.txt` is not a version source (stale at 0.6.0.11).

**App: Content-Security-Policy** (Electron security checklist item 7;
Electron warns in dev). Do it as a **response header** set by our `app://`
handler for packaged builds (strict), rather than a `<meta>` tag (one
policy for dev and prod, so it'd have to allow Vite's inline styles and dev
WebSocket). Intended policy: `default-src 'self'`; `script-src 'self'`;
`style-src 'self'` (dev needs `'unsafe-inline'`: Vite injects `<style>`);
`font-src 'self'`; `img-src 'self'` (+ `data:`, + Twitch's CDN
`https://static-cdn.jtvnw.net` only once we show badges/emotes);
`connect-src 'self'` (dev: Vite's WebSocket; the renderer never talks to
Twitch, main does); `object-src`, `base-uri`, `form-action` `'none'`.
Electron's checklist also shows `session.webRequest.onHeadersReceived`.

Later:
- Twitch bridge: a separate program that writes the inbox from Twitch chat
  (anonymous IRC read is enough), with name aliases and flood control
  (per-user cooldown, global rate, pending cap).
- Untested: the red "nearly full" warning in high combo mode.
- Triple taps (Triple Kickflip = Double Kickflip's own `ExtraTricks`) would
  need walking `ExtraTricks` by hand and a triple-tap glyph string.
- Compiler: add `switch`/`elseif`/`Random*` so any script can be recompiled.
