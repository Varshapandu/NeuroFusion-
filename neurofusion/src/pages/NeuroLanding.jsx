import React from "react";
import bg from "../assets/background.png";

export default function Landing() {
  return (
    <div
      className="relative w-full h-screen bg-cover bg-center bg-no-repeat"
      style={{ backgroundImage: `url(${bg})` }}
    >
      {/* TEXT */}
      <div className="absolute top-[34%] left-[40%]">
        <h1 className="text-white text-7xl font-bold">
          NEUROFUSION
        </h1>

        <p className="text-[#ff00dd] text-2xl mt-4 leading-snug">
          A Federated Hybrid Ensemble Learning Framework <br />
          for EEG-based Harmful Brain Activity Detection
        </p>
      </div>

      {/* BUTTON */}
      <button
        className="absolute bottom-[18%] right-[15%]
                   px-10 py-4 text-white text-xl
                   border border-[#ff00dd] rounded-xl
                   shadow-[0_0_20px_#ff00dd]
                   hover:shadow-[0_0_35px_#ff00dd]
                   hover:bg-[#ff00dd]/20 transition-all"
      >
        Dashboard
      </button>
    </div>
  );
}
