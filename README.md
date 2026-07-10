# HemoCheck — Anemia Prediction Web Application

A full-stack ML web app that predicts anemia risk from CBC (Complete Blood
Count) values, built with Flask + scikit-learn on the backend and plain
HTML/CSS/JavaScript on the frontend.


## Live Demo: 
https://anemia-prediction-kdj9.onrender.com

<img width="1054" height="1492" alt="Hemocheck poster" src="https://github.com/user-attachments/assets/6b001299-5b3e-4202-addb-1bdd4e29b02f" />

<img width="864" height="1232" alt="2" src="https://github.com/user-attachments/assets/451e7fa1-163f-49e7-aee3-5a406e2325a0" />


## Project Structure

```
anemia-app/
├── app.py                  # Flask backend (routes + prediction API)
├── model.pkl               # Trained model bundle (RandomForest + scaler)
├── requirements.txt
├── model/
│   └── train_model.py      # Script that generates data & trains model.pkl
├── templates/
│   ├── index.html          # Home page
│   └── predict.html        # Prediction form + results page
└── static/
    ├── css/style.css       # All styling (design system, responsive, animations)
    └── js/
        ├── main.js         # Shared behavior (mobile nav)
        └── predict.js      # Form validation, API call, result rendering
```

## Setup

```bash
cd anemia-app
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## (Re)train the model

`model.pkl` is already included and ready to use. To regenerate it from
scratch (e.g. after tweaking `train_model.py`):

```bash
python model/train_model.py
```

This generates a clinically-plausible synthetic CBC dataset, trains a
`RandomForestClassifier` with a `StandardScaler`, prints accuracy /
classification report, and saves everything into `model.pkl`.

## Run the app

```bash
python app.py
```

Then open **http://localhost:5000** in your browser.

- `/` — Home page (hero, about anemia, features, how it works)
- `/predict` — Prediction form and results

## API

`POST /api/predict`

Request body (JSON):
```json
{
  "Age": 28, "Gender": 1, "Hemoglobin": 13.5, "RBC": 4.8, "WBC": 7.2,
  "HCT": 41, "MCV": 88, "MCH": 29, "MCHC": 33, "Platelets": 270
}
```
`Gender`: `1` = Male, `0` = Female.

Response:
```json
{
  "success": true,
  "prediction": "No Anemia",
  "anemia_detected": false,
  "confidence": 97.4,
  "health_status": "Normal",
  "recommendations": {
    "precautions": ["..."],
    "diet": ["..."],
    "doctor_advice": "..."
  }
}
```

## Notes

- The model is trained on **synthetic data** generated from realistic CBC
  reference ranges (see `model/train_model.py`) since no labeled clinical
  dataset was provided. Swap in a real, licensed dataset by adjusting
  `generate_dataset()` or loading your own CSV before training for
  production/clinical use.
- This tool is for informational purposes only and is not a substitute for
  professional medical diagnosis.
