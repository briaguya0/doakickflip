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
    minors): the `@electron-forge/*` packages use `~` (patch updates
    only, kept in lockstep); everything else `^` + the lockfile. Needs Node 22.12+, ESM-only.
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
- **Lint / format: oxlint + oxfmt** (Oxc / VoidZero, MIT; oxlint 1.87,
  oxfmt 0.72 as of 2026-10). Fallback if something specific doesn't work:
  add ESLint for just those rules, with `eslint-plugin-oxlint` turning off
  everything oxlint already covers.
  - oxlint: 870+ built-in rules (ESLint core, TypeScript, React, import,
    jsx-a11y, unicorn, Vitest; check the React hooks rules are there).
    **Type-aware** via `oxlint-tsgolint` + `--type-aware` (or
    `options.typeAware`), using the TypeScript 7 Go compiler: 59 of 61
    typescript-eslint type-aware rules incl. `typescript/no-floating-promises`
    (forgotten awaits in main-process file/IPC/Twitch code). Needs
    TypeScript 7+ (7.0.2 out since 2026-07) and no legacy tsconfig options
    like `baseUrl` (shadcn's Vite steps add it; `paths` works without).
  - Config is its own `.oxlintrc.json` / `oxlint.config.ts` (ESLint-shaped;
    doesn't read `eslint.config.js`; `@oxlint/migrate` converts once).
    Existing ESLint plugins go under `jsPlugins` (alpha; plugin rules that
    need type info aren't supported): try `@tanstack/eslint-plugin-query`
    and `@tanstack/eslint-plugin-router` there.
  - oxfmt: Prettier-compatible formatter, pre-1.0 (the main risk; Biome for
    formatting is the fallback).
  - Compared:
    - **Biome** (2.5.15; the original lean): one tool, mature formatter,
      React hooks + import rules stable, but `noFloatingPromises` /
      `noMisusedPromises` are nursery and use Biome's own type inference,
      no TanStack rules, Tailwind class sorting nursery.
    - **ESLint + Prettier** (10.12 / typescript-eslint 8.71 / 3.9): full
      type-checked rules, TanStack plugins, official react-hooks plugin,
      mature Tailwind sorting, Forge's default; but two tools, ~6 packages,
      slower.
    - **Vite+** (`vite-plus` 1.1.0, MIT): bundles Vite, Vitest, oxlint,
      oxfmt, Rolldown, tsdown, a task runner (`vp check` = fmt + lint +
      types) and Node/package-manager management. Skipped for now: it wants
      to be the entry point (`vp dev`/`vp build`) that Forge's Vite plugin
      already is, its docs don't cover Electron or frameworks that drive
      Vite, partial use is undocumented (risk of two Vites), and its Node
      management overlaps `.nvmrc`. We use the same oxlint/oxfmt directly;
      revisit later.
- **Test fixtures: our own, nothing from THUG2 or THUG Pro committed.**
  Layers:
  1. **Format correctness, fully synthetic:** our code against the formats
     as documented in [formats.md](formats.md): LZSS on random data and
     edge cases (ring wrap, threshold, uncompressed entries), PRX pack ↔
     unpack, QB compile → decompile → compile byte-identical. For bytecode,
     borrow only *which features* real files use (opcodes, fast-if/Random
     variants, line numbers: facts) and write our own scripts exercising
     each; `roundtrip.py`'s skipped files show what the compiler still
     can't do.
  2. **Patch logic, hand-written scripts** for each case: hook block once,
     nested `if`s inside it, several `is_singlesession` blocks with only one
     holding the High Score Run items, block missing (clear error, no broken
     archive), already patched, uninstall restoring byte-for-byte, the
     `.bak` bug. They repeat only the few names the patcher looks for, as
     `mod/doakickflip.q` already does. Archives are built at test time by
     our own tools (only source text committed).
  3. **Real game, local and opt-in** (pointed at a THUG Pro folder, e.g.
     `THUGPRO_DIR`; never on public CI): the real patch works, and the TS
     port matches the Python reference. Only **fingerprints** are committed
     (SHA-256 of each THUG Pro version's `thugpro_qb.prx` + "verified"),
     which doubles as a **known-versions table** for the app's "untested
     THUG Pro version" status. The table can also be **seeded from THUG Pro's
     published update manifests** (a CRC32 per file per release; see
     [thugpro-versions.md](thugpro-versions.md)), not only from local runs.
  - Considered and dropped: pulling THUG Pro in CI. `THUGProSetup.exe`
    (dl.thugpro.com, a 600 KB .NET downloader) doesn't contain the files: it
    reads `current.json` (release/version) and fetches files via
    `update/…/update.json` (it names `data/pre/thugpro_qb.prx`); our guesses
    at that URL got 403. Feasible after decompiling the downloader, but it
    means scripting their updater (server load, their permission), public-CI
    leak risks (artifacts/snapshots/logs), tests going red when THUG Pro
    updates, and the archive's copyright status (THUG Pro scripts grew out
    of THUG2's) isn't simple.
  - What stays hard: noticing a THUG Pro change nobody has run the local
    tests on yet; the known-versions table at least shows it as "untested".
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
    - **Always reconnects on launch** to whatever is saved; no setting.
      Stop / Log out clears the saved connection (keep the channel name
      filled in), so the next launch stays disconnected. A "don't reconnect"
      setting would bring back an idle-but-saved state (not "needs fixing",
      so not red) with its own UI; not worth it unless someone asks. Not
      wanting effects in game = the Dashboard's Enabled toggle.
    - Opened again within 4h, or within 30 days: reconnects the way it was
      left, no clicks (a quiet refresh after 4h; each refresh restarts the
      30 days). Read chat never expires.
    - After 30 days unused (logged in): the refresh fails; nothing
      connects. The sidebar's Twitch marker and the Dashboard Status row go
      **red** (`power_off`, the "needs addressing" state); the Twitch page
      shows the two options again with the login-expired message. **No
      fallback** to reading chat: it would add a "reading because the login
      expired" state and hide that redeems don't work (viewers spending
      points on rewards that do nothing). It only happens after 30 days
      without opening the app, so in practice at launch, before going live
      (tokens refresh on their own while running).
- **UI components: shadcn/ui on Base UI, with Tailwind CSS v4.** shadcn
  copies component source into the repo (we own and restyle it) rather than
  being a dependency; it can sit on Base UI, React Aria or Radix, and Base UI
  became its default in 2026-07. Our prototype tokens (asphalt, THUG gold,
  GitHub alert colours) become its CSS variables. Rough mapping: segmented
  controls → Toggle Group, toggles → Switch, sliders → Slider, kind chips →
  Toggle, edit card → Card, toasts → Sonner, and the trick picker → Command
  (cmdk) in a Popover/Dialog.
- **Icons: ~~Material Symbols from npm~~ superseded by Phosphor (see App
  scaffold).** Was: Material Symbols from npm (`material-symbols`, Apache 2.0,
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
- **Packaging: ZIP only** (`@electron-forge/maker-zip`, any platform). No
  installers: Squirrel (and `electron-squirrel-startup`) dropped, no bare
  `.deb`/`.rpm` (we're not targeting distro repos; loose packages are bad).
  macOS isn't a target (THUG Pro is Windows-only; Linux players use
  Proton/Wine). Linux: Flatpak preferred later; AppImage (community
  `@reforged/maker-appimage`) possible. electron-builder (portable `.exe`,
  first-party AppImage, `electron-updater`) was considered and passed on:
  staying on Forge.
- **Electron fuses:** the template's six kept (`RunAsNode` off,
  `EnableCookieEncryption` on, `EnableNodeOptionsEnvironmentVariable` off,
  `EnableNodeCliInspectArguments` off, `EnableEmbeddedAsarIntegrityValidation`
  on (macOS/Windows only), `OnlyLoadAppFromAsar` on), plus
  **`GrantFileProtocolExtraPrivileges` off**. With `RunAsNode` off,
  `child_process.fork` doesn't work: use `utilityProcess` if we ever need a
  child process. Maybe later: `strictlyRequireAllFuses: true` so new fuses
  in Electron upgrades need an explicit decision.
- **Renderer served over `app://`, not `file://`.** Electron's security
  checklist item 18 says to prefer a custom protocol (a `file://` page "has
  unilateral access to every file", so XSS could read arbitrary files: our
  page shows chat text and usernames), and its fuse docs say to disable
  `GrantFileProtocolExtraPrivileges` when not serving from `file://`.
  Forge's Vite docs only cover `file://` (`base: './'`, `loadFile`).
  Verified: with the fuse off, `loadFile` gives a blank page (Chromium
  won't run Vite's module script from `file://`); with `app://` it works.
  Implementation follows the `protocol.handle` example in Electron's
  protocol API docs (`registerSchemesAsPrivileged` with `standard`,
  `secure`, `supportFetchAPI`; path-traversal check), except `path.join`
  instead of the example's `path.resolve` (which treats the URL's leading
  `/` as absolute and would reject every path). Dev still loads the Vite
  dev server URL.
- **Commits:** Angular-style conventional commits (`feat`, `fix`, `docs`,
  `chore`, …), no scopes; `chore` for dependency/tooling changes (as
  Renovate/Dependabot do). commitlint and semantic-release planned.
- **Dependency ranges:** `^` + lockfile; `@electron-forge/*` on `~` (Forge's
  Vite plugin: "Future minor releases may contain breaking changes").
  `^` on 0.x packages (oxfmt) already means patch-only.
- **Configs as `.ts`** with `"type": "module"` in `package.json` (oxlint
  loads its config via Node; a `.ts` config in a CommonJS package warns).
  Formatter: oxfmt with the template's settings (single quotes, width 80,
  no `package.json` sorting); Tailwind class sorting to add with Tailwind.
- **Node 24** (LTS), pinned in `.nvmrc`: run `nvm use` before any node/npm
  command.
- **Package manager: npm** (with nvm for Node). pnpm considered: works fine
  with nvm (best via Corepack + a pinned `packageManager` field; Corepack is
  bundled with Node 24 but not from Node 25), but Electron Forge's packaging
  doesn't handle pnpm's symlinked `node_modules`, so it would need
  `node-linker=hoisted`, giving up most of what pnpm offers. npm avoids the
  Electron wrinkles.
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

## App scaffold (`app-scaffold` branch)

The real app lives in `app/` on the `app-scaffold` branch, built in small
reviewed commits on top of the repo's initial commit (worktree at
`../doakickflip-app`). Decisions made while building it, beyond the ones
above:

