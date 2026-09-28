// doakickflip: high combo mode where chat picks the tricks.
// Appended to qb\game\menu\gamemenu_pause.qb by tools/build_mod.py.
//
// "Do a Kickflip!" in the free skate pause menu shows a list of requested
// tricks (the stock Skate-Tricks stack, bottom right), each with the name of
// whoever asked for it. Requests come from data\doakickflip\inbox.qb, which
// THUG Pro's file redirect resolves to <THUG Pro>\User\Data\doakickflip\inbox.qb
// (tools/call_trick.py and tools/fake_chat.py write it):
//     doakickflip_inbox = [ { seq = N trick = "Kickflip" user = "name" } ... ]
//     doakickflip_inbox_settings = { max_pending = 8 }
// The settings are re-read every poll, so the cap can change while playing.
//
// A request clears as soon as the trick is done, mid-combo: every frame we ask
// how many times the trick is in the current combo (GetNumberOfTrickOccurrences,
// the same check levels use for "do a kickflip over X" goals) and compare
// against the count when the request came in. It's a global function (it finds
// the skater itself); called as "skater: GetNumberOfTrickOccurrences" its
// result never reaches our script. If
// more than max_pending requests pile up, the skater bails and the
// list clears. The score is just the normal combo score.
//
// Each request is an entry in the stock tetris_tricks_menu, tagged with
// trick / baseline / removing, so the menu's children are the pending queue.

doakickflip_active = 0
doakickflip_last_seq = 0
// 1 = show a debug overlay (top left, drawn above the pause menu): the last
// few events, then one line per entry with its count, baseline and position.
// Pause to freeze it for a screenshot.
doakickflip_debug = 0

script doakickflip_pause_menu_items
    if (doakickflip_active = 1)
        make_thugpro_menu_item {
        text = "Stop Do a Kickflip!"
        id = menu_doakickflip_end
        pad_choose_script = menu_select
        pad_choose_params = { menu_select_script = doakickflip_end }
        }
    else
        make_thugpro_menu_item {
        text = "Do a Kickflip!"
        id = menu_doakickflip_start
        pad_choose_script = menu_select
        pad_choose_params = { menu_select_script = doakickflip_start }
        }
    endif
endscript

script doakickflip_start
    doakickflip_create_ui
    doakickflip_load_inbox
    doakickflip_skip_old_requests
    change doakickflip_active = 1
    KillSpawnedScript name = doakickflip_loop
    SpawnScript doakickflip_loop
    exit_pause_menu
endscript

script doakickflip_end
    exit_pause_menu
    change doakickflip_active = 0
    KillSpawnedScript name = doakickflip_loop
    doakickflip_destroy_ui
endscript

// The list reuses the stock Skate-Tricks UI: create_tetris_menu for the
// menu, and each request is built the way the engine builds a Skate-Tricks
// entry (THUGPro.exe ~0x570100): a ContainerElement (dims 100x20) in
// tetris_tricks_menu with child 0 = trick name (newtrickfont) and child 1 =
// button glyphs from goal_tetris_trick_text, animated by the stock
// goal_tetris_* scripts.
script doakickflip_create_ui
    doakickflip_destroy_ui
    create_tetris_menu
endscript

script doakickflip_destroy_ui
    if ScreenElementExists id = tetris_menu_anchor
        DestroyScreenElement id = tetris_menu_anchor
    endif
    if ScreenElementExists id = doakickflip_debug_text
        DestroyScreenElement id = doakickflip_debug_text
    endif
endscript

// line: remember as the most recent debug event (keeps the last four).
// Kept as tags on the list's anchor element: a bare global name in an
// expression is just its checksum, and string globals didn't work either.
script doakickflip_log
    if NOT ScreenElementExists id = tetris_menu_anchor
        return
    endif
    <ev1> = ""
    <ev2> = ""
    <ev3> = ""
    tetris_menu_anchor: GetTags
    tetris_menu_anchor: SetTags ev4 = <ev3> ev3 = <ev2> ev2 = <ev1> ev1 = <line>
endscript

