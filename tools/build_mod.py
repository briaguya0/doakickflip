#!/usr/bin/env python3
"""Build a patched thugpro_qb.prx with the doakickflip pause-menu entry.

Usage: build_mod.py THUGPRO_DIR [--out build/thugpro_qb.prx] [--install]

Reads the original archive from THUGPRO_DIR/data/pre/ (preferring
thugpro_qb.prx.bak if a previous --install created it), patches the pause
menu script, and writes the result to --out. With --install it also backs up
the original to thugpro_qb.prx.bak (once) and copies the build into place.
"""
import argparse
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(__file__))
import prx
import qbc
import qbdec

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAUSE = 'qb\\game\\menu\\gamemenu_pause.qb'
TETRIS = 'qb\\game\\goals\\goal_tetris.qb'
HOOK_CALL = 'doakickflip_pause_menu_items'
TRICK_HOOK_CALL = 'doakickflip_on_trick_added'


def insert_hook(text):
    """Call HOOK_CALL inside the `if GameModeEquals is_singlesession` block of the
    pause menu, just before that block's endif (i.e. after the High Score Run items)."""
    lines = text.split('\n')
    starts = [i for i, l in enumerate(lines) if re.fullmatch(r'\s*if GameModeEquals is_singlesession\s*', l)]
    # the one that holds the High Score Run menu items
    starts = [i for i in starts if any('TrickAttack_MenuStartRun' in l for l in lines[i:i + 40])]
    if len(starts) != 1:
        sys.exit(f'expected one singlesession block with High Score Run items, found {len(starts)}')
    start = starts[0]
    indent = len(lines[start]) - len(lines[start].lstrip())
    depth = 0
    for j in range(start, len(lines)):
        word = lines[j].strip().split(' ', 1)[0]
        if word == 'if':
            depth += 1
        elif word == 'endif':
            depth -= 1
            if depth == 0:
                lines.insert(j, ' ' * (indent + 4) + HOOK_CALL)
                return '\n'.join(lines)
    sys.exit('unterminated singlesession block')


def insert_trick_hook(text):
    """Call TRICK_HOOK_CALL at the top of goal_tetris_add_trick, which the engine
    runs each time it adds a trick to a Skate-Tricks stack."""
    lines = text.split('\n')
    starts = [i for i, l in enumerate(lines) if l.strip() == 'script goal_tetris_add_trick']
    if len(starts) != 1:
        sys.exit(f'expected one goal_tetris_add_trick script, found {len(starts)}')
    lines.insert(starts[0] + 1, '    ' + TRICK_HOOK_CALL)
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('thugpro_dir')
    ap.add_argument('--out', default=os.path.join(ROOT, 'build', 'thugpro_qb.prx'))
    ap.add_argument('--install', action='store_true')
    args = ap.parse_args()

    pre = os.path.join(args.thugpro_dir, 'data', 'pre')
    live, backup = os.path.join(pre, 'thugpro_qb.prx'), os.path.join(pre, 'thugpro_qb.prx.bak')
    src = backup if os.path.exists(backup) else live

    data = open(src, 'rb').read()
    files = {name: blob if not csize else prx.lzss_decompress(blob, size)
             for name, size, csize, _crc, blob in prx.entries(data)}
    for body in files.values():
        qbdec.harvest(body)
    pause = insert_hook(qbdec.Dec(files[PAUSE]).run())
    pause += '\n' + open(os.path.join(ROOT, 'mod', 'doakickflip.q')).read()
    tetris = insert_trick_hook(qbdec.Dec(files[TETRIS]).run())
    patched = {PAUSE: qbc.compile_text(pause), TETRIS: qbc.compile_text(tetris)}

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    prx.replace(src, args.out, patched)
    print(f'built {args.out} from {src}')
    for name, body in patched.items():
        print(f'  {name}: {len(files[name])} -> {len(body)} bytes')

    if args.install:
        if not os.path.exists(backup):
            shutil.copy2(live, backup)
            print(f'backed up original to {backup}')
        shutil.copy2(args.out, live)
        print(f'installed to {live}')


if __name__ == '__main__':
    main()
