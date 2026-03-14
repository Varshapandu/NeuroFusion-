// src/pages/ModelPerformance.jsx
import { useEffect, useState } from "react";
import axios from "axios";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, BarChart, Bar } from "recharts";
import ChartWrapper from "../components/ChartWrapper";
import Card from "../components/Card";

export default function ModelPerformance() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      const response = await axios.get("http://127.0.0.1:5000/api/fl/status");
      const data = response.data;

      // Transform metrics_history into chart-compatible format
      const acc = (data.metrics_history || []).map((item, idx) => ({
        epoch: idx + 1,
        round: item.round,
        acc: typeof item.accuracy === 'number' ? item.accuracy : 0
      }));

      const loss = (data.metrics_history || []).map((item, idx) => ({
        epoch: idx + 1,
        round: item.round,
        loss: typeof item.loss === 'number' ? item.loss : 0
      }));

      // Parse confusion matrix from latest round (if available)
      const latestMetrics = data.metrics || {};
      let cm = [
        { label: "TP", value: 0 },
        { label: "FP", value: 0 },
        { label: "FN", value: 0 },
        { label: "TN", value: 0 }
      ];

      // If confusion_matrix is available, try to extract TP, FP, FN, TN
      if (Array.isArray(latestMetrics.confusion_matrix)) {
        try {
          const confMatrix = latestMetrics.confusion_matrix;
          // Assuming 2x2 confusion matrix [TN, FP], [FN, TP]
          if (confMatrix.length >= 2 && confMatrix[0].length >= 2) {
            cm = [
              { label: "TP", value: confMatrix[1]?.[1] || 0 },
              { label: "FP", value: confMatrix[0]?.[1] || 0 },
              { label: "FN", value: confMatrix[1]?.[0] || 0 },
              { label: "TN", value: confMatrix[0]?.[0] || 0 }
            ];
          }
        } catch (e) {
          console.warn("Could not parse confusion matrix:", e);
        }
      }

      setMetrics({ 
        acc: acc.length > 0 ? acc : generateMockData('acc'),
        loss: loss.length > 0 ? loss : generateMockData('loss'),
        cm 
      });
      setError(null);
    } catch (err) {
      console.error("Error fetching metrics:", err);
      setError("Failed to load metrics from server");
      // Fall back to mock data
      setMetrics({
        acc: generateMockData('acc'),
        loss: generateMockData('loss'),
        cm: [
          { label: "TP", value: 40 },
          { label: "FP", value: 5 },
          { label: "FN", value: 3 },
          { label: "TN", value: 52 }
        ]
      });
    } finally {
      setLoading(false);
    }
  };

  // Helper to generate mock data when backend has no data yet
  const generateMockData = (type) => {
    if (type === 'acc') {
      return Array.from({ length: 20 }).map((_, i) => ({
        epoch: i + 1,
        acc: 0.6 + i * 0.02 + (Math.random() - 0.5) * 0.02
      }));
    } else {
      return Array.from({ length: 20 }).map((_, i) => ({
        epoch: i + 1,
        loss: Math.exp(-i / 6) + (Math.random() - 0.5) * 0.02
      }));
    }
  };

  useEffect(() => {
    fetchMetrics();
    // Refresh every 5 seconds to get real-time updates
    const interval = setInterval(fetchMetrics, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !metrics) return (
    <div className="text-gray-400 text-center py-8">
      <div className="inline-block">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-purple-500"></div>
        <p className="mt-2">Loading metrics...</p>
      </div>
    </div>
  );

  if (!metrics) return <div className="text-gray-400">No metrics available yet. start a training run.</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-semibold">Model Performance</h1>
          <p className="text-gray-400 text-sm">Accuracy, loss curves and confusion matrix</p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={fetchMetrics}
            disabled={loading}
            className={`px-3 py-1 rounded text-sm transition ${
              loading
                ? "bg-gray-700 text-gray-500 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700 text-white"
            }`}
          >
            {loading ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-yellow-900/20 border border-yellow-600 text-yellow-300 p-3 rounded-lg text-sm">
          ⚠️ {error} (showing demo data)
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Accuracy (per epoch)">
          <ChartWrapper height={260}>
            <LineChart data={metrics.acc}>
              <CartesianGrid stroke="#222" />
              <XAxis dataKey="epoch" stroke="#aaa" />
              <YAxis stroke="#aaa" domain={[0, 1]} />
              <Tooltip formatter={(value) => value?.toFixed(4) || "N/A"} />
              <Line type="monotone" dataKey="acc" stroke="#60a5fa" dot={false} />
            </LineChart>
          </ChartWrapper>
        </Card>

        <Card title="Loss (per epoch)">
          <ChartWrapper height={260}>
            <LineChart data={metrics.loss}>
              <CartesianGrid stroke="#222" />
              <XAxis dataKey="epoch" stroke="#aaa" />
              <YAxis stroke="#aaa" />
              <Tooltip formatter={(value) => value?.toFixed(4) || "N/A"} />
              <Line type="monotone" dataKey="loss" stroke="#fb7185" dot={false} />
            </LineChart>
          </ChartWrapper>
        </Card>
      </div>

      <div>
        <Card title="Confusion Matrix">
          <BarChart width={400} height={180} data={metrics.cm}>
            <CartesianGrid stroke="#222" />
            <XAxis dataKey="label" stroke="#aaa" />
            <YAxis stroke="#aaa" />
            <Tooltip />
            <Bar dataKey="value" fill="#34d399" />
          </BarChart>
        </Card>
      </div>
    </div>
  );
}
