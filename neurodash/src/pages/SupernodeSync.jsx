import { useState, useEffect } from "react";
import { triggerSupernodeSync } from "../api/flaskApi";
import axios from "axios";

export default function SupernodeSync() {
  const [syncInfo, setSyncInfo] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSync = async () => {
    setLoading(true);

    try {
      const res = await triggerSupernodeSync();
      const timestamp = res.data.at || Date.now();

      const newEntry = {
        version: res.data.model_version ?? history.length + 1,
        time: timestamp,
        status: "success",
      };

      setSyncInfo(res.data);
      setHistory([newEntry, ...history]);
    } catch (err) {
      console.error(err);

      const newEntry = {
        version: history.length + 1,
        time: Date.now(),
        status: "failed",
      };

      setHistory([newEntry, ...history]);
      setSyncInfo({ error: true });
    }

    setLoading(false);
  };

  useEffect(() => {
    // Optional: Load sync history from backend if you implement /supernode/history
  }, []);

  const formatTime = (ts) => new Date(ts).toLocaleString();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Supernode Synchronization</h1>
        <p className="text-gray-400 text-sm">
          Trigger global model aggregation and view sync history.
        </p>
      </div>

      {/* Trigger Sync Button */}
      <div className="bg-gray-900 border border-gray-800 p-6 rounded-lg flex items-center justify-between">
        <div>
          <p className="text-gray-300 text-sm mb-1">Trigger global model sync</p>
          <p className="text-xs text-gray-500">
            This will aggregate updates from all available nodes.
          </p>
        </div>

        <button
          onClick={handleSync}
          disabled={loading}
          className={`px-6 py-2 rounded-md text-white transition ${
            loading ? "bg-gray-700" : "bg-amber-600 hover:bg-amber-700"
          }`}
        >
          {loading ? "Syncing..." : "Trigger Sync"}
        </button>
      </div>

      {/* Latest Sync Result */}
      {syncInfo && (
        <div className="bg-gray-900 border border-gray-800 p-6 rounded-lg">
          <h2 className="text-lg font-medium mb-3">Latest Sync</h2>

          {syncInfo.error ? (
            <p className="text-red-400 text-sm">Sync failed.</p>
          ) : (
            <div className="space-y-2 text-gray-300 text-sm">
              <p>
                <span className="text-gray-400">Status:</span>{" "}
                <span className="text-green-400">Success</span>
              </p>
              <p>
                <span className="text-gray-400">Model Version:</span>{" "}
                {syncInfo.model_version ?? "—"}
              </p>
              <p>
                <span className="text-gray-400">Time:</span>{" "}
                {formatTime(syncInfo.at)}
              </p>
            </div>
          )}
        </div>
      )}

      {/* Sync History */}
      <div className="bg-gray-900 border border-gray-800 p-6 rounded-lg">
        <h2 className="text-lg font-medium mb-4">Sync History</h2>

        {history.length === 0 ? (
          <p className="text-gray-500 text-sm">No syncs performed yet.</p>
        ) : (
          <div className="space-y-4">
            {history.map((item, idx) => (
              <div
                key={idx}
                className="flex justify-between bg-gray-800 p-3 rounded-md"
              >
                <div>
                  <p className="text-sm text-gray-300">
                    Model Version: {item.version}
                  </p>
                  <p className="text-xs text-gray-400">
                    {formatTime(item.time)}
                  </p>
                </div>

                <span
                  className={`text-sm ${
                    item.status === "success" ? "text-green-400" : "text-red-400"
                  }`}
                >
                  {item.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
