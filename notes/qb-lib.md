# nsqb: NeverScript ↔ QB library

The script side of the mod (compiling and decompiling QB) will be a
**separate library in its own repo**, not code inside doakickflip. Working
name **`nsqb`** (NeverScript ↔ QB; free on npm as of 2026-10-16).

- Its history shouldn't start in doakickflip, and there's useful work to do
  with it standalone before integrating it.
- doakickflip consumes it like any other package. Until it's published,
  doakickflip vendors an `npm pack` tarball (a `file:vendor/…tgz`
  dependency is fine).
- To work on both at once, doakickflip's app gets a **gitignored npm
  workspace dir**, `app/packages/`, that a local checkout of the library can
  drop into. No turbo: one library and one app don't need it.
- The checkout in `packages/` is a **worktree (or clone), not a symlink**:
  Node resolves a symlink to its real path, so the library would resolve its
  imports from its own `node_modules` instead of the app's.

## Direction

- **Text format: NeverScript (`.ns`)**, byxor's language that compiles to
  QB, rather than the Neversoft-style `.q` our Python tooling
  (`qbdec.py` / `qbc.py`) uses. Tested on THUG2 / THPS4 (THUG Pro is
  THUG2-based), and it's what Revert's MIT-licensed tooling and mods use, so
  `nsqb` stays compatible with an existing ecosystem. `mod/doakickflip.q`
  would move to `.ns`.
