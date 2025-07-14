import React, { useState } from 'react';
import './App.css';

function App() {
  const [uploadedImage, setUploadedImage] = useState(null);
  const [resultImage, setResultImage] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [predictionError, setPredictionError] = useState(false);

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      setUploadedFile(file);
      setUploadedImage(null);          // Clear previous preview
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
    setUploadedImage(previewUrl); // Show left image only upon submission


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
        setPredictionError(false); // ensure it's cleared
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

    // Fake progress bar animation
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

  return (
    <div className="container">
      <h1 className="title">Othello Recommender</h1>

      <div className="button-row right-align">
        <label className="custom-upload-button">
          Upload Image
          <input type="file" accept="image/*" onChange={handleImageUpload} hidden />
        </label>
        <button onClick={handleSubmit}>Submit</button>
      </div>

      <div className="image-row">
        {/* Left Image */}
        <div className={`image-box ${!uploadedImage ? 'placeholder' : ''}`}>
          {uploadedImage ? (
            <img src={uploadedImage} alt="Original" style={{ maxWidth: '100%', maxHeight: '100%' }} />
          ) : (
            <p>📷 Original Image</p>
          )}
        </div>

        {/* Right Image */}
        <div className={`image-box ${!resultImage && !predictionError ? 'placeholder' : ''}`}>
        {isProcessing ? (
          <div className="progress-container">
            <div className="progress-spinner" />
            <div className="progress-text">{progress}%</div>
          </div>
        ) : predictionError === "corner" ? (
          <div className="error-placeholder">
            ⚠️ No prediction available. Please upload a clear Othello board.
          </div>
        ) : predictionError === "piece" ? (
          <div className="error-placeholder">
            ⚠️ Unable to detect pieces properly. Please try again with a clearer image.
          </div>
        ) : predictionError === "minimax" ? (
          <div className="error-placeholder">
            ⚠️ Something went wrong during move recommendation. Try again later.
          </div>
        ) : resultImage ? (
          <img src={resultImage} alt="Recommended Moves" style={{ maxWidth: '100%', maxHeight: '100%' }} />
        ) : (
          <p>🤖 Image Showing Recommended Moves</p>
        )}
        
        </div>
      </div>

      <div className="score-board">
        <p>White Score: —</p>
        <p>Black Score: —</p>
        <p>Display Who is in Lead: —</p>
      </div>
    </div>
  );
}

export default App;
