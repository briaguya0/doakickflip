# File formats: PRE/PRX, QB keys, QB bytecode

## PRE / PRX archives (`data/pre/*.prx`)

Little-endian, version 3:

```
header:  u32 total_file_size, u16 version (=3), u16 magic (=0xABCD), u32 file_count
entry:   u32 size, u32 compressed_size (0 = stored), u32 name_len, u32 name_checksum
         name (NUL-terminated, padded to name_len, name_len is a multiple of 4)
         data (compressed_size or size bytes), padded to 4
```

- `name_checksum` is the QB key of the lowercased path (e.g. `qb\thugpro\control_setup.qb`).
- Compression is Neversoft LZSS: 4096-byte ring buffer, initial write position
  4078 (N - F), max match 18, threshold 2, flag byte read LSB first, `1` = literal.
  Match = 2 bytes: `pos = b0 | (b1 & 0xF0) << 4`, `len = (b1 & 0x0F) + 3`.
- Stored (uncompressed) entries are accepted by the game, which is what
  `prx.replace()` writes. A no-op repack reproduces the original byte-for-byte.

## QB key (checksum)

`crc32(name.lower()) ^ 0xFFFFFFFF`, i.e. standard CRC-32 without the final XOR.

## QB bytecode (THUG2 / THUG Pro PC)

A flat token stream; each token is one opcode byte plus operands. Names are
checksums; each file ends with a name table of `0x2B` entries
(`0x2B, u32 checksum, NUL-terminated name`) then `0x00`. Harvest these tables
across all files for name resolution; accept an entry only if
`qbkey(name) == checksum` (matching raw `0x2B` bytes gives false hits).

| op | meaning | operands |
|----|---------|----------|
| 00 | end of file; **inside a script it is an alternate encoding of `begin`** (pairs with 21; ~200 occurrences) | |
| 01 | end of line | |
| 02 | end of line + line number (decompiled as a line starting with `@N`) | u32 |
| 03/04 | `{` / `}` | |
| 05/06 | `[` / `]` | |
| 07 `=`, 08 `.`, 09 `,`, 0A `-`, 0B `+`, 0C `/`, 0D `*`, 0E `(`, 0F `)` | | |
| 11 `==`, 12 `<`, 13 `<=`, 14 `>`, 15 `>=` | | |
| 16 | name | u32 checksum |
| 17 | int | i32 |
| 18 | hex int | u32 |
| 1A | float | f32 |
| 1B | string | u32 len (incl. NUL), bytes |
| 1C | local string | u32 len, bytes |
| 1E | vector | 3×f32 |
| 1F | pair | 2×f32 |
| 20 / 21 / 22 | begin / repeat / break | |
| 23 / 24 | script / endscript | |
| 25 / 26 / 28 | if / else / endif (old form, no offsets) | |
| 27 | elseif | u16, u16 |
| 29 | return | |
| 2B | name table entry | u32 checksum, C string |
| 2C | `<...>` (all args) | |
| 2D | argument prefix, followed by 16 → `<name>` | |
| 2E | jump | u32 |
| 2F / 37 / 40 / 41 | Random / Random2 / RandomNoRepeat / RandomPermute | u32 n, n×u16 weights, n×u32 offsets (**all four** have weights) |
| 30 / 38 | RandomRange / RandomRange2 | |
| 32 `\|\|`, 33 `&&`, 39 `NOT`, 42 `:` | | |
| 3C / 3D / 3E / 3F | switch / endswitch / case / default | |
| 47 | fast if | u16 offset |
| 48 | fast else | u16 offset |
| 49 | short jump (switch/case) | u16 |

Fast if/else offsets are measured **from the u16 field itself**. `if` jumps to
just past the matching `else`'s u16 (or just past `endif`); `else` jumps to
just past `endif`.

Tooling status: `qbdec.py` decompiles all 810 script files from both games.
`qbc.py` compiles the same syntax. `roundtrip.py` decompiles and recompiles
every file and compares the code bytes: 527 are byte-identical, 0 mismatch, and
283 are skipped because the compiler doesn't yet support
`switch`/`elseif`/`Random*`.
