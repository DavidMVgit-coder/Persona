"""Lit data/dictionnaire.json : tous les mots, emojis et domaines utilisés par le détecteur.

Le fichier est vérifié au chargement : en cas d'erreur, le message dit exactement quoi corriger
(par exemple « scam.urgence.points doit être un nombre ») au lieu d'un plantage obscur plus loin.
"""
import json
from dataclasses import dataclass

import config
from i18n import DEFAUT, LANGUES, langue_valide


class ErreurDictionnaire(ValueError):
    pass


@dataclass(frozen=True)
class Raison:
    """Texte affiché, par langue. Retombe sur le français si la traduction manque."""
    textes: dict

    def texte(self, langue: str) -> str:
        return self.textes.get(langue_valide(langue)) or self.textes[DEFAUT]


@dataclass(frozen=True)
class CategorieMots:
    nom: str
    raison: Raison
    mots: list          # toutes langues confondues, dans l'ordre du fichier
    points: int = 0
    resume: Raison | None = None    # bout de phrase pour le résumé de l'IA (optionnel)


@dataclass(frozen=True)
class TypeArnaque:
    """Une sorte d'arnaque (colis, banque, faux proche…) avec le conseil à donner."""
    nom: str
    titre: Raison       # « arnaque au colis » (s'insère dans une phrase)
    conseil: Raison
    mots: list


@dataclass(frozen=True)
class CategorieEmojis:
    nom: str
    raison: Raison
    emojis: frozenset
    points: int


@dataclass(frozen=True)
class Dictionnaire:
    scam: list
    emojis: list
    raccourcis: tuple
    extensions_suspectes: tuple
    marques: dict
    abus: list
    accusations: CategorieMots
    ldnoobw_raison: Raison
    ldnoobw_exclusions: frozenset
    types: list = ()


# ---------- vérifications ----------

def _exiger(cond: bool, chemin: str, attendu: str) -> None:
    if not cond:
        raise ErreurDictionnaire(f"{config.DICTIONNAIRE_PATH.name} : {chemin} doit être {attendu}")


def _objet(valeur, chemin: str) -> dict:
    _exiger(isinstance(valeur, dict), chemin, "un objet { … }")
    return valeur


def _liste_textes(valeur, chemin: str) -> list:
    _exiger(isinstance(valeur, list) and all(isinstance(v, str) and v.strip() for v in valeur),
            chemin, "une liste de textes non vides")
    return [v.strip() for v in valeur]


def _raison(valeur, chemin: str) -> Raison:
    textes = _objet(valeur, chemin)
    _exiger(isinstance(textes.get(DEFAUT), str) and textes[DEFAUT].strip(),
            f"{chemin}.{DEFAUT}", "un texte non vide")
    for langue, texte in textes.items():
        _exiger(langue in LANGUES, f"{chemin}.{langue}", f"une langue connue ({', '.join(LANGUES)})")
        _exiger(isinstance(texte, str), f"{chemin}.{langue}", "un texte")
    return Raison(textes)


def _mots_par_langue(valeur, chemin: str) -> list:
    par_langue = _objet(valeur, chemin)
    mots = []
    for langue, liste in par_langue.items():
        _exiger(langue in LANGUES, f"{chemin}.{langue}", f"une langue connue ({', '.join(LANGUES)})")
        mots += _liste_textes(liste, f"{chemin}.{langue}")
    _exiger(bool(mots), chemin, "une liste contenant au moins un mot")
    return list(dict.fromkeys(mots))


def _points(valeur, chemin: str) -> int:
    _exiger(isinstance(valeur, int) and not isinstance(valeur, bool) and 0 <= valeur <= 100,
            chemin, "un nombre entier entre 0 et 100")
    return valeur


