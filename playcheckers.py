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

'''
 Board setup is in this shape and has corresponding position numbers assigned
 |   W   W   W   W   |   00  01  02  03 |
 | W   W   W   W     | 04  05  06  07   |
 |   W   W   W   W   |   08  09  10  11 |
 | O   O   O   O     | 12  13  14  15   |
 |   O   O   O   O   |   16  17  18  19 |
 | B   B   B   B     | 20  21  22  23   |
 |   B   B   B   B   |   24  25  26  27 |
 | B   B   B   B     | 28  29  30  31   |
 
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
blk_kng_row = [0, 1, 2, 3]
wht_chkr = -blk_chkr
wht_kng_chkr = -blk_kng_chkr
wht_kng_row = [28, 29, 30, 31]

# dict of neighbors to be used to determine valid moves
# neighbors are listed in the order of upper-left neighbor clockwise
# if no neighbor exists in a corner it is indicated by ''
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

# neighbors that exist if the direct neighbor is jumped over
# '' is used if no jump neighbor exists
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

class CheckersBoard(object):

    def __init__(self):
        initial_state = StringIO("""-1,-1,-1,-1
            -1,-1,-1,-1
            -1,-1,-1,-1
            0,0,0,0
            0,0,0,0
            1,1,1,1
            1,1,1,1
            1,1,1,1
        """)
        self.state = pd.read_csv(initial_state, sep=",", header=-1, index_col=None)
        #print(self.state)
        #TODO initialize board object

    def print_board(self):
        for i in range(8):
            toprint = ''
            if i%2 == 0:
                toprint += '  '
            if i < 2:
                toprint += '0'+str(i*4)+'  '+'0'+str(i*4+1)+'  '+'0'+str(i*4+2)+'  '+'0'+str(i*4+3)
            elif i == 2:
                toprint += '0'+str(i*4)+'  '+'0'+str(i*4+1)+'  '+str(i*4+2)+'  '+str(i*4+3)
            else:
                toprint += str(i*4)+'  '+str(i*4+1)+'  '+str(i*4+2)+'  '+str(i*4+3)
            if i%2 != 0:
                toprint += '  '
            toprint += '| '

            if i%2 == 0:
                toprint += '  '
            for j in range(4):
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
        #TODO print the current state of the board

    #TODO fix play code to force jump if one is available
    def get_valid_jumps(self, player_turn):
        jump_list = list()

        if player_turn == 1:
            king_val = blk_kng_chkr
            chck_val = blk_chkr
            move_dir = [0,1]
        else:
            king_val = wht_kng_chkr
            chck_val = wht_chkr
            move_dir = [2, 3]

        board_copy = self.state.copy()
        board_copy = np.reshape(board_copy.as_matrix(), (32,))

        for i in range(32):
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
        #TODO generate a list of moves and their probability of leading to a win
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
        board_copy = np.reshape(board_copy.as_matrix(), (32,))

        for i in range(32):
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
        #TODO update board positions based on selected movement, player that made the move, and whether
        #TODO or not the player eliminated a piece
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
        board_copy = np.reshape(board_copy.as_matrix(), (32,))

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

            board_copy = pd.DataFrame(np.reshape(board_copy, (8,4)))
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
        #np.ndarray(shape=(32,32,4))
        #self.boye_moves = np.zeros(shape=(32, 32, 4))

    def load_boye(self, file_dir):
        try:
            file = FileIO(file_dir, 'r')
            self.boye_moves = pickle.load(file)
            file.close()
        except FileNotFoundError:
            print("No file found to load")

    def save_boye(self, file_dir):
        try:
            makedirs(dirname(file_dir))
        except OSError as exc:
            pass
        file = FileIO(file_dir, 'w')
        pickle.dump(self.boye_moves, file)
        file.close()

    def get_moves(self, board):
        #TODO:return a list of moves and their probability of winning the game
        board_shape = np.reshape(board.state.as_matrix(), (32,))
        board_shape = hash(tuple(board_shape))
        if board_shape in self.boye_moves:
            move_probabilities = self.boye_moves[board_shape]
        else:
            move_probabilities = np.zeros(shape=(32, 4))
        return move_probabilities

    def update_move_p(self, board_state, move, rate, reward, next_board_state):
        move = self.modify_move_shape(move)
        #print(board_state)
        board_shape = np.reshape(board_state.as_matrix(), (32,))
        #print(board_shape)
        next_shape = np.reshape(next_board_state.as_matrix(), (32,))

        board_shape = hash(tuple(board_shape))
        next_shape = hash(tuple(next_shape))
        if board_shape in self.boye_moves:
            move_probabilities = self.boye_moves[board_shape]
        else:
            move_probabilities = np.zeros(shape=(32, 4))
        orig_val = move_probabilities[move[0]][move[1]]
        if board_state.equals(next_board_state):
            move_probabilities[move[0]][move[1]] = orig_val+rate*(reward+reward-orig_val)
        else:
            move_probabilities[move[0]][move[1]] = orig_val+rate*(reward+self.max_reward(next_shape)-orig_val)
        #if board_shape not in self.boye_moves:
        self.boye_moves[board_shape] = move_probabilities
        #else:
         #   self.boye_moves[board_shape] = move_probabilities

    def modify_move_shape(self, move):
        init_pos = move[0]
        if move[1] in direct_neighbors[init_pos]:
            finl_dir = direct_neighbors[init_pos].index(move[1])
        else:
            finl_dir = jump_neighbors[init_pos].index(move[1])
        return [init_pos, finl_dir]

    def max_reward(self, board_shaped):
        if board_shaped in self.boye_moves:
            next_move_probs = self.boye_moves[board_shaped]
        else:
            next_move_probs = np.zeros(shape=(32, 4))
        max_row = 0
        for row in next_move_probs:
            max_row = np.maximum(max_row, np.amax(row))
        return max_row

    def choose_best_move(self, board, cont_pos, player_turn):
        move_p = self.get_moves(board)
        best_move_p = 0
        best_move_start = -1
        best_move_dir = -1
        valid_moves, is_jump = board.get_valid_moves(player_turn)
        if len(valid_moves) == 0:
            return 0,0,0,False
        for i in range(32):
            for j in range(4):
                if move_p[i][j] > best_move_p or best_move_start == -1:
                    if [i, j] in valid_moves and (cont_pos == -1 or i == cont_pos):
                        best_move_p = move_p[i][j]
                        best_move_start = i
                        best_move_dir = j
        if best_move_p != 0:
            #print("best_Ps")
            #print(best_move_p)
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

    loaddir = "checker_boye_masturb3.txt"
    savedir = "checker_boye_qsave"+"432"+".txt"

    print("?")
    boye.load_boye(loaddir)
    print("!")

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
                    #TODO case when win
                    #TODO case when draw
                else: #normal movement case
                    move = move.split(',')

                    try:
                        init_pos = int(move[0])
                        finl_pos = int(move[1])
                        if init_pos > 31 or init_pos < 0 or finl_pos > 31 or finl_pos < 0:
                            print("Not a valid move. try again")
                            invalid_count += 1
                            continue
                        if abs(finl_pos - init_pos) > 5:
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
                            print("Not a valid move. try again")
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
            #TODO: determine what move to be making for ai
            #TODO: ai will determine on its own whether no more moves are available
            print("\n\nWhite's turn.")
            board.print_board()
            valid_move = False
            invalid_count = 0

            while not valid_move:
                #TODO first check if a jump exists since that has to be taken

                init_pos, finl_dir, movep, isjump = boye.choose_best_move(board, cont_pos, turn)

                if 1 == 2:
                    print("uwot")
                    #TODO case when win
                    #TODO case when draw
                else: #normal movement case

                    #determine final position of movement
                    #shit code below. cleanup later when bored
                    if isjump: #if the move is a jump
                        finl_pos = jump_neighbors[init_pos][finl_dir]
                    else: #else
                        finl_pos = direct_neighbors[init_pos][finl_dir]
                    #TODO this is getting an error once white runs out of pieces
                    if finl_pos == '':
                        if invalid_count > 3:
                            print("Assuming no more valid moves exist.\nBlack wins!")
                            playing = False
                            valid_move = True
                            break
                        print("Not a valid move. try again")
                        invalid_count += 1
                        continue
                    if abs(finl_pos - init_pos) > 5:
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

    boye.save_boye(savedir)


if __name__ == '__main__':
    #define variables to control board
    #black is assumed to be positioned at the bottom of the screen
    no_chkr = 0

    no_cap_max = 75

    valid_positions = range(32)

    play_checkers()