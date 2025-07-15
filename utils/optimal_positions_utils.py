import numpy as np
# 8 possible directions: vertical, horizontal, diagonal
DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),          (0, 1),
    (1, -1),  (1, 0), (1, 1)
]

def is_on_board(x, y):
    return 0 <= x < 8 and 0 <= y < 8

def get_valid_moves(board, player):
    opponent = -player
    valid_moves = set()

    for row in range(8):
        for col in range(8):
            if board[row][col] != 0:
                continue  # already occupied

            for dx, dy in DIRECTIONS:
                x, y = row + dx, col + dy
                found_opponent = False

                # Step in the current direction
                while is_on_board(x, y) and board[x][y] == opponent:
                    x += dx
                    y += dy
                    found_opponent = True

                # Check if there's a sandwich: opponent(s) followed by your piece
                if found_opponent and is_on_board(x, y) and board[x][y] == player:
                    valid_moves.add((row, col))
                    break  # no need to check other directions

    return list(valid_moves)

def make_move(board, move, player):
    """
    Places a move on the board and flips opponent pieces.
    
    Parameters:
        board (np.ndarray): Current board state (8x8)
        move (tuple): (row, col) where player wants to move
        player (int): -1 for black, 1 for white
        
    Returns:
        np.ndarray: New board state after move
    """
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),          (0, 1),
                  (1, -1),  (1, 0),  (1, 1)]
    
    board = board.copy()
    row, col = move
    board[row, col] = player  # Place the piece

    for dr, dc in directions:
        r, c = row + dr, col + dc
        discs_to_flip = []

        while 0 <= r < 8 and 0 <= c < 8 and board[r, c] == -player:
            discs_to_flip.append((r, c))
            r += dr
            c += dc

        if 0 <= r < 8 and 0 <= c < 8 and board[r, c] == player:
            for fr, fc in discs_to_flip:
                board[fr, fc] = player

    return board

def evaluate_board(board):
    """
    Evaluates the board by counting pieces for both players.

    Returns:
    - eval_score: Net advantage for white (white - black)
    - white_score: Count of white pieces (represented as 1)
    - black_score: Count of black pieces (represented as -1)
    """
    white_score = int(np.sum(board == 1))
    black_score = int(np.sum(board == -1))
    eval_score = white_score - black_score
    return eval_score, white_score, black_score



def minimax(board, depth, alpha, beta, maximizing_player, player):
    """
    Minimax algorithm with alpha-beta pruning.

    Returns:
    - eval_score: Score difference for evaluation purposes
    - best_move: Move (row, col) with the best score
    - white_score: Final white piece count after best move
    - black_score: Final black piece count after best move
    """
    valid_moves = get_valid_moves(board, player)

    # Base case: evaluate static board when depth exhausted or no moves
    if depth == 0 or not valid_moves:
        eval_score, white_score, black_score = evaluate_board(board)
        return eval_score, None, white_score, black_score

    if maximizing_player:
        max_eval = float('-inf')
        best_move = None
        best_white = 0
        best_black = 0

        for move in valid_moves:
            new_board = make_move(board.copy(), move, player)
            eval_score, _, w_score, b_score = minimax(
                new_board, depth - 1, alpha, beta, False, -player
            )

            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
                best_white = w_score
                best_black = b_score

            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break  # Beta pruning

        return max_eval, best_move, best_white, best_black

    else:
        min_eval = float('inf')
        best_move = None
        best_white = 0
        best_black = 0

        for move in valid_moves:
            new_board = make_move(board.copy(), move, player)
            eval_score, _, w_score, b_score = minimax(
                new_board, depth - 1, alpha, beta, True, -player
            )

            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
                best_white = w_score
                best_black = b_score

            beta = min(beta, eval_score)
            if beta <= alpha:
                break  # Alpha pruning

        return min_eval, best_move, best_white, best_black
