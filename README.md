# doakickflip

Tooling for modding THUG Pro (Tony Hawk's Underground 2 mod) scripts, and a
mod that adds **Do a Kickflip!** to the free skate pause menu: high combo mode
where chat picks the tricks. Requested tricks appear in the stock Skate-Tricks
list, with button combos and the requester's name. Each one clears as soon as
you do it mid-combo, and if too many pile up you bail. Requests come from an
outside program through a file (`tools/call_trick.py`, `tools/fake_chat.py`
for testing, a Twitch bridge later).

This repo contains no game data. You need your own THUG2 and THUG Pro
installs; everything derived from them (`extracted/`, `build/`, `logs/`) is
gitignored.

## Tools (`tools/`, Python 3, no dependencies)

| tool | what it does |
|------|--------------|
| `prx.py OUT_DIR a.prx ...` | unpack PRE/PRX archives (also provides `replace()` for repacking) |
| `qbdec.py [-n NAMES_DIR] f.qb ...` | decompile QB bytecode to readable `.q` next to each file |
| `qbc.py in.q out.qb` | compile `.q` back to QB bytecode (no `switch`/`elseif`/`Random` yet) |
| `roundtrip.py DIR ...` | decompile and recompile every `.qb`, check the bytes match |
| `extract.py --thug2 DIR --thugpro DIR` | unpack and decompile both games' scripts into `extracted/` |
| `call_trick.py --thugpro DIR [TRICK ...]` | send trick requests by display name (`Kickflip`, `"Pop Shove-It"`); reads stdin (`user: trick`) if no args; `--reset` creates an empty inbox |
| `fake_chat.py --thugpro DIR [--rate N]` | simulate chat: random tricks from made-up users, ~N per minute with bursts |
| `build_mod.py THUGPRO_DIR [--install]` | build the patched `thugpro_qb.prx` into `build/`, optionally install it (backs up the original to `.bak` once) |
| `run_thugpro.sh` | launch `THUGPro.exe` via `umu-run` with Proton logging into `logs/` (set `GAMESCOPE="-w 3840 -h 2160 -f"` etc. to run in gamescope) |

## Quick start

```sh
# paths to your installs
THUG2="/path/to/Tony Hawk's Underground 2"
THUGPRO="/path/to/prefix/drive_c/users/steamuser/AppData/Local/THUG Pro"

python3 tools/extract.py --thug2 "$THUG2" --thugpro "$THUGPRO"   # for reading scripts
python3 tools/roundtrip.py extracted/thugpro extracted/thug2     # sanity check the tools
python3 tools/build_mod.py "$THUGPRO" --install                  # build and install the mod
python3 tools/call_trick.py --thugpro "$THUGPRO" --reset          # create the (empty) trick inbox

WINEPREFIX=/path/to/prefix PROTONPATH=/path/to/GE-Proton tools/run_thugpro.sh
# in free skate: pause -> Do a Kickflip!, then in another terminal:
python3 tools/fake_chat.py --thugpro "$THUGPRO"                   # or call_trick.py for single tricks
```

Launch `THUGPro.exe` directly rather than through `THUGProLauncher.exe`, whose
updater may put the stock archive back. To uninstall, move
`data/pre/thugpro_qb.prx.bak` back over `thugpro_qb.prx`. A modified archive may
cause trouble on online servers.

The mod source is `mod/doakickflip.q`. `build_mod.py` appends it to the pause
menu script and inserts one call into the free skate section. While the mode
is on, the game polls `User/Data/doakickflip/inbox.qb` for requests.

See [NOTES.md](NOTES.md) for file formats, how the Skate-Tricks goal works, and
the debugging trail.
