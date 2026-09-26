// doakickflip: Skate-Tricks (Skatetris) from the free skate pause menu.
// Appended to qb\game\menu\gamemenu_pause.qb by tools/build_mod.py.
//
// List mode (doakickflip_start, no menu item): calls out tricks in the order given by
// data\doakickflip\tricks.qb, which THUG Pro's file redirect resolves to
// <THUG Pro>\User\Data\doakickflip\tricks.qb (tools/tricks.py writes it):
//     doakickflip_tricks = [ { goal_tetris_key_combos = [ <combo> ] } ... ]
//
// Live mode ("Do a Kickflip!"): the goal sits idle and calls out one trick per
// request found in data\doakickflip\inbox.qb (User\Data again;
// tools/call_trick.py writes it), polled while the goal is active:
//     doakickflip_inbox = [ { seq = N goal_tetris_key_combos = [ <combo> ] } ... ]
//
// How both work: the engine picks each new trick at random from the goal's
// goal_tetris_key_combos, so we keep that list at exactly one entry. The engine
// runs goal_tetris_add_trick every time it adds a trick; build_mod.py makes that
// call doakickflip_on_trick_added, which either swaps in the next trick (list
// mode) or holds off further adds (live mode).
//
// Holding off adds: the engine adds a trick when its "ms since last add" counter
// exceeds goal param #648d8d2a (no known name; copied from trick_time when the
// goal activates, then shortened by acceleration_percent every
// acceleration_interval cleared tricks). Setting it huge pauses adding; setting
// it low adds on the next frame. Don't use wait_to_add_tricks for this: it makes
// the engine skip the whole Skate-Tricks update, including fading tricks you've
// done in the current combo and the "stack nearly full" red warning.

doakickflip_trick_index = 0
doakickflip_live = 0
doakickflip_pending = 0
doakickflip_last_seq = 0

script doakickflip_pause_menu_items
    if GoalManager_GoalExists name = doakickflip
        if GoalManager_GoalIsActive name = doakickflip
            make_thugpro_menu_item {
            text = "End Skate-Tricks"
            id = menu_doakickflip_end
            pad_choose_script = menu_select
            pad_choose_params = { menu_select_script = doakickflip_end }
            }
            return
        endif
    endif
    // List mode (doakickflip_start) is still available but has no menu item.
    make_thugpro_menu_item {
    text = "Do a Kickflip!"
    id = menu_doakickflip_start_live
    pad_choose_script = menu_select
    pad_choose_params = { menu_select_script = doakickflip_start_live }
    }
endscript

script doakickflip_start
    UnloadQB "doakickflip\\tricks.qb"
    LoadQB "doakickflip\\tricks.qb"
    doakickflip_add_goal
    change doakickflip_live = 0
    GoalManager_EditGoal name = doakickflip Params = { can_retry_goal wait_to_add_tricks = 0 trick_time = 3000 }
    change doakickflip_trick_index = 0
    doakickflip_set_next_trick
    GoalManager_ActivateGoal name = doakickflip
    exit_pause_menu
endscript

script doakickflip_start_live
    doakickflip_add_goal
    change doakickflip_live = 1
    change doakickflip_pending = 0
    doakickflip_load_inbox
    doakickflip_skip_old_requests
    GoalManager_EditGoal name = doakickflip Params = { can_retry_goal wait_to_add_tricks = 0 }
    GoalManager_ActivateGoal name = doakickflip
    // after activation, which resets the interval from trick_time
    doakickflip_hold_adds
    KillSpawnedScript name = doakickflip_inbox_poll
    SpawnScript doakickflip_inbox_poll
    exit_pause_menu
endscript

script doakickflip_end
    exit_pause_menu
    KillSpawnedScript name = doakickflip_inbox_poll
    GoalManager_DeactivateGoal name = doakickflip
endscript

