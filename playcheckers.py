import numpy as np
import tensorflow as tf
import pandas as pd
from pandas.util.testing import assert_frame_equal
from io import StringIO
from io import FileIO
import pickle
import random
from os.path import isfile, dirname
from os import makedirs
import pymysql
from multiprocessing import Lock

'''
 Board setup is in this shape and has corresponding position numbers assigned
 Board is smaller than a real checker board because the time limitations
 |   W   W   W  |   00  01  02 |
 | W   W   W    | 03  04  05   |
 |   O   O   O  |   06  07  08 |
 | O   O   O    | 09  10  11   |
 |   B   B   B  |   12  13  14 |
 | B   B   B    | 15  16  17   |
 
 Board setup in terms of array
 [[-1, -1, -1, -1],
 [-1, -1, -1, -1],
 [-1, -1, -1, -1],
 [ 0,  0,  0,  0],
 [ 0,  0,  0,  0],
 [ 1,  1,  1,  1],
 [ 1,  1,  1,  1],
 [ 1,  1,  1,  1]]
 
'''

blk_chkr = 1
blk_kng_chkr = 2
blk_kng_row = [0, 1, 2]
wht_chkr = -blk_chkr
wht_kng_chkr = -blk_kng_chkr
wht_kng_row = [15, 16, 17]

# dict of neighbors to be used to determine valid moves
# neighbors are listed in the order of upper-left neighbor clockwise
# if no neighbor exists in a corner it is indicated by ''
direct_neighbors = {
    0: ['', '', 4, 3],
    1: ['', '', 5, 4],
    2: ['', '', '', 5],
    3: ['', 0, 6, ''],
    4: [0, 1, 7, 6],
    5: [1, 2, 8, 7],
    6: [3, 4, 10, 9],
    7: [4, 5, 11, 10],
    8: [5, '', '', 11],
    9: ['', 6, 12, ''],
    10: [6, 7, 13, 12],
    11: [7, 8, 14, 13],
    12: [9, 10, 16, 15],
    13: [10, 11, 17, 16],
    14: [11, '', '', 17],
    15: ['', 12, '', ''],
    16: [12, 13, '', ''],
    17: [13, 14, '', '']
}

# neighbors that exist if the direct neighbor is jumped over
# '' is used if no jump neighbor exists
jump_neighbors = {
    0: ['', '', 7, ''],
    1: ['', '', 8, 6],
    2: ['', '', '', 7],
    3: ['', '', 10, ''],
    4: ['', '', 11, 9],
    5: ['', '', '', 10],
    6: ['', 1, 13, ''],
    7: [0, 2, 14, 12],
    8: [1, '', '', 13],
    9: ['', 4, 16, ''],
    10: [3, 5, 17, 15],
    11: [4, '', '', 16],
    12: ['', 7, '', ''],
    13: [6, 8, '', ''],
    14: [7, '', '', ''],
    15: ['', 10, '', ''],
    16: [9, 11, '', ''],
    17: [10, '', '', '']
}

