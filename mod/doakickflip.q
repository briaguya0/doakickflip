// doakickflip: start a Skate-Tricks (Skatetris) goal from the free skate pause menu,
// calling out tricks in the order given by a trick list file.
// Appended to qb\game\menu\gamemenu_pause.qb by tools/build_mod.py.
//
// The trick list is loaded at goal start from data\doakickflip\tricks.qb, which
// THUG Pro's file redirect resolves to <THUG Pro>\User\Data\doakickflip\tricks.qb
// (tools/tricks.py writes it). It must define
//     doakickflip_tricks = [ { goal_tetris_key_combos = [ <combo> ] } ... ]
//
// Sequencing: the engine picks each new trick at random from the goal's
// goal_tetris_key_combos, so we keep that list at exactly one entry and swap in
// the next one every time the engine adds a trick (build_mod.py makes
// goal_tetris_add_trick call doakickflip_on_trick_added).

doakickflip_trick_index = 0

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
    make_thugpro_menu_item {
    text = "Start Skate-Tricks"
    id = menu_doakickflip_start
    pad_choose_script = menu_select
    pad_choose_params = { menu_select_script = doakickflip_start }
    }
endscript

script doakickflip_start
    UnloadQB "doakickflip\\tricks.qb"
    LoadQB "doakickflip\\tricks.qb"
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
        // { key_combo = X num_taps = N } structs. Replaced per trick below.
        goal_tetris_key_combos = [ Air_SquareL ]
        }
        }
    endif
    GoalManager_EditGoal name = doakickflip Params = { can_retry_goal wait_to_add_tricks = 0 }
    change doakickflip_trick_index = 0
    doakickflip_set_next_trick
    GoalManager_ActivateGoal name = doakickflip
    exit_pause_menu
endscript

script doakickflip_end
    exit_pause_menu
    GoalManager_DeactivateGoal name = doakickflip
endscript

// Called from goal_tetris_add_trick (for every Skate-Tricks goal), after the
// engine has added a trick to the stack.
script doakickflip_on_trick_added
    if GoalManager_GoalExists name = doakickflip
        if GoalManager_GoalIsActive name = doakickflip
            doakickflip_set_next_trick
        endif
    endif
endscript

// Point the goal's trick pool at the next trick in the list, or stop adding
// tricks once the list is used up.
script doakickflip_set_next_trick
    GetArraySize doakickflip_tricks
    if (doakickflip_trick_index < <array_size>)
        GoalManager_EditGoal name = doakickflip Params = (doakickflip_tricks [ doakickflip_trick_index ])
        change doakickflip_trick_index = (doakickflip_trick_index + 1)
    else
        GoalManager_EditGoal name = doakickflip Params = { wait_to_add_tricks = 1 }
    endif
endscript