script doakickflip_add_goal
    if NOT GoalManager_GoalExists name = doakickflip
        GoalManager_AddGoal name = doakickflip {
        // Same as goal_tetris_genericParams minus trigger_obj_id / start_pad_id /
        // restart_node: those name level nodes that don't exist outside a career
        // level, and with quick_start goal_initialize_skater does
        // ResetSkaters node_name = <restart_node>.
        Params = {
        Goal_Text = "Skate-Tricks"
        View_Goals_Text = "Skate-Tricks"
        init = goal_tetris_init
        uninit = goal_uninit
        activate = goal_tetris_activate
        success = goal_tetris_success
        fail = goal_tetris_fail
        deactivate = goal_tetris_deactivate
        expire = goal_tetris_expire
        trick_time = 3000
        max_tricks = 15
        acceleration_interval = 5
        acceleration_percent = 0.1
        time_to_stop_adding_tricks = 5
        tetris
        record_type = score
        quick_start
        unlimited_time
        // The Skate-Tricks updater in THUGPro.exe (~0x56fb3e) reads
        // goal_tetris_key_combos; without it, it falls back to goal_tetris_tricks
        // and dereferences NULL. Elements may be bare key-combo names or
        // { key_combo = X num_taps = N } structs. Replaced per trick.
        goal_tetris_key_combos = [ Air_SquareL ]
        }
        }
    endif
endscript

// Called from goal_tetris_add_trick (for every Skate-Tricks goal), after the
// engine has added a trick to the stack.
script doakickflip_on_trick_added
    if GoalManager_GoalExists name = doakickflip
        if GoalManager_GoalIsActive name = doakickflip
            if (doakickflip_live = 1)
                doakickflip_hold_adds
                change doakickflip_pending = 0
            else
                doakickflip_set_next_trick
            endif
        endif
    endif
endscript

// List mode: point the goal's trick pool at the next trick in the list, or stop
// adding tricks once the list is used up.
script doakickflip_set_next_trick
    GetArraySize doakickflip_tricks
    if (doakickflip_trick_index < <array_size>)
        GoalManager_EditGoal name = doakickflip Params = (doakickflip_tricks [ doakickflip_trick_index ])
        change doakickflip_trick_index = (doakickflip_trick_index + 1)
    else
        doakickflip_hold_adds
    endif
endscript

// Stop the engine adding tricks until the interval is lowered again.
script doakickflip_hold_adds
    GoalManager_EditGoal name = doakickflip Params = { #648d8d2a = 2000000000 }
endscript

// Live mode below.

script doakickflip_load_inbox
    UnloadQB "doakickflip\\inbox.qb"
    LoadQB "doakickflip\\inbox.qb"
endscript

// Mark everything already in the inbox as handled, so only requests made after
// the goal starts are called out.
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

// Runs while live mode is active. One request in flight at a time: the next one
// is taken only after the engine has added the previous trick.
script doakickflip_inbox_poll
    begin
        if NOT GoalManager_GoalExists name = doakickflip
            break
        endif
        if NOT GoalManager_GoalIsActive name = doakickflip
            break
        endif
        if (doakickflip_pending = 0)
            doakickflip_load_inbox
            doakickflip_take_next_request
        endif
        wait 0.1 seconds
    repeat
endscript

// Requests are in seq order (oldest first); take the first one not yet handled.
script doakickflip_take_next_request
    GetArraySize doakickflip_inbox
    if (<array_size> > 0)
        <i> = 0
        begin
            if (((doakickflip_inbox [ <i> ]).seq) > doakickflip_last_seq)
                change doakickflip_last_seq = ((doakickflip_inbox [ <i> ]).seq)
                change doakickflip_pending = 1
                GoalManager_EditGoal name = doakickflip Params = (doakickflip_inbox [ <i> ])
                // The add-counter has been running while idle, so this fires on the
                // next frame; after the add it restarts from 0, and 100 ms leaves the
                // hook time to hold adds again before a duplicate could be added.
                GoalManager_EditGoal name = doakickflip Params = { #648d8d2a = 100 }
                break
            endif
            <i> = (<i> + 1)
        repeat <array_size>
    endif
endscript
