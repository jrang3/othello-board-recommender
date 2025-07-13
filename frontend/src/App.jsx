import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [uploadedImage, setUploadedImage] = useState(null);
  const [resultImage, setResultImage] = useState(null);
  const [uploadedFile, setUploadedFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0); // NEW

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      setUploadedFile(file);
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

    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setResultImage(previewUrl);
          setIsProcessing(false);
          return 100;
        }
        return prev + 2;
      });
    }, 50); // Increase every 50ms → ~2.5 seconds total
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
        <div className={`image-box ${!uploadedImage ? 'placeholder' : ''}`}>
          {uploadedImage ? (
            <img src={uploadedImage} alt="Original" style={{ maxWidth: '100%', maxHeight: '100%' }} />
          ) : (
            <p>📷 Original Image</p>
          )}
        </div>

        <div className={`image-box ${!resultImage ? 'placeholder' : ''}`}>
          {isProcessing ? (
            <div className="progress-container">
              <div className="progress-spinner" />
              <div className="progress-text">{progress}%</div>
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