// Redrawn every poll: last four events, then one line per entry.
script doakickflip_debug_draw
    <ev1> = ""
    <ev2> = ""
    <ev3> = ""
    <ev4> = ""
    if ScreenElementExists id = tetris_menu_anchor
        tetris_menu_anchor: GetTags
    endif
    FormatText TextName = lines "%d\\n%c\\n%b\\n%a\\n--" a = <ev1> b = <ev2> c = <ev3> d = <ev4>
    if GetScreenElementChildren id = tetris_tricks_menu
        GetArraySize <children>
        if (<array_size> > 0)
            <i> = 0
            begin
                <child> = (<children> [ <i> ])
                <child>: GetTags
                Number_Of_Occurrences = -1
                GetNumberOfTrickOccurrences TrickText = <trick>
                GetScreenElementPosition id = <child>
                <x> = (<ScreenElementPos>.(1.0, 0.0))
                <y> = (<ScreenElementPos>.(0.0, 1.0))
                FormatText TextName = lines "%l\\n%t occ=%o base=%b rm=%r pos=%x,%y" l = <lines> t = <trick> o = <Number_Of_Occurrences> b = <baseline> r = <removing> x = <x> y = <y>
                <i> = (<i> + 1)
            repeat <array_size>
        endif
    endif
    if ScreenElementExists id = doakickflip_debug_text
        DestroyScreenElement id = doakickflip_debug_text
    endif
    SetScreenElementLock id = root_window off
    CreateScreenElement {
    type = TextBlockElement
    parent = root_window
    id = doakickflip_debug_text
    font = small
    text = <lines>
    pos = (20.0, 60.0)
    just = [ left top ]
    internal_just = [ left top ]
    dims = (600.0, 300.0)
    scale = 0.6
    rgba = [ 128 128 0 128 ]
    z_priority = 10000
    }
endscript

script doakickflip_load_inbox
    UnloadQB "doakickflip\\inbox.qb"
    LoadQB "doakickflip\\inbox.qb"
endscript

// Mark everything already in the inbox as handled, so only requests made after
// the mode starts show up.
script doakickflip_skip_old_requests
    change doakickflip_last_seq = 0
    GetArraySize doakickflip_inbox
    if (<array_size> > 0)
        <i> = 0
        begin
            if (((doakickflip_inbox [ <i> ]).seq) > doakickflip_last_seq)
                change doakickflip_last_seq = ((doakickflip_inbox [ <i> ]).seq)
            endif
            <i> = (<i> + 1)
        repeat <array_size>
    endif
endscript

// Every frame: clear done tricks. Every 6th frame: pick up new requests.
script doakickflip_loop
    <poll> = 0
    begin
        if (doakickflip_active = 0)
            break
        endif
        doakickflip_check_done
        <poll> = (<poll> + 1)
        if (<poll> > 5)
            <poll> = 0
            doakickflip_load_inbox
            doakickflip_take_new_requests
            doakickflip_refresh_layout
            if (doakickflip_debug = 1)
                doakickflip_debug_draw
            endif
        endif
        wait 1 gameframe
    repeat
endscript

// A VMenu only lays its children out when it's locked; locking on then off
// re-runs the layout (same as refresh_scrolling_menu in net_vault_menu.q).
// Done every poll so entries reflow after adds (their grow-in animation starts
// at scale 0) and after removed entries finish animating out.
script doakickflip_refresh_layout
    if ScreenElementExists id = tetris_tricks_menu
        SetScreenElementLock id = tetris_tricks_menu on
        SetScreenElementLock id = tetris_tricks_menu off
    endif
endscript

// Requests are in seq order (oldest first); add every one not yet shown.
script doakickflip_take_new_requests
    GetArraySize doakickflip_inbox
    if (<array_size> > 0)
        <i> = 0
        begin
            if (((doakickflip_inbox [ <i> ]).seq) > doakickflip_last_seq)
                <req> = (doakickflip_inbox [ <i> ])
                change doakickflip_last_seq = (<req>.seq)
                doakickflip_add_request trick = (<req>.trick) user = (<req>.user)
            endif
            <i> = (<i> + 1)
        repeat <array_size>
    endif
    doakickflip_count_pending
    <max> = ((doakickflip_inbox_settings).max_pending)
    if (<pending> > <max>)
        doakickflip_overflow
    else
        // like the stock Skate-Tricks stack: red from 75% of the cap
        // (pending * 4 >= max * 3, written with > because the game's scripts
        // never use >= / <= and using >= froze the game)
        if ((<pending> * 4) > ((<max> * 3) - 1))
            doakickflip_color_pending color_script = goal_tetris_turn_trick_red
        else
            doakickflip_color_pending color_script = goal_tetris_turn_trick_white
        endif
    endif
endscript

script doakickflip_color_pending
    if GetScreenElementChildren id = tetris_tricks_menu
        GetArraySize <children>
        if (<array_size> > 0)
            <i> = 0
            begin
                <child> = (<children> [ <i> ])
                <child>: GetTags
                if (<removing> = 0)
                    RunScriptOnScreenElement id = <child> <color_script> Params = { id = <child> }
                endif
                <i> = (<i> + 1)
            repeat <array_size>
        endif
    endif
endscript

