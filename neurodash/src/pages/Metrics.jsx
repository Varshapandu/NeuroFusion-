// import { useEffect, useRef, useState } from "react";
// import { io } from "socket.io-client";
// import ChartWrapper from "../components/ChartWrapper";
//
// export default function Metrics() {
//   const socketRef = useRef(null);
//
//   const [dataPoints, setDataPoints] = useState([]);
//   const [connected, setConnected] = useState(false);
//
//   useEffect(() => {
//     // Connect to Socket.IO namespace for metrics
//     const socket = io("http://127.0.0.1:5000/metrics");
//     socketRef.current = socket;
//
//     socket.on("connect", () => {
//       setConnected(true);
//       console.log("Connected to /metrics WebSocket");
//     });
//
//     socket.on("disconnect", () => {
//       setConnected(false);
//       console.log("Disconnected from /metrics WebSocket");
//     });
//
//     socket.on("metric", (msg) => {
//         const safeAccuracy =
//           typeof msg.loss === "number"
//             ? Math.max(0, Math.min(1, 1 - msg.loss))
//             : null;
//
//         setDataPoints((prev) => [
//           ...prev.slice(-50),
//           {
//             ...msg,
//             accuracy: safeAccuracy,
//           },
//         ]);
//     });
//
//
//     return () => socket.close();
//   }, []);
//
//   return (
//   <div className="space-y-6">
//     <div>
//       <h1 className="text-2xl font-semibold">Training Metrics</h1>
//       <p className="text-gray-400 text-sm">
//         Real-time accuracy and loss updates from your federated learning server.
//       </p>
//     </div>
//
//     {/* WebSocket status */}
//     <div className="text-sm text-gray-400">
//       WebSocket:{" "}
//       {connected ? (
//         <span className="text-green-400">Connected</span>
//       ) : (
//         <span className="text-red-400">Disconnected</span>
//       )}
//     </div>
//
//     {/* Charts */}
//     <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
//       <ChartWrapper
//         title="Accuracy Over Rounds"
//         xKey="round"
//         yKey="accuracy"
//         data={dataPoints}
//         color="rgb(34,197,94)"
//       />
//
//       <ChartWrapper
//         title="Loss Over Rounds"
//         xKey="round"
//         yKey="loss"
//         data={dataPoints}
//         color="rgb(239,68,68)"
//       />
//     </div>
//
//     {/* Confusion Matrix */}
//     {dataPoints.length > 0 &&
//       dataPoints.at(-1)?.confusion_matrix && (
//         <div className="bg-gray-900 p-4 rounded-lg">
//           <h2 className="text-lg font-semibold mb-3">
//             Confusion Matrix (Latest Round)
//           </h2>
//
//           <div className="overflow-x-auto">
//             <table className="border-collapse">
//               <tbody>
//                 {dataPoints.at(-1).confusion_matrix.map((row, i) => (
//                   <tr key={i}>
//                     {row.map((val, j) => (
//                       <td
//                         key={j}
//                         className="border border-gray-700 px-4 py-2 text-center"
//                       >
//                         {val}
//                       </td>
//                     ))}
//                   </tr>
//                 ))}
//               </tbody>
//             </table>
//           </div>
//         </div>
//       )}
//   </div>
// );
