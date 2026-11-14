"""Score de scam : règles sur le texte (mots, camouflage, emojis, liens) et numéros de téléphone."""
import pytest

from phone import analyser_numero
from rules import analyser_regles


# ---------- texte ----------

def test_scam_colis():
    txt = "Postes Canada : payez 2,99 $ dans les 24 heures http://postes-canada-suivi.xyz/p"
    score, raisons = analyser_regles(txt)
    assert score >= 70
    assert any("Imite" in r for r in raisons)


def test_sextorsion():
    score, _ = analyser_regles("J'ai piraté votre webcam. Payez en bitcoin sinon j'envoie la vidéo à tous vos contacts.")
    assert score >= 70


def test_emojis_scam():
    score, raisons = analyser_regles("🚨🚨 Dernière chance ! 🎁 Gagnez 👉 http://bit.ly/x 💰")
    assert score >= 70
    assert any("Emojis" in r for r in raisons)


@pytest.mark.parametrize("texte", [
    "P@y3z les fr@is de livr@ison",          # leetspeak
    "V I R E M E N T reçu",                   # lettres espacées
    "ᴜʀɢᴇɴᴛ : ᴅᴇʀɴɪᴇʀ ᴀᴠɪs",                  # petites capitales
    "𝐅é𝐥𝐢𝐜𝐢𝐭𝐚𝐭𝐢𝐨𝐧𝐬",                          # lettres mathématiques
    "Ur​gent",                           # espace invisible
])
def test_mots_camoufles(texte):
    _, raisons = analyser_regles(texte)
    assert any("camouflés" in r for r in raisons)


@pytest.mark.parametrize("texte", [
    "Salut, on se voit demain à 18 h au resto ?",
    "Bonne fête 🎉🎂 ! Je t'ai pris un petit cadeau",
    "J'ai raté le bus, je serai en retard. Le pneu est crevé.",
    "Le rendez-vous est le 1er mars à 14h30, salle 3B.",
    "R.B.C. ferme à 17 h. Coût : 49,99$.",
    "Peux-tu imprimer le document et le supprimer après ?",
])
def test_messages_normaux(texte):
    score, raisons = analyser_regles(texte)
    assert score < 40, raisons
    assert not any("camouflés" in r for r in raisons)


# ---------- liens ----------

def test_lien_officiel_ok():
    _, raisons = analyser_regles("Ton relevé est prêt : https://www.desjardins.com/releve")
    assert not any("Imite" in r for r in raisons)


def test_domaine_cyrillique():
    score, raisons = analyser_regles("https://рaypal-secure.com/login")
    assert score >= 70
    assert any("Imite" in r and "paypal" in r for r in raisons)


# ---------- téléphone ----------

def test_numero_international():
    score, _ = analyser_numero("+1 809 555 0142")
    assert score >= 40


def test_numero_invalide():
    score, _ = analyser_numero("abc")
    assert score >= 40
