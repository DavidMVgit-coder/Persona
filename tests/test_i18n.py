import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from abus import analyser_abus
from i18n import TEXTES
from phone import analyser_numero
from rules import analyser_regles


def test_memes_cles_fr_en():
    assert TEXTES["fr"].keys() == TEXTES["en"].keys()


def test_raisons_en_anglais():
    _, raisons = analyser_regles("🚨 P@y3z now http://bit.ly/x", "en")
    assert any(r.startswith("Unusual mention of money") for r in raisons)
    assert any(r.startswith("Words disguised") for r in raisons)
    assert "Link without HTTPS" in raisons


def test_langue_inconnue_retombe_sur_francais():
    _, raisons = analyser_regles("http://bit.ly/x", "de")
    assert "Lien sans HTTPS" in raisons


def test_telephone_en_anglais():
    _, raisons = analyser_numero("+1 809 555 0142", "en")
    assert raisons == ["Area code 809 often used in scams"]


def test_abus_en_anglais():
    assert any(a.startswith("Insults") for a in analyser_abus("you moron", "en"))
