import csv
import hmac
import joblib
from flask import Flask, jsonify, render_template, request

import config
from abus import analyser_abus
from i18n import langue_valide, t
from phone import analyser_numero
from rules import analyser_regles

app = Flask(
    __name__,
    template_folder=str(config.FRONTEND_DIR / "templates"),
    static_folder=str(config.FRONTEND_DIR / "static"),
)

# Le modèle est optionnel : sans model.joblib, on utilise seulement les règles
MODEL = joblib.load(config.MODEL_PATH) if config.MODEL_PATH.exists() else None
if MODEL is None:
    print("model.joblib introuvable : lance `python train.py` (mode règles seulement).")


def niveau(score: int) -> str:
    if score >= config.SEUIL_ELEVE:
        return "élevé"
    if score >= config.SEUIL_MOYEN:
        return "moyen"
    return "faible"


def evaluer(kind: str, contenu: str, langue: str):
    if kind == "phone":
        return analyser_numero(contenu, langue)

    score_regles, raisons = analyser_regles(contenu, langue)
    if MODEL is None:
        return score_regles, raisons

    proba_ml = MODEL.predict_proba([contenu])[0][1] * 100
    if proba_ml >= 60:
        raisons.append(t(langue, "ml"))
    score = int(max(0.6 * proba_ml + 0.4 * score_regles, 0.8 * score_regles))
    return min(100, score), raisons


def cle_valide() -> bool:
    if not config.API_KEY:
        return True
    envoyee = request.headers.get("X-API-Key", "")
    return hmac.compare_digest(envoyee, config.API_KEY)


def lire_langue() -> str:
    """« langue » dans le JSON (fr ou en), sinon français par défaut."""
    data = request.get_json(silent=True) or {}
    return langue_valide(data.get("langue"))


def lire_json():
    data = request.get_json(silent=True) or {}
    kind = data.get("type")
    contenu = (data.get("contenu") or "").strip()
    if kind not in ("message", "email", "phone") or not contenu:
        return None, None
    return kind, contenu[: config.MAX_LEN]


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/analyser")
def analyser():
    langue = lire_langue()
    if not cle_valide():
        return jsonify(erreur=t(langue, "err.cle")), 401
    kind, contenu = lire_json()
    if kind is None:
        return jsonify(erreur=t(langue, "err.champs")), 400

    score, raisons = evaluer(kind, contenu, langue)
    # Insultes / diffamation / menaces : signalées à part, sans changer le score de scam
    alertes = [] if kind == "phone" else analyser_abus(contenu, langue)
    return jsonify(score=score, niveau=niveau(score), raisons=raisons, alertes=alertes)


@app.post("/feedback")
def feedback():
    langue = lire_langue()
    if not cle_valide():
        return jsonify(erreur=t(langue, "err.cle")), 401
    data = request.get_json(silent=True) or {}
    kind, contenu = lire_json()
    if kind is None or data.get("label") not in (0, 1):
        return jsonify(erreur=t(langue, "err.champs_label")), 400

    config.FEEDBACK_PATH.parent.mkdir(exist_ok=True)
    with open(config.FEEDBACK_PATH, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([kind, contenu, data["label"]])
    return jsonify(ok=True)


if __name__ == "__main__":
    # extra_files : redémarre aussi quand on modifie le dictionnaire de mots
    app.run(host=config.HOST, port=config.PORT, debug=True, extra_files=[str(config.DICTIONNAIRE_PATH)])
