import { useState } from "react";

// Layout
import Layout from "./layout/Layout";
// Pages
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Home from "./pages/Home";
import UploadEEG from "./pages/UploadEEG";
import Preprocess from "./pages/Preprocess";
import Predict from "./pages/Predict";
import FLStatus from "./pages/FLStatus";
import SupernodeSync from "./pages/SupernodeSync";
import Logs from "./pages/Logs";
import ModelPerformance from "./pages/ModelPerformance";

export default function App() {
  // ******* Fix #1: define fileId + setter ********
  const [fileId, setFileId] = useState(null);

  // For navigation
  const [page, setPage] = useState("landing");

  // User authentication (optional)
  const [user, setUser] = useState(() => {
    const token = localStorage.getItem("neuro_token");
    return token ? { token } : null;
  });

  // ******* Fix #2: Import Login page works here ********
  if (!user) {
    return <Login onLogin={(u) => setUser(u)} />;
  }

  // Show landing first
  if (page === "landing") return <Landing onEnter={setPage} />;

  return (
    <Layout currentPage={page} onNavigate={setPage}>
      {page === "home" && <Home />}


      {page === "upload" && (
        <UploadEEG setFileId={setFileId} />   // ← Fix #3: UploadEEG now receives the setter
      )}

      {page === "preprocess" && (
        <Preprocess fileId={fileId} />        // ← Fix #4: Preprocess needs fileId
      )}

      {page === "predict" && (
        <Predict fileId={fileId} />           // ← Fix #5: Predict needs fileId
      )}

      {page === "fl" && <FLStatus />}
      {page === "supernode" && <SupernodeSync />}
      {page === "logs" && <Logs />}
      {page === "performance" && <ModelPerformance />}
    </Layout>
  );
}
