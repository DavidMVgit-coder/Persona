"""Défait le camouflage des mots utilisé pour contourner les filtres anti-scam.

Exemples ramenés à « payez » / « urgent » / « virement » :
    p@y3z, ᴜʀɢᴇɴᴛ, 𝐮𝐫𝐠𝐞𝐧𝐭, ｕｒｇｅｎｔ, v i r e m e n t, v.i.r.e.m.e.n.t, urg​ent (espace invisible),
    рayez (avec un « р » cyrillique).
"""
import re
import unicodedata

from i18n import DEFAUT, avec_exemples, t

# Caractères invisibles glissés au milieu des mots
INVISIBLES_RE = re.compile("[​‌‍⁠⁡⁢⁣⁤﻿­᠎]")

# Lettres d'autres alphabets qui ressemblent à des lettres latines (minuscules)
HOMOGLYPHES = str.maketrans({
    # cyrillique
    "а": "a", "в": "b", "е": "e", "ё": "e", "к": "k", "м": "m", "н": "h", "о": "o", "р": "p",
    "с": "c", "т": "t", "у": "y", "х": "x", "і": "i", "ї": "i", "ј": "j", "ѕ": "s", "ԁ": "d",
    "ԛ": "q", "ԝ": "w", "һ": "h", "ӏ": "l",
    # grec
    "α": "a", "β": "b", "ε": "e", "η": "n", "ι": "i", "κ": "k", "ν": "v", "ο": "o", "ρ": "p",
    "τ": "t", "υ": "u", "χ": "x", "ω": "w",
    # petites capitales (ᴜʀɢᴇɴᴛ) que la normalisation Unicode ne convertit pas
    "ᴀ": "a", "ʙ": "b", "ᴄ": "c", "ᴅ": "d", "ᴇ": "e", "ꜰ": "f", "ғ": "f", "ɢ": "g", "ʜ": "h",
    "ɪ": "i", "ᴊ": "j", "ᴋ": "k", "ʟ": "l", "ᴍ": "m", "ɴ": "n", "ᴏ": "o", "ᴘ": "p", "ǫ": "q",
    "ʀ": "r", "ꜱ": "s", "ᴛ": "t", "ᴜ": "u", "ᴠ": "v", "ᴡ": "w", "ʏ": "y", "ᴢ": "z",
    # autres sosies courants
    "ı": "i", "ɑ": "a", "ɡ": "g", "ℓ": "l",
})

# Chiffres et symboles utilisés comme lettres (« leetspeak »)
LEET = str.maketrans({
    "0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "8": "b", "9": "g",
    "@": "a", "$": "s", "€": "e", "!": "i", "|": "l", "+": "t",
})
LEET_CHARS = set("013457895@$€!|+")

# Lettres isolées séparées par des espaces, points, tirets… : « v i r e m e n t »
LETTRES_ESPACEES_RE = re.compile(r"(?<!\w)(?:\w[ .\-_*·•/]+){3,}\w(?!\w)")
ALPHABETS_RE = re.compile(r"[a-z]")
NON_LATIN_RE = re.compile(r"[Ͱ-ϿЀ-ӿԀ-ԯ]")


def sans_accents(texte: str) -> str:
    decompose = unicodedata.normalize("NFD", texte)
    return "".join(c for c in decompose if not unicodedata.combining(c))


def normaliser_simple(texte: str) -> str:
    """Minuscules + sans accents + apostrophes uniformisées. Ne défait aucun camouflage."""
    return sans_accents(texte.lower()).replace("’", "'")


def _deleet(mot: str) -> str:
    # Seulement dans les mots qui mélangent lettres et chiffres/symboles (« p@yez », « c0mpte »),
    # pour ne pas toucher aux montants, heures ou numéros.
    if mot.isalpha() or not any(c.isalpha() for c in mot) or not (set(mot) & LEET_CHARS):
        return mot
    if "://" in mot or mot.startswith("www."):
        return mot
    # garde la ponctuation de fin (« p@yez! » -> « payez! » et pas « payezi »)
    fin = re.search(r"[!.,;:?]+$", mot)
    coeur, queue = (mot[: fin.start()], fin.group(0)) if fin else (mot, "")
    return coeur.translate(LEET) + queue


def normaliser(texte: str) -> str:
    """Normalisation complète : défait le camouflage, puis minuscules sans accents."""
    s = INVISIBLES_RE.sub("", texte)
    s = unicodedata.normalize("NFKC", s)        # 𝐮𝐫𝐠𝐞𝐧𝐭, ｕｒｇｅｎｔ, ⓤⓡⓖ… -> urgent
    s = s.lower().translate(HOMOGLYPHES)
    s = re.sub(r"\S+", lambda m: _deleet(m.group(0)), s)
    s = LETTRES_ESPACEES_RE.sub(lambda m: re.sub(r"[ .\-_*·•/]+", "", m.group(0)), s)
    return normaliser_simple(s)


def motif_mots(formes) -> re.Pattern:
    """Regex qui trouve l'une des formes (déjà normalisées) en mot entier, la plus longue d'abord."""
    alt = "|".join(sorted({re.escape(f) for f in formes}, key=len, reverse=True))
    return re.compile(rf"(?<!\w)(?:{alt})(?!\w)")


def trompeurs(texte: str) -> list[tuple[str, list[str]]]:
    """Signaux qui ne s'expliquent presque jamais dans un message honnête : [(code, exemples)].

    Codes : « invisibles » (caractères invisibles), « alphabets » (mot qui mélange des alphabets).
    """
    trouves = []
    if INVISIBLES_RE.search(texte):
        trouves.append(("invisibles", []))
    for mot in re.findall(r"\w+", texte.lower()):
        if ALPHABETS_RE.search(mot) and NON_LATIN_RE.search(mot):
            trouves.append(("alphabets", [mot]))
            break
    return trouves


def caracteres_trompeurs(texte: str, langue: str = DEFAUT) -> list[str]:
    """Mêmes signaux que trompeurs(), sous forme de phrases prêtes à afficher."""
    return [avec_exemples(langue, code, mots) if mots else t(langue, code) for code, mots in trompeurs(texte)]
