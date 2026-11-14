"""Entraîne le modèle TF-IDF + régression logistique et l'enregistre dans model.joblib.

Usage : python train.py
Fusionne data/data.csv et data/feedback.csv (retours des utilisateurs) si présent.
"""
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline

from config import DATA_PATH, FEEDBACK_PATH, MODEL_PATH


def charger_donnees() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)[["text", "label"]]
    if FEEDBACK_PATH.exists():
        fb = pd.read_csv(FEEDBACK_PATH, names=["type", "text", "label"], header=None)
        fb = fb[fb["type"] != "phone"][["text", "label"]]
        df = pd.concat([df, fb], ignore_index=True)
    return df.dropna().drop_duplicates()


def main():
    df = charger_donnees()
    print(f"{len(df)} exemples ({int(df.label.sum())} scams, {int((1 - df.label).sum())} légitimes)")

    model = make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2), lowercase=True, min_df=1, sublinear_tf=True),
        LogisticRegression(max_iter=1000, class_weight="balanced"),
    )

    # Avec un petit jeu de données, on évalue puis on réentraîne sur tout
    if len(df) >= 60:
        X_tr, X_te, y_tr, y_te = train_test_split(
            df.text, df.label, test_size=0.2, stratify=df.label, random_state=42)
        model.fit(X_tr, y_tr)
        print(classification_report(y_te, model.predict(X_te)))
    else:
        print("Jeu de données petit : pas d'évaluation fiable, ajoute plus d'exemples dans data/data.csv.")

    model.fit(df.text, df.label)
    joblib.dump(model, MODEL_PATH)
    print(f"Modèle enregistré : {MODEL_PATH}")


if __name__ == "__main__":
    main()
