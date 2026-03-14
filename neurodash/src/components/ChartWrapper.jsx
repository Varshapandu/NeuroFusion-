// src/components/ChartWrapper.jsx
import { ResponsiveContainer } from "recharts";
export default function ChartWrapper({ children, height = 220 }) {
  return <div style={{ height }} className="w-full"><ResponsiveContainer>{children}</ResponsiveContainer></div>;
}