- **Renderer named `frontend`** (Forge's `name: 'main_window'` renamed).
  Lowercase on purpose: URL hosts are case-insensitive and get lowercased,
  so `app://kickflipFrontend/` would arrive as `kickflipfrontend` and fail
  the handler's host check. Forge derives `FRONTEND_VITE_NAME` /
  `FRONTEND_VITE_DEV_SERVER_URL` from the name (upper snake case) and
  injects them at build time; they're declared in `src/declarations.d.ts`
  ourselves (dev URL as `string | undefined`, which is what it is in
  packaged builds) instead of referencing Forge's `forge-vite-env` types,
  which hard-code `MAIN_WINDOW_*`.
- **Output layout:** main/preload build to `.vite/build/`, each renderer to
  `.vite/renderer/<name>/` (same inside `app.asar`), hence
  `../renderer/frontend` from main's `__dirname` (main is bundled to CJS,
  so `__dirname` exists despite `"type": "module"`).
- **`src/protocol.ts`** exports the `appScheme` (`CustomScheme`) and
  `handleAppProtocol`; `main.ts` calls `protocol.registerSchemesAsPrivileged`
  and `protocol.handle` itself. `isInRendererDir(file)` is the
  path-traversal check (also rejects the renderer dir itself). Verified
  with the packaged app: page loads over `app://`, other hosts, `../` and
  `%2e%2e` escapes and `file://` fetches all fail.
