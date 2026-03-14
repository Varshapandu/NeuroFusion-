import { useState } from "react";
import { predictEEG } from "../api/flaskApi";

export default function Predict({ fileId }) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState("");

  const runPrediction = async () => {
    if (!fileId) {
      setMsg("Upload an EEG file first.");
      return;
    }

    setMsg("");
    setLoading(true);

    try {
      const res = await predictEEG(fileId);
      setResult(res.data);
    } catch (err) {
      console.error(err);
      setMsg("Prediction failed. Check backend logs.");
    }

    setLoading(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Predict Harmful Activity</h1>
        <p className="text-gray-400 text-sm">Model inference results</p>
      </div>

      <button
        onClick={runPrediction}
        className="px-6 py-2 bg-blue-600 rounded hover:bg-blue-700"
      >
        Run Prediction
      </button>

      {loading && <div className="text-gray-400">Running prediction...</div>}
      {msg && <div className="text-red-400">{msg}</div>}

      {result && (
        <div className="bg-gray-900 p-6 rounded-lg border border-gray-700 space-y-6">

          {/* SCORE */}
          <div>
            <h2 className="text-xl font-semibold">Risk Score</h2>
             <p className="text-green-400 text-4xl font-bold">
             {result.risk_score ?? "--"}%
             </p>

          </div>

          {/* LABEL */}
          <div>
            <h2 className="text-lg font-semibold">Detected Pattern</h2>
            <p className="text-white text-xl">{result.labels?.[0] || "N/A"}</p>
          </div>

          {/* SIMPLE EXPLANATION */}
          <div className="bg-gray-800 p-4 rounded-md">
            <h3 className="font-semibold text-gray-300">Summary</h3>
            <p className="text-gray-400">{result.plain_explanation}</p>
          </div>

          {/* DOCTOR SUMMARY */}
          {result.doctor_summary && (
            <div className="bg-gray-800 p-4 rounded-md space-y-2">
              <h3 className="font-semibold text-gray-300">AI Neurologist Analysis</h3>
              <p className="text-gray-400">
                <b>Interpretation:</b> {result.doctor_summary.interpretation}
              </p>
              <p className="text-gray-400">
                <b>Model Certainty:</b> {result.doctor_summary.model_certainty}
              </p>

              <p className="text-gray-400">
                <b>Risk Probability:</b> {result.doctor_summary.risk_percent}%
              </p>

              <p className="text-yellow-400 font-semibold">
                <b>Decision:</b> {result.doctor_summary.decision}
              </p>


              {result.doctor_summary.notes?.length > 0 && (
                <ul className="list-disc list-inside text-gray-400">
                  {result.doctor_summary.notes.map((n, i) => (
                    <li key={i}>{n}</li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {/* VISUAL OUTPUTS */}
          <div className="space-y-4">
            <h3 className="font-semibold text-gray-300">Visual Explainability</h3>

            {/* GRADCAM */}
            {result.file_paths?.gradcam && (
              <div>
                <p className="text-gray-400 mb-2">Grad-CAM Heatmap</p>
                <img
                  src={`http://127.0.0.1:5000/api/get-file?path=${encodeURIComponent(result.file_paths.gradcam)}`}
                  alt="GradCAM"
                  className="rounded-lg w-full max-w-xl border border-gray-700"
                />
              </div>
            )}

            {/* PSD */}
            {result.file_paths?.psd && (
              <div>
                <p className="text-gray-400 mb-2">Power Spectral Density</p>
                <img
                  src={`http://127.0.0.1:5000/api/get-file?path=${encodeURIComponent(result.file_paths.psd)}`}
                  alt="PSD"
                  className="rounded-lg w-full max-w-xl border border-gray-700"
                />
              </div>
            )}

            {/* SPECTROGRAM */}
            {result.file_paths?.spectrogram && (
              <div>
                <p className="text-gray-400 mb-2">Spectrogram</p>
                <img
                  src={`http://127.0.0.1:5000/api/get-file?path=${encodeURIComponent(result.file_paths.spectrogram)}`}
                  alt="Spectrogram"
                  className="rounded-lg w-full max-w-xl border border-gray-700"
                />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
