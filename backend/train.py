"""Entraîne l'« IA » maison (voir ia.py) et l'enregistre dans model.joblib.

Usage : python train.py

Données :
- data/data.csv      : vrais exemples écrits à la main (comptent 3 fois plus)
- data/feedback.csv  : retours des utilisateurs (« c'était un scam / légitime »), si présent
- generer_donnees.py : exemples fabriqués (scams et pièges légitimes)
- data/examen.csv    : messages JAMAIS utilisés pour l'entraînement, pour noter l'IA honnêtement

Mesures affichées :
- validation croisée : l'IA est réentraînée 5 fois, chaque fois sans 1/5 des vrais exemples,
  puis notée sur ce 1/5 qu'elle n'a pas vu
- examen : note sur data/examen.csv
"""
import argparse

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

from config import DATA_PATH, EXAMEN_PATH, FEEDBACK_PATH, MODEL_PATH
from generer_donnees import generer
from ia import IA

POIDS_VRAIS = 3.0       # un vrai exemple compte comme 3 exemples fabriqués
SEUIL_DECISION = 50     # pour noter : score >= 50 = « l'IA dit scam »


def charger_vrais() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)[["text", "label"]]
    if FEEDBACK_PATH.exists():
        fb = pd.read_csv(FEEDBACK_PATH, names=["type", "text", "label"], header=None)
        fb = fb[fb["type"] != "phone"][["text", "label"]]
        df = pd.concat([df, fb], ignore_index=True)
    return df.dropna().drop_duplicates(subset="text").reset_index(drop=True)


def charger_fabriques() -> pd.DataFrame:
    return pd.DataFrame(generer(), columns=["text", "label"])


def entrainer(vrais: pd.DataFrame, fabriques: pd.DataFrame, **reglages) -> IA:
    tout = pd.concat([vrais, fabriques], ignore_index=True)
    poids = np.r_[np.full(len(vrais), POIDS_VRAIS), np.ones(len(fabriques))]
    scams_connus = vrais[vrais.label == 1].text          # seulement de vrais exemples pour « ressemble à… »
    return IA.entrainer(tout.text, tout.label, poids, scams_connus, **reglages)


def noter(ia: IA, df: pd.DataFrame) -> tuple[int, list]:
    """(nombre de bonnes réponses, erreurs) ; sans interroger Google pour rester rapide et reproductible."""
    justes, erreurs = 0, []
    for texte, label in zip(df.text, df.label):
        score = ia.analyser(texte, reseau=False).score
        if (score >= SEUIL_DECISION) == bool(label):
            justes += 1
        else:
            erreurs.append((int(label), score, texte))
    return justes, erreurs


def validation_croisee(vrais: pd.DataFrame, fabriques: pd.DataFrame, plis: int = 5, **reglages) -> tuple[int, list]:
    justes, erreurs = 0, []
    decoupe = StratifiedKFold(n_splits=plis, shuffle=True, random_state=0)
    for i_train, i_test in decoupe.split(vrais.text, vrais.label):
        ia = entrainer(vrais.iloc[i_train], fabriques, **reglages)
        j, e = noter(ia, vrais.iloc[i_test])
        justes += j
        erreurs += e
    return justes, erreurs


def afficher_erreurs(erreurs: list) -> None:
    for label, score, texte in erreurs:
        attendu = "scam    " if label else "légitime"
        print(f"    attendu {attendu} | score {score:3} | {texte[:90]}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--rapide", action="store_true", help="saute la validation croisée")
    args = parser.parse_args()

    vrais, fabriques = charger_vrais(), charger_fabriques()
    print(f"Vrais exemples : {len(vrais)} ({int(vrais.label.sum())} scams) | "
          f"fabriqués : {len(fabriques)} ({int(fabriques.label.sum())} scams)")

    if not args.rapide:
        justes, erreurs = validation_croisee(vrais, fabriques)
        print(f"\nValidation croisée sur les vrais exemples : {justes}/{len(vrais)} ({justes / len(vrais):.0%})")
        afficher_erreurs(erreurs)

    ia = entrainer(vrais, fabriques)

    if EXAMEN_PATH.exists():
        examen = pd.read_csv(EXAMEN_PATH)
        justes, erreurs = noter(ia, examen)
        print(f"\nExamen (messages jamais vus) : {justes}/{len(examen)} ({justes / len(examen):.0%})")
        afficher_erreurs(erreurs)

    joblib.dump(ia, MODEL_PATH)
    print(f"\nIA enregistrée : {MODEL_PATH}")


if __name__ == "__main__":
    main()
