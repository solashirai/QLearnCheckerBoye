from playcheckers import CheckerBoye, CheckersBoard
import numpy as np
import random

def play_self_boye():
    boye = CheckerBoye()
    black_boye = CheckerBoye()
    board = 0

    boye.load_boye(loaddir)
    black_boye.load_boye(loaddirblk)

    #this is probably far too many games to realistically play
    fuckin_max = 10000000
    fuckin_count = 0
    while fuckin_count < fuckin_max:
        board = CheckersBoard()
        boye_moves = list()
        boye_states = list()
        black_boye_moves = list()
        black_boye_states = list()
        reward = 0

        # 1 is black turn, -1 is white
        turn = 1
        # used to save position to continue chain captures
        cont_pos = -1

        playing = True

        no_cap_count = 0
        while playing:
            if no_cap_count > no_cap_max:
                playing = False
                reward = 0.2
                break
            if turn == 1:  # black turn
                black_boye_states.append(board.state)
                valid_move = False
                invalid_count = 0

                while not valid_move:

                    if random.randint(0,100) > randchance:
                        init_pos, finl_dir, movep, isjump = black_boye.choose_best_move(board, cont_pos, turn)
                    else:
                        init_pos, finl_dir, movep, isjump = black_boye.choose_rando_move(board, cont_pos, turn)


                    if isjump:  # if the move is a jump
                        finl_pos = jump_neighbors[init_pos][finl_dir]
                    else:  # else
                        finl_pos = direct_neighbors[init_pos][finl_dir]
                    if finl_pos == '':
                        if invalid_count > 3:
                            reward = 1
                            playing = False
                            valid_move = True
                            break
                        # print("Not a valid move. try again")
                        invalid_count += 1
                        continue
                    if abs(finl_pos - init_pos) > 5:
                        elim_p = True
                        no_cap_count = 0
                    else:
                        elim_p = False
                    valid_move, cont_jump = board.update_board_positions(movement=[init_pos, finl_pos],
                                                                         player_turn=turn,
                                                                         eliminated_piece=elim_p)

                    if not valid_move:
                        if invalid_count > 3:
                            reward = 1
                            playing = False
                            valid_move = True
                            break
                        # print("Not a valid move. try again")
                        invalid_count += 1
                    elif cont_pos > -1 and init_pos != cont_pos:
                        if invalid_count > 3:
                            reward = 1
                            playing = False
                            valid_move = True
                            break
                        # print("Not a valid move. try again")
                        invalid_count += 1
                    else:
                        black_boye_moves.append([init_pos, finl_pos])
                        no_cap_count += 1
                        if cont_jump:
                            cont_pos = finl_pos
                        else:
                            cont_pos = -1
                            turn = -turn
                            boye_states.append(board.state)
            else:  # white turn. for now checkerboye is always white
                valid_move = False
                invalid_count = 0

                while not valid_move:

                    if random.randint(0,100) > randchance:
                        init_pos, finl_dir, movep, isjump = boye.choose_best_move(board, cont_pos, turn)
                    else:
                        init_pos, finl_dir, movep, isjump = boye.choose_rando_move(board, cont_pos, turn)

                    if isjump:  # if the move is a jump
                        finl_pos = jump_neighbors[init_pos][finl_dir]
                    else:  # else
                        finl_pos = direct_neighbors[init_pos][finl_dir]
                    if finl_pos == '':
                        if invalid_count > 3:
                            reward = -1
                            playing = False
                            valid_move = True
                            break
                        #print("Not a valid move. try again")
                        invalid_count += 1
                        continue
                    if abs(finl_pos - init_pos) > 5:
                        elim_p = True
                        no_cap_count = 0
                    else:
                        elim_p = False
                    valid_move, cont_jump = board.update_board_positions(movement=[init_pos, finl_pos],
                                                                         player_turn=turn,
                                                                         eliminated_piece=elim_p)

                    if not valid_move:
                        if invalid_count > 3:
                            reward = -1
                            playing = False
                            valid_move = True
                            break
                        #print("Not a valid move. try again")
                        invalid_count += 1
                    elif cont_pos > -1 and init_pos != cont_pos:
                        if invalid_count > 3:
                            reward = -1
                            playing = False
                            valid_move = True
                            break
                        #print("Not a valid move. try again")
                        invalid_count += 1
                    else:
                        #print("White moved piece %s" % [init_pos, finl_pos])
                        no_cap_count += 1
                        boye_moves.append([init_pos, finl_pos])
                        if cont_jump:
                            cont_pos = finl_pos
                            boye_states.append(board.state)
                        else:
                            cont_pos = -1
                            turn = -turn
        if len(boye_states) > len(boye_moves):
            del boye_states[-1]
        boye.update_move_p(boye_states[len(boye_states) - 1], boye_moves[len(boye_moves) - 1], learn_rate,
                       reward, boye_states[len(boye_states) - 1])
        for i in range(1, len(boye_moves)):
            boye.update_move_p(boye_states[len(boye_states) - 1 - i], boye_moves[len(boye_moves)-1-i], learn_rate,
                               reward, boye_states[len(boye_states) -i])


        if len(black_boye_states) > len(black_boye_moves):
            del black_boye_states[-1]
        black_boye.update_move_p(black_boye_states[len(black_boye_states) - 1], black_boye_moves[len(black_boye_moves) - 1], learn_rate,
                       reward, black_boye_states[len(black_boye_states) - 1])
        for i in range(1, len(black_boye_moves)):
            black_boye.update_move_p(black_boye_states[len(black_boye_states) - 1 - i], black_boye_moves[len(black_boye_moves)-1-i], learn_rate,
                               reward, black_boye_states[len(black_boye_states) -i])
        fuckin_count += 1

        if fuckin_count%10000 == 0:
            boye.save_boye(savedir)
            black_boye.save_boye(savedirblk)
            print("saved")

    print("Fuckin Max")



