# QLearnCheckerBoye
super simple reinforced learning checkers AI

This code requires you to set up two mySQL databases ('checker_smol' and 'checker_black_smol' by default)

This checkers AI plays on a 3 by 6 sized board and implements a simple Q-learning algorithm to learn to play checkers.
The only actually relevant files left in this repository are:
playerchecker.py (for a human player to play a game against the AI)
and learncheckers.py (learn checkers by playing against another qlearning AI)

Gameplay takes place on a text-based board. Users must input in the form "start_pos, end_pos" to make moves.
The game follows standard checkers rules, where a jump must be made if possible and chained jumps are allowed.

For the sake of simplicity, this game considers a match to be tied if no pieces have been captured within X turns.

To implement self play, two q-learning checkers AIs face off against each others. In order to facilitate greater variance in moves, the black checkers AI always starts with a random move, and every 20 games plays all moves randomly.

Because of the way ties are implemented, it seems that in the checker AI's self play ties are the most common outcome.
This is a very naiive implementation of Qlearning, so it takes quite a large number of games to get any tangible learning results.
Moves are stored and read from an SQL database (implemented in this way for the sake of learning to do it), which probably contributes quite a bit to slowing down the learning process.