class CheckersBoard(object):

    def __init__(self):
        initial_state = StringIO("""-1,-1,-1
            -1,-1,-1
            0,0,0
            0,0,0
            1,1,1
            1,1,1
        """)
        self.state = pd.read_csv(initial_state, sep=",", header=-1, index_col=None)

    def print_board(self):
        for i in range(6):
            toprint = ''
            if i%2 == 0:
                toprint += '  '
            if i < 3:
                toprint += '0'+str(i*3)+'  '+'0'+str(i*3+1)+'  '+'0'+str(i*3+2)
            elif i == 3:
                toprint += '0'+str(i*3)+'  '+str(i*3+1)+'  '+str(i*3+2)
            else:
                toprint += str(i*3)+'  '+str(i*3+1)+'  '+str(i*3+2)
            if i%2 != 0:
                toprint += '  '
            toprint += '| '

            if i%2 == 0:
                toprint += '  '
            for j in range(3):
                thisstate = self.state[j][i]
                if thisstate == 1:
                    toprint += 'b   '
                elif thisstate == 2:
                    toprint += 'B   '
                elif thisstate == -1:
                    toprint += 'w   '
                elif thisstate == -2:
                    toprint += 'W   '
                else:
                    toprint += 'o   '
            if i%2 != 0:
                toprint += '  '
            print(toprint)

    def get_valid_jumps(self, player_turn):
        jump_list = list()

        if player_turn == 1:
            king_val = blk_kng_chkr
            chck_val = blk_chkr
            move_dir = [0, 1]
        else:
            king_val = wht_kng_chkr
            chck_val = wht_chkr
            move_dir = [2, 3]

        board_copy = self.state.copy()
        board_copy = np.reshape(board_copy.as_matrix(), (18,))

        for i in range(18):
            piece = board_copy[i]
            dneighbors = direct_neighbors[i]
            jneighbors = jump_neighbors[i]

            if piece == chck_val:
                for dir in move_dir:
                    neighbor = dneighbors[dir]
                    nneighbor = jneighbors[dir]
                    if neighbor != '' and nneighbor != '' and board_copy[nneighbor] == 0 and \
                            (board_copy[neighbor] == -chck_val or board_copy[neighbor] == -king_val):
                        jump_list.append([i, dir])
            elif piece == king_val:
                for dir in range(4):
                    neighbor = dneighbors[dir]
                    nneighbor = jneighbors[dir]
                    if neighbor != '' and nneighbor != '' and board_copy[nneighbor] == 0 and \
                            (board_copy[neighbor] == -chck_val or board_copy[neighbor] == -king_val):
                        jump_list.append([i, dir])
        return jump_list

    def get_valid_moves(self, player_turn):
        valid_moves = list()
        jump_moves = self.get_valid_jumps(player_turn)
        if len(jump_moves) > 0:
            return jump_moves, True

        if player_turn == 1:
            king_val = blk_kng_chkr
            chck_val = blk_chkr
            move_dir = [0,1]
        else:
            king_val = wht_kng_chkr
            chck_val = wht_chkr
            move_dir = [2, 3]

        board_copy = self.state.copy()
        board_copy = np.reshape(board_copy.as_matrix(), (18,))

        for i in range(18):
            piece = board_copy[i]
            dneighbors = direct_neighbors[i]

            if piece == chck_val:
                for dir in move_dir:
                    neighbor = dneighbors[dir]
                    if neighbor != '' and board_copy[neighbor] == 0:
                        valid_moves.append([i, dir])
            elif piece == king_val:
                for dir in range(4):
                    neighbor = dneighbors[dir]
                    if neighbor != '' and board_copy[neighbor] == 0:
                        valid_moves.append([i, dir])

        return valid_moves, False

    def update_board_positions(self, movement, player_turn, eliminated_piece):
        init_pos = movement[0]
        finl_pos = movement[1]

        if player_turn == 1:
            king_row = blk_kng_row
            king_val = blk_kng_chkr
            chck_val = blk_chkr
        else:
            king_row = wht_kng_row
            king_val = wht_kng_chkr
            chck_val = wht_chkr

        board_copy = self.state.copy()
        board_copy = np.reshape(board_copy.as_matrix(), (18,))

        king_changed = False
        cont_jump = False

        if not eliminated_piece and len(self.get_valid_jumps(player_turn)) > 0:
            #a jump exists but wasn't taken. invalid move
            return False, False
        if (board_copy[init_pos] == chck_val or board_copy[init_pos] == king_val) and board_copy[finl_pos] == 0 and ((eliminated_piece and finl_pos in jump_neighbors[init_pos]) or (not eliminated_piece and finl_pos in direct_neighbors[init_pos])):
            #valid move, update positions on the board
            board_copy[finl_pos] = board_copy[init_pos]
            board_copy[init_pos] = 0 #empty original position

            #update to king if on the appropriate row
            if finl_pos in king_row:
                board_copy[finl_pos] = king_val

            if eliminated_piece:
                #figure out which piece should be eliminated
                if finl_pos in jump_neighbors.get(init_pos):
                    jump_direction = jump_neighbors.get(init_pos).index(finl_pos)
                    jumped_pos = direct_neighbors.get(init_pos)[jump_direction]
                    #eliminate piece
                    board_copy[jumped_pos] = 0
                else:
                    #invalid jump
                    return False, False

            board_copy = pd.DataFrame(np.reshape(board_copy, (6,3)))
            self.state = board_copy

            if eliminated_piece:
                #determine if a chain capture exists
                cont_jump_list = self.get_valid_jumps(player_turn)
                if len(cont_jump_list) > 0 and (finl_pos not in king_row or (finl_pos in king_row and not king_changed)):
                    for pairing in cont_jump_list:
                        if finl_pos == pairing[0]:
                            cont_jump = True
            return True, cont_jump
        else:
            #not a valid move
            return False, False