// trick, user
script doakickflip_add_request
    Number_Of_Occurrences = 0
    GetNumberOfTrickOccurrences TrickText = <trick>
    <baseline> = <Number_Of_Occurrences>
    doakickflip_find_key_combo trick = <trick>
    if (doakickflip_debug = 1)
        // everything FormatText references must exist
        <dbg_combo> = none
        if GotParam key_combo
            <dbg_combo> = <key_combo>
        endif
        <trick_checksum> = none
        <cat_num> = none
        GoalManager_GetTrickFromKeyCombo key_combo = Air_SquareL
        FormatText TextName = dbg "add %t base=%b combo=%k | Air_SquareL -> %x / %n" t = <trick> b = <baseline> k = <dbg_combo> x = <trick_checksum> n = <cat_num>
        doakickflip_log line = <dbg>
    endif
    FormatText TextName = label "%t \\c1%u\\c0" t = <trick> u = <user>
    CreateScreenElement {
    type = ContainerElement
    parent = tetris_tricks_menu
    dims = (100.0, 20.0)
    }
    <entry> = <id>
    CreateScreenElement {
    type = TextElement
    parent = <entry>
    font = newtrickfont
    text = <label>
    not_focusable
    }
    if GotParam key_combo
        if GotParam double_tap
            <buttons> = (goal_tetris_trick_text_double_tap.<key_combo>)
        else
            <buttons> = (goal_tetris_trick_text.<key_combo>)
        endif
        CreateScreenElement {
        type = TextElement
        parent = <entry>
        font = small
        text = <buttons>
        not_focusable
        }
        RunScriptOnScreenElement id = <entry> goal_tetris_add_trick Params = { id = <entry> }
    else
        RunScriptOnScreenElement id = <entry> goal_tetris_add_trick Params = { id = <entry> no_key_combo }
    endif
    <entry>: SetTags trick = <trick> baseline = <baseline> removing = 0 last_occ = <baseline>
endscript

// Which key combo is this trick (by display name) bound to? For each air/lip
// slot, GoalManager_GetTrickFromKeyCombo returns the slot trick's name
// (trick_string) and its double-tap trick's name (extra_trick_string, e.g.
// Method on the Melon slot); then the special slots are checked the same way.
// Returns key_combo (plus double_tap), or nothing for tricks that aren't in any
// slot (manuals, grinds); those are shown without buttons. Names are compared
// as checksums (case-insensitive, and local strings vs strings don't compare).
script doakickflip_find_key_combo
    FormatText ChecksumName = want "%s" s = <trick>
    GetArraySize doakickflip_key_combos
    <i> = 0
    begin
        <combo> = (doakickflip_key_combos [ <i> ])
        RemoveParameter trick_string
        RemoveParameter extra_trick_string
        GoalManager_GetTrickFromKeyCombo key_combo = <combo>
        if GotParam trick_string
            FormatText ChecksumName = have "%s" s = <trick_string>
            if (<want> = <have>)
                return key_combo = <combo>
            endif
        endif
        if GotParam extra_trick_string
            if StructureContains structure = (goal_tetris_trick_text_double_tap) <combo>
                FormatText ChecksumName = have "%s" s = <extra_trick_string>
                if (<want> = <have>)
                    return key_combo = <combo> double_tap
                endif
            endif
        endif
        <i> = (<i> + 1)
    repeat <array_size>
    GetArraySize doakickflip_special_key_combos
    <i> = 0
    begin
        <combo> = (doakickflip_special_key_combos [ <i> ])
        RemoveParameter trick_string
        GoalManager_GetTrickFromKeyCombo special key_combo = <combo>
        if GotParam trick_string
            FormatText ChecksumName = have "%s" s = <trick_string>
            if (<want> = <have>)
                return key_combo = <combo>
            endif
        endif
        <i> = (<i> + 1)
    repeat <array_size>
endscript

doakickflip_key_combos = [
Air_SquareU Air_SquareD Air_SquareL Air_SquareR
Air_SquareUL Air_SquareUR Air_SquareDL Air_SquareDR
Air_CircleU Air_CircleD Air_CircleL Air_CircleR
Air_CircleUL Air_CircleUR Air_CircleDL Air_CircleDR
Air_U_U_Square Air_D_D_Square Air_L_L_Square Air_R_R_Square
Air_U_U_Circle Air_D_D_Circle Air_L_L_Circle Air_R_R_Circle
Lip_TriangleU Lip_TriangleD Lip_TriangleL Lip_TriangleR
Lip_TriangleUL Lip_TriangleUR Lip_TriangleDL Lip_TriangleDR
]

