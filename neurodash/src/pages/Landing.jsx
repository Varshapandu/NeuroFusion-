import React from "react";
import bg from "../assets/background.png"; // <-- make sure path is correct

export default function Landing({ onEnter }) {
  return (
    <div
      className="landing"
      style={{
        backgroundImage: `url(${bg})`,
        backgroundRepeat: "no-repeat",
        backgroundSize: "cover",
        backgroundPosition: "center",
        backgroundColor: "#0c0017",
        height: "100vh",
        width: "100%",
        position: "relative",
        overflow: "hidden",
      }}
    >

      {/* TEXT CONTENT */}
      <div
        className="text-box"
        style={{
          position: "absolute",
          top: "33%",
          left: "47%",
          transform: "translateX(-10%)",
        }}
      >
        <h1
          style={{
            color: "#F5F1FF",
            fontSize: "72px",
            fontWeight: "900",
            letterSpacing: "2px",
            textShadow: "0 0 25px rgba(255,255,255,0.35)",
            margin: 0,
          }}
        >
          NEUROFUSION
        </h1>

        <p
          style={{
            marginTop: "18px",
            fontSize: "26px",
            lineHeight: "1.4",
            color: "#d38bff",
            textShadow: "0 0 25px rgba(255,0,221,0.3.5)",
            fontWeight: 500,
          }}
        >
          A Federated Hybrid Ensemble Learning Framework <br />
          for EEG-based Harmful Brain Activity Detection
        </p>
      </div>

      {/* BUTTON */}
      <button
        onClick={() => onEnter("home")} // KEEP your functionality
        style={{
          position: "absolute",
          bottom: "18%",
          right: "15%",
          padding: "15px 40px",
          fontSize: "22px",
          borderRadius: "14px",
          border: "2px solid #d38bff",
          background: "rgba(255,255,255,0.02)",
          color: "white",
          cursor: "pointer",
          boxShadow: "0 0 20px rgba(211,139,255,0.25)",
          transition: "0.25s ease",
        }}
        onMouseOver={(e) => {
          e.target.style.boxShadow = "0 0 22px rgba(211,139,255,0.35)";
          e.target.style.background = "rgba(211,139,255,0.12)";
        }}
        onMouseOut={(e) => {
          e.target.style.boxShadow = "0 0 12px rgba(211,139,255,0.25)";
          e.target.style.background = "rgba(255,255,255,0.02)";
        }}
      >
        Dashboard
      </button>

    </div>
  );
}
