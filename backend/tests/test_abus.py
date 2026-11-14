"""Alertes de contenu offensant : insultes, menaces, diffamation, mots vulgaires (LDNOOBW)."""
import pytest

from abus import analyser_abus


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


@pytest.mark.parametrize("texte", [
    "Une belle gerbe de fleurs", "Il a pêché une tanche", "Mon chat et ma chatte",
    "Diplômé cum laude", "The rooster (cock) crowed", "This movie sucks",
])
def test_ldnoobw_double_sens_ignores(texte):
    assert analyser_abus(texte) == []


def test_ldnoobw_detecte_meme_camoufle():
    assert any("vulgaire" in a for a in analyser_abus("espèce de p0uffi@sse"))
