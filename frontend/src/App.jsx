import React, { useState, useEffect } from "react";
import "./App.css";

function App() {
  const [uploadedFile, setUploadedFile] = useState(null);
  const [uploadedImage, setUploadedImage] = useState(null);
  const [resultImage, setResultImage] = useState(null);
  const [whiteScore, setWhiteScore] = useState(null);
  const [blackScore, setBlackScore] = useState(null);
  const [leadMessage, setLeadMessage] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [predictionError, setPredictionError] = useState(null);
  const [previousSubmissions, setPreviousSubmissions] = useState([]);
  const [selectedSubmissionId, setSelectedSubmissionId] = useState(null);
  const [isGameOver, setIsGameOver] = useState(false);
  const [isBoardEmpty, setIsBoardEmpty] = useState(false);

  useEffect(() => {
    fetch("http://localhost:5001/history")
      .then((res) => res.json())
      .then((data) => setPreviousSubmissions(data))
      .catch((err) => console.error("❌ Failed to fetch submission history:", err));
  }, []);

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    setUploadedFile(file);
    setResultImage(null);
    setPredictionError(null);
  };

  const clearScores = () => {
    setWhiteScore(null);
    setBlackScore(null);
    setLeadMessage("");
  };
  

  const handleSubmit = () => {
    if (!uploadedFile) {
      alert("Please upload an image before submitting.");
      return;
    }

    const previewUrl = URL.createObjectURL(uploadedFile);
    setUploadedImage(previewUrl);

    setIsProcessing(true);
    setProgress(0);

    const formData = new FormData();
    formData.append("image", uploadedFile);

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
        clearScores();
        setResultImage(null);
      })
      .finally(() => {
        setIsProcessing(false);
        setProgress(100);

         // Refresh dropdown
        fetch("http://localhost:5001/history")
        .then((res) => res.json())
        .then((data) => setPreviousSubmissions(data))
        .catch((err) => console.error("❌ Failed to refetch submission history:", err));
      });

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

  const handleSubmissionSelect = (submissionId) => {
    if (!submissionId) return;

    fetch(`http://localhost:5001/history/${submissionId}`)
      .then((res) => res.json())
      .then((data) => {
        setSelectedSubmissionId(submissionId);
        setResultImage("data:image/png;base64," + data.image);
        setUploadedImage("data:image/png;base64," + data.original_image);
        setWhiteScore(data.white_score ?? "—");
        setBlackScore(data.black_score ?? "—");
        setLeadMessage(data.lead ?? "");
        setPredictionError(null); // ✅ Reset error so the scores and images show up
      })
      .catch((err) => {
        console.error("❌ Error loading previous submission:", err);
        alert("Failed to load previous submission.");
      });
  };

  return (
    <div className="container">
      <h1 className="title">Othello Recommender</h1>

      <div className="button-row right-align" style={{ display: "flex", alignItems: "center", gap: "2rem" }}>
        <label className="custom-upload-button">
          Upload Image
          <input type="file" accept="image/*" onChange={handleImageUpload} hidden />
        </label>
        <button onClick={handleSubmit}>Submit</button>
      </div>

      <div className="dropdown-row" style={{ marginTop: "1rem", marginLeft: "60px" }}>
        <label style={{ marginRight: "0.5rem", fontWeight: "bold" }}>Previous Uploads:</label>
        <select
          value={selectedSubmissionId || ""}
          onChange={(e) => handleSubmissionSelect(e.target.value)}
          style={{ padding: "0.4rem", fontSize: "1rem", borderRadius: "6px" }}
        >
          <option value="">Select a previous image</option>
          {previousSubmissions.map((item) => (
            <option key={item.id} value={item.id}>
              {item.filename}
            </option>
          ))}
        </select>
      </div>

      <div style={{ marginBottom: "1rem", marginLeft: "60px", fontSize: "1.1rem" }}>
        {uploadedFile ? (
          <p>Most Recent File Uploaded: <strong>{uploadedFile.name}</strong></p>
        ) : (
          <p>No new file uploaded yet.</p>
        )}
      </div>

      <div className="image-row">
        <div className={`image-box ${!uploadedImage ? "placeholder" : ""}`}>
          {uploadedImage ? (
            <img src={uploadedImage} alt="Original" style={{ maxWidth: "100%", maxHeight: "100%" }} />
          ) : (
            <p>📷 Original Image</p>
          )}
        </div>

        <div style={{ display: "flex", gap: "20px" }}>
          <div className={`image-box ${!resultImage && !predictionError ? "placeholder" : ""}`}>
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
              <img src={resultImage} alt="Recommended Moves" style={{ maxWidth: "100%", maxHeight: "100%" }} />
            ) : (
              <p>🤖 Image Showing Recommended Moves</p>
            )}
          </div>

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