// src/pages/Preprocess.jsx
import { useEffect, useState } from "react";
import { preprocessEEG } from "../api/flaskApi";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

function MiniWave({ values, height = 60 }) {
  const data = values.map((v, i) => ({ x: i, y: v }));
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data}>
        <Line dataKey="y" stroke="#10b981" strokeWidth={1} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export default function Preprocess({ fileId }) {
  const [pre, setPre] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [channel, setChannel] = useState(0);
  const [showRaw, setShowRaw] = useState(false);
  const [view, setView] = useState("clean"); // clean | multi | spectrogram

  useEffect(() => {
  if (!fileId) {
    setMessage("No file selected. Upload an EEG file first.");
    setPre(null);
    return;
  }

  setMessage("");
  setLoading(true);

  (async () => {
    try {
      const res = await preprocessEEG(fileId);

      // ✅ DEBUG LOG MUST BE INSIDE THE ASYNC FUNCTION
      console.log("PREPROCESS RESPONSE:", res.data);

      // backend returns { preprocessed: {...}, spectrograms: [...] }
      const p = res.data.preprocessed || res.data || {};
      const specs = res.data.spectrograms || null;

      setPre({ ...p, spectrograms: specs });
    } catch (err) {
      console.error(err);
      setMessage("Failed to preprocess EEG. Check backend.");
    } finally {
      setLoading(false);
    }
  })();
}, [fileId]);



  const cleaned = pre?.cleaned || [];
  const raw = pre?.raw || [];
  const times = pre?.times || [];

  const channelCount = cleaned.length || raw.length || 0;
  const selectedClean = cleaned[channel] || [];
  const selectedRaw = raw[channel] || [];
  const spectrogramForChannel = pre?.spectrograms?.[channel] || null;

  // Prepare chart data for the selected channel
  const chartData = selectedClean.map((v, i) => ({
    t: times[i] ?? i,
    value: v,
    raw: selectedRaw[i]
  }));

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Preprocess EEG</h1>
        <p className="text-gray-400 text-sm">Signal cleaning & visualization</p>
      </div>

      {message && (
        <div className="text-sm text-gray-300 bg-gray-800 p-3 rounded-md">
          {message}
        </div>
      )}

      {loading && <div className="text-gray-400">Processing EEG...</div>}

      {!loading && pre && (
        <>
          {/* Controls */}
          <div className="flex items-center gap-4">
            <label className="text-sm">Channel</label>
            <select
              value={channel}
              onChange={(e) => setChannel(Number(e.target.value))}
              className="bg-gray-800 p-2 rounded"
            >
              {Array.from({ length: channelCount }).map((_, i) => (
                <option key={i} value={i}>
                  Ch {i + 1}
                </option>
              ))}
            </select>

            <label className="ml-4 text-sm">
              <input type="checkbox" checked={showRaw} onChange={() => setShowRaw(!showRaw)} />{" "}
              Show raw
            </label>

            <div className="ml-4">
              <button onClick={() => setView("clean")} className="px-3 py-1 bg-gray-700 rounded mr-1">Clean</button>
              <button onClick={() => setView("multi")} className="px-3 py-1 bg-gray-700 rounded mr-1">Multi</button>
              <button onClick={() => setView("spectrogram")} className="px-3 py-1 bg-gray-700 rounded">Spectrogram</button>
            </div>
          </div>

          {/* Main view */}
          {view === "clean" && (
            <div className="bg-gray-900 border border-gray-800 p-6 rounded-lg mt-4">
              <h2 className="text-lg font-medium mb-4">Cleaned EEG Signal (Ch {channel + 1})</h2>
              <div style={{ width: "100%", height: "360px" }}>
                  <ResponsiveContainer width="100%" height="100%">

                  <LineChart data={chartData}>
                    <CartesianGrid stroke="#333" />
                    <XAxis dataKey="t" stroke="#aaa" tick={{ fill: "#aaa" }} />
                    <YAxis stroke="#aaa" tick={{ fill: "#aaa" }} />
                    <Tooltip contentStyle={{ backgroundColor: "#111", border: "1px solid #333" }} />
                    <Line type="monotone" dataKey="value" stroke="#10b981" strokeWidth={2} dot={false} />
                    {showRaw && <Line type="monotone" dataKey="raw" stroke="#f97316" strokeWidth={1} dot={false} strokeDasharray="5 5" />}
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}

          {view === "multi" && (
            <div className="bg-gray-900 border border-gray-800 p-6 rounded-lg mt-4">
              <h2 className="text-lg font-medium mb-4">20-Channel Mini Grid</h2>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
                {Array.from({ length: Math.max(channelCount, 20) }).map((_, i) => (
                  <div key={i} className={`p-2 bg-gray-800 rounded ${i === channel ? "ring-2 ring-indigo-500" : ""}`}>
                    <div className="text-xs text-gray-400 mb-2">Ch {i + 1}</div>
                    <MiniWave values={(cleaned[i] || []).slice(0, 2000)} height={64} />
                  </div>
                ))}
              </div>
            </div>
          )}

          {view === "spectrogram" && (
            <div className="bg-gray-900 border border-gray-800 p-6 rounded-lg mt-4">
              <h2 className="text-lg font-medium mb-4">Spectrogram (Ch {channel + 1})</h2>
              {spectrogramForChannel ? (
                <div className="w-full h-72 bg-black/50 rounded p-2">
                  {/* We'll render spectrogram as an image via base64 if backend returns it,
                      otherwise fallback to a simple matrix view (the backend returns nested arrays) */}
                  <SpectrogramMatrix matrix={spectrogramForChannel} />
                </div>
              ) : (
                <div className="text-sm text-gray-400">No spectrogram available.</div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}

/* Small helper component to render spectrogram matrix as canvas image.
   This keeps frontend dependency light (no external plotting libs).
*/
function SpectrogramMatrix({ matrix }) {
  // matrix is a 2D array (freq × time) - use canvas to draw
  const ref = (node) => {
    if (!node || !matrix) return;
    const F = matrix.length;
    const T = matrix[0].length;
    const canvas = node;
    canvas.width = Math.min(900, T);
    canvas.height = Math.min(300, F);
    const ctx = canvas.getContext("2d");
    const img = ctx.createImageData(canvas.width, canvas.height);
    // flatten matrix -> normalize values
    let min = Infinity, max = -Infinity;
    for (let i=0;i<F;i++) for (let j=0;j<T;j++){
      const v = matrix[i][j];
      if (v < min) min = v;
      if (v > max) max = v;
    }
    const range = max - min + 1e-8;
    for (let y=0;y<canvas.height;y++){
      const fi = Math.floor((y / canvas.height) * F);
      for (let x=0;x<canvas.width;x++){
        const tj = Math.floor((x / canvas.width) * T);
        const v = matrix[fi][tj];
        const norm = Math.round(255 * (v - min) / range);
        const idx = (y * canvas.width + x) * 4;
        // map to a colormap: use simple jet-ish mapping
        img.data[idx+0] = norm; // R
        img.data[idx+1] = 255 - norm; // G
        img.data[idx+2] = 128; // B
        img.data[idx+3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
  };
  return <canvas ref={ref} style={{ width: "100%", height: 300 }} />;
}
