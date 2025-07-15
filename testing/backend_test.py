import os
import sys

# 👇 Add root path so Python can find 'utils' from project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import cv2
import json
import matplotlib.pyplot as plt
import ast

# 👇 Now import from 'utils' folder
from utils import hough_utils
from utils import piece_detection_utils


def detect_corners():
    datadir = 'Test_Images/'
    savedir = 'Corners/'
    for i in range(1, 11): 
        print(f"Detecting Corners on input image #{i}")
        image_file = f'Othello_Game_Board{i}.png'
        input_image_path = os.path.join(datadir, image_file)

        img = np.float32(cv2.imread(input_image_path, cv2.IMREAD_COLOR_RGB) / 255.0)
        corners = hough_utils.hough(img)
        corners_list = corners.tolist()

        # Save corners directly to a .json file
        corner_file_path = os.path.join(savedir, f'corners_{i}.json')
        with open(corner_file_path, 'w') as f:
            json.dump(corners_list, f)

        print(f"✅ Saved corners to: {corner_file_path}")


def idenitfy_board_pieces():
    #Iterate over Test_Images and Corners_Test_Images folders and for each image use the corresponding corners to detect value of each piece 
    datadir_images = 'Test_Images/'
    datadir_corners = 'Corners/'
    matches = 0
    for i in range(3,4):
        # Construct image and corner file names
        image_file = f'Othello_Game_Board{i}.png'
        corner_file = f'corners_{i}.json'
        full_image_path = os.path.join(datadir_images, image_file)
        full_corner_path = os.path.join(datadir_corners, corner_file)

        # Check if both the image and corner file exist
        if not os.path.exists(full_image_path):
            print(f"Image not found, skipping: {image_file}")
            continue

        if not os.path.exists(full_corner_path):
            print(f"Corner file not found, skipping: {corner_file}")
            continue

        # Load the image and the corners
        input_image = np.float32(cv2.imread(full_image_path, cv2.IMREAD_COLOR) / 255.0)
        plt.figure(figsize=(3, 3))  # Adjust the size as needed
        plt.imshow(input_image)
        plt.title(image_file)
        plt.axis("off")  # Optional, hides the axes
        plt.show()
        with open(full_corner_path, 'r') as f:
            corners = eval(f.read())

        # Convert corners to a NumPy array
        corners = np.array(corners, dtype=np.float32)
        #Skip we don't have 4 corners
        if len(corners) != 4: #Note we need exactly 4 corners for piece detection algorithm to work 
            print(f"Skipping image #{i} because there aren't exactly 4 corners that were detected")
            print("Accuracy: 0 Score: 0")
            continue


        # Extract the board state
        board_state = np.zeros((8, 8))

        for row in range(8):
            for col in range(8):
                piece = piece_detection_utils.detect_piece(input_image, corners, row, col)
                board_state[row][col] = piece[0]

                if row == 0 and col == 0:
                    plt.figure(figsize=(3, 3))
                    plt.imshow(piece[1])
                    plt.show()
                
                #Display the avg_x, avg_y cooridnate on the real input image (Note this was done for testing purpose to ensure that avg_x and avg_y indeed show up on the right location on the original image!)
                avg_x, avg_y = piece[4]
                plt.figure(figsize=(6, 6))
                plt.imshow(input_image)
                plt.scatter(avg_x, avg_y, c='red', s=100)
                plt.title(f"Overlay of Region Corners for Square ({row}, {col})")
                plt.show()
            

        # Print the final board state and save it
        # print(f"Board State for {image_file}:")
        # print(board_state)
        board_path = os.path.join("Board_States", image_file.replace(".png", ".npy"))
        np.save(board_path, board_state)
        # print(f"✅ Saved board state to: {board_path}")

        matches += piece_detection_utils.compare_board_states(board_state, i)
    accuracy = (matches / (640)) * 100
    print(f"Total Piece Detection Accuracy Across All Boards: {accuracy:.2f}%\n")
    

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

def evaluate_board(board, player):
    # Score: player pieces - opponent pieces
    player_count = np.sum(board == player)         # Sum up all the piece values that = player's value
    opponent_count = np.sum(board == -player)      # Sum up all the piece values that = opponent's value
    return player_count - opponent_count           # Return the net advantage for the current player


def minimax(board, depth, alpha, beta, maximizing_player, player):
    valid_moves = get_valid_moves(board, player)
    
    if depth == 0 or not valid_moves:
        return evaluate_board(board, player), None

    best_move = None

    if maximizing_player:
        max_eval = float('-inf')
        for move in valid_moves:
            new_board = make_move(board.copy(), move, player) #Appropriate tokens flip based on a spot on the board that a player selects to place their token 
            eval_score, _ = minimax(new_board, depth - 1, alpha, beta, False, -player) #Now its other player's turn so we go down a node in the tree
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_move = move
            
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break  # Beta cutoff (prune)
        
        return max_eval, best_move

    else:
        min_eval = float('inf')
        for move in valid_moves:
            new_board = make_move(board.copy(), move, player)
            eval_score, _ = minimax(new_board, depth - 1, alpha, beta, True, -player)
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_move = move
            
            beta = min(beta, eval_score)
            if beta <= alpha:
                break  # Alpha cutoff (prune)
        
        return min_eval, best_move

def determine_optimal_moves():
    for i in range(1, 11):  
        board_path = f"Board_States/Othello_Game_Board{i}.npy"
        board = np.load(board_path)
        
        print(f"\n🔍 Board {i}")
        print(board)

        # White
        white_best = None
        white_moves = get_valid_moves(board, player=1)
        if white_moves:
            _, white_best = minimax(board, 3, float('-inf'), float('inf'), True, 1)
            print(f"⚪ White optimal move: {white_best}")
        else:
            print("⚪ White has no valid moves.")

        # Black
        black_best = None
        black_moves = get_valid_moves(board, player=-1)
        if black_moves:
            _, black_best = minimax(board, 3, float('-inf'), float('inf'), True, -1)
            print(f"⚫ Black optimal move: {black_best}")
        else:
            print("⚫ Black has no valid moves.")

def process_images():
    # Step 1: Detect corners off the board and save them in json files
    #detect_corners() #This commented out to save time when testing

    #Step 2: Determine value of each grid cell and save them into 2d array
    idenitfy_board_pieces()

    # print("Now displaying optimal move for each individual board")
    #Step 3 Determine Optimal Move for each player
    determine_optimal_moves()

if __name__ == "__main__":
    board = process_images()