def _categorie_mots(nom: str, bloc, chemin: str, avec_points: bool) -> CategorieMots:
    bloc = _objet(bloc, chemin)
    return CategorieMots(
        nom=nom,
        raison=_raison(bloc.get("raison"), f"{chemin}.raison"),
        mots=_mots_par_langue(bloc.get("mots"), f"{chemin}.mots"),
        points=_points(bloc.get("points"), f"{chemin}.points") if avec_points else 0,
        resume=_raison(bloc["resume"], f"{chemin}.resume") if "resume" in bloc else None,
    )


def _type(nom: str, bloc, chemin: str) -> TypeArnaque:
    bloc = _objet(bloc, chemin)
    return TypeArnaque(
        nom=nom,
        titre=_raison(bloc.get("nom"), f"{chemin}.nom"),
        conseil=_raison(bloc.get("conseil"), f"{chemin}.conseil"),
        mots=_mots_par_langue(bloc.get("mots"), f"{chemin}.mots"),
    )


def _emojis(nom: str, bloc, chemin: str) -> CategorieEmojis:
    bloc = _objet(bloc, chemin)
    # « ⚠️ » collé depuis un clavier contient un sélecteur de variante invisible : on le retire
    emojis = frozenset(e.replace("️", "") for e in _liste_textes(bloc.get("emojis"), f"{chemin}.emojis"))
    for e in emojis:
        _exiger(len(e) == 1, f"{chemin}.emojis ({e})", "des emojis d'un seul caractère")
    return CategorieEmojis(nom, _raison(bloc.get("raison"), f"{chemin}.raison"), emojis,
                           _points(bloc.get("points"), f"{chemin}.points"))


def analyser_dictionnaire(donnees) -> Dictionnaire:
    racine = _objet(donnees, "le fichier")
    liens = _objet(racine.get("liens"), "liens")
    marques = _objet(liens.get("marques"), "liens.marques")
    ldnoobw = _objet(racine.get("ldnoobw"), "ldnoobw")
    exclusions = _objet(ldnoobw.get("exclusions"), "ldnoobw.exclusions")

    return Dictionnaire(
        scam=[_categorie_mots(n, b, f"scam.{n}", True) for n, b in _objet(racine.get("scam"), "scam").items()],
        emojis=[_emojis(n, b, f"emojis.{n}") for n, b in _objet(racine.get("emojis"), "emojis").items()],
        raccourcis=tuple(d.lower() for d in _liste_textes(liens.get("raccourcis"), "liens.raccourcis")),
        extensions_suspectes=tuple(
            e.lower() for e in _liste_textes(liens.get("extensions_suspectes"), "liens.extensions_suspectes")),
        marques={m.lower().replace("-", "").replace(" ", ""): tuple(d.lower() for d in _liste_textes(v, f"liens.marques.{m}"))
                 for m, v in marques.items()},
        abus=[_categorie_mots(n, b, f"abus.{n}", False) for n, b in _objet(racine.get("abus"), "abus").items()],
        accusations=_categorie_mots("accusations", racine.get("accusations"), "accusations", False),
        ldnoobw_raison=_raison(ldnoobw.get("raison"), "ldnoobw.raison"),
        ldnoobw_exclusions=frozenset(
            m.lower() for langue, liste in exclusions.items()
            for m in _liste_textes(liste, f"ldnoobw.exclusions.{langue}")),
        # « types » est optionnel : sans lui, l'IA ne nomme simplement pas le type d'arnaque
        types=[_type(n, b, f"types.{n}") for n, b in _objet(racine.get("types", {}), "types").items()],
    )


def charger(chemin=None) -> Dictionnaire:
    chemin = chemin or config.DICTIONNAIRE_PATH
    try:
        donnees = json.loads(chemin.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ErreurDictionnaire(f"Fichier introuvable : {chemin}") from None
    except json.JSONDecodeError as e:
        # ligne/colonne pour retrouver vite une virgule oubliée
        raise ErreurDictionnaire(f"{chemin.name} : JSON invalide ligne {e.lineno}, colonne {e.colno} ({e.msg})") from None
    return analyser_dictionnaire(donnees)


DICO = charger()
