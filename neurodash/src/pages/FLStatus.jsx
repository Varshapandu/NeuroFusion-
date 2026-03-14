// import { useEffect, useState, useCallback } from "react";
// import { getFLStatus } from "../api/flaskApi";
// import axios from "axios";
//
//
//
// // -------------------------------------------------------------
// // Modal Component
// // -------------------------------------------------------------
// function NodeDetailsModal({ node, onClose }) {
//   if (!node) return null;
//
//   return (
//     <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
//       <div className="bg-gray-900 border border-gray-800 p-6 rounded-lg w-[400px] shadow-xl">
//         <h2 className="text-xl font-semibold mb-4">Node Details</h2>
//
//         <div className="space-y-2 text-sm text-gray-300">
//           <p><span className="text-gray-400">Node ID:</span> {node.id}</p>
//           <p><span className="text-gray-400">IP:</span> {node.ip}</p>
//           <p><span className="text-gray-400">Status:</span> {node.status}</p>
//           <p><span className="text-gray-400">Rounds Completed:</span> {node.rounds_completed}</p>
//           <p><span className="text-gray-400">Last Seen:</span> {new Date(node.last_seen).toLocaleString()}</p>
//
//           {node.last_training_time && (
//             <p><span className="text-gray-400">Training Time:</span> {node.last_training_time.toFixed(2)} sec</p>
//           )}
//
//           {node.meta && (
//             <>
//               <p className="mt-3 text-gray-400 font-medium">Hardware</p>
//               <p>CPU: {node.meta.cpu}</p>
//               <p>RAM: {node.meta.ram}</p>
//               <p>GPU: {node.meta.gpu}</p>
//             </>
//           )}
//         </div>
//
//         <button
//           onClick={onClose}
//           className="mt-6 w-full bg-blue-600 hover:bg-blue-700 transition py-2 rounded-md"
//         >
//           Close
//         </button>
//       </div>
//     </div>
//   );
// }
//
// // -------------------------------------------------------------
// // Node Card Component
// // -------------------------------------------------------------
// function NodeCard({ node, onClick }) {
//   const statusColor =
//     node.status === "training"
//       ? "text-green-400"
//       : node.status === "idle"
//       ? "text-blue-300"
//       : node.status === "offline"
//       ? "text-red-400"
//       : "text-gray-300";
//
//   return (
//     <button
//       onClick={onClick}
//       className={`bg-gray-900 border border-gray-800 p-4 rounded-md flex items-center justify-between w-full hover:bg-gray-800 transition`}
//     >
//       <div>
//         <div className="text-sm text-gray-300 font-medium">{node.id}</div>
//         <div className="text-xs text-gray-400">{node.ip}</div>
//         <div className="text-xs text-gray-400 mt-1">
//           Rounds: {node.rounds_completed}
//         </div>
//       </div>
//
//       <div className={`text-sm font-semibold ${statusColor}`}>
//         {node.status}
//       </div>
//     </button>
//   );
// }
//
// // -------------------------------------------------------------
// // MAIN PAGE
// // -------------------------------------------------------------
// export default function FLStatus() {
//   const [status, setStatus] = useState(null);
//   const [loading, setLoading] = useState(false);
//   const [modalNode, setModalNode] = useState(null);
//   const [training, setTraining] = useState(false);
//   const [roundRunning, setRoundRunning] = useState(false);
//   const [elapsed, setElapsed] = useState(0);
//
//   // Fetch FL status
//   const fetchStatus = useCallback(async () => {
//     setLoading(true);
//     try {
//       const res = await getFLStatus();
//       const data = res?.data ?? res;
//       setStatus(data);
//
//
//     setRoundRunning(Boolean(data?.round_running));
//
//
//
//
//       console.log("Metrics history:", res?.data?.metrics_history);
//
//     } catch (e) {
//       console.error("Failed to load FL status", e);
//     }
//     setLoading(false);
//   }, []);
//
//   // Auto-refresh
//   useEffect(() => {
//     fetchStatus();
//     const timer = setInterval(fetchStatus, 3000);
//     return () => clearInterval(timer);
//   }, [fetchStatus]);
//
//   const startTrainingRound = async () => {
//     setTraining(true);
//     try {
//       await axios.post("http://127.0.0.1:5000/api/fl/start_training");
//       alert("Training round triggered!");
//       fetchStatus();
//     } catch (err) {
//       alert("Error triggering training");
//     }
//     setTraining(false);
//   };
//
//   const metrics = status?.metrics;
//   const progress = status?.training_progress;
//
//
//   return (
//     <div className="space-y-6">
//       {/* Title */}
//       <h1 className="text-2xl font-semibold">Federated Learning — Status</h1>
//       <p className="text-gray-400 text-sm">Monitor and control FL system</p>
//
//
//       {/* Header Metrics */}
//       <div className="flex flex-wrap gap-4 items-start">
//
//
//         {/* Global Round */}
//         <div className="bg-gray-900 border border-gray-800 p-4 rounded-lg min-w-[220px]">
//           <div className="text-xs text-gray-400">Global Round</div>
//           <div className="text-3xl font-semibold mt-1">
//             {status?.global_round ?? "—"}
//           </div>
//         </div>
//
//         {/* Connected Nodes */}
//         <div className="bg-gray-900 border border-gray-800 p-4 rounded-lg min-w-[220px]">
//           <div className="text-xs text-gray-400">Connected Nodes</div>
//           <div className="text-3xl font-semibold mt-1">
//             {status?.nodes?.filter((n) => n.status !== "offline").length ?? 0}
//             {" / "}
//             {status?.nodes?.length ?? 0}
//           </div>
//         </div>
//
//         {/* DP Metrics */}
//         <div className="bg-gray-900 border border-gray-800 p-4 rounded-lg min-w-[260px]">
//           <div className="text-xs text-gray-400 mb-2">DP Metrics</div>
//
//           <div className="text-sm text-gray-300 space-y-1">
//             <p>Epsilon (Full): <span className="font-semibold">{metrics?.epsilon_full ?? "—"}</span></p>
//             <p>Epsilon (Sampled): <span className="font-semibold">{metrics?.epsilon_sampled ?? "—"}</span></p>
//             <p>Sigma: <span className="font-semibold">{metrics?.sigma ?? "—"}</span></p>
//             <p>q (sampling): <span className="font-semibold">{metrics?.q ?? "—"}</span></p>
//             <p>Round Time: <span className="font-semibold">{metrics?.round_time?.toFixed?.(2) ?? "—"} sec</span></p>
//           </div>
//         </div>
//         {status?.metrics_history?.length > 0 && (
//   <div className="bg-gray-900 border border-gray-800 p-4 rounded-lg">
//     <div className="text-xs text-gray-400 mb-2">Last FL Round</div>
//     <div className="text-sm text-gray-300">
//       Round #{status.metrics_history.at(-1).round}
//       <br />
//       Accuracy: {status.metrics_history.at(-1).accuracy.toFixed(4)}
//       <br />
//       Loss: {status.metrics_history.at(-1).loss.toFixed(2)}
//     </div>
//   </div>
// )}
//
//
//         {/* Training Button */}
//         <button
//           onClick={startTrainingRound}
//           disabled={training}
//           className={`ml-auto px-4 py-2 rounded-md text-white transition ${
//             training ? "bg-gray-700" : "bg-green-600 hover:bg-green-700"
//           }`}
//         >
//           {training ? "Starting..." : "Start Training"}
//         </button>
//
//         {/* Refresh */}
//         <button
//           onClick={fetchStatus}
//           disabled={loading}
//           className={`px-4 py-2 rounded-md text-white transition ${
//             loading ? "bg-gray-700" : "bg-blue-600 hover:bg-blue-700"
//           }`}
//         >
//           {loading ? "Refreshing..." : "Refresh"}
//         </button>
//       </div>
//       {/* Training Progress */}
//       {/* Training Progress */}
//       {roundRunning ? (
//   <div className="bg-green-900/40 border border-green-600 p-3 rounded text-green-300">
//     🚀 Training in progress
//     {progress?.total > 0 && (
//       <span className="ml-2">
//         ({progress.current} / {progress.total} batches)
//       </span>
//     )}
//   </div>
// ) : status?.metrics?.accuracy ? (
//   <div className="bg-blue-900/40 border border-blue-600 p-3 rounded text-blue-300">
//     ✅ Training completed
//     <div className="text-sm mt-1">
//       Accuracy: {status.metrics.accuracy.toFixed(4)} |
//       Loss: {status.metrics.loss.toFixed(2)}
//     </div>
//   </div>
// ) : (
//   <div className="bg-gray-900 border border-gray-800 p-3 rounded text-gray-400">
//     System idle — no training started
//   </div>
// )}
//
//
//
//
//
//       {/* Node Grid */}
//       <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
//         {status?.nodes?.map((node) => (
//           <NodeCard key={node.id} node={node} onClick={() => setModalNode(node)} />
//         ))}
//       </div>
//
//       {/* Modal */}
//       <NodeDetailsModal node={modalNode} onClose={() => setModalNode(null)} />
//     </div>
//   );
// }

