# QB scripting gotchas

Things that bit us writing `mod/doakickflip.q`.

- A bare global name in an expression is its checksum, not its value
  (`<x> = some_global` gives `some_global`). Parentheses evaluate it, but
  reading/writing global *strings* didn't work in either form. Keep strings in
  element tags (`SetTags` / `GetTags`) instead.
- Script `printf` is a no-op in this build (`Printf` → `0x5b9760`, a
  `return true` stub), and `ScriptAssert` formats and discards. For debugging,
  `doakickflip_debug = 1` shows an overlay with recent events and each entry's
  count, baseline and position. It uses `z_priority = 10000` so it draws over
  the pause menu, which also freezes it for screenshots.
- `"\n"` in `.q` source is needed for the game's newline escape; `"
"`
  compiles to a raw newline character.
- Keywords can't be used as parameter names (`script = ...`); `qbc.py`
  now rejects that.
- Don't use `>=` or `<=`. The bytecode has opcodes for them (`0x13` / `0x15`),
  but none of the 810 stock scripts use them, and a condition with `>=` froze
  the game. For integers write `a > (b - 1)`. `qbc.py` rejects them.
