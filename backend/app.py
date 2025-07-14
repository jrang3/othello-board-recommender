from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import base64
from io import BytesIO
from PIL import Image
import sys
import numpy as np
import cv2

# Add root path so backend/app.py can import from utils/
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import hough_utils, piece_detection_utils, optimal_positions_utils



app = Flask(__name__)
CORS(app)

@app.route("/predict", methods=["POST"])
def predict():
    print(f"Reached predict!!!")
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    
    #Extract the image and convert to RGB
    image = request.files['image']
    img_pil = Image.open(image.stream).convert("RGB")
    img_np = np.array(img_pil)
    img_rgb = np.float32(img_np) / 255.0
    print(f"Converted Image to desired format")

    #Detect 4 corners
    corners = hough_utils.hough(img_rgb)
    if corners.shape != (4, 2):
        print("⚠️ Hough failed to detect exactly 4 corners.")
        return jsonify({"error": "corner_detection_failed"}), 400

    corners_list = corners.tolist()
    print(f"🟩 4 Corners: {corners_list}")

    #Detect each piece
    board_state = np.zeros((8, 8))
    dict_board = {} #Map each position on 2D board_state array to actual coordinate in the original image, so that when we get recommened move on 2d array we can easily obtain actual coordinate on the original board
    for row in range(8):
        for col in range(8):
            piece = piece_detection_utils.detect_piece(img_rgb, corners, row, col)
            board_state[row][col] = piece[0]
            avg_x, avg_y = piece[4]
            dict_board[(row, col)] = (avg_y, avg_x)
    #print(f"Dict_board: {dict_board}")

    #Now determine optimal moves for both players 
    # White
    white_best = None
    white_moves = optimal_positions_utils.get_valid_moves(board_state, player=1)
    if white_moves:
        _, white_best = optimal_positions_utils.minimax(board_state, 3, float('-inf'), float('inf'), True, 1)
        original_coordinates_white_best = dict_board[white_best]
        print(f"⚪ White optimal move: {white_best}, coordinates on original image: {original_coordinates_white_best}")
    else:
        print("⚪ White has no valid moves.")

    # Black
    black_best = None
    black_moves = optimal_positions_utils.get_valid_moves(board_state, player=-1)
    if black_moves:
        _, black_best =optimal_positions_utils. minimax(board_state, 3, float('-inf'), float('inf'), True, -1)
        original_coordinates_black_best = dict_board[black_best]
        print(f"⚫ Black optimal move: {black_best}, coordinates on original image: {original_coordinates_black_best}")
    else:
        print("⚫ Black has no valid moves.")
    
    #Now display the actual coordinates on the original image
    


    # Convert image to base64 string (Will Change at End!!!)
    img = Image.open(image.stream)
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')

    return jsonify({"image": img_str}), 200



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
