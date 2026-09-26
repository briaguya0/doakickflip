#!/usr/bin/env python3
"""Decompile THUG2 / THUG Pro .qb bytecode into readable QB-ish text.

Usage: qbdec.py [-n NAMES_DIR ...] FILE.qb [FILE.qb ...]
  -n DIR  extra directory of .qb files to harvest checksum names from
          (every input file's own name table is always used)
Output goes next to each input as FILE.q.
"""
import os
import re
import struct
import sys
import zlib

NAMES = {}


def harvest(data):
    i = data.find(b'\x2b')
    while i != -1:
        if i + 5 < len(data):
            end = data.find(b'\0', i + 5)
            if end != -1 and end - (i + 5) < 128:
                raw = data[i + 5:end]
                crc = struct.unpack_from('<I', data, i + 1)[0]
                if raw and (zlib.crc32(raw.lower()) ^ 0xFFFFFFFF) == crc:
                    NAMES.setdefault(crc, raw.decode('latin-1'))
        i = data.find(b'\x2b', i + 1)


IDENT = re.compile(r'[A-Za-z_][A-Za-z0-9_]*|[0-9]+[A-Za-z_][A-Za-z0-9_]*')
KEYWORDS = {'script', 'endscript', 'if', 'else', 'elseif', 'endif', 'begin', 'repeat',
            'break', 'return', 'NOT', 'switch', 'case', 'default', 'endswitch'}


def name(crc):
    n = NAMES.get(crc)
    if n is None or not IDENT.fullmatch(n) or n in KEYWORDS or re.fullmatch(r'\d+e\d*|inf|nan', n, re.I):
        return f'#{crc:08x}'
    return n


def fstr(v):
    for n in range(1, 10):
        t = f'{v:.{n}g}'
        if struct.pack('<f', float(t)) == struct.pack('<f', v):
            break
    return repr(float(t))


def qstr(s, q='"'):
    s = s.replace('\\', '\\\\').replace(q, '\\' + q).replace('\n', '\\n').replace('\r', '\\r')
    return q + s + q


