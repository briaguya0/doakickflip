# Frontend

The app streamers (and we, for testing) will use: connect Twitch, choose what
chat can yell, see what's been yelled, test without chat. It writes the inbox
file the mod reads; see [high-combo-mode.md](high-combo-mode.md).

## Where we are

Static HTML/CSS mockups in `frontend/prototype/` (no JS, no build), being
reviewed page by page. Serve them over HTTP rather than opening the files
(Flatpak Firefox can't load `style.css` next to a `file://` page):

```sh
# no-store so the browser never shows a stale style.css after an edit
cd frontend/prototype && python3 -c '
import http.server
class H(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store"); super().end_headers()
http.server.ThreadingHTTPServer(("127.0.0.1", 8765), H).serve_forever()'
# http://127.0.0.1:8765/
```

Reviewed and settled so far: the **sidebar**, and on the **Dashboard** the
session log and most of the top row (Quick settings + Status). Still open on
the Dashboard: the last Quick settings rows (see Next) and the testing tools,
which haven't been reviewed yet.

## Decisions so far

- **Look:** modelled on [Sail](https://github.com/HarbourMasters/Sail)'s
  layout (sidebar, cards, tokens), not its stack. Night-session identity:
  asphalt surfaces, THUG gold for actions, green for live/ok, Twitch purple
  only for Twitch. Status colours use GitHub's alert palette (note / tip /
  important / warning / caution) so warnings don't look like the gold.
- **One-way only:** the app never gets state back from the game (no memory
  reading: antivirus, especially Windows Defender, flags that; see
  [input-channels.md](input-channels.md)). The UI only shows what the app
  knows: what it sent and whether the setup looks right. Nothing like "on the
  stack", "done", "bailed".
- **Terminology:** a request from chat is a **yell**, from the games' own
  goals: THPS4 "Nail the Tricks They Yell Out", THUG1 "Nail the tricks I yell
  out". The game's side talks about tricks that come up and that you nail /
  clear. "Inbox" stays an internal name only.
- **Sidebar:** brand icon ("Skateboard" by Delapouite, CC BY 3.0, no
  animation), plain divider, nav **Dashboard / Tricks / Twitch / Settings**.
  No status section: the Twitch tab shows its connection state, Settings shows
  a red `error` marker when the game setup has a problem.
- **Dashboard:** what people want to do from there: turn it on/off, tweak
  the few knobs that shape the game, and check everything is up.
  - Top row, two cards side by side:
    - **Quick settings** (wide). A title plus plain setting rows: a toggle as
      the card title read badly ("Taking yells"), and so did no title. Rows:
      **Enabled** (toggle), **Trick clears** (Immediate / Landed),
      **Stack limit** (8), then the rows still being decided (see Next).
    - **Status** (thin, 240px): **THUG Pro version** (not found / untested
      version / ok), **Mod installed**, **Yells → Game**, **Twitch**. Checks
      are ok / warning / problem / skipped (`check_circle`, `warning`,
      `error`, `radio_button_unchecked`). Replaces separate Game and Twitch
      cards: a whole card for one Twitch status was too much.
  - **No "game mode".** Modes are what people build from the knobs. "High
    combo" = Trick clears: Immediate, Stack limit 8, overflow: bail. A named
    preset might come back later.
  - **Twitch connection icon:** filled plug everywhere (card, nav tab, Twitch
    page): `power_off` grey = not connected, `power` blue = connecting,
    `power` green = connected, `power_off` red = error. Considered link,
    sensors, chat bubbles, cloud, sync, wifi_tethering and generic. Sail just
    uses dots, and puts errors in a banner with the message: worth copying.
  - **Session log** table: time, type (chat / test / sim only), user (Twitch
    style: name colour + badges), command (monospace), trick with its button
    combo. No headers, no subtitle.
  - **Testing tools** (send a trick, fake chat) below the log, only when
    Settings > Testing > "Show testing tools" is on. No separate tab.
- **Page subtitles:** none.
- **Icons:** Material Symbols (Apache 2.0) everywhere; Twitch logo from Font
  Awesome Free brands (CC BY 4.0). Twitch's brand rules allow the logo only in
  purple, black or white.
- **Button combo glyphs** (Settings > Button prompts):
  - Directions: Material Symbols arrows (`west`, `north_west`, ...), heavy and
    white like the in-game prompts. Two-direction inputs (specials, manuals)
    are two arrows side by side, like the in-game Special Tricks list
    (Manual = up, down; Nose Manual = down, up).
  - Xbox: Mr. Breakfast's Free Prompts single-colour set; PlayStation: its
    `ps5_*_color_dark` (CC0).
  - Generic: PromptFont positional glyphs (north/south/east/west), credited as
    the author asks: "PromptFont by Shinmera (Yukari Hafner), available at
    https://shinmera.com/promptfont" (OFL, license bundled).
  - Custom: typed text per action (covers keyboard, e.g. `KP4`).
  - Rejected: Kenney (style), Xelu's PNG-only 360/PS3 sets, drawing our own.
  - Open: grinds (inputs are relative to the rail).
- **Twitch users:** IRC tags give `display-name`, `color` (can be empty: then
  imitate Twitch's default colours) and `badges`. Badge *images* need the
  Twitch API with an app client ID (Sail ships one); the prototype uses
  placeholder badges.
- **Credits** for every third-party asset: `frontend/prototype/CREDITS.md`
  and the Settings credits card.

## Next

- Finish **Quick settings**:
  - an overflow row, e.g. "When the stack is full: bail / drop oldest /
    ignore new yells" (all doable in the mod script),
  - repeats: can a trick already on the stack be yelled again? ("Same trick
    twice" was confusing; reword or drop),
  - move **Per-viewer cooldown** out: it's Twitch-specific, so it belongs
    with the Twitch side (with rate limit, command prefix, commands).
- Mod work behind the knobs: **Landed** needs telling a landed combo from a
  bail (maybe `SkaterLastScoreLandedGreaterThan` or similar); the new
  overflow behaviours; settings travel in `doakickflip_inbox_settings` like
  `max_pending` does.
- Settings page still says "Bail after": rename to Stack limit when we get
  there.
- Review the **testing tools** on the Dashboard and make them compact
  (one card? quick-send row + fake chat on/off and rate).
- Fake chat must be impossible to forget while live: a loud indicator when
  it's running.
- Terminology pass: "yell" everywhere user-facing ("Send a trick", Settings'
  "Inbox" field, fake chat text).
- Review the **Tricks**, **Twitch** and **Settings** pages.
- Later: pick the real stack (not decided; avoid packaging that Defender
  likes to flag, e.g. PyInstaller-style bundles), then build it.
