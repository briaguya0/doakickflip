#!/usr/bin/env python3
"""Unpack / patch Neversoft PRE/PRX archives (THUG2 / THUG Pro, version 3).

Usage: prx.py OUT_DIR ARCHIVE.prx [ARCHIVE.prx ...]
"""
import os
import struct
import sys
import zlib


def lzss_decompress(src, out_size):
    N, F, THRESHOLD = 4096, 18, 2
    ring = bytearray(N)
    r = N - F
    out = bytearray()
    i = 0
    flags = 0
    while len(out) < out_size and i < len(src):
        flags >>= 1
        if not flags & 0x100:
            flags = src[i] | 0xFF00
            i += 1
        if flags & 1:
            c = src[i]
            i += 1
            out.append(c)
            ring[r] = c
            r = (r + 1) & (N - 1)
        else:
            if i + 1 >= len(src):
                break
            pos = src[i] | ((src[i + 1] & 0xF0) << 4)
            length = (src[i + 1] & 0x0F) + THRESHOLD
            i += 2
            for k in range(length + 1):
                c = ring[(pos + k) & (N - 1)]
                out.append(c)
                ring[r] = c
                r = (r + 1) & (N - 1)
    return bytes(out[:out_size])


def entries(data):
    """Yield (name, size, csize, crc, stored_bytes) for each archive entry."""
    _total, version, magic, count = struct.unpack_from('<IHHI', data, 0)
    if magic != 0xABCD or version != 3:
        raise ValueError(f'unexpected header version={version} magic={magic:#x}')
    off = 12
    for _ in range(count):
        size, csize, name_len, crc = struct.unpack_from('<IIII', data, off)
        off += 16
        name = data[off:off + name_len].split(b'\0')[0].decode('latin-1')
        off += name_len
        stored = csize if csize else size
        yield name, size, csize, crc, data[off:off + stored]
        off += (stored + 3) & ~3


def replace(src_path, dst_path, replacements):
    """Copy an archive, swapping in new contents (stored uncompressed) for the named entries.

    replacements maps archive entry name (e.g. 'qb\\game\\foo.qb', case-insensitive) to bytes.
    """
    data = open(src_path, 'rb').read()
    todo = {k.lower(): v for k, v in replacements.items()}
    out = bytearray(12)
    count = 0
    for name, size, csize, crc, blob in entries(data):
        new = todo.pop(name.lower(), None)
        if new is not None:
            size, csize, blob = len(new), 0, new
        raw_name = name.encode('latin-1') + b'\0'
        raw_name += b'\0' * (-len(raw_name) % 4)
        out += struct.pack('<IIII', size, csize, len(raw_name), crc) + raw_name
        out += blob + b'\0' * (-len(blob) % 4)
        count += 1
    if todo:
        raise KeyError(f'entries not found in {src_path}: {sorted(todo)}')
    struct.pack_into('<IHHI', out, 0, len(out), 3, 0xABCD, count)
    with open(dst_path, 'wb') as f:
        f.write(out)


def unpack(path, out_dir):
    data = open(path, 'rb').read()
    _total, version, magic, count = struct.unpack_from('<IHHI', data, 0)
    if magic != 0xABCD or version != 3:
        raise ValueError(f'{path}: unexpected header version={version} magic={magic:#x}')
    off = 12
    for _ in range(count):
        size, csize, name_len, _crc = struct.unpack_from('<IIII', data, off)
        off += 16
        name = data[off:off + name_len].split(b'\0')[0].decode('latin-1')
        off += name_len
        stored = csize if csize else size
        blob = data[off:off + stored]
        off += (stored + 3) & ~3
        body = lzss_decompress(blob, size) if csize else blob
        dest = os.path.join(out_dir, *name.replace('\\', '/').split('/'))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, 'wb') as f:
            f.write(body)
    return count


if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    out = sys.argv[1]
    for p in sys.argv[2:]:
        print(f'{p}: {unpack(p, out)} files')