- **Scope: `.ns` ↔ `.qb` and QB keys only.** PRX archives and LZSS stay out
  (there's likely existing tooling for those; see below).
- **QB keys:** every name in bytecode is `crc32(name.lower()) ^ 0xFFFFFFFF`
  (see [formats.md](formats.md)); each `.qb` ends with a checksum → name
  table, which THUG Pro strips. `nsqb` computes keys, reads/writes name
  tables and takes extra names from the caller, but **ships no key lists**
  (those would be the game's identifiers). Callers (doakickflip) build
  dictionaries at runtime from the user's own install.
- **Provenance:** our own tooling was worked out from the game files
  ([formats.md](formats.md)). Other projects are references for checking
  understanding, not code to copy.

## Prior art: QB / QScript

No official spec exists. Neversoft called the language **QScript** (`.q`
source, `.qb` "q binary", compiler `qcomp`), per
[NxDocs](https://donnaken15.com/FastGH3/docs/NxDocs2/Q/) (donnaken15's
informal "test wiki", unlinked from the rest of the site).

- [byxor/NeverScript](https://github.com/byxor/NeverScript) (Go, 2023):
  NeverScript → QB compiler, PRE/PRX generator; decompiler not implemented.
  `compiler/tokens.go`, `docs/neverscript-syntax.ns`. No licence; the README
  says "Feel free to fork the repo and make as many changes/improvements as
  you like. There's no license, you don't owe me a thing." We won't use Go
  code anyway.
- [violetvandal/revert](https://github.com/violetvandal/revert)
  ([docs](https://docs.thug2vandal.com/codecs/)) and
  [revert-mods](https://github.com/violetvandal/revert-mods) (Go, MIT,
  2026): THUG2 toolkit, "ships no game data"; mods in `.ns`, compiled by a
  patched NeverScript fork described as a byte-perfect recompiler (gaps in
  its `LIMITATIONS.md`).
- [fretworks/nodeqbc](https://gitgud.io/fretworks/nodeqbc) (JS, 2022–2026,
  no licence): `.q` ↔ `.qb` compiler/decompiler, compile + decompile for THUG,
  THUG2, THAW, GH3, GHWT. Port of the lost `bloowm/qbc`.
  [donnaken15/NodeQBC](https://github.com/donnaken15/NodeQBC) is an older
  copy (THUG2 decompile only).
- [Guitar Hero SDK](https://gitgud.io/fretworks/guitar-hero-sdk) (Zedek,
  `"license": "ISC"` in `package.json`, no LICENSE file): wiki QB pages
  (Data Types, Keywords and Symbols, Math Operations, Struct Tricks), GH-era
  syntax.
- [slfx77/neversoft-multitool](https://github.com/slfx77/neversoft-multitool)
  (C#, 2026): QB decompile (THPS3–THUG2), PRE archives, QB keys.
- Older THUG2 tools, no licence: [LeonBlade/qb](https://github.com/LeonBlade/qb),
  [kennythps/QBReader](https://github.com/kennythps/QBReader), roq
  (workflow: [leaty/thug-pro-scripting](https://github.com/leaty/thug-pro-scripting)),
  ThMods guides ([835](http://thmods.com/forum/viewtopic.php?t=835),
  [472](http://thmods.com/forum/viewtopic.php?t=472)).
- donnaken15 also has [qcc](https://github.com/donnaken15/qcc) (unfinished
  compiler) and [QDB](https://github.com/donnaken15/QDB) (GH3 debugger).
- Licence pattern: the older tools have no licence; the licensed ones are
  recent, and a fork's licence can't cover code carried over from an
  unlicensed upstream.
- PRX / LZSS (out of `nsqb`'s scope): neversoft-multitool, thugkit's PRE
  codec, PreTool / PRXReaper. npm not checked yet.

**To check before committing to NeverScript:** whether its grammar covers
everything THUG2 scripts use (`switch`, `elseif`, `Random*`); whether
Revert's fork adds a `.qb` → `.ns` decompiler; which repo the fork is and
its licence.

## Prior art: openedx

[frontend-template-application](https://github.com/openedx/frontend-template-application)
developing against [frontend-base](https://github.com/openedx/frontend-base):

- The app's `package.json` has `"workspaces": ["packages/*"]`, and
  `.gitignore` has `packages/`, so nothing of the library is committed.
- `npm install` then links the local copy. The library's dev version is
  `0.0.0-dev`, and the app's range allows it (`"^2.0.0-alpha || 0.0.0-dev"`).
- turbo (`turbo.site.json`, driven from the `Makefile`) builds the packages
  first, then runs the library's `watch:build` next to the app's dev server.

## Spike (2026-10-15)

A throwaway library (one function, `tsc` to `dist/`, local git repo in the
scratch dir) wired into the app worktree, then everything reverted. Nothing
committed or published.

- **Vendored tarball:** `npm install ./vendor/qb-spike-0.1.0.tgz` records
  `"qb-spike": "file:vendor/qb-spike-0.1.0.tgz"`; dev and packaged builds
  use it. The Forge template's `.gitignore` ignores `*.tgz`
  (`app/.gitignore`, "Output of 'npm pack'"), so committing the tarball
  needs `!vendor/*.tgz`.
- **Bundled into main:** Forge's Vite plugin bundles the library (and
  whatever it imports) into `.vite/build/main.cjs`. The packaged app has no
  `node_modules`: the plugin sets `packagerConfig.ignore` to everything not
  under `/.vite` (`VitePlugin.js`).
- **Worktree in `packages/`:** with `"workspaces": ["packages/*"]` and
  `packages/` gitignored, `git worktree add <app>/packages/qb-spike` from
  the library's sibling checkout, then a plain `npm install` in the app:
  the app now uses the checkout instead of the vendored tarball, in dev and
  packaged builds. `package.json` is untouched (still the `file:` tarball).
  `git worktree remove` + `npm install` goes back to the tarball. A branch
  can only be checked out in one worktree, so the sibling checkout and the
  one in `packages/` need different branches (or one detached).
- **Lockfile:** while `packages/` has a checkout, `npm install` rewrites the
  lock entry to a link (`"resolved": "packages/qb-spike", "link": true`).
  With `packages/` empty, `npm install` goes back to the tarball; the only
  lasting difference from a tarball-only lock is the `workspaces` field.
  **Don't commit `package-lock.json` while `packages/` is populated.**
- **Dev loop:** library `tsc` (or `tsc --watch`) rebuilds `dist/`; Forge
  notices and rebuilds main, but doesn't restart Electron (same as editing
  `main.ts` itself). Type `rs` in the `npm start` terminal ("Type rs in
  terminal to restart main process.").
- Not tried: using the library from the renderer (only main is planned), and
  a registry dependency (`"^0.1.0"`) where the local copy's version doesn't
  satisfy the range.
