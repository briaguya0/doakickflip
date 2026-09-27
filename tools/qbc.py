#!/usr/bin/env python3
"""Compile QB text (the syntax qbdec.py emits) into THUG2 / THUG Pro .qb bytecode.

Usage: qbc.py IN.q OUT.qb

Supported: script/endscript, if/else/endif, begin/repeat/break, return,
structs, arrays, pairs/vectors, strings ("..." and '...'), ints, hex ints,
floats, <param>, <...>, NOT/&&/||, comparison and arithmetic operators,
member access (a.b), object prefix (obj: Func), raw checksums (#1234abcd),
line-numbered line breaks (a line starting with @N).
Not supported (yet): switch/case, elseif, Random*.
"""
import re
import struct
import sys
import zlib

TOKEN_RE = re.compile(r'''
    (?P<nl>\n)
  | (?P<ws>[ \t\r]+)
  | (?P<comment>//[^\n]*)
  | (?P<str>"(?:\\.|[^"\\])*")
  | (?P<lstr>'(?:\\.|[^'\\])*')
  | (?P<allargs><\.\.\.>)
  | (?P<arg><[^<>\s=]+>)
  | (?P<lineno>@\d+)
  | (?P<crc>\#[0-9a-fA-F]{8})
  | (?P<hex>0x[0-9a-fA-F]+)
  | (?P<float>(?:-?\d+\.\d*(?:e[+-]?\d+)?|-?\d+e[+-]?\d+|-?inf|nan)(?![\w]))
  | (?P<int>-?\d+(?![\w]))
  | (?P<op>==|<=|>=|&&|\|\||[{}\[\]=.,+\-*/():<>])
  | (?P<name>[^\s{}\[\]=.,+*/():<>"']+)
''', re.X)

SIMPLE = {
    '{': 0x03, '}': 0x04, '[': 0x05, ']': 0x06, '=': 0x07, '.': 0x08, ',': 0x09,
    '-': 0x0A, '+': 0x0B, '/': 0x0C, '*': 0x0D, '(': 0x0E, ')': 0x0F,
    '==': 0x11, '<': 0x12, '<=': 0x13, '>': 0x14, '>=': 0x15,
    '||': 0x32, '&&': 0x33, ':': 0x42,
}
KEYWORDS = {'begin': 0x20, 'repeat': 0x21, 'break': 0x22, 'return': 0x29, 'NOT': 0x39}


def qbkey(s):
    return zlib.crc32(s.lower().encode('latin-1')) ^ 0xFFFFFFFF


def unescape(body):
    return re.sub(r'\\(.)', lambda m: {'n': '\n', 'r': '\r'}.get(m.group(1), m.group(1)), body)


def tokenize(src):
    pos = 0
    out = []
    while pos < len(src):
        m = TOKEN_RE.match(src, pos)
        if not m:
            line = src.count('\n', 0, pos) + 1
            raise SyntaxError(f'line {line}: cannot tokenize {src[pos:pos + 20]!r}')
        pos = m.end()
        kind = m.lastgroup
        if kind in ('ws', 'comment'):
            continue
        out.append((kind, m.group()))
    return out


