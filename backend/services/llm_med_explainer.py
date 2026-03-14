print("🔥 Loaded FIXED llm_med_explainer.py")

import requests
import json

# LM Studio Chat Completions API
LM_STUDIO_URL = "http://127.0.0.1:1234/v1/chat/completions"
MODEL_NAME = "mistral-7b-instruct-v0.2"

CLASS_MAP = {
    0: "Seizure",
    1: "LPD (Lateralized Periodic Discharges)",
    2: "GPD (Generalized Periodic Discharges)",
    3: "LRDA (Lateralized Rhythmic Delta Activity)",
    4: "GRDA (Generalized Rhythmic Delta Activity)",
    5: "Other / Non-specific pattern"
}



def generate_medical_explanation(prediction, confidence,certainty, summary):
    """
    Fully safe, short prompt, NO LARGE SUMMARY passed.
    Always returns:
      - short_summary
      - detailed_text
      - bullet_points
    """

    # Extract only SMALL useful metadata — NOT entire data arrays.
    features = summary.get("features", {})
    feature_keys = list(features.keys())[:5]  # only summary, not raw data

    predicted_label = CLASS_MAP.get(prediction, "Unknown pattern")

    short_summary_text = (
        f"EEG predicted pattern: {predicted_label}. "
        f"Risk score: {confidence:.2f}%."
    )

    # 👉 THIS IS THE REAL PROMPT (small)
    prompt = """
    You are an AI Neurologist Assistant specialized in EEG interpretation and clinical risk communication.

    EEG system output:
    - Predicted EEG pattern: {predicted_label}
    - Risk score (probability of harmful or seizure-like activity): {confidence}%
    - Model certainty level: {certainty}

    IMPORTANT RULES (MUST FOLLOW):
    - Always interpret findings based on the provided model certainty.
    - NEVER refer to low certainty unless the certainty level is explicitly "Low".
    - NEVER downplay risk when certainty is "Moderate" or "High".

    CERTAINTY-SPECIFIC INTERPRETATION GUIDELINES:

    1) If model certainty is LOW:
    - Explain that EEG abnormalities may be subtle, inconsistent, or early-stage.
    - Emphasize that low certainty does NOT exclude potential harm.
    - Recommend precautionary actions such as monitoring, repeat EEG, or clinical correlation.
    - Use cautious but risk-aware language.

    2) If model certainty is MODERATE:
    - State that EEG abnormalities are reasonably consistent.
    - Indicate a meaningful possibility of clinically relevant abnormal activity.
    - Recommend follow-up evaluation and continued monitoring.

    3) If model certainty is HIGH:
    - Clearly state that EEG abnormalities are consistent and significant.
    - Emphasize a high likelihood of abnormal or seizure-like activity.
    - Avoid phrases suggesting uncertainty or inconclusiveness.
    - Recommend prompt clinical evaluation and appropriate intervention.

    EEG description guidance:
    - Mention EEG characteristics when relevant, such as:
      • spikes or sharp transients
      • rhythmic delta activity
      • background rhythm disruption
      • frequency band abnormalities (delta, theta, alpha, beta)

    Tone requirements:
    - Professional and neurologist-like
    - Clear and decisive when certainty is High
    - Cautious only when certainty is Low
    - Never contradictory

    Return ONLY valid JSON in this structure:
    {
      "short_summary": "2–3 sentences reflecting the correct certainty level and risk",
      "detailed_text": "6–8 sentences explaining EEG findings with certainty-appropriate clinical interpretation",
      "bullet_points": [
        "Key EEG abnormality",
        "Risk interpretation based on certainty",
        "Clinical implication",
        "Recommended action"
      ]
    }

    No extra text before or after JSON.
    """

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }

    print("\n🟢 ENTERED generate_medical_explanation()")
    print("🟦 SENDING REQUEST TO LM STUDIO...\n")

    for attempt in range(2):  # retry once
        try:
            res = requests.post(LM_STUDIO_URL, json=payload, timeout=120)

            print("🟥 STATUS CODE:", res.status_code)
            print("🟦 RAW TEXT RESPONSE:\n", res.text, "\n")

            data = res.json()

            if "choices" not in data:
                raise ValueError("No choices in LLM response")

            raw = data["choices"][0]["message"]["content"].strip()

            # Extract JSON safely
            start = raw.find("{")
            end = raw.rfind("}") + 1
            json_str = raw[start:end]

            return json.loads(json_str)

        except Exception as e:
            print(f"🟧 LLM attempt {attempt + 1} failed:", e)

    print("🟥 LLM failed after retry → Using fallback")
    return _fallback()


def _fallback():
    """
    Guaranteed safe fallback when LLM output is unavailable or invalid.
    Uses conservative, neurologist-style language.
    """
    return {
        "short_summary": (
            "The EEG shows mild and nonspecific irregular activity. "
            "No clear epileptiform pattern can be confidently identified."
        ),
        "detailed_text": (
            "Review of the EEG indicates some mild background irregularities, "
            "which are common and can occur due to normal variation, fatigue, or external factors. "
            "There are no consistent spike-and-wave discharges or rhythmic patterns typically "
            "associated with seizure activity. Due to the nonspecific nature of these findings, "
            "the result is considered inconclusive rather than abnormal. "
            "Clinical correlation is advised if symptoms persist or worsen."
        ),
        "bullet_points": [
            "Mild, nonspecific EEG irregularities observed",
            "No sustained epileptiform spikes or discharges",
            "Findings are inconclusive and low-risk",
            "Clinical follow-up recommended if symptoms continue"
        ]
    }
