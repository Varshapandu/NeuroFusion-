import os, json
import sys

CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
sys.path.insert(0, PROJECT_ROOT)

from flask import Blueprint, request, jsonify, send_file
from backend.services.llm_med_explainer import generate_medical_explanation
from backend.services.eeg_processor import process_eeg_file
from src.features.run_eeg_analysis import run_full_pipeline

analysis_bp = Blueprint("analysis_bp", __name__)

UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, "backend", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ----------------------------------------------------
# BASIC UPLOAD
# ----------------------------------------------------
@analysis_bp.route("/upload", methods=["POST"])
def upload_eeg():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    filename = file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    return jsonify({"status": "uploaded", "filepath": filepath})


# ----------------------------------------------------
# FIXED GET-FILE (WORKING)
# ----------------------------------------------------
@analysis_bp.route("/get-file", methods=["GET"])
def get_file():
    path = request.args.get("path")

    # Convert relative path → absolute
    if not os.path.isabs(path):
        abs_path = os.path.join(PROJECT_ROOT, path)
    else:
        abs_path = path

    print("📁 get-file → RESOLVED PATH:", abs_path)

    if not os.path.exists(abs_path):
        return jsonify({"error": "File not found", "path": abs_path}), 404

    return send_file(abs_path)


# ----------------------------------------------------
# REACT FRIENDLY: PREPROCESS
# ----------------------------------------------------
@analysis_bp.route("/process_eeg", methods=["POST"])
def preprocess_eeg():
    data = request.get_json()
    if not data or "file_id" not in data:
        return jsonify({"error": "file_id missing"}), 400

    filepath = data["file_id"]
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found", "path": filepath}), 404

    from src.features.run_eeg_analysis import analyze_eeg

    try:
        summary = analyze_eeg(filepath, "models/neurofusion_best_fast.pt")

        pre = summary.get("preprocessed", {})
        specs = summary.get("spectrograms", None)

        return jsonify({
            "preprocessed": pre,
            "spectrograms": specs
        })


    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ----------------------------------------------------
# MAIN PREDICT ENDPOINT (WITH LLM EXPLANATION)
# ----------------------------------------------------
@analysis_bp.route("/predict", methods=["POST"])
def predict_harmful_activity():
    data = request.get_json()
    if not data or "file_id" not in data:
        return jsonify({"error": "file_id missing"}), 400

    filepath = data["file_id"]
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404

    # Run EEG pipeline
    print("[PREDICT] Running pipeline...")
    result = run_full_pipeline(filepath)

    pred = result.get("prediction", "Unknown")
    conf = float(result.get("confidence", 0))
    # ---------------- Uncertainty-aware decision ----------------
    if conf < 40:
        decision = "Inconclusive – requires clinical review"
        certainty_label = "Low"
    elif conf < 70:
        decision = "Possible abnormality detected"
        certainty_label = "Moderate"
    else:
        decision = "High likelihood of abnormal activity"
        certainty_label = "High"

    # Load summary JSON file
    with open(result["summary_path"], "r") as f:
        summary_data = json.load(f)

    # Get LLM explanation
    llm_json = generate_medical_explanation(
        prediction=pred,
        confidence=conf,
        certainty=certainty_label,
        summary=summary_data
    )

    response = {
        "risk_score": round(conf, 1),
        "labels": result.get("labels", []),
        "plain_explanation": llm_json["detailed_text"],
        "doctor_summary": {
            "interpretation": llm_json["short_summary"],
            "model_certainty": certainty_label,
            "risk_percent": round(conf,2),
            "decision": decision,
            "notes": llm_json["bullet_points"][:5]
        },
        "file_paths": result.get("file_paths", {})
    }

    return jsonify(response)
