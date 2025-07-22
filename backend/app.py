from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import base64
from io import BytesIO
from PIL import Image
import sys
import numpy as np
import cv2
import sqlite3
import uuid

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
    try:
        for row in range(8):
            for col in range(8):
                piece = piece_detection_utils.detect_piece(img_rgb, corners, row, col)
                board_state[row][col] = piece[0]
                avg_x, avg_y = piece[4]
                dict_board[(row, col)] = (avg_y, avg_x)
    except Exception as e:
        print("⚠️ Piece detection failed:", e)
        return jsonify({"error": "piece_detection_failed"}), 400

    # Obtain actual scores on current board so that we don't detect score when recommened moves shown (score of original board)
    _, white_score, black_score = optimal_positions_utils.evaluate_board(board_state)

    # Check for special board states
    board_is_empty = not np.any(board_state != 0)
    board_is_full = not np.any(board_state == 0)

    # Check valid moves
    white_moves = optimal_positions_utils.get_valid_moves(board_state, player=1)
    black_moves = optimal_positions_utils.get_valid_moves(board_state, player=-1)

    white_best = black_best = original_coordinates_white_best = original_coordinates_black_best = None

    # Determine message and skip move prediction if applicable
    if board_is_empty:
        lead_message = "No pieces on the board yet — the game hasn’t started."
    elif board_is_full or (not white_moves and not black_moves):
        if white_score > black_score:
            lead_message = "Game over. ⚪ White wins!"
        elif black_score > white_score:
            lead_message = "Game over. ⚫ Black wins!"
        else:
            lead_message = "Game over. It’s a tie!"
    else:
        if white_moves:
            _, white_best, _, _ = optimal_positions_utils.minimax(
                board_state, 3, float('-inf'), float('inf'), True, 1
            )
            original_coordinates_white_best = dict_board[white_best]
            print(f"⚪ White optimal move: {white_best}, coordinates on original image: {original_coordinates_white_best}")
        else:
            print("⚪ White has no valid moves.")

        if black_moves:
            _, black_best, _, _ = optimal_positions_utils.minimax(
                board_state, 3, float('-inf'), float('inf'), True, -1
            )
            original_coordinates_black_best = dict_board[black_best]
            print(f"⚫ Black optimal move: {black_best}, coordinates on original image: {original_coordinates_black_best}")
        else:
            print("⚫ Black has no valid moves.")

        # Ongoing game status
        if white_score > black_score:
            lead_message = "White is currently in the lead."
        elif black_score > white_score:
            lead_message = "Black is currently in the lead."
        else:
            lead_message = "The game is currently tied."

    # Draw annotated image with best moves (if applicable)
    img_annotated = draw_optimal_moves(
        img_rgb,
        original_coordinates_white_best if white_best else None,
        original_coordinates_black_best if black_best else None
    )

    # Encode image to base64
    buffered = BytesIO()
    Image.fromarray(img_annotated).save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

   

    # Create submission ID and base64 of original image
    submission_id = str(uuid.uuid4())
    original_filename = image.filename

    # Save original image to base64
    buffered_orig = BytesIO()
    Image.fromarray((img_rgb * 255).astype(np.uint8)).save(buffered_orig, format="PNG")
    original_img_str = base64.b64encode(buffered_orig.getvalue()).decode("utf-8")

    # Store in database
    try:
        conn = sqlite3.connect("submissions.db")
        cursor = conn.cursor()

        # Create table with timestamp
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                original_filename TEXT UNIQUE,  -- Prevent duplicates
                original_image_base64 TEXT,
                result_image_base64 TEXT,
                white_score INTEGER,
                black_score INTEGER,
                lead_message TEXT
            )
        """)

        # Check for duplicate by filename
        cursor.execute("SELECT 1 FROM submissions WHERE original_filename = ?", (original_filename,))
        if cursor.fetchone():
            print(f"⚠️ Duplicate filename '{original_filename}' detected. Skipping insert.")
        else:
            # ✅ Use datetime('now') directly in SQL
            cursor.execute("""
                INSERT INTO submissions (
                    id, timestamp, original_filename, original_image_base64,
                    result_image_base64, white_score, black_score, lead_message
                )
                VALUES (?, datetime('now'), ?, ?, ?, ?, ?, ?)
            """, (
                submission_id,
                original_filename,
                original_img_str,
                img_str,
                int(white_score),
                int(black_score),
                lead_message
            ))
            conn.commit()
            print(f"✅ Submission saved with ID {submission_id}")

        conn.close()

    except Exception as e:
        print("⚠️ Failed to save to database:", e)




    return jsonify({
        "image": img_str,
        "white_score": int(white_score),
        "black_score": int(black_score),
        "lead": lead_message
    }), 200

@app.route("/history/<submission_id>", methods=["GET"])
def get_submission(submission_id):
    try:
        # Connect to your database
        conn = sqlite3.connect("submissions.db")
        cursor = conn.cursor()

        # Fetch submission by ID
        cursor.execute("SELECT original_filename, original_image_base64, result_image_base64, white_score, black_score, lead_message FROM submissions WHERE id = ?", (submission_id,))
        row = cursor.fetchone()

        conn.close()

        if row:
            return jsonify({
                "filename": row[0],
                "original_image": row[1],
                "image": row[2],
                "white_score": row[3],
                "black_score": row[4],
                "lead": row[5]
            })
        else:
            return jsonify({"error": "submission_not_found"}), 404

    except Exception as e:
        print("❌ Failed to load previous submission:", e)
        return jsonify({"error": "internal_error"}), 500

@app.route("/history", methods=["GET"])
def history():
    try:
        conn = sqlite3.connect("submissions.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id, original_filename, timestamp FROM submissions ORDER BY timestamp DESC")
        rows = cursor.fetchall()
        conn.close()

        submissions = []
        for row in rows:
            submissions.append({
                "id": row[0],
                "filename": row[1],
                "timestamp": row[2]
            })

        return jsonify(submissions)

    except Exception as e:
        print("❌ Failed to fetch history:", e)
        return jsonify({"error": "internal_error"}), 500



def draw_optimal_moves(image, white_coord=None, black_coord=None):
    """
    Draws circle markers with red outlines on the image at the specified white and black
    optimal move coordinates.

    Parameters:
    - image: np.ndarray (float32 image normalized to 0–1, RGB)
    - white_coord: Tuple (y, x) or None
    - black_coord: Tuple (y, x) or None
    - marker_radius: int or None — if None, will be computed based on image size

    Returns:
    - image with circles drawn (as np.uint8 RGB image)
    """
    image_copy = (image.copy() * 255).astype("uint8")
    height, width = image_copy.shape[:2]
    cell_size = min(height, width) / 8
    marker_radius = int(cell_size * 0.25)  # 30% of a cell; adjust 0.3 if needed
    marker_radius = max(3, marker_radius)
    print(f"marker_radius: {marker_radius}")

    if white_coord:
        x_w = int(round(white_coord[1]))
        y_w = int(round(white_coord[0]))
        cv2.circle(image_copy, (x_w, y_w), marker_radius + 4, (255, 0, 0), -1)      # Red border
        cv2.circle(image_copy, (x_w, y_w), marker_radius, (255, 255, 255), -1)     # White fill

    if black_coord:
        x_b = int(round(black_coord[1]))
        y_b = int(round(black_coord[0]))
        cv2.circle(image_copy, (x_b, y_b), marker_radius + 4, (255, 0, 0), -1)      # Red border
        cv2.circle(image_copy, (x_b, y_b), marker_radius, (0, 0, 0), -1)           # Black fill

    return image_copy





if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