if __name__ == '__main__':

    loaddir = "checker_boye_masturb3.txt"
    loaddirblk = "checker_black_boye_masturb3.txt"
    savedir = "checker_boye_masturb3.txt"
    savedirblk = "checker_black_boye_masturb3.txt"

    learn_rate = 0.1
    randchance = 5

    #define variables to control board
    #black is assumed to be positioned at the bottom of the screen
    no_chkr = 0
    blk_chkr = 1
    blk_kng_chkr = 2
    blk_kng_row = [0,1,2,3]
    wht_chkr = -blk_chkr
    wht_kng_chkr = -blk_kng_chkr
    wht_kng_row = [28,29,30,31]

    outcomes = ['1-0', '1/2-1/2', '0-1']

    no_cap_max = 30

    valid_positions = range(32)

    #dict of neighbors to be used to determine valid moves
    #neighbors are listed in the order of upper-left neighbor clockwise
    #if no neighbor exists in a corner it is indicated by ''
    direct_neighbors = {
        0: ['', '', 5, 4],
        1: ['', '', 6, 5],
        2: ['', '', 7, 6],
        3: ['', '', '', 7],
        4: ['', 0, 8, ''],
        5: [0, 1, 9, 8],
        6: [1, 2, 10, 9],
        7: [2, 3, 11, 10],
        8: [4, 5, 13, 12],
        9: [5, 6, 14, 13],
        10: [6, 7, 15, 14],
        11: [7, '', '', 15],
        12: ['', 8, 16, ''],
        13: [8, 9, 17, 16],
        14: [9, 10, 18, 17],
        15: [10, 11, 19, 18],
        16: [12, 13, 21, 20],
        17: [13, 14, 22, 21],
        18: [14, 15, 23, 22],
        19: [15, '', '', 23],
        20: ['', 16, 24, ''],
        21: [16, 17, 25, 24],
        22: [17, 18, 26, 25],
        23: [18, 19, 27, 26],
        24: [20, 21, 29, 28],
        25: [21, 22, 30, 29],
        26: [22, 23, 31, 30],
        27: [23, '', '', 31],
        28: ['', 24, '', ''],
        29: [24, 25, '', ''],
        30: [25, 26, '', ''],
        31: [26, 27, '', '']
    }

    #neighbors that exist if the direct neighbor is jumped over
    #'' is used if no jump neighbor exists
    jump_neighbors = {
        0: ['', '', 9, ''],
        1: ['', '', 10, 8],
        2: ['', '', 11, 9],
        3: ['', '', '', 10],
        4: ['', '', 13, ''],
        5: ['', '', 14, 12],
        6: ['', '', 15, 13],
        7: ['', '', '', 14],
        8: ['', 1, 17, ''],
        9: [0, 2, 18, 16],
        10: [1, 3, 19, 17],
        11: [2, '', '', 18],
        12: ['', 5, 21, ''],
        13: [4, 6, 22, 20],
        14: [5, 7, 23, 21],
        15: [6, '', '', 22],
        16: ['', 9, 25, ''],
        17: [8, 10, 26, 24],
        18: [9, 11, 27, 25],
        19: [10, '', '', 26],
        20: ['', 13, 29, ''],
        21: [12, 14, 30, 28],
        22: [13, 15, 31, 29],
        23: [14, '', '', 30],
        24: ['', 17, '', ''],
        25: [16, 18, '', ''],
        26: [17, 19, '', ''],
        27: [18, '', '', ''],
        28: ['', 21, '', ''],
        29: [20, 22, '', ''],
        30: [21, 23, '', ''],
        31: [22, '', '', '']
    }

    play_self_boye()