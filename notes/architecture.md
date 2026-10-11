# App architecture

How the real app (replacing the static prototype in `frontend/prototype/`)
gets built. Decided things first, then what's still open.
Aim: more conventional than [Sail](https://github.com/HarbourMasters/Sail)
(Wails, Go, hand-rolled Twitch client), reusing existing libraries.

## Decided

- **Electron + React + TypeScript.** One language for the UI and all the
  logic. No Python running inside the app (and no PyInstaller-style bundle
  for Windows Defender to flag).
- **All logic in TS:** mod install/uninstall (PRX archives, LZSS, QB
  decompile/patch/compile), writing the inbox, trigger matching, Twitch.
  Needs ports of `tools/prx.py`, the `qbdec` + `qbc` path `build_mod.py`
  uses, and the inbox writer in `call_trick.py`.
- **Electron Forge 8 with the Vite + TypeScript template** (Forge's Vite
  plugin), over electron-vite.
  - Forge: official Electron project, released 2026-09 (8.0.1), Vite 8,
    covers dev, packaging, installers ("makers") and publishing. Its Vite
    plugin is still labelled experimental (breaking changes possible in
    minors): pin exact versions. Needs Node 22.12+, ESM-only.
  - electron-vite: nicer dev loop (main/preload hot reload, one config, V8
    bytecode option) but only builds; packaging needs electron-builder too.
    Last stable 5.0.0 (2025-12), 6.0 in beta.
  - Switching later is mostly build config, not app code.
- **TanStack Router + TanStack Query, client-only; not TanStack Start.**
  Start's SPA mode still assumes its own server for server functions /
  routes; in Electron the main process (over IPC) is the backend already.
  - Router with its Vite plugin (file-based, typed); hash or memory history
    in the packaged app (`file://` has no real history).
  - Query wraps the IPC calls to main: e.g. reading settings and saving
    them (mutation), mod status and Install / Uninstall, the trigger list,
    the session log, Twitch connection state. Pushes from main (a new yell
    in the log, Twitch dropping) update the cache. We'll see where it's most
    useful once we start building.
  - TanStack Form maybe later for the trigger editor.
- **Process layout:** main (Node: files, mod, inbox, Twitch, stored
  settings/tokens) ↔ preload (small typed `window.api` via
  `contextBridge`) ↔ renderer (React, no Node). `contextIsolation` on,
  `nodeIntegration` off.
- **Python tools stay** as discovery tools and as the reference for the TS
  port: local-only parity tests that the TS output is byte-identical to the
  Python output (like `tools/roundtrip.py`).
- **Twitch: Twurple** (`@twurple/chat`, `auth`, `eventsub-ws`, `api`;
  8.2.0, 2026-09). The only maintained library covering all of it: chat
  with or without login, EventSub (redeems, follows, subs, cheers), the
  Helix API (creating/editing rewards), auth incl. Device Code Flow, native
  TS. Passed on:
  - `tmi.js` (chat/IRC only, no channel points; last release 2021),
    `@tmi.js/chat` (chat only, 0.x).
  - comfy.js: chat via tmi.js v1 plus its own EventSub client and reward
    API calls, but no token handling at all (README points at third-party
    token generator sites); plain JS, hobby-bot oriented.
  - twitch-js, twitch-chat-client: dead. Rolling our own (Sail's way):
    we'd own reconnects, keepalives, rate limits, token refresh.
  - We still need our own Twitch application (client ID), like Sail.
- **Twitch connections:**
  - **Read chat:** Twurple `ChatClient` (IRC underneath) with no auth
    provider. Messages and cheers both come through chat.
  - **Logged in:** **EventSub only** (`@twurple/eventsub-ws`), one WebSocket
    for chat (`channel.chat.message`, needs `user:read:chat`), cheers, subs,
    follows and redeems. No IRC. Logging in while reading stops the IRC
    client and starts EventSub.
  - Twurple doesn't hide the difference (two APIs, `ChatMessage` vs
    `EventSubChannelChatMessageEvent`), so we have our own small "chat
    source" layer turning both into one shape (user, display name, colour,
    badges, text, bits). Trigger matching never knows which it came from.
