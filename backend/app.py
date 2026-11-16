import csv
import hmac
from flask import Flask, Response, abort, jsonify, render_template, request

import config
import ia
import typescript_web
from abus import analyser_abus
from i18n import langue_valide, t
from phone import analyser_numero
from rules import analyser_regles

app = Flask(
    __name__,
    template_folder=str(config.FRONTEND_DIR / "templates"),
    static_folder=str(config.FRONTEND_DIR / "static"),
)

# L'IA est optionnelle : sans model.joblib (ou s'il est trop ancien), on utilise seulement les règles
MODEL = ia.charger()
if MODEL is None:
    print("IA indisponible : lance `python train.py` dans backend/ (mode règles seulement).")


def niveau(score: int) -> str:
    if score >= config.SEUIL_ELEVE:
        return "élevé"
    if score >= config.SEUIL_MOYEN:
        return "moyen"
    return "faible"


def evaluer(kind: str, contenu: str, langue: str):
    """Renvoie (score, raisons, avis de l'IA ou None)."""
    if kind == "phone":
        return (*analyser_numero(contenu, langue), None)

    if MODEL is None:
        return (*analyser_regles(contenu, langue), None)

    avis = MODEL.analyser(contenu, langue)
    return avis.score, avis.raisons, avis


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


@app.get("/js/<nom>.js")
def javascript(nom: str):
    """Le navigateur demande /js/app.js : on lui sert frontend/src/app.ts traduit en JavaScript."""
    try:
        return Response(typescript_web.traduire(nom), mimetype="text/javascript")
    except typescript_web.TypeScriptIntrouvable:
        abort(404)


@app.post("/analyser")
def analyser():
    langue = lire_langue()
    if not cle_valide():
        return jsonify(erreur=t(langue, "err.cle")), 401
    kind, contenu = lire_json()
    if kind is None:
        return jsonify(erreur=t(langue, "err.champs")), 400

    score, raisons, avis = evaluer(kind, contenu, langue)
    # Insultes / diffamation / menaces : signalées à part, sans changer le score de scam
    alertes = [] if kind == "phone" else analyser_abus(contenu, langue)
    reponse = dict(score=score, niveau=niveau(score), raisons=raisons, alertes=alertes)
    if avis is not None:
        # « Analyse IA » : verdict, résumé, type d'arnaque, conseil, indices, scam connu le plus proche
        reponse["ia"] = dict(
            verdict=avis.verdict,
            scam=avis.verdict == "scam",            # gardé pour les clients existants (app Android)
            confiance=avis.confiance,
            resume=avis.resume,
            type=avis.type,
            conseil=avis.conseil,
            indices=avis.indices,
            indices_vers_scam=avis.indices_vers_scam,
            similaire=avis.similaire,
        )
    return jsonify(**reponse)


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
