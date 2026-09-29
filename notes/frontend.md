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

Reviewed and settled so far: the **sidebar** and the **Dashboard** (Quick
settings, Status, session log, testing tools). The Settings page got the
things moved off the Dashboard but hasn't been reviewed itself yet.

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
      the card title read badly ("Taking yells"), and so did no title. Just
      three rows: **Enabled** (toggle), **Trick clears** (Immediate /
      Landed), **Stack overflow penalty** (Bail / None). Two-way choices use
      a segmented control. Stack limit moved to Settings; per-viewer cooldown
      and "same trick twice" left the Dashboard (Twitch side / Settings).
    - **Status** (thin, 240px): **THUG Pro version** (not found / untested
      version / ok), **Mod installed**, **Yells → Game**, **Twitch**. Checks
      are ok / warning / problem / skipped (`check_circle`, `warning`,
      `error`, `radio_button_unchecked`). Replaces separate Game and Twitch
      cards: a whole card for one Twitch status was too much.
  - **No "game mode".** Modes are what people build from the knobs. "High
    combo" = Trick clears: Immediate, Stack limit 8, overflow penalty: Bail.
    A named preset might come back later.
  - **Trick clears: Landed** works exactly like the vanilla Skate-Tricks goal:
    done tricks stay on the stack until the combo lands (a bail un-does them).
    With it comes a **tricks-landed counter** (plus maybe a **high count**)
    as the score: a stack overflow resets it. **Overflow penalty: None** = no
    forced bail, the counter resets and the stack clears, carry on (no
    restart from the pause menu). The counter has to be shown **in game**
    (one-way: the app can't know it).
  - **Twitch connection icon:** filled plug everywhere (card, nav tab, Twitch
    page): `power_off` grey = not connected, `power` blue = connecting,
    `power` green = connected, `power_off` red = error. Considered link,
    sensors, chat bubbles, cloud, sync, wifi_tethering and generic. Sail just
    uses dots, and puts errors in a banner with the message: worth copying.
  - **Session log** table: time, type (chat / test / sim only), user (Twitch
    style: name colour + badges), command (monospace), trick with its button
    combo. No headers, no subtitle.
  - **Testing tools** below the log, only when Settings > Testing > "Show
    testing tools" is on. No separate tab. Two equal-height cards, each title
    starting with the `science` icon (= testing, as the old tab had):
    - **Send a trick:** a **Count** slider (1 up to the stack limit,
      **defaults to 1**) and two buttons that send that many: the quick-send
      trick (Kickflip, with its combo; which trick is set in Settings) and
      **Random** (`shuffle` icon, one line). No typing on the Dashboard (no
      "from" field, no trick name box). Tried and dropped for Random: dice,
      a shuffle + cycling face button, four-wedge "any button" slices.
    - **Fake chat:** status in the title (`forum` green "Running" /
      `comments_disabled` grey "Stopped"), the **Rate** slider, and one big
      **Stop** (red) / **Start** (green, play) button, same size as the send
      buttons.
  - **Settings > Testing** holds the set-once parts: show testing tools,
    quick-send trick, fake chat **Bursts**, and **Fake chat yells: All
    allowed tricks / Only these** (a separate short list, so testing one or
    two tricks never changes the real Tricks setup).
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

- **Tricks-landed counter:** a toggle for keeping the count (and maybe
  showing a high count); where it lives (Quick settings or Settings) isn't
  decided. Shown in game.
- Mod work behind the knobs: **Landed** needs telling a landed combo from a
  bail (the stock goal does its clearing from `ClearPanel_Landed`; look for a
  hook); the counter and high count on the HUD; **overflow penalty None**
  (reset counter + clear stack, no bail). Settings travel in
  `doakickflip_inbox_settings` like `max_pending` does.
- Twitch side: per-viewer cooldown, rate limit, command prefix, commands.
  "Same trick twice" needs rewording or dropping.
- Settings page still says "Bail after": rename to Stack limit.
- Fake chat must be impossible to forget while live: a loud indicator when
  it's running (beyond its own card).
- Terminology pass: "yell" everywhere user-facing (Settings' "Inbox" field,
  fake chat text).
- Review the **Tricks**, **Twitch** and **Settings** pages.
- Later: pick the real stack (not decided; avoid packaging that Defender
  likes to flag, e.g. PyInstaller-style bundles), then build it.
