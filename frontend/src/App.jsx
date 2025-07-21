import React, { useState } from 'react';
import './App.css';

function App() {
  const [uploadedImage, setUploadedImage] = useState(null);
  const [resultImage, setResultImage] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [predictionError, setPredictionError] = useState(false);

  const [whiteScore, setWhiteScore] = useState(null);
  const [blackScore, setBlackScore] = useState(null);
  const [leadMessage, setLeadMessage] = useState("—");

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      setUploadedFile(file);
      setUploadedImage(null);
      setResultImage(null);
      setPredictionError(false);
    }
  };

  const handleSubmit = () => {
    if (!uploadedFile) {
      alert('Please upload an image before submitting.');
      return;
    }

    const previewUrl = URL.createObjectURL(uploadedFile);
    setUploadedImage(previewUrl);

    setIsProcessing(true);
    setProgress(0);

    const formData = new FormData();
    formData.append('image', uploadedFile);

    fetch("http://localhost:5001/predict", {
      method: "POST",
      body: formData,
    })
      .then((response) => {
        if (!response.ok) {
          return response.json().then((errorData) => {
            throw new Error(errorData.error || "Backend response error");
          });
        }
        return response.json();
      })
      .then((data) => {
        const imageUrl = "data:image/png;base64," + data.image;
        setResultImage(imageUrl);
        setPredictionError(false);

        setWhiteScore(data.white_score ?? "—");
        setBlackScore(data.black_score ?? "—");
        setLeadMessage(data.lead ?? "");
      })
      .catch((error) => {
        console.error("❌ Error sending image:", error);

        if (error.message === "corner_detection_failed") {
          alert("⚠️ Please upload a clear image of an Othello board.");
          setPredictionError("corner");
        } else if (error.message === "piece_detection_failed") {
          alert("⚠️ Could not detect pieces properly on the board.");
          setPredictionError("piece");
        } else if (error.message === "minimax_failed") {
          alert("⚠️ Something went wrong while computing the optimal move.");
          setPredictionError("minimax");
        } else {
          alert("⚠️ Unexpected error occurred.");
          setPredictionError("generic");
        }

        setResultImage(null);
      })
      .finally(() => {
        setIsProcessing(false);
        setProgress(100);
      });

    // Simulated progress bar
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 98) {
          clearInterval(interval);
          return 98;
        }
        return prev + 2;
      });
    }, 50);
  };

  const isGameOver = leadMessage.startsWith("Game over");
  const isBoardEmpty = leadMessage.startsWith("No pieces");

  return (
    <div className="container">
      <h1 className="title">Othello Recommender</h1>

      {/* Upload + Submit */}
      <div className="button-row right-align" style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
        <label className="custom-upload-button">
          Upload Image
          <input type="file" accept="image/*" onChange={handleImageUpload} hidden />
        </label>
        <button onClick={handleSubmit}>Submit</button>
      </div>

      {/* Filename */}
      <div style={{ marginBottom: '1rem', marginLeft: '60px', fontSize: '1.1rem' }}>
        {uploadedFile ? (
          <p>File Uploaded: <strong>{uploadedFile.name}</strong></p>
        ) : (
          <p>No file uploaded yet.</p>
        )}
      </div>

      {/* Images */}
      <div className="image-row">
        <div className={`image-box ${!uploadedImage ? 'placeholder' : ''}`}>
          {uploadedImage ? (
            <img src={uploadedImage} alt="Original" style={{ maxWidth: '100%', maxHeight: '100%' }} />
          ) : (
            <p>📷 Original Image</p>
          )}
        </div>

        <div style={{ display: 'flex', gap: '20px' }}>
          <div className={`image-box ${!resultImage && !predictionError ? 'placeholder' : ''}`}>
            {isProcessing ? (
              <div className="progress-container">
                <div className="progress-spinner" />
                <div className="progress-text">{progress}%</div>
              </div>
            ) : predictionError === "corner" ? (
              <div className="error-placeholder">⚠️ No prediction available. Please upload a clear Othello board.</div>
            ) : predictionError === "piece" ? (
              <div className="error-placeholder">⚠️ Unable to detect pieces properly. Please try again with a clearer image.</div>
            ) : predictionError === "minimax" ? (
              <div className="error-placeholder">⚠️ Something went wrong during move recommendation. Try again later.</div>
            ) : resultImage ? (
              <img src={resultImage} alt="Recommended Moves" style={{ maxWidth: '100%', maxHeight: '100%' }} />
            ) : (
              <p>🤖 Image Showing Recommended Moves</p>
            )}
          </div>

          {/* Legend (only show if game is active and not empty) */}
          {(resultImage && !predictionError && !isGameOver && !isBoardEmpty) && (
            <div className="legend right-of-image">
              <p>
                <span className="legend-icon white"></span>
                Recommended move for White
              </p>
              <p>
                <span className="legend-icon black"></span>
                Recommended move for Black
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Scoreboard */}
      {(whiteScore > 0 || blackScore > 0 || isGameOver || isBoardEmpty || leadMessage.includes("lead")) && (
        <div className="score-board">
          <p>White Score: {whiteScore ?? "—"}</p>
          <p>Black Score: {blackScore ?? "—"}</p>
          {leadMessage && <p>{leadMessage}</p>}
        </div>
      )}
    </div>
  );
}

export default App;
