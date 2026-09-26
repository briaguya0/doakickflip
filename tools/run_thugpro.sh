#!/usr/bin/env bash
# Launch THUGPro.exe directly (skipping THUGProLauncher.exe and its updater, which
# may restore the stock thugpro_qb.prx) with Proton logging and SEH/debug-string
# tracing, so crashes show up with an address in logs/steam-default.log.
#
# Usage: WINEPREFIX=/path/to/prefix PROTONPATH=/path/to/GE-Proton tools/run_thugpro.sh
# Optional: THUGPRO_DIR (defaults to the Lutris install location inside the prefix)
set -euo pipefail
: "${WINEPREFIX:?set WINEPREFIX to the wine prefix of the game}"
: "${PROTONPATH:?set PROTONPATH to the Proton build (e.g. .../compatibilitytools.d/GE-Proton11-7-x86_64)}"
THUGPRO_DIR="${THUGPRO_DIR:-$WINEPREFIX/drive_c/users/steamuser/AppData/Local/THUG Pro}"
LOG_DIR="$(cd "$(dirname "$0")/.." && pwd)/logs"
mkdir -p "$LOG_DIR"
rm -f "$LOG_DIR/steam-default.log"
cd "$THUGPRO_DIR"
export WINEPREFIX PROTONPATH GAMEID=umu-default PROTON_LOG=1 PROTON_LOG_DIR="$LOG_DIR"
export WINEDEBUG="${WINEDEBUG:-+seh,+debugstr}"
exec umu-run ./THUGPro.exe
