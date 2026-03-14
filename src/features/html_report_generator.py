import os

import os

def build_html_report(summary, doctor_report, output_path):

    try:
        pred = summary.get("predicted_class", "Unknown")
        conf = summary.get("confidence", 0)

        # SAFE plot path extraction
        plot_paths = summary.get("plot_paths", {}) or {}
        psd_path = plot_paths.get("psd")
        spect_path = plot_paths.get("spectrogram")

        # Optional gradcam
        gradcam_path = summary.get("gradcam")

        features = summary.get("features", {})

        # Doctor report fallback
        if not doctor_report:
            doctor_report = "No LLM explanation available."

        # Build HTML safely
        html = f"""
        <html>
        <head>
            <title>EEG Analysis Report</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 30px;
                    background: #f7f9fc;
                }}
                h1 {{
                    color: #2a4d69;
                }}
                .section {{
                    background: white;
                    padding: 20px;
                    margin-top: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
                }}
                img {{
                    width: 100%;
                    border-radius: 8px;
                    margin-top: 10px;
                    border: 1px solid #ccc;
                }}
            </style>
        </head>

        <body>

            <h1>EEG Analysis Report</h1>

            <div class="section">
                <h2>1. Model Prediction</h2>
                <p><b>Predicted Class:</b> {pred}</p>
                <p><b>Confidence Score:</b> {conf:.2f}%</p>
            </div>

            <div class="section">
                <h2>2. Feature Summary</h2>
                <pre>{features}</pre>
            </div>

            <div class="section">
                <h2>3. Power Spectral Density (PSD)</h2>
                {"<img src='" + psd_path + "'>" if psd_path else "<p>No PSD image generated.</p>"}
            </div>

            <div class="section">
                <h2>4. Spectrogram</h2>
                {"<img src='" + spect_path + "'>" if spect_path else "<p>No Spectrogram generated.</p>"}
            </div>

            <div class="section">
                <h2>5. Grad-CAM Heatmap</h2>
                {"<img src='" + gradcam_path + "'>" if gradcam_path else "<p>No Grad-CAM generated.</p>"}
            </div>

            <div class="section">
                <h2>6. Doctor / LLM Interpretation</h2>
                <p>{doctor_report}</p>
            </div>

        </body>
        </html>
        """

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        print(f"[INFO] HTML Report saved at: {output_path}")

    except Exception as e:
        print("[HTML ERROR]", e)
        print("[NOTE] HTML generation skipped but prediction will continue.")