import { useEffect, useState, useCallback } from "react";
import { getFLStatus } from "../api/flaskApi";
import axios from "axios";

// -------------------------------------------------------------
// Modal Component
// -------------------------------------------------------------
function NodeDetailsModal({ node, onClose }) {
  if (!node) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-gray-900 border border-gray-800 p-6 rounded-lg w-[400px] shadow-xl">
        <h2 className="text-xl font-semibold mb-4">Node Details</h2>

        <div className="space-y-2 text-sm text-gray-300">
          <p><span className="text-gray-400">Node ID:</span> {node.id}</p>
          <p><span className="text-gray-400">IP:</span> {node.ip ?? "—"}</p>
          <p><span className="text-gray-400">Status:</span> {node.status}</p>
          <p><span className="text-gray-400">Rounds Completed:</span> {node.rounds_completed ?? 0}</p>
          <p><span className="text-gray-400">Last Seen:</span> {node.last_seen ? new Date(node.last_seen).toLocaleString() : "—"}</p>

          {node.last_training_time && (
            <p>
              <span className="text-gray-400">Training Time:</span>{" "}
              {node.last_training_time.toFixed(2)} sec
            </p>
          )}

          {node.meta && (
            <>
              <p className="mt-3 text-gray-400 font-medium">Hardware</p>
              <p>CPU: {node.meta.cpu}</p>
              <p>RAM: {node.meta.ram}</p>
              <p>GPU: {node.meta.gpu}</p>
            </>
          )}
        </div>

        <button
          onClick={onClose}
          className="mt-6 w-full bg-blue-600 hover:bg-blue-700 transition py-2 rounded-md"
        >
          Close
        </button>
      </div>
    </div>
  );
}

