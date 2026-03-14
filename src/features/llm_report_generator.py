# import requests
# import json
#
# LMSTUDIO_URL = "http://localhost:1234/v1/chat/completions"
# MODEL_NAME = "Meta-Llama-3-8B-Instruct-GGUF"
#
#
# def generate_medical_eeg_report(summary):
#     """
#     Calls LM Studio (OpenAI compatible mode) and safely parses all possible response formats.
#     """
#
#     prompt = f"""
#     You are a medical neurologist. Generate a clear, structured EEG interpretation.
#
#     EEG Summary:
#     {json.dumps(summary, indent=2)}
#
#     Write a clinical-style EEG report that includes:
#     - Overall brain activity interpretation
#     - Spike/anomaly observations
#     - Bandpower significance (delta/theta/alpha/beta/gamma)
#     - Severity estimation (mild/moderate/severe)
#     - Possible medical implications
#     - Final recommendation for a doctor
#
#     Keep it understandable for a clinician.
#     """
#
#     payload = {
#         "model": MODEL_NAME,
#         "messages": [
#             {"role": "system", "content": "You are an expert neurologist."},
#             {"role": "user", "content": prompt}
#         ],
#         "temperature": 0.4
#     }
#
#     # ----------------------
#     # Send request to LM Studio
#     # ----------------------
#     response = requests.post(LMSTUDIO_URL, json=payload)
#
#     try:
#         data = response.json()
#     except Exception:
#         return "ERROR: LM Studio returned non-JSON response."
#
#     # ----------------------
#     # Handle LM Studio formats safely
#     # ----------------------
#
#     # Case 1: OpenAI-style
#     if "choices" in data and len(data["choices"]) > 0:
#         return data["choices"][0]["message"]["content"]
#
#     # Case 2: Local model returns plain "message"
#     if "message" in data:
#         return data["message"]
#
#     # Case 3: Error from LM Studio
#     if "error" in data:
#         return f"LM STUDIO ERROR: {data['error']}"
#
#     # Case 4: Unknown response
#     return f"UNKNOWN RESPONSE FORMAT:\n{json.dumps(data, indent=2)}"


import requests
import json

LM_STUDIO_URL = "http://127.0.0.1:1234/v1/chat/completions"
MODEL_NAME = "med42-70b"   # replace with the LM Studio model you install

def generate_medical_eeg_report(summary):
    """
    Generates a neurologist-level EEG explanation using a local LM Studio model.
    """

    prompt = f"""
You are a senior neurologist. Analyze this EEG summary and explain it in extremely simple
language suitable for a non-medical person. Use analogies if necessary.

Include:
- what the prediction means,
- why the confidence matters,
- what the Grad-CAM heatmap highlights,
- how PSD and spectrogram indicate abnormalities,
- a risk rating (Low / Medium / High),
- what the patient should do next,
- one small visual ASCII diagram if useful.

EEG SUMMARY (JSON):
{json.dumps(summary, indent=2)}
"""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are a medical neurologist."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 600
    }

    response = requests.post(LM_STUDIO_URL, json=payload)
    data = response.json()

    return data["choices"][0]["message"]["content"]
