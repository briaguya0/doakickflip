#!/usr/bin/env python3
"""Extract and decompile THUG2 + THUG Pro scripts into extracted/ for reading.

Usage: extract.py --thug2 THUG2_DIR --thugpro THUGPRO_DIR [--out extracted]

THUG2_DIR    the "Tony Hawk's Underground 2" install (contains Game/Data/pre)
THUGPRO_DIR  the "THUG Pro" install (contains data/pre/thugpro_qb.prx)

Produces extracted/thug2/... and extracted/thugpro/... with the original .qb
files plus a decompiled .q next to each. Names are resolved using the name
tables from both games.
"""
import argparse
import glob
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import prx
import qbdec


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--thug2', required=True)
    ap.add_argument('--thugpro', required=True)
    ap.add_argument('--out', default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'extracted'))
    args = ap.parse_args()

    sources = {
        'thug2': sorted(glob.glob(os.path.join(args.thug2, 'Game', 'Data', 'pre', '*_scripts.prx'))),
        'thugpro': sorted(glob.glob(os.path.join(args.thugpro, 'data', 'pre', 'thugpro_qb.prx'))
                          + glob.glob(os.path.join(args.thugpro, 'data', 'pre', '*_[Ss]cripts.prx'))),
    }
    for name, archives in sources.items():
        if not archives:
            sys.exit(f'no script archives found for {name}; check the path')
        dest = os.path.join(args.out, name)
        total = sum(prx.unpack(a, dest) for a in archives)
        print(f'{name}: {len(archives)} archives, {total} files -> {dest}')

    qbs = [os.path.join(r, f) for r, _, fs in os.walk(args.out) for f in fs if f.lower().endswith('.qb')]
    for f in qbs:
        qbdec.harvest(open(f, 'rb').read())
    partial = []
    for f in qbs:
        text = qbdec.Dec(open(f, 'rb').read()).run()
        open(os.path.splitext(f)[0] + '.q', 'w').write(text)
        if '!!! unknown' in text:
            partial.append(f)
    print(f'decompiled {len(qbs)} files ({len(partial)} stopped early on unknown opcodes)')
    for f in partial:
        print('  partial:', os.path.relpath(f, args.out))


if __name__ == '__main__':
    main()
