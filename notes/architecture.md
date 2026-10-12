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
- **Process layout:** main (Node: files, mod, inbox, Twitch, stored
  settings/tokens) ↔ preload (small typed `window.api` via
  `contextBridge`) ↔ renderer (React, no Node). `contextIsolation` on,
  `nodeIntegration` off.
- **IPC: Electron's recommended pattern + our own thin typed layer, no
  library.**
  - The problem: the renderer (Chromium page, no file/system access) and
    main (Node, full access) are separate processes that can only exchange
    messages (a name + data). Nearly every real action crosses that gap
    (Install mod, Save trigger, Read chat, Send a trick → inbox; and back:
    a yell arrived, Twitch dropped). Two risks: **silent mismatches** (TS
    can't see across the gap: rename a field on one side and it compiles,
    but e.g. saved triggers quietly lose their cooldown) and **trust** (the
    page shows outside content: usernames, chat text, badge images; main
    shouldn't accept arbitrary messages).
  - What Electron itself recommends
    ([IPC tutorial](https://www.electronjs.org/docs/latest/tutorial/ipc),
    [security checklist](https://www.electronjs.org/docs/latest/tutorial/security)):
    `invoke`/`handle` for renderer → main (not `sendSync` or send/reply);
    `webContents.send` for main → renderer; **never expose `ipcRenderer`**,
    expose narrow functions via `contextBridge` from preload; wrap listeners
    so the page only gets the data, not the event object (item 20);
    `contextIsolation` on (item 3); **validate the sender of every IPC
    message** (item 17). Electron says nothing about TypeScript, and the
    checklist has no explicit item on validating message *data*.
  - Our additions: one shared contract file (every call: name + zod input +
    zod output; every main → renderer event: name + zod payload), compiled
    against by main, preload and renderer, so mismatches are compile errors;
    main runs each input through its schema (and checks the sender) before
    any handler code. Errors come back as explicit `{ ok, error: { code,
    message } }` (thrown errors lose their type and get wrapped crossing
    IPC). Handlers are plain async functions, testable in Vitest without
    Electron; only the small `ipcMain` glue needs Electron. Maybe 50–100
    lines.
  - Libraries looked at:
    - `electron-better-ipc` (3.0.0, 2026-10, Electron 44+): adds main →
      renderer request/reply with `await`, renderer ↔ renderer calls, whole
      error objects (`serialize-error`), the sender window, and shared
      channel types, but "the types are not checked at runtime" (so no
      answer to trust). We don't need its main point (our main → renderer
      messages are one-way notices; one window).
    - `@electron-toolkit/typed-ipc` (1.0.2, 2024): compile-time types only.
    - `electron-trpc` (0.7.1, 2024): unreleased since 2024.
    - `electron-typed-ipc` (2020), `typed-ipc` (2021), `interprocess`
      (2023): dead or near it. `electron-ipc-cat` (2026-07): not looked
      into.
    - A [teamdev.com blog post](https://teamdev.com/mobrowser/blog/what-is-wrong-with-electron-ipc-and-how-to-fix-it/)
      on Electron IPC's problems: nothing we could use.
- **Stored settings: our own small store, zod + `atomically`, no store
  library and no database.**
  - What's saved (in main, under `app.getPath('userData')`): settings (THUG
    Pro folder, quick settings, testing, button prompts), triggers, Twitch
    connection mode + channel (tokens separately via `safeStorage`), maybe
    the session log and the inbox `seq`. Files like `settings.json`,
    `triggers.json`, each with a `version` field for upgrade steps we write.
  - Ours is: load → parse → zod check → defaults; save →
    `atomically.writeFile`. A few dozen lines; no filesystem-level code of
    our own.
  - Options compared:
    - **SQLite** (`better-sqlite3`): overkill for a few dozen settings and a
      short trigger list; a native module complicates packaging.
    - **Renderer `localStorage`**: main needs the data; renderer is the
      untrusted side.
    - **`electron-store`** (11.0.2, 2025; a thin wrapper over `conf`): nice
      API (defaults, watch, dot paths, atomic writes via `atomically`), but
      validates with JSON Schema/ajv (no zod hook), its **migrations carry
      the author's "known bugs, no support" disclaimer**, it throws at
      startup on a required field without a default, and `additionalProperties:
      false` conflicts with migrations. Its "encryption" isn't for security.
      It wouldn't help with the inbox either (it only manages its own
      files).
    - Schema setups considered to keep it fair (zod isn't sacred): A)
      electron-store + ajv everywhere (types kept in sync by hand; verbose);
      B) electron-store + TypeBox (`typebox` 1.x: one definition → TS type +
      JSON Schema for ajv); C) electron-store + zod, feeding it
      `z.toJSONSchema()` (zod v4 has it; refinements/transforms don't carry
      over); D) our own store + zod + `atomically` (chosen; C was the runner-up).
    - Also looked at: `electron-settings` (2024, lodash), `lowdb` (2023,
      `steno` writes).
- **Atomic writes: `atomically`** (2.1.1, 2026-02), for settings **and the
  inbox**, over `write-file-atomic` (8.0.0, 2026-05, npm CLI team).
  - Both: temp file next to the target → `fsync` → `rename`; queue writes
    to the same file; remove the temp file on exit; keep owner/permissions
    on POSIX.
  - The deciding difference: **`atomically` retries** every step including
    the rename (via `stubborn-fs`) on `EPERM`/`EBUSY`/`EACCES`/`EAGAIN`/
    `EMFILE`/`ENFILE`, every 200 ms for up to 7.5 s (1 s sync); it also has
    a retrying `readFile` and shortens over-long temp names.
    **`write-file-atomic` doesn't retry** (its only `EPERM` handling is
    ignoring a failed chown).
  - Why it matters here: on Windows a rename over a file another process
    has open fails with `EPERM`/`EACCES` (antivirus, indexers), and **THUG
    Pro re-reads the inbox every few frames**, so un-retried inbox writes
    would sometimes fail. (The Python `call_trick.py` uses plain
    `os.replace`: same weakness on Windows; only run on Linux so far.)
  - Trade-offs accepted: one maintainer (vs the npm team; ~21M vs ~102M
    weekly downloads), ESM-only (fine with Forge 8). It's what electron-store
    (via `conf`) already relies on.
  - Plan: a shorter `timeout` (~1–2 s) for inbox writes, the default for
    settings.
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
- **Validation: zod (v4).** One schema gives both the TS type and a runtime
  check, for data from outside the code: saved settings/trigger files
  (older versions, hand edits, half-written files), every IPC message from
  the renderer in main (Electron treats the renderer as untrusted), and the
  saved Twitch tokens (corrupt → "log in again"). Twurple's events are
  already typed. Alternatives looked at: Valibot (smaller; size doesn't
  matter on desktop), ArkType, TypeBox, hand-written checks.
- **No form library yet.** Most of the app saves instantly (toggles, quick
  settings) or is a single field (channel name, THUG Pro folder). The
  trigger editor is the only real form: build it with plain React state +
  its zod schema. If it gets awkward (change tracking, conditional fields,
  async checks like "command already used"), add TanStack Form then (it
  takes zod schemas); react-hook-form is the other option.
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
