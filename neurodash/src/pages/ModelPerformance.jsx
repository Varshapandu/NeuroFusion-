// src/pages/ModelPerformance.jsx
import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, BarChart, Bar } from "recharts";
import ChartWrapper from "../components/ChartWrapper";
import Card from "../components/Card";

export default function ModelPerformance() {
  const [metrics, setMetrics] = useState(null);

  useEffect(() => {
    // mock now; replace with API call to backend metrics endpoint if you add one
    const acc = Array.from({ length: 20 }).map((_, i) => ({ epoch: i + 1, acc: 0.6 + i * 0.02 + (Math.random() - .5) * 0.02 }));
    const loss = Array.from({ length: 20 }).map((_, i) => ({ epoch: i + 1, loss: Math.exp(-i / 6) + (Math.random() - .5) * 0.02 }));
    const cm = [{ label: "TP", value: 40 }, { label: "FP", value: 5 }, { label: "FN", value: 3 }, { label: "TN", value: 52 }];
    setMetrics({ acc, loss, cm });
  }, []);

  if (!metrics) return <div className="text-gray-400">Loading metrics...</div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Model Performance</h1>
        <p className="text-gray-400 text-sm">Accuracy, loss curves and confusion matrix</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card title="Accuracy (per epoch)">
          <ChartWrapper height={260}>
            <LineChart data={metrics.acc}>
              <CartesianGrid stroke="#222" />
              <XAxis dataKey="epoch" stroke="#aaa" />
              <YAxis stroke="#aaa" />
              <Tooltip />
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
              <Tooltip />
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
