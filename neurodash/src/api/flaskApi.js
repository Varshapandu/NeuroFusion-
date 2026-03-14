// src/api/flaskApi.js
import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:5000/api", // note: mounted blueprint at /api
  // withCredentials: true   // enable if you need cookies/auth
});

// Upload EEG file -> POST /api/upload
export const uploadEEG = (file) => {
  const formData = new FormData();
  formData.append("file", file);
  return API.post("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
};

// Preprocess EEG -> POST /api/process_eeg
export const preprocessEEG = (fileId) =>
  API.post("/process_eeg", { file_id: fileId });

// Predict harmful brain activity -> POST /api/predict
export const predictEEG = async (fileId) => {
  return API.post("/predict", {
    file_id: fileId,
    include_explanations: true,   // ask backend for detailed explanation
    include_files: true           // request GradCAM, PSD, Spectrogram paths
  });
};
// FL Node Status
export const getFLStatus = () => API.get("/fl/status");

// Supernode Sync
export const triggerSupernodeSync = () => API.post("/supernode/sync");

// Live Logs (websocket URL) - Socket.IO client will use /logs namespace on 127.0.0.1:5000
export const logsWebSocketURL = "ws://127.0.0.1:5000/logs";