// -------------------------------------------------------------
// Node Card Component
// -------------------------------------------------------------
function NodeCard({ node, onClick }) {
  const status = node.status || "idle";

  const statusColor =
    status === "training"
      ? "text-green-400"
      : status === "idle" || status === "online"
      ? "text-blue-300"
      : status === "offline"
      ? "text-red-400"
      : "text-gray-400";

  return (
    <button
      onClick={onClick}
      className="bg-gray-900 border border-gray-800 p-4 rounded-md flex items-center justify-between w-full hover:bg-gray-800 transition"
    >
      <div>
        <div className="text-sm text-gray-300 font-medium">{node.id}</div>
        <div className="text-xs text-gray-400">{node.ip ?? "—"}</div>
        <div className="text-xs text-gray-400 mt-1">
          Rounds: {node.rounds_completed ?? 0}
        </div>
      </div>

      <div className={`text-sm font-semibold ${statusColor}`}>
        {status}
      </div>
    </button>
  );
}

// -------------------------------------------------------------
// MAIN PAGE
// -------------------------------------------------------------
export default function FLStatus() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [modalNode, setModalNode] = useState(null);
  const [training, setTraining] = useState(false);
  const [roundRunning, setRoundRunning] = useState(false);

  const fetchStatus = useCallback(async () => {
    setLoading(true);
    try {
      const res = await getFLStatus();
      const data = res?.data ?? res;
      setStatus(data);
      setRoundRunning(Boolean(data?.round_running));
    } catch (e) {
      console.error("Failed to load FL status", e);
    }
    setLoading(false);
  }, []);

  // Auto-refresh
  useEffect(() => {
    fetchStatus();
    const timer = setInterval(fetchStatus, 3000);
    return () => clearInterval(timer);
  }, [fetchStatus]);

  const startTrainingRound = async () => {
    setTraining(true);
    try {
      await axios.post("http://127.0.0.1:5000/api/fl/start_training");
      fetchStatus();
    } catch {
      alert("Error triggering training");
    }
    setTraining(false);
  };

  const metrics = status?.metrics;
  const progress = status?.training_progress;
  const nodes = status?.nodes ?? [];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Federated Learning — Status</h1>
      <p className="text-gray-400 text-sm">Monitor and control FL system</p>

      {/* Header Metrics */}
      <div className="flex flex-wrap gap-4 items-start">
        <div className="bg-gray-900 border border-gray-800 p-4 rounded-lg min-w-[220px]">
          <div className="text-xs text-gray-400">Global Round</div>
          <div className="text-3xl font-semibold mt-1">
            {status?.global_round ?? "—"}
          </div>
        </div>

        <div className="bg-gray-900 border border-gray-800 p-4 rounded-lg min-w-[220px]">
          <div className="text-xs text-gray-400">Connected Nodes</div>
          <div className="text-3xl font-semibold mt-1">
            {nodes.filter(n => n.status !== "offline").length} / {nodes.length}
          </div>
        </div>

        <div className="bg-gray-900 border border-gray-800 p-4 rounded-lg min-w-[260px]">
          <div className="text-xs text-gray-400 mb-2">DP Metrics</div>
          <div className="text-sm text-gray-300 space-y-1">
            <p>Epsilon (Full): <b>{metrics?.epsilon_full ?? "—"}</b></p>
            <p>Epsilon (Sampled): <b>{metrics?.epsilon_sampled ?? "—"}</b></p>
            <p>Sigma: <b>{metrics?.sigma ?? "—"}</b></p>
            <p>q: <b>{metrics?.q ?? "—"}</b></p>
            <p>Round Time: <b>{metrics?.round_time?.toFixed?.(2) ?? "—"} sec</b></p>
          </div>
        </div>

        <button
          onClick={startTrainingRound}
          disabled={training}
          className={`ml-auto px-4 py-2 rounded-md text-white transition ${
            training ? "bg-gray-700" : "bg-green-600 hover:bg-green-700"
          }`}
        >
          {training ? "Starting..." : "Start Training"}
        </button>

        <button
          onClick={fetchStatus}
          disabled={loading}
          className={`px-4 py-2 rounded-md text-white transition ${
            loading ? "bg-gray-700" : "bg-blue-600 hover:bg-blue-700"
          }`}
        >
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {roundRunning ? (
  <div className="bg-green-900/40 border border-green-600 p-3 rounded text-green-300">
    🚀 Training in progress
    {progress?.total > 0 && (
      <span className="ml-2">
        ({progress.current} / {progress.total} batches)
      </span>
    )}
  </div>
) : status?.metrics?.accuracy ? (
  <div className="bg-blue-900/40 border border-blue-600 p-3 rounded text-blue-300">
    Training completed
    <div className="text-sm mt-1">
      Accuracy: {status.metrics.accuracy.toFixed(4)} |
      Loss: {status.metrics.loss.toFixed(2)}
    </div>
  </div>
) : status?.connected_nodes > 0 ? (
  <div className="bg-yellow-900/40 border border-yellow-600 p-3 rounded text-yellow-300">
    💤 System idle — clients connected
  </div>
) : (
  <div className="bg-gray-900 border border-gray-800 p-3 rounded text-gray-400">
    System idle — waiting for clients
  </div>
)}


      {/* Nodes */}
      {nodes.length === 0 ? (
        <div className="bg-gray-900 border border-gray-800 p-4 rounded text-gray-400">
          No federated clients connected
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {nodes.map(node => (
            <NodeCard key={node.id} node={node} onClick={() => setModalNode(node)} />
          ))}
        </div>
      )}

      <NodeDetailsModal node={modalNode} onClose={() => setModalNode(null)} />
    </div>
  );
}