class Compiler:
    def __init__(self):
        self.b = bytearray()
        self.names = {}
        self.stack = []  # (kind, offset_field_pos)

    def name(self, s):
        k = qbkey(s)
        self.names.setdefault(k, s)
        self.b += b'\x16' + struct.pack('<I', k)

    def u16_placeholder(self):
        pos = len(self.b)
        self.b += b'\0\0'
        return pos

    def patch(self, field_pos):
        struct.pack_into('<H', self.b, field_pos, len(self.b) - field_pos)

    def number_group(self, toks, i):
        """Match ( num , num [, num] ) -> pair/vector literal."""
        vals = []
        j = i + 1
        while j < len(toks) and toks[j][0] in ('int', 'float'):
            vals.append(float(toks[j][1]))
            j += 1
            if j < len(toks) and toks[j][1] == ',':
                j += 1
                continue
            break
        if 2 <= len(vals) <= 3 and j < len(toks) and toks[j][1] == ')':
            return vals, j + 1
        return None, i

    def compile(self, src):
        toks = tokenize(src)
        i = 0
        self.lineno = 1
        while i < len(toks):
            kind, t = toks[i]
            if kind == 'nl':
                self.lineno += 1
                self.b += b'\x01'
            elif kind == 'str':
                s = unescape(t[1:-1]).encode('latin-1') + b'\0'
                self.b += b'\x1b' + struct.pack('<I', len(s)) + s
            elif kind == 'lstr':
                s = unescape(t[1:-1]).encode('latin-1') + b'\0'
                self.b += b'\x1c' + struct.pack('<I', len(s)) + s
            elif kind == 'lineno':
                # decompiler writes 0x02 N as a line break followed by @N
                if not self.b or self.b[-1] != 0x01:
                    raise SyntaxError(f'line {self.lineno}: @N must start a line')
                self.b[-1] = 0x02
                self.b += struct.pack('<I', int(t[1:]))
            elif kind == 'allargs':
                self.b += b'\x2c'
            elif kind == 'arg':
                self.b += b'\x2d'
                inner = t[1:-1]
                if inner.startswith('#'):
                    self.b += b'\x16' + struct.pack('<I', int(inner[1:], 16))
                else:
                    self.name(inner)
            elif kind == 'crc':
                self.b += b'\x16' + struct.pack('<I', int(t[1:], 16))
            elif kind == 'hex':
                self.b += b'\x18' + struct.pack('<I', int(t, 16))
            elif kind == 'int':
                self.b += b'\x17' + struct.pack('<i', int(t))
            elif kind == 'float':
                self.b += b'\x1a' + struct.pack('<f', float(t))
            elif kind == 'op':
                if t == '(':
                    vals, j = self.number_group(toks, i)
                    if vals:
                        op = 0x1F if len(vals) == 2 else 0x1E
                        self.b += bytes([op]) + struct.pack(f'<{len(vals)}f', *vals)
                        i = j
                        continue
                self.b.append(SIMPLE[t])
            elif kind == 'name':
                nxt = toks[i + 1][1] if i + 1 < len(toks) else None
                if nxt == '=' and t in ('script', 'endscript', 'if', 'else', 'endif', 'begin',
                                        'repeat', 'break', 'return', 'switch', 'case',
                                        'default', 'endswitch', 'elseif'):
                    raise SyntaxError(f'line {self.lineno}: keyword {t!r} used as a name')
                if t == 'script':
                    self.b.append(0x23)
                elif t == 'endscript':
                    if self.stack:
                        raise SyntaxError(f'line {self.lineno}: endscript with open blocks {self.stack}')
                    self.b.append(0x24)
                elif t == 'if':
                    self.b.append(0x47)
                    self.stack.append(('if', self.u16_placeholder(), self.lineno))
                elif t == 'else':
                    if not self.stack or self.stack[-1][0] != 'if':
                        raise SyntaxError(f'line {self.lineno}: else without if')
                    kind0, field, _ = self.stack.pop()
                    self.b.append(0x48)
                    new_field = self.u16_placeholder()
                    self.patch(field)
                    self.stack.append(('else', new_field, self.lineno))
                elif t == 'endif':
                    if not self.stack:
                        raise SyntaxError(f'line {self.lineno}: endif without if')
                    kind0, field, _ = self.stack.pop()
                    self.b.append(0x28)
                    self.patch(field)
                elif t in KEYWORDS:
                    self.b.append(KEYWORDS[t])
                elif t in ('switch', 'case', 'default', 'endswitch', 'elseif') or t.startswith('Random'):
                    raise SyntaxError(f'line {self.lineno}: {t} not supported yet')
                else:
                    self.name(t)
            i += 1
        if self.stack:
            raise SyntaxError(f'unclosed blocks at end of file: {self.stack}')
        body = bytes(self.b)
        table = b''.join(b'\x2b' + struct.pack('<I', k) + s.encode('latin-1') + b'\0'
                         for k, s in self.names.items())
        return body, table


def compile_text(src):
    body, table = Compiler().compile(src)
    return body + table + b'\0'


if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    data = compile_text(open(sys.argv[1]).read())
    open(sys.argv[2], 'wb').write(data)
    print(f'{sys.argv[2]}: {len(data)} bytes')