class CheckerBoye():

    def __init__(self):
        #TODO: load in trained data. for now, we just start everything off as zeros
        self.boye_moves = {}
        self.connec = ''
        self.move_cache = {}
        #self.boye_moves = np.zeros(shape=(32, 32, 4))

    def load_boye(self, dbname):
        self.connec = pymysql.connect(host='localhost',
                                      user='checkerboye',
                                      password='password',
                                      db=dbname)
        self.c = self.connec.cursor()
        self.c.execute("CREATE TABLE IF NOT EXISTS statemoves "+
                        "(boardstate varchar(32), startpos int, "+
                        "upleft float, upright float, botright float, botleft float, "+
                        "primary key (boardstate, startpos))")
        #self.dblock.release()
        print("Connected to db")

    def set_db_connection(self, dbcon):
        self.connec = dbcon
        print("DB Connection set up completed")

    def save_boye(self):
        self.connec.commit()
        print("Boye saved")

    def end_boye(self):
        self.connec.close()

    def clear_moves(self):
        #clear out move cache
        self.move_cache = {}

    def get_moves(self, board):
        board_shape = np.reshape(board.state.as_matrix(), (18,))
        board_shape = str(hash(tuple(board_shape)))
        move_probabilities = np.zeros(shape=(18, 4))
        if board_shape in self.move_cache:
            move_probabilities = self.move_cache[board_shape]
        else:
            self.c.execute("SELECT * FROM statemoves WHERE boardstate = %s", (board_shape,))
            resultset = self.c.fetchall()
            #print(resultset)
            for row in resultset:
                move_probabilities[row[1]] = [row[2], row[3], row[4], row[5]]
            self.move_cache[board_shape] = move_probabilities
        return move_probabilities

    def update_move_p(self, board_state, move, rate, reward, next_board_state):
        move = self.modify_move_shape(move)
        #print(board_state)
        board_shape = np.reshape(board_state.as_matrix(), (18,))
        #print(board_shape)
        next_shape = np.reshape(next_board_state.as_matrix(), (18,))

        board_shape = str(hash(tuple(board_shape)))
        next_shape = str(hash(tuple(next_shape)))

        move_probabilities = np.zeros(shape=(18, 4))
        self.c.execute("SELECT * FROM statemoves WHERE boardstate = %s AND startpos = %s", (board_shape, move[0]))
        resultset = self.c.fetchone()
        if resultset is not None:
            movedata = [board_shape, move[0], resultset[2], resultset[3], resultset[4], resultset[5]]
        else:
            movedata = [board_shape, move[0], 0, 0, 0, 0]

        #print(movedata)
        orig_val = movedata[move[1]+2]
        if board_state.equals(next_board_state):
            new_val = orig_val+rate*(reward+reward-orig_val)
        else:
            new_val = orig_val+rate*(reward+self.max_reward(next_shape)-orig_val)
        movedata[move[1]+2] = float(new_val)
        self.c.execute("REPLACE INTO statemoves VALUES (%s,%s,%s,%s,%s,%s)", (movedata[0], movedata[1], movedata[2], movedata[3], movedata[4], movedata[5]))

    def modify_move_shape(self, move):
        init_pos = move[0]
        if move[1] in direct_neighbors[init_pos]:
            finl_dir = direct_neighbors[init_pos].index(move[1])
        else:
            finl_dir = jump_neighbors[init_pos].index(move[1])
        return [init_pos, finl_dir]

    def max_reward(self, board_shape):
        next_move_probabilities = np.zeros(shape=(18, 4))
        self.c.execute("SELECT * FROM statemoves WHERE boardstate = %s", (board_shape,))
        resultset = self.c.fetchall()
        for row in resultset:
            next_move_probabilities[row[1]] = [row[2], row[3], row[4], row[5]]
        max_row = 0
        for row in next_move_probabilities:
            max_row = np.maximum(max_row, np.amax(row))
        return max_row

    def choose_best_move(self, board, cont_pos, player_turn):
        move_p = self.get_moves(board)
        best_move_p = 0
        best_move_start = -1
        best_move_dir = -1
        valid_moves, is_jump = board.get_valid_moves(player_turn)
        #all_ps = list()
        if len(valid_moves) == 0:
            return 0,0,0,False
        for i in range(18):
            for j in range(4):
                if move_p[i][j] > best_move_p or best_move_start == -1:
                    if [i, j] in valid_moves and (cont_pos == -1 or i == cont_pos):
                        best_move_p = move_p[i][j]
                        best_move_start = i
                        best_move_dir = j
                #all_ps.append(move_p[i][j])
        if best_move_p != 0:
            #print("best_Ps")
            #print(best_move_p)
            #print(all_ps)
            return best_move_start, best_move_dir, best_move_p, is_jump
        else: #determine a random move if no best move exists
            rand_choice = random.choice(valid_moves)
            best_move_start = rand_choice[0]
            best_move_dir = rand_choice[1]
            #safetynet to ensure movement is correct if a chain jump exists
            while (cont_pos != -1 and best_move_start != cont_pos):
                rand_choice = random.choice(valid_moves)
                best_move_start = rand_choice[0]
                best_move_dir = rand_choice[1]
            #print("best_Ps")
            #print(best_move_p)
            #print(all_ps)
            return best_move_start, best_move_dir, 0, is_jump

    def choose_rando_move(self, board, cont_pos, player_turn):
        move_p = self.get_moves(board)
        best_move_p = 0
        best_move_start = -1
        best_move_dir = -1
        valid_moves, is_jump = board.get_valid_moves(player_turn)
        if len(valid_moves) == 0:
            return 0,0,0,False
        #else: #determine a random move if no best move exists
        rand_choice = random.choice(valid_moves)
        best_move_start = rand_choice[0]
        best_move_dir = rand_choice[1]
        #safetynet to ensure movement is correct if a chain jump exists
        while (cont_pos != -1 and best_move_start != cont_pos):
            rand_choice = random.choice(valid_moves)
            best_move_start = rand_choice[0]
            best_move_dir = rand_choice[1]
        return best_move_start, best_move_dir, 0, is_jump

