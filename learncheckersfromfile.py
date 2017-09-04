from playcheckers import CheckerBoye, CheckersBoard
import numpy as np
import tensorflow as tf
import pandas as pd
from io import StringIO
from io import FileIO
import pickle
import random
from os.path import isfile, dirname
from os import makedirs
import threading

def learn_boye():
    boye = CheckerBoye()
    boye.load_boye(dbname)
    board = 0
    data = list()
    win_data = 0
    lose_data = 0
    draw_data = 0
    corrupt_data = 0
    dummylock = threading.Lock()

    #OCA_2.0 has the board flipped compared to this checkers board
    with open(open_file) as file:
        for line in file.readlines():
            if board == 0:
                if 'result' in line or 'Result' in line:
                    if outcomes[0] in line:
                        result_bonus = -1
                        lose_data += 1
                    elif outcomes[1] in line:
                        result_bonus = 0.25
                        draw_data += 1
                    elif outcomes[2] in line:
                        result_bonus = 1
                        win_data += 1
                elif line[0:2] == '1.':
                    board = CheckersBoard()
                    data.append(line)
            elif isinstance(board, CheckersBoard):

                if line != '\n':
                    data.append(line)
                elif line == '\n':
                    data = ' '.join(data)
                    # Remove any parenthetical comments
                    if '{' in data or '}' in data:
                        str1 = data[0: data.index('{')]
                        str2 = data[data.index('}') + 1:]
                        data = str1.join(str2)

                    data = data.split('\n')
                    data = ''.join(data)
                    data = data.split('.')

                    match_moves = list()
                    board_states = list()
                    corrupted = False

                    try:
                        del data[0]
                    #    del data[0]
                    #    del data[0]
                    except IndexError:
                        corrupted = True

                    for datum in data:
                        datum = datum.split(' ')
                        del datum[0]
                        if len(datum) in range(1, 4):
                            if '-' in datum[0]:
                                datum_part = datum[0].split('-')
                                moves1 = [datum_part[0], datum_part[1]]
                            else:
                                datum_parts = datum[0].split('x')
                                moves1 = list()
                                for i in range(1, len(datum_parts)):
                                    moves1.append([datum_parts[i-1], datum_parts[i]])
                            if len(datum) == 3:
                                if '-' in datum[1]:
                                    datum_part = datum[1].split('-')
                                    moves2 = [datum_part[0], datum_part[1]]
                                else:
                                    datum_parts = datum[1].split('x')
                                    moves2 = list()
                                    for i in range(1, len(datum_parts)):
                                        moves2.append([datum_parts[i-1], datum_parts[i]])
                                match_moves.append([moves1, moves2])
                            else:
                                match_moves.append([moves1, ['20','16']])
                        else:
                            corrupt_data += 1
                            print("corrupt_data")
                            corrupted = True
                            board = 0
                            data = list()

                    if not corrupted:
                        match_moves = fix_match_moves(match_moves)
                        for moves in match_moves:
                            if len(moves[0]) == 2:
                                if isinstance(moves[0][0], int):
                                    board.update_board_positions(movement=moves[0], player_turn=1, eliminated_piece=(np.abs(moves[0][0]-moves[0][1]) > 5))
                                    board_states.append(board.state)
                                else:
                                #special case for double jump
                                    board.update_board_positions(movement=moves[0][0], player_turn=1, eliminated_piece=True)
                                    board.update_board_positions(movement=moves[0][1], player_turn=1, eliminated_piece=False)
                                    board_states.append(board.state)
                            else: #jumps move
                                for jm in range(0, len(moves[0])-1):
                                    board.update_board_positions(movement=moves[0][jm], player_turn=1, eliminated_piece=True)
                                board.update_board_positions(movement=moves[0][len(moves[0])-1], player_turn=1,
                                                             eliminated_piece=False)
                                board_states.append(board.state)
                            if len(moves) == 2:
                                if len(moves[1]) == 2:
                                    if isinstance(moves[1][0], int):
                                        board.update_board_positions(movement=moves[1], player_turn=-1, eliminated_piece=(np.abs(moves[1][0]-moves[1][1]) > 5))
                                    else:
                                    #special case for double jump
                                        board.update_board_positions(movement=moves[1][0], player_turn=-1, eliminated_piece=True)
                                        board_states.append(board.state)
                                        board.update_board_positions(movement=moves[1][1], player_turn=-1, eliminated_piece=False)
                                else: #jumps move
                                    for jm in range(0, len(moves[1])-1):
                                        board.update_board_positions(movement=moves[1][jm], player_turn=-1, eliminated_piece=True)
                                        board_states.append(board.state)
                                    if len(moves[1]) != 0:
                                        board.update_board_positions(movement=moves[1][len(moves[1])-1], player_turn=-1,
                                                                 eliminated_piece=False)

                        statedif = 0
                        if len(match_moves[len(match_moves)-1]) == 2:
                            if len(match_moves[len(match_moves)-1][1]) > 0:
                                if isinstance(match_moves[len(match_moves)-1][1][0], int):
                                    #print("11")
                                    boye.update_move_p(board_states[len(board_states)-1-statedif], match_moves[len(match_moves)-1][1], learn_rate, result_bonus, board_states[len(board_states)-1-statedif], dummylock)
                                    statedif += 1
                                else:
                                    #print("12")
                                    boye.update_move_p(board_states[len(board_states)-1-statedif], match_moves[len(match_moves)-1][1][len(match_moves[len(match_moves)-1][1])-1], learn_rate, result_bonus, board_states[len(board_states)-1-statedif], dummylock)
                                    statedif += 1
                                    for i in range(1, len(match_moves[len(match_moves)-1][1])):
                                        #print("13")
                                        boye.update_move_p(board_states[len(board_states) - 1 - statedif],
                                                           match_moves[len(match_moves) - 1][1][len(match_moves[len(match_moves)-1][1])-1-i], learn_rate, result_bonus,
                                                           board_states[len(board_states) - statedif], dummylock)
                                        statedif += 1

                        #print(len(match_moves))
                        try:
                            for i in range(1, len(match_moves)):
                                #print(i)
                                #TODO this loop isn't running quite enough?
                                i += 1
                                innermove = match_moves[len(match_moves) - i][1]
                                if len(innermove) > 0:
                                    if isinstance(innermove[0], int):
                                        #print("1")
                                        boye.update_move_p(board_states[len(board_states)-1-statedif], innermove, learn_rate, result_bonus, board_states[len(board_states)-statedif], dummylock)
                                        statedif += 1
                                    else:
                                        #print("2")
                                        boye.update_move_p(board_states[len(board_states)-1-statedif], innermove[len(innermove)-1], learn_rate, result_bonus, board_states[len(board_states)-statedif],dummylock)
                                        statedif += 1
                                        for j in range(1, len(innermove)):
                                            #print(len(innermove))
                                            j += 1
                                            #print("3")
                                            boye.update_move_p(board_states[len(board_states) - 1 - statedif],
                                                               innermove[len(innermove) - 1-j], learn_rate, result_bonus,
                                                               board_states[len(board_states) - statedif], dummylock)
                                            statedif += 1

                        except IndexError:
                            print("corrupt_data")
                            corrupted = True
                            break
                        board = 0
                        data = list()
                        print(win_data, lose_data, draw_data)
                    else:
                        board = 0
                        data = list()
                        print("Corrupt")

    file.close()
    boye.save_boye()
    boye.end_boye()
    return

