#!/usr/bin/env python3
"""Round-trip test: decompile each .qb, recompile, and compare code bytes.

Usage: roundtrip.py DIR [DIR ...]
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(__file__))
import qbc
import qbdec


def code_end(d):
    """Offset of the first name-table entry (0x2B) or terminator in the token stream."""
    i = 0
    in_script = False
    while i < len(d):
        op = d[i]
        if op == 0x2B or (op == 0x00 and not in_script):
            return i
        if op == 0x23: in_script = True
        elif op == 0x24: in_script = False
        i += 1
        if op in (0x16, 0x17, 0x18, 0x1A, 0x02, 0x2E): i += 4
        elif op in (0x1B, 0x1C): i += 4 + struct.unpack_from('<I', d, i)[0]
        elif op == 0x1E: i += 12
        elif op == 0x1F: i += 8
        elif op in (0x47, 0x48, 0x49): i += 2
        elif op == 0x27: i += 4
        elif op in (0x2F, 0x37, 0x40, 0x41):
            n = struct.unpack_from('<I', d, i)[0]
            i += 4 + 6 * n
    return i


def normalize_begin(d):
    """Rewrite mid-script 0x00 (alternate begin encoding) to 0x20 so it compares equal."""
    d = bytearray(d)
    i = 0
    in_script = False
    while i < len(d):
        op = d[i]
        if op == 0x00 and in_script:
            d[i] = 0x20
        elif op == 0x23:
            in_script = True
        elif op == 0x24:
            in_script = False
        i += 1
        if op in (0x16, 0x17, 0x18, 0x1A, 0x02, 0x2E): i += 4
        elif op in (0x1B, 0x1C): i += 4 + struct.unpack_from('<I', d, i)[0]
        elif op == 0x1E: i += 12
        elif op == 0x1F: i += 8
        elif op in (0x47, 0x48, 0x49): i += 2
        elif op == 0x27: i += 4
        elif op in (0x2F, 0x37, 0x40, 0x41):
            i += 4 + 6 * struct.unpack_from('<I', d, i)[0]
    return bytes(d)


def main(dirs):
    files = [os.path.join(r, f) for d in dirs for r, _, fs in os.walk(d) for f in fs if f.lower().endswith('.qb')]
    for f in files:
        qbdec.harvest(open(f, 'rb').read())
    ok = skipped = bad = 0
    for f in sorted(files):
        orig = open(f, 'rb').read()
        text = qbdec.Dec(orig).run()
        try:
            body, _ = qbc.Compiler().compile(text)
        except SyntaxError as e:
            skipped += 1
            if 'not supported' not in str(e):
                print(f'COMPILE ERROR {f}: {e}')
            continue
        want = normalize_begin(orig[:code_end(orig)])
        if body == want:
            ok += 1
        else:
            bad += 1
            n = next((k for k in range(min(len(body), len(want))) if body[k] != want[k]), min(len(body), len(want)))
            print(f'MISMATCH {f} at {n:#x}: got {body[n:n+12].hex()} want {want[n:n+12].hex()}')
    print(f'{ok} identical, {bad} mismatched, {skipped} skipped (unsupported syntax)')


if __name__ == '__main__':
    main(sys.argv[1:])
