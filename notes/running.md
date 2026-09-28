# Running and debugging under Lutris + umu (GE-Proton)

- `lutris lutris:rungameid/N` hands off to a running Lutris GUI, so you don't
  get its output.
- `tools/run_thugpro.sh` runs `THUGPro.exe` directly via `umu-run` with
  `PROTON_LOG=1`, `WINEDEBUG=+seh,+debugstr`, and the log in
  `logs/steam-default.log`. Grep for `c0000005` / `Exception 0x` to find the
  faulting address, then `objdump -d -M intel --start-address=... THUGPro.exe`
  (image base 0x400000, no ASLR) and resolve pushed checksums against the
  harvested name table.
- On this machine the Lutris install has `drive_c/users/briaguya` symlinked to
  `steamuser`, and THUG Pro lives at
  `drive_c/users/steamuser/AppData/Local/THUG Pro`.
- Gamescope: Lutris wraps the launch as `gamescope <args> -- <umu cmd>` (game
  res → `-w/-h`, output res → `-W/-H`, window mode defaults to `-f`).
  `run_thugpro.sh` does the same when `GAMESCOPE` is set. Running fullscreen
  without it, the game minimizes when it loses focus.
- The game's own `thugpro.log` only had script-not-found warnings. It didn't
  show either crash.
