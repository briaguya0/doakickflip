# THUG Pro file redirect and `User\Data`

`thugpro.dll` hooks `CreateFileA` (hook entry `0x10014bb0`). For any path
containing `Data\` (matched with `StrStrIA`, so case-insensitive; the engine
uses lowercase `data\`) and not `thugpro.exe`:

1. Look the path up in a cache of earlier redirects (`0x10015350`, FNV hash map;
   filled at `0x10015211` after a successful search). It isn't an override
   mechanism.
2. Rewrite `.pre` to `.prx` (plus a similar swap on a `...tex` extension), then try
   these roots in order, taking the first that opens (observed with `+file`):
   1. the THUG Pro folder (stock install)
   2. `<THUG Pro>\..\output\`
   3. the THUG2 install folder (e.g. `C:\Program Files (x86)\Activision\Tony Hawk's Underground 2\Game\`)
   4. `<THUG Pro>\User\`
3. A missing-image fallback substitutes a placeholder texture.

So `User\Data\...` can only **add** files the stock install lacks; it can't
override `data\pre\thugpro_qb.prx`. A `+file` trace of startup, loading a level,
and free skate showed the only files probed under `User\` and not found are
`manifest_levels.dat` and `manifest_soundtracks.dat` (custom level / soundtrack
manifests). No stray script loads, so there's no zero-patch hook. Custom
levels load `User\data\levels\<name>\<name>_scripts.qb`, which would only
work inside that level.

`LoadQB "doakickflip\\tricks.qb"` from script does go through the redirect and
reads a loose `User\Data\doakickflip\tricks.qb` (verified). The mod uses this
for the trick list: the file is compiled QB (from `mod/tricks.txt` via
`tools/tricks.py`) and reloaded every time the goal starts, so it can change
without restarting the game.
