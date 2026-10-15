# QB / PRX library

The mod side (PRX archives, LZSS, QB keys, decompiling and compiling QB) will
be a **separate library in its own repo**, not code inside doakickflip:

- Its history shouldn't start in doakickflip, and there's useful work to do
  with it standalone before integrating it.
- doakickflip consumes it like any other package. Until it's published,
  doakickflip vendors an `npm pack` tarball.
- To work on both at once, doakickflip's app gets a **gitignored npm
  workspace dir**, `app/packages/`, that a local checkout of the library can
  drop into. No turbo: one library and one app don't need it.
- The checkout in `packages/` is a **worktree (or clone), not a symlink**:
  Node resolves a symlink to its real path, so the library would resolve its
  imports from its own `node_modules` instead of the app's.

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
