#!/usr/bin/env python3
"""Compile a plain-text trick list into the tricks.qb the doakickflip mod loads.

Usage: tricks.py TRICKS.txt (--thugpro THUGPRO_DIR | --out FILE.qb)

With --thugpro the result goes to THUGPRO_DIR/User/Data/doakickflip/tricks.qb,
which the game picks up the next time Skate-Tricks is started (no restart needed).

File format: one trick per line, in the order they should be called out.
A trick is a key-combo name as used by the game's trick slots, e.g.
    Air_SquareL          # left + flip button
    Air_CircleU x2       # up + grab, double tap
Blank lines and '#' comments are ignored. Combo names look like
Air_SquareU, Air_CircleDL, Air_L_L_Square, SpAir_D_U_Circle, Lip_TriangleU,
SpGrind_L_R_Triangle, SpMan_U_D_Triangle, ...
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import qbc

COMBO = re.compile(r'(Air|Lip|SpAir|SpGrind|SpLip|SpMan|Extra)_[A-Za-z_]+')


def parse_trick(text):
    """Parse one trick like 'Air_SquareL' or 'Air_CircleU x2' into (combo, taps).
    Returns None for blank/comment-only text; raises ValueError if malformed."""
    line = text.split('#', 1)[0].strip()
    if not line:
        return None
    m = re.fullmatch(r'(\S+)(?:\s+x(\d+))?', line)
    if not m or not COMBO.fullmatch(m.group(1)):
        raise ValueError(f'expected a key combo like Air_SquareL [x2], got {line!r}')
    return m.group(1), int(m.group(2) or 1)


def combo_q(combo, taps):
    """QB text for one goal_tetris_key_combos element."""
    return combo if taps == 1 else f'{{ key_combo = {combo} num_taps = {taps} }}'


def parse(path):
    tricks = []
    for n, raw in enumerate(open(path), 1):
        try:
            t = parse_trick(raw)
        except ValueError as e:
            sys.exit(f'{path}:{n}: {e}')
        if t:
            tricks.append(t)
    if not tricks:
        sys.exit(f'{path}: no tricks')
    return tricks


def to_q(tricks):
    out = ['doakickflip_tricks = [']
    for combo, taps in tricks:
        out.append(f'{{ goal_tetris_key_combos = [ {combo_q(combo, taps)} ] }}')
    out.append(']')
    return '\n'.join(out) + '\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('tricks')
    dest = ap.add_mutually_exclusive_group(required=True)
    dest.add_argument('--thugpro')
    dest.add_argument('--out')
    args = ap.parse_args()

    tricks = parse(args.tricks)
    out = args.out or os.path.join(args.thugpro, 'User', 'Data', 'doakickflip', 'tricks.qb')
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    open(out, 'wb').write(qbc.compile_text(to_q(tricks)))
    print(f'wrote {len(tricks)} tricks to {out}')


if __name__ == '__main__':
    main()