doakickflip_special_key_combos = [
SpAir_D_L_Circle SpAir_D_L_Square SpAir_D_R_Circle SpAir_D_R_Square
SpAir_D_U_Circle SpAir_D_U_Square SpAir_L_D_Circle SpAir_L_D_Square
SpAir_L_R_Circle SpAir_L_R_Square SpAir_L_U_Circle SpAir_L_U_Square
SpAir_R_D_Circle SpAir_R_D_Square SpAir_R_L_Circle SpAir_R_L_Square
SpAir_R_U_Circle SpAir_R_U_Square SpAir_U_D_Circle SpAir_U_D_Square
SpAir_U_L_Circle SpAir_U_L_Square SpAir_U_R_Circle SpAir_U_R_Square
SpGrind_D_L_Triangle SpGrind_D_R_Triangle SpGrind_D_U_Triangle SpGrind_L_D_Triangle
SpGrind_L_R_Triangle SpGrind_L_U_Triangle SpGrind_R_D_Triangle SpGrind_R_L_Triangle
SpGrind_R_U_Triangle SpGrind_U_D_Triangle SpGrind_U_L_Triangle SpGrind_U_R_Triangle
SpLip_D_L_Triangle SpLip_D_R_Triangle SpLip_D_U_Triangle SpLip_L_D_Triangle
SpLip_L_R_Triangle SpLip_L_U_Triangle SpLip_R_D_Triangle SpLip_R_L_Triangle
SpLip_R_U_Triangle SpLip_U_D_Triangle SpLip_U_L_Triangle SpLip_U_R_Triangle
SpLip_U_U_Triangle SpMan_D_L_Triangle SpMan_D_R_Triangle SpMan_D_U_Triangle
SpMan_L_D_Triangle SpMan_L_R_Triangle SpMan_L_U_Triangle SpMan_R_D_Triangle
SpMan_R_L_Triangle SpMan_R_U_Triangle SpMan_U_D_Triangle SpMan_U_L_Triangle
SpMan_U_R_Triangle
]

script doakickflip_check_done
    if NOT ScreenElementExists id = tetris_tricks_menu
        return
    endif
    if NOT GetScreenElementChildren id = tetris_tricks_menu
        return
    endif
    GetArraySize <children>
    if (<array_size> > 0)
        <i> = 0
        begin
            <child> = (<children> [ <i> ])
            <child>: GetTags
            if (<removing> = 0)
                Number_Of_Occurrences = 0
                GetNumberOfTrickOccurrences TrickText = <trick>
                if NOT (<Number_Of_Occurrences> = <last_occ>)
                    <child>: SetTags last_occ = <Number_Of_Occurrences>
                    if (doakickflip_debug = 1)
                        FormatText TextName = dbg "occ %t %o (base %b)" t = <trick> o = <Number_Of_Occurrences> b = <baseline>
                        doakickflip_log line = <dbg>
                    endif
                endif
                if (<Number_Of_Occurrences> > <baseline>)
                    <child>: SetTags removing = 1
                    if (doakickflip_debug = 1)
                        FormatText TextName = dbg "clear %t" t = <trick>
                        doakickflip_log line = <dbg>
                    endif
                    SpawnScript goal_tetris_play_trick_removed_sound
                    RunScriptOnScreenElement id = <child> goal_tetris_remove_trick Params = { id = <child> }
                else
                    // the combo ended (landed or bailed): counts start over
                    if (<Number_Of_Occurrences> < <baseline>)
                        <child>: SetTags baseline = <Number_Of_Occurrences>
                    endif
                endif
            endif
            <i> = (<i> + 1)
        repeat <array_size>
    endif
endscript

// returns pending = number of requests not yet done
script doakickflip_count_pending
    <pending> = 0
    if ScreenElementExists id = tetris_tricks_menu
        if GetScreenElementChildren id = tetris_tricks_menu
            GetArraySize <children>
            if (<array_size> > 0)
                <i> = 0
                begin
                    <child> = (<children> [ <i> ])
                    <child>: GetTags
                    if (<removing> = 0)
                        <pending> = (<pending> + 1)
                    endif
                    <i> = (<i> + 1)
                repeat <array_size>
            endif
        endif
    endif
    return pending = <pending>
endscript

// Too many requests piled up: bail and start the list over.
script doakickflip_overflow
    doakickflip_log line = "overflow: bail"
    MakeSkaterGoto YawBail
    if GetScreenElementChildren id = tetris_tricks_menu
        GetArraySize <children>
        if (<array_size> > 0)
            <i> = 0
            begin
                <child> = (<children> [ <i> ])
                <child>: SetTags removing = 1
                RunScriptOnScreenElement id = <child> goal_tetris_turn_trick_red Params = { id = <child> }
                RunScriptOnScreenElement id = <child> goal_tetris_remove_trick Params = { id = <child> }
                <i> = (<i> + 1)
            repeat <array_size>
        endif
    endif
endscript
