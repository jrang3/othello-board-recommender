# 🕹️ Othello Recommender

This is a full-stack web application that recommends the optimal move for each player in the game of Othello. Given an image of a real-world Othello board, the app uses computer vision to detect the board state, analyze the best moves using a minimax algorithm, and display results visually.

---

## 📸 Features

- Upload a photo of an Othello board (real or printed)
- Automatically detects the board layout and piece positions
- Computes the best move for both Black and White using Minimax + Alpha-Beta pruning
- Displays board state and suggested moves with overlays
- Tracks and allows replay of previous submissions

---

## 🧠 Tech Stack

- **Frontend**: React.js (Vite + App.jsx)
- **Backend**: Python (Flask)
- **Computer Vision**: OpenCV, NumPy
- **AI/Logic**: Minimax Algorithm
- **Database**: SQLite (stores submission history)

---

## 🚀 Getting Started

### 🔁 1. Clone the Repository

```bash
git clone https://github.com/your-username/othello-recommender.git
cd othello-recommender
```

### 🛠️ 2. Backend Setup (Python + Flask)

```bash
cd backend

# (Optional but recommended) Create and activate a virtual environment:
# On macOS/Linux:
python3 -m venv venv
source venv/bin/activate

# On Windows:
# python -m venv venv
# venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Start the Flask backend
python app.py  # Runs at http://localhost:5001

# ⚠️ Make sure Python 3.7+ is installed
```

### 💻 3. Frontend Setup (React + Vite)

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev  # Runs at http://localhost:5173
```
