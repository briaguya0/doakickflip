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

- **Twitch library and login flow:** still being discussed. Looked at so
  far (nothing chosen):
  - Twurple (`@twurple/*` 8.2.0, 2026-09): chat without login when no auth
    provider is given; `RefreshingAuthProvider` supports Twitch's Device
    Code Flow (public client, no secret, no redirect server); EventSub over
    WebSocket; Helix API for rewards. DCF refresh tokens are one-time use
    and expire after 30 days unused.
  - `tmi.js` (last release 2021), `@tmi.js/chat` (0.x),
    `@twurple/auth-electron` (last release 2023).
  - Either way we need our own Twitch application (client ID), like Sail.
- **Test fixtures for mod install.** Nothing from THUG2 or THUG Pro can be
  committed. Idea: a hand-written fake pause-menu script with the same shape
  as the hook point (`if GameModeEquals is_singlesession` … `endif`),
  compiled and packed into a fake `thugpro_qb.prx` by our own tools. It
  repeats a few of the game's script names, as `mod/doakickflip.q` already
  does: is that acceptable?
- **Real-install tests:** opt-in, only when pointed at a THUG Pro folder
  (e.g. `THUGPRO_DIR`); never on public CI; outputs never committed.
