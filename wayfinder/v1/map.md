# Map: doakickflip v1

## Destination

A buildable spec for v1, with no decision left open: a streamer on Windows
or Linux downloads the app (unsigned ZIP, GitHub Releases), it installs the
mod into their own THUG Pro, they connect Twitch, and chat's yells show up
in game. Building happens outside the map, in small commits on the app
branch.

## Notes

- Domain: THUG Pro scripting (QB / NeverScript), the Electron app, Twitch.
  Reference material lives in [notes/](../../notes/README.md); terms in
  [GLOSSARY.md](../../GLOSSARY.md) (yell, nail, nailed count).
- Tracker: local markdown. Tickets in [issues/](issues/), research write-ups
  in `research/`, prototypes in `prototypes/`. Research stays on the docs
  branch; no pushed `research/*` branches.
- Nothing derived from THUG2 / THUG Pro is committed, including in research
  and prototypes: describe findings in our own words.
- One question at a time when grilling.
- Research tickets wait until the nsqb and prxhawk maps are charted; what
  those turn up may answer or reshape them.
- Grilling tickets: use the grilling and domain-modeling skills.
- v1 scope, decided while charting (2026-11-08):
  - Install / uninstall from the app, built on nsqb and prxhawk (only the
    slice v1 needs is on this map).
  - Online access is blocked for as long as the mod is installed.
  - Handle a THUG Pro update replacing the archive (stale backup).
  - Check the THUG Pro version against known-good versions.
  - The user picks the THUG Pro folder.
  - Only yells the skater can do; every trick that can be performed is
    supported, triple taps included.
  - Trick clears: Immediate and Landed. Overflow penalty: Bail and None.
  - Nailed count, shown in game.
  - Twitch: anonymous chat read plus login (Redeem and Event triggers).
  - Testing tools: fake chat and quick-send.
  - The prototype (`frontend/prototype/`) is a reference only; open UI
    questions are decided against the real app.
  - The Python `tools/` are retired as the TS side takes over each job.

## Decisions so far

## Not yet specified

- Where the nailed count (and the stack) sit on the HUD.
- Uninstall UX, and how the app explains that online is blocked while the
  mod is installed.
- Linux packaging details beyond the ZIP.
- How the install flow is laid out in the app (status, errors, re-install
  after an update).

## Out of scope

- Side-by-side installs (a modded copy next to a clean one for online play):
  worth looking into after v1.
- Auto-detecting the THUG Pro folder: hit or miss across Wine prefixes, and
  harder with side-by-side installs.
- High count.
- Replies in chat.
- OBS overlay.
- Code signing.
- Auto-update.
- nsqb and prxhawk as standalone projects (playground, full decompile,
  grammar, publishing): their own maps, in `wayfinder/` on the docs branch
  of `~/code/nsqb` and `~/code/prxhawk`.
