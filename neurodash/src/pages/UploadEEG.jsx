// import { useState } from "react";
// import { uploadEEG } from "../api/flaskApi";
//
// export default function UploadEEG({ setFileId }) {
//   const [file, setFile] = useState(null);
//   const [uploading, setUploading] = useState(false);
//   const [message, setMessage] = useState("");
//
//   const handleFileSelect = (e) => {
//     setFile(e.target.files[0]);
//   };
//
//   const handleUpload = async () => {
//     if (!file) {
//       setMessage("Please select an EEG file.");
//       return;
//     }
//
//     setUploading(true);
//     setMessage("");
//
//     try {
//       const response = await uploadEEG(file);
//       const id = response.data.filepath;     // backend key
//
//       if (!id) {
//     setMessage("Upload succeeded, but no filepath returned.");
//     return;
//   }
//       setFileId(id);
//       setMessage(`Uploaded successfully! File ID: ${id}`);
//     } catch (error) {
//       console.error(error);
//       setMessage("Upload failed. Check backend.");
//     }
//
//     setUploading(false);
//   };
//
//   return (
//     <div className="space-y-8">
//       {/* Title */}
//       <div>
//         <h1 className="text-2xl font-semibold">Upload EEG File</h1>
//         <p className="text-gray-400 text-sm">Supported formats: EDF, CSV , Parquet</p>
//       </div>
//
//       {/* File input section */}
//       <div className="bg-gray-900 border border-gray-800 p-6 rounded-lg space-y-4">
//
//         {/* File selector */}
//         <input
//           type="file"
//           accept=".edf,.csv,.parquet"
//           onChange={handleFileSelect}
//           className="w-full text-sm text-gray-300 file:mr-4 file:py-2 file:px-4
//           file:rounded file:border-0 file:bg-gray-800 file:text-gray-200 hover:file:bg-gray-700"
//         />
//
//         {/* Upload button */}
//         <button
//           onClick={handleUpload}
//           disabled={uploading}
//           className={`px-6 py-2 rounded-md text-white transition
//             ${uploading ? "bg-gray-700" : "bg-blue-600 hover:bg-blue-700"}
//           `}
//         >
//           {uploading ? "Uploading..." : "Upload"}
//         </button>
//
//         {/* Message */}
//         {message && (
//           <div className="text-sm text-gray-300 bg-gray-800 p-3 rounded-md">
//             {message}
//           </div>
//         )}
//       </div>
//     </div>
//   );
// }

import { useState } from "react";
import { uploadEEG } from "../api/flaskApi";
import bg from "../assets/bg.png";

export default function UploadEEG({ setFileId }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState("");

  const handleFileSelect = (e) => {
    setFile(e.target.files[0]);
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage("Please select an EEG file.");
      return;
    }

    setUploading(true);
    setMessage("");

    try {
      const response = await uploadEEG(file);
      const id = response.data.filepath;

      if (!id) {
        setMessage("Upload succeeded, but no filepath returned.");
        return;
      }

      setFileId(id);
      setMessage(`Uploaded successfully! File ID: ${id}`);
    } catch (error) {
      console.error(error);
      setMessage("Upload failed. Check backend.");
    }

    setUploading(false);
  };

  return (
    <div style={{ position: "relative", width: "100%", minHeight: "100%" }}>
        <center>
      {/* 🔵 BACKGROUND LAYER (FULL VIEWPORT, NO SHRINK) */}


      {/* 🟣 CONTENT */}
      <div style={{ maxWidth: "720px" }} className="space-y-8">

        {/* Title */}
        <div>
          <h1 className="text-3xl font-semibold">Upload EEG File</h1>
          <p className="text-gray-300 text-sm mt-1">
            Supported formats: EDF, Parquet
          </p>
        </div>

        {/* Upload Card */}
        <div
          style={{
            width: "520px",              // controlled width (professional)
            minHeight: "220px",          // balanced height
            background: "rgba(17, 24, 39, 0.82)",
            backdropFilter: "blur(14px)",
            border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: "18px",
            padding: "28px 32px",
            display: "flex",
            flexDirection: "column",
            justifyContent: "space-between",
            boxShadow: "0 20px 40px rgba(0,0,0,0.35)",
          }}
          className="p-6 rounded-xl space-y-5 shadow-lg"
        >
          {/* File selector */}
          <input
            type="file"
            accept=".edf,.csv,.parquet"
            onChange={handleFileSelect}
            className="w-full text-sm text-gray-300
              file:mr-4 file:py-2 file:px-4
              file:rounded-md file:border-0
              file:bg-gray-800 file:text-gray-200
              hover:file:bg-gray-700"
          />

          {/* Upload button */}
          <button
            onClick={handleUpload}
            disabled={uploading}
            className={`px-6 py-2 rounded-md text-white transition
              ${
                uploading
                  ? "bg-gray-700 cursor-not-allowed"
                  : "bg-blue-600 hover:bg-blue-700"
              }
            `}
          >
            {uploading ? "Uploading..." : "Upload"}
          </button>

          {/* Message */}
          {message && (
            <div className="text-sm text-gray-200 bg-gray-800/70 p-3 rounded-md">
              {message}
            </div>
          )}
        </div>
      </div>
      </center>
    </div>
  );
}
