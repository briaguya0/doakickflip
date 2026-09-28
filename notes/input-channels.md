# Channels for live input

- **Chat commands**: `global_cmd_array` in `qb/thugpro/command_parser.q` maps
  `/COMMAND` strings to scripts. You can type chat yourself only
  `if InNetGame`. Incoming messages are parsed as commands only when the sender
  is in `whitelist_player_array` (`qb/engine/menu/consolemessage.q`). This is the
  likely network path.
- **Registry**: THUG Pro exposes `GetRegKeyValue` / `SetRegKeyValue` /
  `RegKeyExist` to scripts (it keeps its settings in `HKCU\Software\THUG Pro`).
  Rejected: messy for Windows users.
- **File inbox** (chosen next): poll `LoadQB` of a small `.qb` in `User\Data`.
- No script-level "read a text file" function exists in `THUGPro.exe` or
  `thugpro.dll`. THUG Pro's own script functions include `StripStringColorCodes`,
  `ResizeStringInPlace`, `LookupChecksumName`, `CastChecksumToInteger`,
  `SplitConsoleMessage`, `GetSaveDirectoryListing`, `FindSpawnedScriptWithID`.
