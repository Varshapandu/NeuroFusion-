

import "./Home.css";
import datasetImg from "../assets/class_distribution.png";
import bg from "../assets/bg.png";



export default function Home() {
  return (
      <div
      className="pageWrapper"
      >
      <div
        className="pageBg"
      />
     <div className="main" >

      <h1>Dashboard</h1>

      <div className="box-row">

        <div className="info-box">
          <div className="info-title">Total EEG Files Uploaded</div>
          <div className="info-value">106,800</div>
        </div>

        <div className="info-box">
          <div className="info-title">Models Used</div>
          <div className="info-value">3</div>
        </div>

        <div className="info-box">
          <div className="info-title">Last Prediction Accuracy</div>
          <div className="info-value">0.66</div>
        </div>

      </div>

      <div className="dataset-box">
        <h2>Dataset Overview</h2>
        <img src={datasetImg} alt="Dataset Chart" className="dataset-img" />
      </div>
     </div>
   </div>
  );
}