- **TypeScript 7:** `esModuleInterop` removed from tsconfig (always on;
  `false` is an error in 7) and `noImplicitAny` (covered by `strict`,
  which is the default since TS 6; checked). Other options left alone.
  `skipLibCheck` is required (a Forge dependency's types don't check).
  Node types come through Electron's own `@types/node` dependency.
- **oxlint:** `options.typeAware: true` in the config (not a CLI flag, so
  every runner agrees) with `oxlint-tsgolint`; `correctness` is `'error'`
  so CI fails on it. The three floating promises in the template's
  `main.ts` (`loadURL` ×2, `app.whenReady().then`) are marked `void`.
  Skipped for now: `no-misused-promises`, `no-deprecated`. Needs Node 24
  (`nvm use`): Node 20 can't load the `.ts` config.
- **`package.json`:** `name` and `productName` both `doakickflip`.
  `productName` names the executable, the ZIP and the settings folder
  (`app.getName()` → `~/.config/<productName>`, `%APPDATA%\<productName>`),
  so no emoji or punctuation there; the window title comes from
  `index.html`'s `<title>`. License MIT, `LICENSE` at the repo root.
- **React** added per Forge's React guide (written for its Webpack
  template, works as is with Vite): `"jsx": "react-jsx"`, `src/frontend/
  app.tsx` rendering into `document.body`, imported from `renderer.ts`.
  Vite's React plugin (Fast Refresh) not added (optional later).
- **Folder layout:** Electron entry points and wiring at `src/` (`main.ts`,
  `preload.ts`, `protocol.ts`, `renderer.ts`); `src/frontend/` for the
  renderer (React). Main-side code goes in sibling folders when it exists,
  e.g. `game/` or `thugpro/` (not `mod/`: clashes with the repo's QB mod
  source folder) and `twitch/`; the IPC contract (used by main, preload and
  frontend) in `shared/` or `ipc/`. Later: separate tsconfigs for
  `frontend/` (DOM) and the main side (Node) so a wrong-side import is a
  type error, not a build failure. (Alternative considered: by process,
  `src/main/`, `src/preload/`, `src/renderer/`, electron-vite style.)
