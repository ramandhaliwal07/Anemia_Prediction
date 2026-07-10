"""
app.py
------
Flask backend for the Anemia Prediction Web Application.

Routes
------
GET  /                 -> Home page
GET  /predict           -> Prediction form page
POST /api/predict       -> Accepts JSON CBC values, returns prediction JSON

The trained model bundle (RandomForestClassifier + StandardScaler +
feature order) is loaded once at startup from model.pkl.
"""

import pickle
import numpy as np
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# ---------------------------------------------------------------------
# Load the trained model bundle once, at startup
# ---------------------------------------------------------------------
with open("model.pkl", "rb") as f:
    BUNDLE = pickle.load(f)

MODEL = BUNDLE["model"]
SCALER = BUNDLE["scaler"]
FEATURE_ORDER = BUNDLE["feature_order"]

# Valid, physiologically sane input ranges used for server-side validation
VALID_RANGES = {
    "Age":        (0, 120),
    "Gender":     (0, 1),
    "Hemoglobin": (3, 20),
    "RBC":        (1.0, 8.0),
    "WBC":        (1.0, 30.0),
    "HCT":        (10, 65),
    "MCV":        (50, 130),
    "MCH":        (10, 45),
    "MCHC":       (20, 40),
    "Platelets":  (10, 800),
}


def validate_payload(data):
    """Returns (cleaned_values_dict, error_message_or_None)."""
    cleaned = {}
    for field, (low, high) in VALID_RANGES.items():
        if field not in data or data[field] in (None, ""):
            return None, f"Missing value for {field}."
        try:
            value = float(data[field])
        except (TypeError, ValueError):
            return None, f"{field} must be a number."
        if not (low <= value <= high):
            return None, f"{field} must be between {low} and {high}."
        cleaned[field] = value
    return cleaned, None


def get_health_status(hb, gender):
    """
    Rule-based severity classification, based on WHO hemoglobin thresholds.
    gender: 1 = Male, 0 = Female
    """
    if gender == 1:  # Male
        if hb >= 13.5:
            return "Normal"
        elif hb >= 11:
            return "Mild Anemia"
        elif hb >= 8:
            return "Moderate Anemia"
        else:
            return "Severe Anemia"
    else:  # Female
        if hb >= 12:
            return "Normal"
        elif hb >= 10:
            return "Mild Anemia"
        elif hb >= 7:
            return "Moderate Anemia"
        else:
            return "Severe Anemia"


def get_recommendations(status, anemia_detected):
    """Returns precautions, diet tips, and doctor-visit advice for a status."""
    if not anemia_detected:
        return {
            "precautions": [
                "Maintain a balanced diet rich in iron, folate, and vitamin B12.",
                "Keep up with routine annual blood checkups.",
                "Stay physically active and maintain a healthy sleep schedule.",
            ],
            "diet": [
                "Leafy greens, lean meats, beans, and fortified cereals.",
                "Vitamin C-rich fruits (citrus, guava) to support iron absorption.",
                "Stay well hydrated throughout the day.",
            ],
            "doctor_advice": "No immediate concern. Continue periodic health screenings "
                              "as part of your regular wellness routine.",
        }

    base = {
        "Mild Anemia": {
            "precautions": [
                "Avoid strenuous activity until energy levels improve.",
                "Monitor for fatigue, dizziness, or shortness of breath.",
                "Recheck hemoglobin levels in 4-6 weeks.",
            ],
            "diet": [
                "Iron-rich foods: spinach, red meat, lentils, tofu.",
                "Pair iron sources with vitamin C to improve absorption.",
                "Limit tea/coffee around meals as they can reduce iron uptake.",
            ],
            "doctor_advice": "Schedule a routine consultation with a physician to "
                              "confirm the cause and discuss iron supplementation.",
        },
        "Moderate Anemia": {
            "precautions": [
                "Reduce physical exertion and rest adequately.",
                "Watch closely for pale skin, rapid heartbeat, or breathlessness.",
                "Avoid skipping meals; eat iron-rich food consistently.",
            ],
            "diet": [
                "Increase intake of red meat, eggs, beans, and iron-fortified grains.",
                "Add folate sources: beans, oranges, avocado.",
                "Consider an iron supplement only under medical supervision.",
            ],
            "doctor_advice": "Consult a doctor within the next few days for blood "
                              "tests and a personalized treatment plan.",
        },
        "Severe Anemia": {
            "precautions": [
                "Avoid any strenuous physical activity immediately.",
                "Seek medical attention promptly; do not delay treatment.",
                "Watch for chest pain, severe fatigue, or fainting and seek emergency care if present.",
            ],
            "diet": [
                "Follow a physician-guided high-iron diet plan.",
                "Supplementation (oral or IV iron) may be required under supervision.",
                "Avoid self-medicating; nutrition alone may not be sufficient.",
            ],
            "doctor_advice": "Urgent medical consultation is strongly recommended. "
                              "Severe anemia may require lab-confirmed diagnosis and treatment.",
        },
    }
    return base.get(status, base["Mild Anemia"])


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/predict")
def predict_page():
    return render_template("predict.html")


@app.route("/api/predict", methods=["POST"])
def api_predict():
    data = request.get_json(silent=True) or {}

    cleaned, error = validate_payload(data)
    if error:
        return jsonify({"success": False, "error": error}), 400

    # Build feature vector in the exact order the model was trained on
    feature_vector = np.array([[cleaned[f] for f in FEATURE_ORDER]])
    scaled_vector = SCALER.transform(feature_vector)

    prediction = int(MODEL.predict(scaled_vector)[0])
    probabilities = MODEL.predict_proba(scaled_vector)[0]
    confidence = round(float(probabilities[prediction]) * 100, 2)

    status = get_health_status(cleaned["Hemoglobin"], int(cleaned["Gender"]))
    recommendations = get_recommendations(status, prediction == 1)

    result = {
        "success": True,
        "prediction": "Anemia Detected" if prediction == 1 else "No Anemia",
        "anemia_detected": bool(prediction == 1),
        "confidence": confidence,
        "health_status": status,
        "recommendations": recommendations,
    }
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
