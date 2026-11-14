import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from abus import analyser_abus
from rules import analyser_regles


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


def test_domaine_cyrillique():
    score, raisons = analyser_regles("https://рaypal-secure.com/login")
    assert score >= 70
    assert any("Imite" in r and "paypal" in r for r in raisons)


def test_emojis_scam():
    score, raisons = analyser_regles("🚨🚨 Dernière chance ! 🎁 Gagnez 👉 http://bit.ly/x 💰")
    assert score >= 70
    assert any("Emojis" in r for r in raisons)


def test_sextorsion():
    score, _ = analyser_regles("J'ai piraté votre webcam. Payez en bitcoin sinon j'envoie la vidéo à tous vos contacts.")
    assert score >= 70


@pytest.mark.parametrize("texte", [
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


def test_insultes_camouflees():
    assert any("Insultes" in a for a in analyser_abus("T'es un c0nnard"))


def test_diffamation():
    alertes = analyser_abus("Jean Tremblay est un voleur, faites tourner !")
    assert any("Accusation" in a for a in alertes)
    assert any("circuler" in a for a in alertes)


def test_menaces():
    assert any("Menaces" in a for a in analyser_abus("Je sais où tu habites"))


def test_negation_pas_accusation():
    assert analyser_abus("Il n'est pas un voleur, arrête.") == []


def test_message_poli_sans_alerte():
    assert analyser_abus("Merci pour ton aide hier, c'était super !") == []
