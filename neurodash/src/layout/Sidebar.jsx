// import { Home, Upload, Layers, Activity, Server, Terminal } from "lucide-react";
//
// const menuItems = [
//   { id: "home", label: "Home", icon: Home },
//   { id: "upload", label: "Upload EEG", icon: Upload },
//   { id: "preprocess", label: "Preprocess", icon: Layers },
//   { id: "predict", label: "Predict", icon: Activity },
//   { id: "fl", label: "FL Status", icon: Server },
//   { id: "supernode", label: "Supernode Sync", icon: Server },
//   { id: "logs", label: "Live Logs", icon: Terminal },
// ];
//
// export default function Sidebar({ currentPage, onNavigate }) {
//   return (
//     <div className="w-56 bg-gray-900 border-r border-gray-800 h-screen fixed left-0 top-0 flex flex-col">
//       <div className="px-6 py-4 border-b border-gray-800">
//         <h1 className="text-xl font-semibold">NeuroDash</h1>
//         <p className="text-xs text-gray-400">Research Dashboard</p>
//       </div>
//
//       <nav className="mt-4 space-y-1">
//         {menuItems.map((item) => {
//           const Icon = item.icon;
//           const active = currentPage === item.id;
//
//           return (
//             <button
//               key={item.id}
//               onClick={() => onNavigate(item.id)}
//               className={`w-full flex items-center gap-3 px-5 py-2 text-sm transition
//                 ${active ? "bg-gray-800 text-white" : "text-gray-400 hover:bg-gray-800 hover:text-white"}
//               `}
//             >
//               <Icon size={18} />
//               {item.label}
//             </button>
//           );
//         })}
//       </nav>
//     </div>
//   );
// }

export default function Sidebar({ onNavigate, currentPage }) {
  return (
    <div
      className="
        w-72 min-h-screen fixed left-0 top-0
        backdrop-blur-xl bg-white/10
        border-r border-white/20
        shadow-xl shadow-black/40
        p-6 flex flex-col
      "
      style={{
        background: "rgba(255, 255, 255, 0.08)",
      }}
    >
      <h2 className="text-2xl font-bold mb-8 text-white drop-shadow-lg">
        Dashboard
      </h2>

      <nav className="space-y-3">

        <button
          onClick={() => onNavigate("home")}
          className={`w-full text-lg px-4 py-3 rounded-xl flex items-center gap-3
            transition-all whitespace-nowrap
            ${
              currentPage === "home"
                ? "bg-gradient-to-r from-purple-600 to-pink-500 text-white shadow-lg shadow-purple-900/40"
                : "text-gray-200 hover:bg-white/10 backdrop-blur-md"
            }
          `}
        >
           Dashboard
        </button>

        <button
          onClick={() => onNavigate("upload")}
          className={`w-full text-lg px-4 py-3 rounded-xl flex items-center gap-3
            transition-all whitespace-nowrap
            ${
              currentPage === "upload"
                ? "bg-gradient-to-r from-purple-600 to-pink-500 text-white shadow-lg shadow-purple-900/40"
                : "text-gray-200 hover:bg-white/10 backdrop-blur-md"
            }
          `}
        >
           Upload EEG
        </button>

        <button
          onClick={() => onNavigate("preprocess")}
          className={`w-full text-lg px-4 py-3 rounded-xl flex items-center gap-3
            transition-all whitespace-nowrap
            ${
              currentPage === "preprocess"
                ? "bg-gradient-to-r from-purple-600 to-pink-500 text-white shadow-lg shadow-purple-900/40"
                : "text-gray-200 hover:bg-white/10 backdrop-blur-md"
            }
          `}
        >
          Preprocess
        </button>

        <button
          onClick={() => onNavigate("predict")}
          className={`w-full text-lg px-4 py-3 rounded-xl flex items-center gap-3
            transition-all whitespace-nowrap
            ${
              currentPage === "predict"
                ? "bg-gradient-to-r from-purple-600 to-pink-500 text-white shadow-lg shadow-purple-900/40"
                : "text-gray-200 hover:bg-white/10 backdrop-blur-md"
            }
          `}
        >
           Predict
        </button>

        <button
          onClick={() => onNavigate("fl")}
          className={`w-full text-lg px-4 py-3 rounded-xl flex items-center gap-3
            transition-all whitespace-nowrap
            ${
              currentPage === "fl"
                ? "bg-gradient-to-r from-purple-600 to-pink-500 text-white shadow-lg shadow-purple-900/40"
                : "text-gray-200 hover:bg-white/10 backdrop-blur-md"
            }
          `}
        >
           FL Status
        </button>

        <button
          onClick={() => onNavigate("logs")}
          className={`w-full text-lg px-4 py-3 rounded-xl flex items-center gap-3
            transition-all whitespace-nowrap
            ${
              currentPage === "logs"
                ? "bg-gradient-to-r from-purple-600 to-pink-500 text-white shadow-lg shadow-purple-900/40"
                : "text-gray-200 hover:bg-white/10 backdrop-blur-md"
            }
          `}
        >
           Logs
        </button>

        <button
          onClick={() => onNavigate("performance")}
          className={`w-full text-lg px-4 py-3 rounded-xl flex items-center gap-3
            transition-all whitespace-nowrap
            ${
              currentPage === "performance"
                ? "bg-gradient-to-r from-purple-600 to-pink-500 text-white shadow-lg shadow-purple-900/40"
                : "text-gray-200 hover:bg-white/10 backdrop-blur-md"
            }
          `}
        >
           Metrics
        </button>

      </nav>
    </div>
  );
}


