# Notes

Everything we've learned so far about THUG Pro's script data, the Skate-Tricks
goal, and building the "Do a Kickflip!" mode. The game data itself is never
committed; run `tools/extract.py` to regenerate `extracted/` locally and follow
along.

Versions this was worked out against: THUG Pro beta 0.7.0.0 (shown in the
launcher; released 2023-10-19 per https://thugpro.com/changelog/). The bundled
`changelog.txt` stopped being updated at 0.6.0.11 (the site lists .12–.19
after it), so don't go by it. On a
retail PC THUG2 install.

- [todo.md](todo.md): what's next and open questions
- [frontend.md](frontend.md): the app's UI: where the prototype is, decisions, next steps
- [architecture.md](architecture.md): how the real app gets built: stack, testing, what's decided and open
- [high-combo-mode.md](high-combo-mode.md): how the current mode works
- [qb-gotchas.md](qb-gotchas.md): QB scripting pitfalls
- [running.md](running.md): launching, logging, finding crashes
- [formats.md](formats.md): PRE/PRX archives, QB keys, QB bytecode
- [scripts.md](scripts.md): where things live in the game's scripts
- [skate-tricks-goal.md](skate-tricks-goal.md): the stock Skate-Tricks goal and its engine internals
- [file-redirect.md](file-redirect.md): THUG Pro's `Data\` file redirect and `User\Data`
- [input-channels.md](input-channels.md): ways to get live input into the game