def fix_match_moves(match_moves):
    #print(match_moves)
    for moves in match_moves:
        if len(moves[0]) == 2:
            if isinstance(moves[0][0], str):
                moves[0][0] = 32 - int(moves[0][0])
                moves[0][1] = 32 - int(moves[0][1])
            else:
                # special case for double jump
                moves[0][0] = [32 - int(moves[0][0][0]), 32 - int(moves[0][0][1])]
                moves[0][1] = [32 - int(moves[0][1][0]), 32 - int(moves[0][1][1])]
        else:  # jumps move
            for jm in range(0, len(moves[0]) - 1):
                moves[0][jm] = [32 - int(moves[0][jm][0]), 32 - int(moves[0][jm][1])]
            moves[0][len(moves[0])-1] = [32 - int(moves[0][len(moves[0])-1][0]), 32 - int(moves[0][len(moves[0])-1][1])]

        if len(moves) == 2:
            if len(moves[1]) == 2:
                if isinstance(moves[1][0], str):
                    moves[1][0] = 32 - int(moves[1][0])
                    moves[1][1] = 32 - int(moves[1][1])
                else:
                    # special case for double jump
                    moves[1][0] = [32 - int(moves[1][0][0]), 32 - int(moves[1][0][1])]
                    moves[1][1] = [32 - int(moves[1][1][0]), 32 - int(moves[1][1][1])]
            else:  # jumps move
                for jm in range(0, len(moves[1]) - 1):
                    moves[1][jm] = [32 - int(moves[1][jm][0]), 32 - int(moves[1][jm][1])]
                if len(moves[1]) > 0:
                    moves[1][len(moves[1])-1] = [32 - int(moves[1][len(moves[1])-1][0]), 32 - int(moves[1][len(moves[1])-1][1])]
    return match_moves


if __name__ == '__main__':

    open_file = "OCA_2.0.pdn"

    dbname = "checker_boye_moves_mysql"

    learn_rate = 0.02

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

    learn_boye()