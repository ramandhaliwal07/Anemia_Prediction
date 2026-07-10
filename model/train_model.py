"""
train_model.py
----------------
Generates a clinically-plausible synthetic dataset for anemia classification
and trains a RandomForestClassifier on it. The trained model, the fitted
StandardScaler, and the feature order are all bundled together and saved
to model.pkl using pickle, so app.py can load a single file.

Run this once to (re)create model.pkl:
    python model/train_model.py
"""

import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report

RANDOM_STATE = 42
N_SAMPLES = 6000

FEATURE_ORDER = [
    "Age", "Gender", "Hemoglobin", "RBC", "WBC",
    "HCT", "MCV", "MCH", "MCHC", "Platelets"
]


def generate_dataset(n_samples=N_SAMPLES, random_state=RANDOM_STATE):
    """
    Builds a synthetic dataset grounded in real CBC (Complete Blood Count)
    reference ranges. Roughly half the samples are simulated as anemic and
    half as healthy, each drawn from gender-specific normal distributions
    that mimic real hematology reference intervals, with noise so the
    classifier has to learn genuine multivariate structure rather than a
    single hard threshold.
    """
    rng = np.random.default_rng(random_state)
    rows = []

    n_healthy = n_samples // 2
    n_anemic = n_samples - n_healthy

    # ---------- Healthy samples ----------
    for _ in range(n_healthy):
        gender = rng.integers(0, 2)  # 0 = Female, 1 = Male
        age = int(np.clip(rng.normal(38, 15), 1, 95))

        if gender == 1:  # Male reference ranges
            hb = rng.normal(15.2, 1.1)
            rbc = rng.normal(5.2, 0.4)
            hct = rng.normal(46, 3.5)
        else:  # Female reference ranges
            hb = rng.normal(13.6, 1.0)
            rbc = rng.normal(4.6, 0.35)
            hct = rng.normal(40, 3.2)

        mcv = rng.normal(90, 5)
        mch = rng.normal(30, 2)
        mchc = rng.normal(34, 1.3)
        wbc = rng.normal(7.5, 1.8)
        platelets = rng.normal(280, 55)

        rows.append([age, gender, hb, rbc, wbc, hct, mcv, mch, mchc, platelets, 0])

    # ---------- Anemic samples ----------
    for _ in range(n_anemic):
        gender = rng.integers(0, 2)
        age = int(np.clip(rng.normal(42, 18), 1, 95))

        severity = rng.choice(["mild", "moderate", "severe"], p=[0.45, 0.35, 0.20])
        if severity == "mild":
            hb_base = rng.uniform(10.5, 12.5)
        elif severity == "moderate":
            hb_base = rng.uniform(8.0, 10.5)
        else:
            hb_base = rng.uniform(4.5, 8.0)

        # Slight gender offset, consistent with lower female reference range
        hb = hb_base - (0.4 if gender == 0 else 0) + rng.normal(0, 0.4)
        rbc = rng.normal(3.3, 0.6) if severity != "mild" else rng.normal(4.0, 0.5)
        hct = hb * rng.normal(3.0, 0.15)  # HCT tracks Hb (rule of three)
        mcv = rng.normal(78, 12)          # anemia often microcytic/variable
        mch = rng.normal(25, 4)
        mchc = rng.normal(31, 2.2)
        wbc = rng.normal(7.2, 2.2)
        platelets = rng.normal(260, 80)

        rows.append([age, gender, hb, rbc, wbc, hct, mcv, mch, mchc, platelets, 1])

    df = pd.DataFrame(
        rows,
        columns=FEATURE_ORDER + ["Anemia"]
    )

    # Clip to physiologically sane bounds and add small measurement noise
    df["Hemoglobin"] = df["Hemoglobin"].clip(3, 20)
    df["RBC"] = df["RBC"].clip(1.5, 7.5)
    df["WBC"] = df["WBC"].clip(2, 20)
    df["HCT"] = df["HCT"].clip(10, 60)
    df["MCV"] = df["MCV"].clip(55, 120)
    df["MCH"] = df["MCH"].clip(15, 40)
    df["MCHC"] = df["MCHC"].clip(25, 38)
    df["Platelets"] = df["Platelets"].clip(50, 550)

    df = df.sample(frac=1, random_state=random_state).reset_index(drop=True)
    return df


def train_and_save():
    df = generate_dataset()

    X = df[FEATURE_ORDER]
    y = df["Anemia"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=10,
        min_samples_split=4,
        min_samples_leaf=2,
        random_state=RANDOM_STATE,
        class_weight="balanced",
    )
    model.fit(X_train_scaled, y_train)

    preds = model.predict(X_test_scaled)
    acc = accuracy_score(y_test, preds)
    print(f"Test Accuracy: {acc * 100:.2f}%")
    print(classification_report(y_test, preds, target_names=["No Anemia", "Anemia"]))

    bundle = {
        "model": model,
        "scaler": scaler,
        "feature_order": FEATURE_ORDER,
        "accuracy": acc,
    }

    with open("model.pkl", "wb") as f:
        pickle.dump(bundle, f)

    print("Saved trained bundle to model.pkl")


if __name__ == "__main__":
    train_and_save()
