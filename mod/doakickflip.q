// doakickflip: start a Skate-Tricks (Skatetris) goal from the free skate pause menu.
// Appended to qb\game\menu\gamemenu_pause.qb by tools/build_mod.py.

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
        // { key_combo = X num_taps = N } structs. (Create-a-Goal builds this
        // array from cag_key_combos in C++.)
        goal_tetris_key_combos = [
        Air_SquareU
        Air_SquareD
        Air_SquareL
        Air_SquareR
        Air_SquareUL
        Air_SquareUR
        Air_SquareDL
        Air_SquareDR
        Air_CircleU
        Air_CircleD
        Air_CircleL
        Air_CircleR
        Air_CircleUL
        Air_CircleUR
        Air_CircleDL
        Air_CircleDR
        ]
        }
        }
    endif
    GoalManager_EditGoal name = doakickflip Params = { can_retry_goal }
    GoalManager_ActivateGoal name = doakickflip
    exit_pause_menu
endscript

script doakickflip_end
    exit_pause_menu
    GoalManager_DeactivateGoal name = doakickflip
endscript
