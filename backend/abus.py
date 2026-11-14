"""Contenu offensant : insultes, propos diffamatoires, menaces et harcèlement.

Ces signaux ne changent PAS le score de scam : ils sont renvoyés à part (champ « alertes »),
parce qu'un message peut être insultant sans être une arnaque, et l'inverse.

Les mots viennent de data/dictionnaire.json (sections « abus », « accusations », « ldnoobw »)
et des listes data/ldnoobw/*.txt.
"""
import re

import config
from dictionnaire import DICO
from i18n import DEFAUT, expliquer
from normalisation import motif_mots, normaliser


def _charger_ldnoobw() -> list[str]:
    mots = []
    for chemin in sorted(config.LDNOOBW_DIR.glob("*.txt")):
        for ligne in chemin.read_text(encoding="utf-8").splitlines():
            mot = ligne.strip()
            if mot and not mot.startswith("#") and mot.lower() not in DICO.ldnoobw_exclusions:
                mots.append(mot)
    return mots


def _motif(mots):
    """Motif sur la forme normalisée + table pour réafficher le mot avec ses accents."""
    forme = {normaliser(m): m for m in reversed(mots)}
    return motif_mots(forme), forme


# Catégories du dictionnaire (insultes, menaces, diffamation, propagation…)
CATEGORIES = [(c.raison, *_motif(c.mots)) for c in DICO.abus]

# Mots LDNOOBW, sauf ceux déjà présents dans une catégorie du dictionnaire (ils y sont mieux classés)
_deja = {normaliser(m) for c in DICO.abus for m in c.mots}
VULGAIRE = [m for m in _charger_ldnoobw() if normaliser(m) not in _deja]
if VULGAIRE:
    CATEGORIES.insert(1, (DICO.ldnoobw_raison, *_motif(VULGAIRE)))

# Accusation grave formulée comme un fait : « X est un voleur », « c'est une fraudeuse »
_NOMS = sorted({re.escape(normaliser(m)) for m in DICO.accusations.mots}, key=len, reverse=True)
ACCUSATION_RE = re.compile(
    r"(?<!\w)(?:est|c'est|etait|c'etait|sont|un vrai|une vraie|is a|is an|was a|are)\s+"
    r"(?:un |une |des |le |la |les |a |an |)?(?:vrai |vraie |gros |grosse |sale |)"
    rf"(?:{'|'.join(_NOMS)})(?!\w)"
)


def analyser_abus(texte: str, langue: str = DEFAUT) -> list[str]:
    t = normaliser(texte)
    alertes = []
    for raison, motif, forme in CATEGORIES:
        trouves = list(dict.fromkeys(forme[m.group(0)] for m in motif.finditer(t)))
        if trouves:
            alertes.append(expliquer(langue, raison.texte(langue), trouves))

    accusations = list(dict.fromkeys(m.group(0) for m in ACCUSATION_RE.finditer(t)))
    if accusations:
        alertes.append(expliquer(langue, DICO.accusations.raison.texte(langue), accusations))
    return alertes
