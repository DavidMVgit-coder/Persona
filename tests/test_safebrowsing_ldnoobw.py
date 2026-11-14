import sys
import urllib.error
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

import config
import safebrowsing
from abus import analyser_abus
from rules import analyser_regles

LIEN = "https://exemple-dangereux.com/connexion"


@pytest.fixture
def google(monkeypatch):
    """Active Safe Browsing avec une fausse clé et simule la réponse de Google (aucun appel réseau)."""
    monkeypatch.setattr(config, "GOOGLE_SAFE_BROWSING_KEY", "fausse-cle")
    safebrowsing._cache.clear()
    appels = []

    def fausse_api(reponse):
        def _interroger(urls):
            appels.append(urls)
            if isinstance(reponse, Exception):
                raise reponse
            return reponse
        monkeypatch.setattr(safebrowsing, "_interroger", _interroger)
        return appels
    yield fausse_api
    safebrowsing._cache.clear()


def test_sans_cle_aucun_appel(monkeypatch):
    monkeypatch.setattr(config, "GOOGLE_SAFE_BROWSING_KEY", "")
    monkeypatch.setattr(safebrowsing, "_interroger", lambda urls: pytest.fail("appel réseau inattendu"))
    assert safebrowsing.verifier([LIEN]) == {}


def test_lien_signale_par_google(google):
    google({LIEN: ("SOCIAL_ENGINEERING", 300)})
    score, raisons = analyser_regles(f"Connectez-vous ici : {LIEN}.")   # point final retiré du lien
    assert score >= 60
    assert any("hameçonnage" in r and "Google" in r for r in raisons)


def test_lien_signale_en_anglais(google):
    google({LIEN: ("MALWARE", 300)})
    _, raisons = analyser_regles(LIEN, "en")
    assert any("malware" in r and "Advisory provided by Google" in r for r in raisons)


def test_type_de_menace_inconnu(google):
    google({LIEN: ("NOUVEAU_TYPE", 300)})
    _, raisons = analyser_regles(LIEN)
    assert any("site dangereux" in r for r in raisons)


def test_google_indisponible_ne_casse_pas_l_analyse(google):
    google(urllib.error.URLError("pas de réseau"))
    score, raisons = analyser_regles(f"Payez ici : {LIEN}")
    assert not any("Google" in r for r in raisons)
    assert score > 0                     # les autres règles fonctionnent toujours


def test_cache(google):
    appels = google({})
    safebrowsing.verifier([LIEN])
    safebrowsing.verifier([LIEN])
    assert len(appels) == 1


@pytest.mark.parametrize("texte", [
    "Une belle gerbe de fleurs", "Il a pêché une tanche", "Mon chat et ma chatte",
    "Diplômé cum laude", "The rooster (cock) crowed", "This movie sucks",
])
def test_ldnoobw_double_sens_ignores(texte):
    assert analyser_abus(texte) == []


def test_ldnoobw_detecte_meme_camoufle():
    assert any("vulgaire" in a for a in analyser_abus("espèce de p0uffi@sse"))
