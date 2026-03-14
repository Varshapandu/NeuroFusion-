import { useEffect, useState, useRef } from "react";
import { io } from "socket.io-client";

// Icons per log level
const levelIcons = {
  INFO: "ℹ️",
  WARNING: "⚠️",
  ERROR: "❌",
  SUCCESS: "✔️",
  CLIENT: "💻",
  OTHER: "•",
};

export default function Logs() {
  const [logs, setLogs] = useState([]);
  const [connected, setConnected] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);

  const [filters, setFilters] = useState({
    INFO: true,
    WARNING: true,
    ERROR: true,
    SUCCESS: true,
    CLIENT: true,
    OTHER: true,
  });

  const containerRef = useRef(null);
  const socketRef = useRef(null);

  // Extract log level from raw message
  const parseLevel = (line) => {
    if (line.includes("[INFO]")) return "INFO";
    if (line.includes("[WARNING]")) return "WARNING";
    if (line.includes("[ERROR]")) return "ERROR";
    if (line.includes("[SUCCESS]")) return "SUCCESS";
    if (line.includes("[CLIENT]")) return "CLIENT";
    return "OTHER";
  };

  // Color coding for each log level
  const levelColors = {
    INFO: "text-blue-300",
    WARNING: "text-yellow-300",
    ERROR: "text-red-400",
    SUCCESS: "text-green-400",
    CLIENT: "text-purple-300",
    OTHER: "text-gray-300",
  };

  // Format a timestamp
  const getTime = () => {
    return new Date().toLocaleTimeString("en-US", { hour12: false });
  };

  // Connect WebSocket + format messages beautifully
  useEffect(() => {
    const socket = io("http://127.0.0.1:5000/logs");
    socketRef.current = socket;

    socket.on("connect", () => setConnected(true));
    socket.on("disconnect", () => setConnected(false));

    socket.on("log", (msg) => {
      const level = parseLevel(msg);
      const entry = {
        time: getTime(),
        level,
        msg,
      };
      setLogs((prev) => [...prev.slice(-300), entry]);
    });

    return () => socket.disconnect();
  }, []);

  // Auto scroll
  useEffect(() => {
    if (autoScroll && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  // Apply filtering
  const visibleLogs = logs.filter((l) => filters[l.level]);

  const toggleFilter = (key) => {
    setFilters((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Live Training Logs</h1>
          <p className="text-gray-400 text-sm">Federated Learning stream</p>
        </div>

        <div className="flex gap-3">
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className="px-3 py-1 text-sm rounded bg-gray-700 hover:bg-gray-600"
          >
            {autoScroll ? "Pause Scroll" : "Resume Scroll"}
          </button>

          <button
            onClick={() => setLogs([])}
            className="px-3 py-1 text-sm rounded bg-red-600 hover:bg-red-500"
          >
            Clear
          </button>
        </div>
      </div>

      {/* WebSocket status */}
      <div className="text-sm text-gray-400">
        WebSocket:{" "}
        {connected ? (
          <span className="text-green-400">Connected</span>
        ) : (
          <span className="text-red-400">Disconnected</span>
        )}
      </div>

      {/* Filters */}
      <div className="flex gap-2 flex-wrap mb-2">
        {Object.keys(filters).map((key) => (
          <button
            key={key}
            onClick={() => toggleFilter(key)}
            className={`px-2 py-1 rounded text-xs border ${
              filters[key]
                ? "bg-gray-700 border-gray-600"
                : "bg-gray-900 border-gray-800 opacity-50"
            }`}
          >
            {key}
          </button>
        ))}
      </div>

      {/* Log Viewer */}
      <div
        ref={containerRef}
        className="bg-black/60 border border-gray-800 p-3 rounded-lg h-[450px] overflow-y-auto text-sm font-mono space-y-1"
      >
        {visibleLogs.map((entry, i) => (
          <div
            key={i}
            className="flex items-start gap-3 bg-black/40 p-2 rounded border border-gray-800"
          >
            {/* Time */}
           Speed
            <div className="text-gray-500 text-xs whitespace-nowrap">{entry.time}</div>

            {/* Level */}
            <div className={`${levelColors[entry.level]} font-bold whitespace-nowrap`}>
              {levelIcons[entry.level]} {entry.level}
            </div>

            {/* Message */}
            <div className="text-gray-200 break-words">{entry.msg}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
