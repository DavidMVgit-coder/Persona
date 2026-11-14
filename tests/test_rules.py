import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rules import analyser_regles
from phone import analyser_numero


def test_scam_colis():
    txt = "Postes Canada : payez 2,99 $ dans les 24 heures http://postes-canada-suivi.xyz/p"
    score, raisons = analyser_regles(txt)
    assert score >= 70
    assert any("Imite" in r for r in raisons)


def test_message_normal():
    score, _ = analyser_regles("Salut, on se voit demain à 18 h au resto ?")
    assert score < 40


def test_lien_officiel_ok():
    score, raisons = analyser_regles("Ton relevé est prêt : https://www.desjardins.com/releve")
    assert not any("Imite" in r for r in raisons)


def test_numero_international():
    score, raisons = analyser_numero("+1 809 555 0142")
    assert score >= 40


def test_numero_invalide():
    score, _ = analyser_numero("abc")
    assert score >= 40
