import copy
import json

import pytest

import config
from dictionnaire import DICO, ErreurDictionnaire, analyser_dictionnaire, charger

BRUT = json.loads(config.DICTIONNAIRE_PATH.read_text(encoding="utf-8"))


def test_fichier_reel_valide():
    assert {c.nom for c in DICO.scam} >= {"urgence", "argent", "gain", "menace", "sextorsion", "action", "sensible"}
    assert all(c.mots and c.points > 0 for c in DICO.scam)
    assert "paypal" in DICO.marques


def test_ajouter_une_categorie_suffit():
    """Ajouter une catégorie dans le JSON doit marcher sans toucher au code."""
    d = copy.deepcopy(BRUT)
    d["scam"]["crypto_romance"] = {"points": 30, "raison": {"fr": "Arnaque sentimentale", "en": "Romance scam"},
                                    "mots": {"fr": ["mon amour, envoie"], "en": ["my love, send"]}}
    dico = analyser_dictionnaire(d)
    cat = next(c for c in dico.scam if c.nom == "crypto_romance")
    assert cat.raison.texte("en") == "Romance scam"


def test_traduction_manquante_retombe_sur_francais():
    d = copy.deepcopy(BRUT)
    del d["scam"]["urgence"]["raison"]["en"]
    cat = next(c for c in analyser_dictionnaire(d).scam if c.nom == "urgence")
    assert cat.raison.texte("en") == cat.raison.texte("fr")


def test_emoji_avec_selecteur_de_variante():
    d = copy.deepcopy(BRUT)
    d["emojis"]["alerte"]["emojis"].append("⚠️")    # ⚠ + U+FE0F, comme collé depuis un clavier
    assert "⚠" in next(c for c in analyser_dictionnaire(d).emojis if c.nom == "alerte").emojis


@pytest.mark.parametrize("modif, message", [
    (lambda d: d["scam"]["urgence"].update(points="20"), "scam.urgence.points"),
    (lambda d: d["scam"]["urgence"].update(points=500), "scam.urgence.points"),
    (lambda d: d["scam"]["urgence"]["mots"].update(fr=["ok", ""]), "scam.urgence.mots.fr"),
    (lambda d: d["scam"]["urgence"]["mots"].update(de=["dringend"]), "scam.urgence.mots.de"),
    (lambda d: d["scam"]["urgence"].update(mots={"fr": [], "en": []}), "scam.urgence.mots"),
    (lambda d: d["scam"]["urgence"].pop("raison"), "scam.urgence.raison"),
    (lambda d: d["abus"]["insultes"]["raison"].pop("fr"), "abus.insultes.raison.fr"),
    (lambda d: d["emojis"]["alerte"].update(emojis=["🚨🚨"]), "emojis.alerte.emojis"),
    (lambda d: d["liens"].pop("marques"), "liens.marques"),
    (lambda d: d["scam"]["urgence"].update(resume="pas un objet"), "scam.urgence.resume"),
    (lambda d: d["types"]["colis"].pop("conseil"), "types.colis.conseil"),
    (lambda d: d["types"]["colis"]["nom"].pop("fr"), "types.colis.nom.fr"),
])
def test_erreurs_claires(modif, message):
    d = copy.deepcopy(BRUT)
    modif(d)
    with pytest.raises(ErreurDictionnaire, match=message.replace(".", r"\.")):
        analyser_dictionnaire(d)


def test_json_invalide_indique_la_ligne(tmp_path):
    f = tmp_path / "dictionnaire.json"
    f.write_text('{\n  "scam": {\n    "urgence": [1, 2,]\n  }\n}', encoding="utf-8")
    with pytest.raises(ErreurDictionnaire, match="ligne 3"):
        charger(f)


def test_types_optionnels():
    """Sans section « types », le dictionnaire reste valide (l'IA ne nomme juste pas le type d'arnaque)."""
    d = copy.deepcopy(BRUT)
    del d["types"]
    assert analyser_dictionnaire(d).types == []
