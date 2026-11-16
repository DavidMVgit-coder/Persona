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


# ---------- nouvelles règles ----------

@pytest.mark.parametrize("texte", [
    "Ton colis a été livré, aucune action requise",
    "No action required on your part",
    "Ce n'est pas urgent, réponds quand tu peux",
])
def test_negation_annule_le_mot_cle(texte):
    score, raisons = analyser_regles(texte)
    assert score == 0, raisons


def test_mot_cle_sans_negation_compte_toujours():
    score, _ = analyser_regles("Action requise : confirmez votre compte")
    assert score > 0


@pytest.mark.parametrize("texte, attendu", [
    ("Confirmez sous 24h : bit.ly/pp-verif", "raccourci"),
    ("Rends-toi sur fizz-reactivation.com pour le réactiver", "fizz"),
    ("Payez ici : postes-canada-suivi.xyz/p", "postes-canada-suivi.xyz"),
])
def test_lien_sans_http(texte, attendu):
    _, raisons = analyser_regles(texte)
    assert any(attendu in r.lower() for r in raisons), raisons


@pytest.mark.parametrize("texte", [
    "Écris à info@desjardins.com pour toute question",     # une adresse courriel n'est pas un lien
    "M.Tremblay arrive à 15 h, etc.",                       # « M.Tremblay » n'est pas un site
    "Voir www.desjardins.com/releve",                       # domaine officiel
])
def test_pas_de_faux_lien(texte):
    score, raisons = analyser_regles(texte)
    assert score == 0, raisons


def test_faux_proche_et_secret():
    score, raisons = analyser_regles("Grand-maman, c'est ton petit-fils. J'ai eu un accident, n'en parle pas à papa.")
    assert any("proche" in r for r in raisons)
    assert any("secret" in r for r in raisons)
    assert score >= 40


def test_messagerie_et_alerte():
    _, raisons = analyser_regles("Commande suspecte sur votre compte. Écris-moi sur WhatsApp.")
    assert any("messagerie" in r for r in raisons)
    assert any("suspecte" in r for r in raisons)