- **React compiler:** `@vitejs/plugin-react` (its own commit) with
  `react({ compiler: true })` + `oxc-transform-react` (Oxc path, per
  https://oxc.rs/blog/2026-08-18-react-compiler-support; the Vite
  integration is marked experimental). Verified on a throwaway component:
  compiled output uses `react/compiler-runtime`'s cache. Lint: oxlint's
  `react` plugin runs the compiler's rules natively (12 in `correctness`
  incl. `void-use-memo`), no `eslint-plugin-react-hooks`. `plugins` is
  listed in full (`eslint`, `typescript`, `unicorn`, `oxc`, `react`):
  setting `plugins` replaces the defaults (the blog's `["react"]` snippet
  silently drops the `typescript` plugin, incl. `no-floating-promises`;
  tested). `overrides` with `plugins: ['react']` also kept the defaults in
  testing, but the docs don't say override plugins merge, and `extends`
  only takes our own configs; we chose to just list them.
- **Tailwind CSS v4** per its Vite guide (both packages as regular
  dependencies, as the guide has it; in our setup only the bundle is
  packaged, so dependency vs devDependency doesn't change what ships).
  `index.css` is only the Tailwind import (template body styles dropped);
  oxfmt `sortTailwindcss: true` (verified it reorders classes).
- **Frontend entry vs component:** `src/frontend/index.tsx` (createRoot,
  renders `<App />`) and `src/frontend/App.tsx` (the root component).
  Vite's template calls the entry `main.tsx`; not used here to avoid
  confusion with Electron's `main.ts`. File casing: PascalCase for React
  components we write, kebab-case for shadcn's generated ones.
- **shadcn/ui:** Base UI with the **Maia** style ("soft and rounded, with
  generous spacing"; Nova, the CLI default, was tried first; Rhea and Luma
  were also liked). `@/` → `src/frontend/` (tsconfig `paths` without
  `baseUrl`, which type-aware oxlint doesn't support; Vite alias via
  `import.meta.dirname`). shadcn's CLI only detects Vite via a
  `vite.config.*` file, so run it with a temporary
  `vite.config.ts` containing `export { default } from
  './vite.renderer.config';` and delete it after. Generated files get
  reformatted by oxfmt. The style lives in each component's classes, not
  in `index.css` (the CSS is the same for every style apart from the
  font). Font: Figtree (from the Maia preset), bundled via fontsource.
  `shadcn` itself is a **devDependency** (only its `tailwind.css` is read
  at build time). Generated components import `cn` from the `cn` package
  directly.
- **Icons: Phosphor** (`@phosphor-icons/react`, MIT), set as shadcn's
  `iconLibrary` (replacing Maia's default Hugeicons) and **replacing the
  earlier Material Symbols decision** for our own icons. Why: every icon
  in six weights (`thin`, `light`, `regular`, `bold`, `fill`, `duotone`),
  so filled state icons and heavy combo arrows are one prop, like
  Material's axes were. Compared: Hugeicons free (outline only; filled is
  Pro), Tabler (MIT, most icons, very active, `…Filled` for many, stroke
  width), Remix (custom Remix Icon License 1.0: fine for apps, but not as
  a logo/standalone pack; fixed stroke), Lucide. All covered our icon
  list. Phosphor's React package was last released 2025-05. Keep the
  official Twitch logo (brand rules), not a library's Twitch icon.
- **Known audit finding:** `braces` ≤ 3.0.3 (GHSA-vfj7-8cjw-p6xm, stack
  exhaustion via nested patterns, published 2026-09-18) has **no fixed
  version yet**; it comes in only through the `shadcn` CLI (`fast-glob` →
  `micromatch` → `braces`), a dev dependency that never ships. npm's
  suggested "fix" (shadcn 1.0.0) is a downgrade. Recheck later.
- **Install scripts:** npm 11 holds back packages' install scripts until
  approved; none pending since the Squirrel maker (`electron-winstaller`)
  went. Electron 44 downloads its binary on first run, not at install.
- **Verifying the running app:** launch with `--remote-debugging-port=N`
  (packaged binary, or `npx electron-forge start -- --remote-debugging-port=N`)
  and use the Chrome DevTools Protocol from a small Node script
  (`/json` for the page list, `Runtime.evaluate` / console events over the
  page's WebSocket) to check the URL, rendered DOM, console warnings, and
  `fetch` results. Stop test processes by their full binary path (a
  `pkill -f` pattern that also matches the calling shell kills the shell).

## Open

Nothing undecided. To check before relying on it:
- What reading chat **without a login** really delivers (messages and
  cheers assumed; sub notices probably too), against Twitch's docs, before
  the Twitch page's Read chat ticks/crosses are final.