class Dec:
    def __init__(self, data):
        self.d = data
        self.i = 0
        self.out = []
        self.line = []
        self.indent = 0
        self.in_script = False
        self.ended_nl = False

    def u8(self):
        v = self.d[self.i]; self.i += 1; return v

    def u16(self):
        v = struct.unpack_from('<H', self.d, self.i)[0]; self.i += 2; return v

    def u32(self):
        v = struct.unpack_from('<I', self.d, self.i)[0]; self.i += 4; return v

    def i32(self):
        v = struct.unpack_from('<i', self.d, self.i)[0]; self.i += 4; return v

    def f32(self):
        v = struct.unpack_from('<f', self.d, self.i)[0]; self.i += 4; return v

    def s(self):
        n = self.u32()
        raw = self.d[self.i:self.i + n]; self.i += n
        return (raw[:-1] if raw.endswith(b'\0') else raw).decode('latin-1')

    def emit(self, t):
        if not self.line:
            self.line_indent = self.indent
        self.line.append(t)

    def newline(self):
        txt = ' '.join(self.line).replace('( ', '(').replace(' )', ')').replace(' . ', '.').replace(' :', ':')
        self.out.append('    ' * max(self.line_indent, 0) + txt if self.line else '')
        self.line = []

    def open_(self, t):
        self.emit(t); self.indent += 1

    def close(self, t):
        self.indent -= 1; self.emit(t)

    def run(self):
        d = self.d
        while self.i < len(d):
            op = self.u8()
            if op not in (0x00, 0x01, 0x2B):
                self.ended_nl = False
            if op == 0x00:
                if not self.in_script:
                    break
                self.open_('begin')  # some scripts encode begin as 0x00
            elif op == 0x01: self.newline(); self.ended_nl = True; continue
            elif op == 0x02: n = self.u32(); self.newline(); self.emit(f'@{n}'); continue  # end of line + line number
            elif op == 0x03: self.emit('{')
            elif op == 0x04: self.emit('}')
            elif op == 0x05: self.emit('[')
            elif op == 0x06: self.emit(']')
            elif op == 0x07: self.emit('=')
            elif op == 0x08: self.emit('.')
            elif op == 0x09: self.emit(',')
            elif op == 0x0A: self.emit('-')
            elif op == 0x0B: self.emit('+')
            elif op == 0x0C: self.emit('/')
            elif op == 0x0D: self.emit('*')
            elif op == 0x0E: self.emit('(')
            elif op == 0x0F: self.emit(')')
            elif op == 0x11: self.emit('==')
            elif op == 0x12: self.emit('<')
            elif op == 0x13: self.emit('<=')
            elif op == 0x14: self.emit('>')
            elif op == 0x15: self.emit('>=')
            elif op == 0x16: self.emit(name(self.u32()))
            elif op == 0x17: self.emit(str(self.i32()))
            elif op == 0x18: self.emit(f'0x{self.u32():08x}')
            elif op == 0x1A: self.emit(fstr(self.f32()))
            elif op == 0x1B: self.emit(qstr(self.s()))
            elif op == 0x1C: self.emit(qstr(self.s(), "'"))
            elif op == 0x1E: self.emit('(%s, %s, %s)' % (fstr(self.f32()), fstr(self.f32()), fstr(self.f32())))
            elif op == 0x1F: self.emit('(%s, %s)' % (fstr(self.f32()), fstr(self.f32())))
            elif op == 0x20: self.open_('begin')
            elif op == 0x21: self.close('repeat')
            elif op == 0x22: self.emit('break')
            elif op == 0x23: self.indent = 0; self.open_('script'); self.in_script = True
            elif op == 0x24: self.indent = 1; self.close('endscript'); self.in_script = False
            elif op in (0x25, 0x47):
                if op == 0x47: self.u16()
                self.open_('if')
            elif op in (0x26, 0x48):
                if op == 0x48: self.u16()
                self.close('else'); self.indent += 1
            elif op == 0x27:
                self.u16(); self.u16()
                self.close('elseif'); self.indent += 1
            elif op == 0x28: self.close('endif')
            elif op == 0x29: self.emit('return')
            elif op == 0x2B: self.i = self.d.index(b'\0', self.i + 4) + 1; continue
            elif op == 0x2C: self.emit('<...>')
            elif op == 0x2D:
                if d[self.i] == 0x16:
                    self.i += 1; self.emit(f'<{name(self.u32())}>')
                else:
                    self.emit('<>')
            elif op == 0x2E: self.u32()
            elif op in (0x2F, 0x37, 0x40, 0x41):
                n = self.u32()
                self.i += 6 * n
                self.emit({0x2F: 'Random', 0x37: 'Random2', 0x40: 'RandomNoRepeat', 0x41: 'RandomPermute'}[op] + f'({n} choices:')
            elif op in (0x30, 0x38): self.emit('RandomRange')
            elif op == 0x32: self.emit('||')
            elif op == 0x33: self.emit('&&')
            elif op == 0x39: self.emit('NOT')
            elif op == 0x3C: self.emit('switch'); self.indent += 2
            elif op == 0x3D: self.indent -= 2; self.emit('endswitch')
            elif op == 0x3E: self.close('case'); self.indent += 1
            elif op == 0x3F: self.close('default'); self.indent += 1
            elif op == 0x42: self.emit(':')
            elif op == 0x49: self.u16()
            else:
                if self.line: self.newline()
                self.out.append(f'// !!! unknown opcode {op:#04x} at {self.i - 1:#x}, stopping')
                break
        if self.line:
            self.newline()
            self.ended_nl = False
        return '\n'.join(self.out) + ('\n' if self.ended_nl else '')


def main(argv):
    extra, files = [], []
    it = iter(argv)
    for a in it:
        if a == '-n':
            extra.append(next(it))
        else:
            files.append(a)
    if not files:
        sys.exit(__doc__)
    for d in extra:
        for root, _, fs in os.walk(d):
            for f in fs:
                if f.lower().endswith('.qb'):
                    harvest(open(os.path.join(root, f), 'rb').read())
    for f in files:
        harvest(open(f, 'rb').read())
    for f in files:
        text = Dec(open(f, 'rb').read()).run()
        open(os.path.splitext(f)[0] + '.q', 'w').write(text)
        bad = text.count('!!! unknown')
        unk = text.count('#')
        print(f'{f}: {len(text.splitlines())} lines, {unk} unresolved-ish, {"STOPPED EARLY" if bad else "ok"}')


if __name__ == '__main__':
    main(sys.argv[1:])
