"""L'« IA » maison : entraînement, verdicts, explications et réponse de l'API."""
import joblib
import pytest

import config
import ia
import rules
import train
from rules import Signal


@pytest.fixture(scope="module")
def cerveau():
    """Une IA entraînée sur les données du projet (quelques secondes, une seule fois pour ce fichier)."""
    return train.entrainer(train.charger_vrais(), train.charger_fabriques())


# ---------- verdicts sur des messages absents de l'entraînement ----------

@pytest.mark.parametrize("texte", [
    "Allo maman, c'est moi, mon cell est brisé. Peux-tu m'envoyer 650 $ par Interac ce soir ? Ne le dis à personne",
    "Desjardins : connexion inhabituelle détectée. Validez votre NIP ici : http://desjardins-validation.top",
    "Congratulations! You won a $500 Amazon gift card. Claim it now: https://amazon-prize.click",
])
def test_reconnait_des_scams(cerveau, texte):
    avis = cerveau.analyser(texte, reseau=False)
    assert avis.verdict == "scam", (avis.score, avis.resume)


@pytest.mark.parametrize("texte", [
    "Postes Canada : votre colis 1234 5678 9012 a été livré à votre porte.",
    "Maman, peux-tu me prêter 15 $ pour la pizza ? Je te rembourse jeudi",
    "Ton code de vérification est 448812. Ne le communique à personne.",
])
def test_ne_crie_pas_au_loup(cerveau, texte):
    avis = cerveau.analyser(texte, reseau=False)
    assert avis.verdict == "legitime", (avis.score, avis.resume)


# ---------- explications ----------

def test_type_conseil_et_resume(cerveau):
    avis = cerveau.analyser("Salut papa, c'est moi, j'ai un nouveau numéro. Envoie-moi 400 $ par Interac, c'est urgent", "fr",
                            reseau=False)
    assert avis.type["nom"] == "Arnaque du faux proche"
    assert avis.conseil == avis.type["conseil"]
    assert avis.resume.startswith("Ce message ressemble à une arnaque du faux proche")


def test_resume_en_anglais(cerveau):
    avis = cerveau.analyser("URGENT: verify your password now at http://bank-secure-login.xyz", "en", reseau=False)
    assert avis.resume.startswith("This message looks like")


def test_legitime_sans_conseil_ni_type(cerveau):
    avis = cerveau.analyser("On se voit au café demain à 10 h ?", reseau=False)
    assert avis.verdict == "legitime"
    assert avis.type is None and avis.conseil is None and avis.similaire is None
    assert not avis.indices_vers_scam


def test_indices_sans_petits_mots(cerveau):
    avis = cerveau.analyser("Votre colis est en attente. Payez les frais de livraison ici : http://colis-frais.xyz",
                            reseau=False)
    assert avis.indices
    assert not any(mot in ia.MOTS_VIDES for indice in avis.indices for mot in indice.split())


def test_scam_connu_le_plus_proche(cerveau):
    connu = cerveau.connus[0]
    avis = cerveau.analyser(connu, reseau=False)
    assert avis.similaire is not None and avis.similaire["similarite"] >= 90


def test_confiance_jamais_100(cerveau):
    avis = cerveau.analyser("🚨 URGENT p@y3z maintenant, compte bloqué, mot de passe : http://bit.ly/x", reseau=False)
    assert avis.confiance <= 99


# ---------- score final ----------

def test_google_est_decisif():
    signal = Signal("url.google", 60, "lien dangereux")
    assert ia.score_final(0.05, [signal]) >= 90


def test_regles_tres_sures_imposent_un_minimum():
    signaux = [Signal("x", 50, "a"), Signal("y", 50, "b")]          # 100 points de règles
    assert ia.score_final(0.0, signaux) == 100 - ia.MARGE_REGLES


# ---------- chargement ----------

def test_ancien_modele_refuse(tmp_path):
    chemin = tmp_path / "model.joblib"
    joblib.dump({"pas": "une IA"}, chemin)
    assert ia.charger(chemin) is None


def test_modele_absent(tmp_path):
    assert ia.charger(tmp_path / "absent.joblib") is None


# ---------- API ----------

def test_api_renvoie_l_avis_de_l_ia(cerveau, monkeypatch):
    import app
    monkeypatch.setattr(app, "MODEL", cerveau)
    monkeypatch.setattr(config, "API_KEY", "")
    monkeypatch.setattr(rules.safebrowsing, "verifier", lambda urls: {})     # pas d'appel réseau
    rep = app.app.test_client().post("/analyser", json={
        "type": "message", "langue": "en",
        "contenu": "Hi mom, this is my new number, my phone broke. Send me $500 now, don't tell dad"})
    donnees = rep.get_json()
    assert rep.status_code == 200
    assert donnees["ia"]["verdict"] == "scam"
    assert donnees["ia"]["scam"] is True                     # champ gardé pour les anciens clients
    assert donnees["ia"]["type"]["nom"] == "Fake relative scam"
    assert donnees["niveau"] == "élevé"