def play_checkers():

    board = CheckersBoard()
    boye = CheckerBoye()

    loaddir = "checker_smol"

    boye.load_boye(loaddir)

    # 1 is black turn, -1 is white
    turn = 1
    # used to save position to continue chain captures
    cont_pos = -1

    #boye.load_boye(file_dir=filedir)

    print("Begin playing checkers.\n\n")
    playing = True

    no_cap_count = 0
    while playing:
        if no_cap_count > no_cap_max:
            playing = False
            Print("Too many turns without a piece capture - Assuming Draw")
            break
        if turn == 1: #black turn
            invalid_count = 0
            print("\n\nBlack's turn.")
            board.print_board()
            valid_move = False

            while not valid_move:
                move = input("Enter move as 'initial_pos, final_pos'")

                if 1 == 2:
                    print("uwot")
                else: #normal movement case
                    move = move.split(',')

                    try:
                        init_pos = int(move[0])
                        finl_pos = int(move[1])
                        if init_pos > 17 or init_pos < 0 or finl_pos > 17 or finl_pos < 0:
                            print("Not a valid move. try again")
                            invalid_count += 1
                            continue
                        if abs(finl_pos - init_pos) > 4:
                            elim_p = True
                            no_cap_count = 0
                        else:
                            elim_p = False
                        valid_move, cont_jump = board.update_board_positions(movement=[init_pos, finl_pos],
                                                                player_turn=turn, eliminated_piece=elim_p)

                        if not valid_move:
                            if invalid_count > 3:
                                print("Assuming no more valid moves exist.\nWhite wins!")
                                playing = False
                                valid_move = True
                                break
                            print("Not a valid move. try again")
                            invalid_count += 1
                        elif cont_pos > -1 and init_pos != cont_pos:
                            if invalid_count > 3:
                                print("Assuming no more valid moves exist.\nWhite wins!")
                                playing = False
                                valid_move = True
                                break
                            print("Nodddt a valid move. try again")
                            invalid_count += 1
                        else:
                            print("Black moved piece %s"  % [init_pos, finl_pos])
                            no_cap_count += 1
                            if cont_jump:
                                cont_pos = finl_pos
                            else:
                                cont_pos = -1
                                turn = -turn
                    except ValueError:
                        print("Not a valid move. try again")
                        invalid_count += 1
                        continue
        else: #white turn. for now checkerboye is always white
            print("\n\nWhite's turn.")
            board.print_board()
            valid_move = False
            invalid_count = 0

            while not valid_move:

                init_pos, finl_dir, movep, isjump = boye.choose_best_move(board, cont_pos, turn)

                if 1 == 2:
                    print("uwot")
                else: #normal movement case

                    #determine final position of movement
                    #shit code below. cleanup later when bored
                    if isjump: #if the move is a jump
                        finl_pos = jump_neighbors[init_pos][finl_dir]
                    else: #else
                        finl_pos = direct_neighbors[init_pos][finl_dir]
                    if finl_pos == '':
                        if invalid_count > 3:
                            print("Assuming no more valid moves exist.\nBlack wins!")
                            playing = False
                            valid_move = True
                            break
                        print("Not a valid move. try again")
                        invalid_count += 1
                        continue
                    if abs(finl_pos - init_pos) > 4:
                        elim_p = True
                        no_cap_count = 0
                    else:
                        elim_p = False
                    valid_move, cont_jump = board.update_board_positions(movement=[init_pos, finl_pos],
                                                              player_turn=turn, eliminated_piece=elim_p)

                    if not valid_move:
                        if invalid_count > 3:
                            print("Assuming no more valid moves exist.\nBlack wins!")
                            playing = False
                            valid_move = True
                            break
                        print("Not a valid move. try again")
                        invalid_count += 1
                    elif cont_pos > -1 and init_pos != cont_pos:
                        if invalid_count > 3:
                            print("Assuming no more valid moves exist.\nBlack wins!")
                            playing = False
                            valid_move = True
                            break
                        print("Not a valid move. try again")
                        invalid_count += 1
                    else:
                        print("White moved piece %s"  % [init_pos, finl_pos])
                        no_cap_count += 1
                        if cont_jump:
                            cont_pos = finl_pos
                        else:
                            cont_pos = -1
                            turn = -turn

    boye.save_boye()


if __name__ == '__main__':
    #define variables to control board
    #black is assumed to be positioned at the bottom of the screen
    no_chkr = 0

    no_cap_max = 75

    valid_positions = range(18)

    play_checkers()