from playcheckers import CheckerBoye, CheckersBoard
import random
from multiprocessing import Process, Queue, current_process

def boye_self_play(update_queue1, update_queue2):

    check_winrate = True
    print("Starting self play...")
    boye = CheckerBoye()
    black_boye = CheckerBoye()
    board = 0

    boye.load_boye(dbname)
    black_boye.load_boye(dbnameblk)

    #this is probably too many games to realistically play
    max_count = 500000
    current_count = 0

    if (check_winrate):
        max_count = 3000

    whitewin = 0
    tiecount = 0
    while current_count < max_count:
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
        #make sure first move is random so that there's more variance in the kind of games played
        firstmove = True

        no_cap_count = 0
        while playing:
            if no_cap_count > no_cap_max:
                playing = False
                reward = -4
                tiecount += 1
                break
            if turn == 1:  # black turn
                black_boye_states.append(board.state)
                valid_move = False
                invalid_count = 0

                while not valid_move:

                    if random.randint(0,100) <= randchance or current_count%20 == 0 or firstmove: #make black do random moves a lot more
                        init_pos, finl_dir, movep, isjump = black_boye.choose_rando_move(board, cont_pos, turn)
                    else:
                        init_pos, finl_dir, movep, isjump = black_boye.choose_best_move(board, cont_pos, turn)
                    firstmove = False

                    if isjump:  # if the move is a jump
                        finl_pos = jump_neighbors[init_pos][finl_dir]
                    else:  # else
                        finl_pos = direct_neighbors[init_pos][finl_dir]
                    if finl_pos == '':
                        if invalid_count > 3:
                            reward = 4
                            whitewin += 1
                            playing = False
                            valid_move = True
                            break
                        invalid_count += 1
                        continue
                    if abs(finl_pos - init_pos) > 4:
                        elim_p = True
                        no_cap_count = 0
                    else:
                        elim_p = False
                    valid_move, cont_jump = board.update_board_positions(movement=[init_pos, finl_pos],
                                                                         player_turn=turn,
                                                                         eliminated_piece=elim_p)

                    if not valid_move:
                        if invalid_count > 3:
                            reward = 4
                            whitewin += 1
                            playing = False
                            valid_move = True
                            break
                        invalid_count += 1
                    elif cont_pos > -1 and init_pos != cont_pos:
                        if invalid_count > 3:
                            reward = 4
                            whitewin += 1
                            playing = False
                            valid_move = True
                            break
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

                while not valid_move: #TODO fix the logic inside here so that there's less repeated code from above

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
                            reward = -4
                            playing = False
                            valid_move = True
                            break
                        invalid_count += 1
                        continue
                    if abs(finl_pos - init_pos) > 4:
                        elim_p = True
                        no_cap_count = 0
                    else:
                        elim_p = False
                    valid_move, cont_jump = board.update_board_positions(movement=[init_pos, finl_pos],
                                                                         player_turn=turn,
                                                                         eliminated_piece=elim_p)

                    if not valid_move:
                        if invalid_count > 3:
                            reward = -4
                            playing = False
                            valid_move = True
                            break
                        invalid_count += 1
                    elif cont_pos > -1 and init_pos != cont_pos:
                        if invalid_count > 3:
                            reward = -4
                            playing = False
                            valid_move = True
                            break
                        invalid_count += 1
                    else:
                        no_cap_count += 1
                        boye_moves.append([init_pos, finl_pos])
                        if cont_jump:
                            cont_pos = finl_pos
                            boye_states.append(board.state)
                        else:
                            cont_pos = -1
                            turn = -turn
        current_count += 1
        update_queue1.put([boye_states, boye_moves, reward])
        update_queue2.put([black_boye_states, black_boye_moves, reward])
        if current_count % 500 == 0:
            print(str(current_count)+" games played by process "+str(current_process()))
    print("reached count max")
    if check_winrate:
        print("White win rate: %s" %(whitewin / current_count))
        print("Tie rate: %s" %(tiecount / current_count))
    return

def do_queue(update_queue, loaddb, boyecolor):
    current_count = 0
    print("Starting queue controller...")
    boye = CheckerBoye()
    boye.load_boye(loaddb)
    while True:
        queue_contents = update_queue.get()
        boye_update(boye, -queue_contents[2], queue_contents[0], queue_contents[1])
        current_count += 1

        if current_count % 250 == 0:
            print("total "+boyecolor+" gamecount: " + str(current_count))

        if current_count % 1000 == 0:
            boye.save_boye()
            print("saved "+boyecolor)


def boye_update(boye, reward, boye_states, boye_moves):
    if len(boye_states) > len(boye_moves):
        del boye_states[-1]
    boye.update_move_p(boye_states[len(boye_states) - 1], boye_moves[len(boye_moves) - 1], learn_rate,
                       reward, boye_states[len(boye_states) - 1])
    for i in range(1, len(boye_moves)):
        boye.update_move_p(boye_states[len(boye_states) - 1 - i], boye_moves[len(boye_moves) - 1 - i], learn_rate,
                           reward, boye_states[len(boye_states) - i])

if __name__ == '__main__':
    dbname = "checker_smol"
    dbnameblk = "checker_black_smol"

    learn_rate = 0.25
    randchance = 5

    #define variables to control board
    #black is assumed to be positioned at the bottom of the screen
    blk_chkr = 1
    blk_kng_chkr = 2
    blk_kng_row = [0, 1, 2]
    wht_chkr = -blk_chkr
    wht_kng_chkr = -blk_kng_chkr
    wht_kng_row = [15, 16, 17]

    no_cap_max = 30

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

    update_queue1 = Queue(1000)
    update_queue2 = Queue(1000)
    for i in range(2):
        Process(target=boye_self_play, args=(update_queue1,update_queue2)).start()
    px = Process(target=do_queue, args=(update_queue1,dbname, "white"))
    Process(target=do_queue, args=(update_queue2,dbnameblk, "black")).start()
    px.start()
    px.join()
    print("Processes started")