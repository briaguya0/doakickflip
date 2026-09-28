# Script layout

Paths inside `extracted/thugpro/` (regenerate with `tools/extract.py`).

- `qb/game/goals/goal_tetris.q`: Skate-Tricks goal. Only a param struct
  (`goal_tetris_genericParams`), init/activate/etc. hooks, the on-screen trick
  list UI, and trick→button-text tables. **All trick selection, timing,
  stacking and completion checks are native code.**
- `qb/game/goal_editor/goal_editor.q`: Create-a-Goal param presets
  (`EditedGoal_ExtraParams_SkateTris`, `..._ComboSkateTris`, `..._TrickTris`)
  and the `cag_key_combos` trick sets.
- `qb/game/net/trick_attack.q`: "High Score Run" (TrickAttack), the pattern
  we copied for starting a goal from the pause menu (`GoalManager_AddGoal`, then
  `GoalManager_EditGoal`, then `GoalManager_ActivateGoal`).
- `qb/game/menu/gamemenu_pause.q`: pause menu. Free skate items live in
  `if GameModeEquals is_singlesession`.
- `qb/game/goal_utilities.q`: `goal_init`, `goal_start`,
  `goal_initialize_skater`.
- `qb/game/Levels.q`: level load adds TrickAttack then `init_goal_manager`
  (`GoalManager_InitializeAllGoals`). Our goal is added later and never
  initialized; that turned out not to matter.
- `qb/thugpro/command_parser.q` / `qb/game/game.q`: chat `/commands` are parsed
  locally before sending (`entered_chat_message`), but the on-screen chat
  keyboard is only offered `if InNetGame`. That's why we went with the pause
  menu.
- Other goal types: `goal_trick_beat.q` (Trick to the Beat).

THUG Pro also loads loose level scripts from
`User\data\levels\<name>\<name>_scripts.qb` (strings in `thugpro.dll`), which
might be another injection route. `THUGPro.exe` still contains the old
`runnow.qb` hook, but it's tied to the "THUG2 Viewer" remote debugger.
