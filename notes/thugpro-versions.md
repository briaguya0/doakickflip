# THUG Pro versions, installer and updater

How THUG Pro is distributed and updated, and how we can tell which version
is installed. Worked out 2026-10-11 against the installed **beta 0.7.0.0**
(released 2023-10-19 per https://thugpro.com/changelog/). Nothing downloaded
here is committed; re-fetch it to follow along.

## The installed version

- The launcher shows **beta 0.7.0.0**.
- `changelog.txt` in the install says 0.6.0.11 at the top. It's the official
  file (its CRC matches the 0.7.0.0 manifest); they just stopped updating
  it. **Not a version source.**
- No version is stored in the registry (`Software\THUG Pro\{Game,Install,
  Settings,Theme,User}` hold settings and `thug2_path` only) or in any config
  file.
- **The version is compiled into `thugpro.dll`.** The THUG Pro script shows
  it in the online bulletin board (`qb/thugpro/thugpro_net.q`):
  `THUGPRO_Version` then `FormatText ... "Welcome To THUGPRO BETA Version
  %a!" a = <version>`. `THUGPRO_Version` is native; the DLL has one
  `%d.%d.%d.%d` string with exactly one reference (file offset `0xfc2f`,
  VA `0x1001082f`), preceded by:

  ```
  6a 00   push 0
  6a 00   push 0
  6a 07   push 7
  6a 00   push 0
  68 <&"%d.%d.%d.%d">
  68 <buffer>
  call sprintf
  ```

  cdecl pushes right to left: `sprintf(buf, "%d.%d.%d.%d", 0, 7, 0, 0)` =
  "0.7.0.0". **Reading the version without running the game:** find the
  format string, compute its VA (image base `0x10000000`), find the single
  `68 <va>` push, read the four pushes before it (`6a imm8`; a number above
  127 would be `68 imm32`). Pure file read: nothing Defender cares about.
  Fall back to CRCs (below) if the pattern isn't found.

## Installer

`https://dl.thugpro.com/THUGProSetup.exe` (613,888 bytes, last-modified
2024-12-04) is a small .NET downloader, not a package of game files. It
reads `http://dl.thugpro.com/current.json` and installs through `updt.dll`.
Also fetches the VC++ 2010 x86 redistributable and the DirectX June 2010
redist from Microsoft.

## Updater (`updt.dll`)

Built from a project called `thugpro_proxy` (`D:\Repos\thugpro_proxy\Update\
Release\updt.pdb`). Exports: `checkForUpdates`, `runInstall`, `runRepair`,
`runUpdater`, `setTHUGProPath`, `testMessageBox` (and a `Direct3DCreate9`
forwarder).

- `http://dl.thugpro.com/current.json` → `{"release":"beta","version":
  "0.7.0.0"}` (also a `testver.json` for test releases).
- `http://dl.thugpro.com/update/<release>/<version>/update.json`, e.g.
  `update/beta/0.7.0.0/update.json` (118 KB): `version`, `release`,
  `data_files`, `other_files`, `streams`. **776 files**, each with `crc32`,
  `link` (`/update/beta/0.7.0.0/<path>`) and `version`. `thugpro_qb.prx` is
  `data/pre/thugpro_qb.prx`, crc32 `09fc08b0`. Streams come from
  `http://dl.thugpro.com/t2/streams.json` / `t2/streams/`.
- It compares versions ("Current version is higher or equal to version in
  manifest") **and validates every file by CRC32** ("Validating Files",
  "File doesn't exist, need it", "Calculating data file deltas", "Downloaded
  CRC didn't match"). So it knows about outdated, missing or damaged files,
  not just the version label.

## Our install vs the 0.7.0.0 manifest

| file | ours | manifest |
|---|---|---|
| `data/pre/thugpro_qb.prx.bak` (our backup) | `09fc08b0` | `09fc08b0` ✓ |
| `data/pre/thugpro_qb.prx` (mod installed) | `576c64f6` | `09fc08b0` (patched, expected) |
| `thugpro.dll`, `THUGPro.exe`, `updt.dll`, `changelog.txt` | match | ✓ |

SHA-256 (local, for reference): `thugpro.dll` d0cc0cb0…b21d05,
`THUGPro.exe` f5f01af0…25a9ca, original `thugpro_qb.prx` 7de9113b…0361ac.

## What it means for us

- **The updater sees our patched archive as damaged.** A repair (and maybe
  an update check) would download the official file over it, silently
  uninstalling the mod. Not yet known whether the launcher validates on
  every start or only on repair/update: test it (see [todo.md](todo.md)).
- **Known-versions table, seeded from THUG Pro's manifests.** They publish a
  CRC32 per file per release; CRCs are metadata, not their content. The app
  can then tell offline whether the live `thugpro_qb.prx` is an official
  original (safe to patch; refresh our backup from it), our patched build
  (installed), or neither (modified/unknown: don't touch).
- **The `.bak` bug** ([todo.md](todo.md)) gets a clean fix from that: if the
  live file matches an official CRC, it's a fresh original.
- **Status card:** label from `thugpro.dll`; tested/untested from the CRC
  table.
- Pulling the files themselves in CI stays dropped (see
  [architecture.md](architecture.md)); fetching a manifest's CRCs is a
  different, much lighter thing.