- **Twitch login: Device Code Flow with `RefreshingAuthProvider`**, all in
  the main process.
  - Provider created with just our client ID (public client: no secret,
    refreshing included).
  - Login: `startDeviceCodeFlow(scopes)` → show `userCode` + open
    `verificationUri`; **we** poll `addUserForDeviceCode` every `interval`
    s until approved / expired (Twurple doesn't poll: handle
    `authorization_pending`, `slow_down`, expiry). All scopes up front
    (redeems read + manage, bits, subs, followers, `user:read:chat`).
  - Tokens: access token ~4h; refresh token one-time use, expires after 30
    days unused. The provider refreshes **on demand** when a client asks for
    a token (treats it as expired 1 min early), fires `onRefresh` → we save
    the new pair **immediately** (encrypted, Electron `safeStorage`); fires
    `onRefreshFailure` and stops retrying that user → we show the login card
    again. Missing scopes throw (a refresh can't add scopes; needs a new
    login). Startup: `addUser(savedUserId, savedToken)`. Log out:
    `removeUser` + `revokeToken` + delete what we saved.
  - Why this flow: Twitch lists Device Code Flow for Electron apps. Implicit
    flow needs a localhost redirect server and gives no refresh (Sail's
    "log out and back in" for new scopes); authorization code needs a
    secret; a Twitch login page in our own window asks for passwords in our
    app.
  - **What the user sees:**
    - First time: two cards. Read chat connects at once (channel saved).
      Log in shows "waiting for approval" with the code and an Open
      twitch.tv/activate button, then "Logged in as …"; an expired code goes
      back to the button.
    - Opened again within 4h, or within 30 days: reconnects the way it was
      left, no clicks (a quiet refresh after 4h; each refresh restarts the
      30 days). Read chat never expires.
    - After 30 days unused (logged in): the refresh fails; the Twitch page
      says the login expired and shows the two options; triggers that need
      a login show "Needs login".
- **UI components: shadcn/ui on Base UI, with Tailwind CSS v4.** shadcn
  copies component source into the repo (we own and restyle it) rather than
  being a dependency; it can sit on Base UI, React Aria or Radix, and Base UI
  became its default in 2026-07. Our prototype tokens (asphalt, THUG gold,
  GitHub alert colours) become its CSS variables. Rough mapping: segmented
  controls → Toggle Group, toggles → Switch, sliders → Slider, kind chips →
  Toggle, edit card → Card, toasts → Sonner, and the trick picker → Command
  (cmdk) in a Popover/Dialog.
- **Icons: Material Symbols from npm** (`material-symbols`, Apache 2.0,
  0.48.0, 2026-10), bundled with the app, so nothing hits Google Fonts (the
  prototype loads it from there). shadcn's default Lucide not used. Check
  the package's variable font keeps the axes the prototype uses (FILL, wght
  100–700, GRAD −50–200); `@fontsource-variable/material-symbols-outlined`
  is the fallback. The Twitch logo is one icon: take it as an SVG from
  `@fortawesome/free-brands-svg-icons` (CC BY 4.0) instead of loading Font
  Awesome's CSS from a CDN.
- **Node 24** (LTS), pinned in `.nvmrc`: run `nvm use` before any node/npm
  command.
- **Testing:** **Vitest** (+ React Testing Library for components) for
  almost everything. **Playwright** only for what Vitest can't cover; there
  may not be much that's truly end-to-end. (Playwright can drive Electron:
  `_electron`, marked experimental; native dialogs have to be stubbed.)
  Things to cover:
  - PRX unpack/pack round trips, LZSS, QB compile/decompile.
  - The mod patch: hook inserted in the right block, archive still unpacks,
    backup made, uninstall restores. Plus the `.bak` bug from
    [todo.md](todo.md).
  - The inbox writer: format, `seq`, trimming (keep 32), atomic writes,
    settings block; read back with our own decoder.
  - Trigger matching (`!doa nose manual`, allowed tricks).

## Open

- **Rest of the frontend stack** (proposed, not decided):

  - **zod**: check settings/trigger files on load, and validate everything
    arriving from the renderer over IPC in main (renderer is untrusted).
  - Forms: TanStack Form (matches the stack, takes zod schemas) or
    react-hook-form (shadcn's older examples).
  - Typed IPC: our own small shared contract (call names + zod schemas)
    rather than `electron-trpc` (last release 2024).
  - Stored settings: our own JSON files in Electron's userData folder, zod +
    atomic writes, rather than `electron-store`.
  - Lint/format: Biome or ESLint + Prettier (Forge's template sets up
    ESLint).
  - Package manager: npm or pnpm (pnpm + Forge needs
    `node-linker=hoisted`).
- **After a login expires (30 days):** fall back to reading the same
  channel's chat so plain chat triggers keep working until you log in again?
- **Reconnect on launch:** a setting, on by default? (Some streamers may not
  want the app talking to Twitch the moment it opens.)
- **Test fixtures for mod install.** Nothing from THUG2 or THUG Pro can be
  committed. Idea: a hand-written fake pause-menu script with the same shape
  as the hook point (`if GameModeEquals is_singlesession` … `endif`),
  compiled and packed into a fake `thugpro_qb.prx` by our own tools. It
  repeats a few of the game's script names, as `mod/doakickflip.q` already
  does: is that acceptable?
- **Real-install tests:** opt-in, only when pointed at a THUG Pro folder
  (e.g. `THUGPRO_DIR`); never on public CI; outputs never committed.
