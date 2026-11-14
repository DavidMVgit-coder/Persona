"""Heuristiques : signaux explicites de scam dans un texte (SMS, courriel)."""
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import safebrowsing
from dictionnaire import DICO, Raison
from i18n import DEFAUT, TEXTES, avec_exemples, expliquer, t
from normalisation import caracteres_trompeurs, normaliser, normaliser_simple

URL_RE = re.compile(r"https?://[^\s<>\"']+", re.I)
PONCTUATION_FIN = ".,;:!?)]}»"
IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")

# Les mots, emojis et domaines viennent de data/dictionnaire.json
RACCOURCIS = DICO.raccourcis
TLD_SUSPECTS = DICO.extensions_suspectes
MARQUES = DICO.marques            # marque (sans tirets ni espaces) -> domaines officiels


def _motif(formes):
    alt = "|".join(sorted({re.escape(f) for f in formes}, key=len, reverse=True))
    return re.compile(rf"(?<!\w)(?:{alt})(?!\w)")


@dataclass(frozen=True)
class Motif:
    """Une catégorie du dictionnaire, prête à chercher dans un texte normalisé."""
    raison: Raison
    points: int
    motif: re.Pattern       # toutes les formes normalisées (camouflage défait, sans accents)
    forme: dict             # forme normalisée -> mot tel qu'écrit dans le dictionnaire
    simple: dict            # forme normalisée -> motif du mot écrit normalement (pour repérer le camouflage)


def _preparer(categorie) -> Motif:
    forme = {normaliser(m): m for m in reversed(categorie.mots)}     # le premier mot du fichier gagne
    simple = {normaliser(m): _motif([normaliser_simple(m)]) for m in categorie.mots}
    return Motif(categorie.raison, categorie.points, _motif(forme), forme, simple)


MOTIFS = [_preparer(c) for c in DICO.scam]
EMOJIS_TOUS = frozenset().union(*(c.emojis for c in DICO.emojis))


def _hote_trompeur(hote: str) -> bool:
    """Domaine écrit avec des lettres non latines (рaypal.com) ou en punycode (xn--…)."""
    return any(not c.isascii() for c in hote) or any(p.startswith("xn--") for p in hote.split("."))


def _decoder_punycode(hote: str) -> str:
    try:
        return ".".join(p.encode().decode("idna") if p.startswith("xn--") else p for p in hote.split("."))
    except UnicodeError:
        return hote


def _hote(url: str) -> str:
    h = (urlparse(url).hostname or "").lower()
    return h[4:] if h.startswith("www.") else h


def _domaine_officiel(hote: str, officiels) -> bool:
    return any(hote == d or hote.endswith("." + d) for d in officiels)


def analyser_urls(texte: str, langue: str = DEFAUT):
    score, raisons = 0, []
    # « …/paiement. » : le point final fait partie de la phrase, pas du lien
    urls = [u.rstrip(PONCTUATION_FIN) for u in URL_RE.findall(texte)]

    # Liste de sites dangereux de Google (si une clé est configurée)
    for url, menace in safebrowsing.verifier(urls).items():
        cle = f"menace.{menace}" if f"menace.{menace}" in TEXTES[DEFAUT] else "menace.THREAT_TYPE_UNSPECIFIED"
        raisons.append(t(langue, "url.google", hote=_hote(url), menace=t(langue, cle)))
        score += 60

    for url in urls:
        hote = _hote(url)
        if not hote:
            continue
        if IP_RE.match(hote):
            raisons.append(t(langue, "url.ip")); score += 30
        if hote in RACCOURCIS:
            raisons.append(t(langue, "url.raccourci")); score += 25
        if hote.endswith(TLD_SUSPECTS):
            raisons.append(t(langue, "url.tld", hote=hote)); score += 25
        if url.lower().startswith("http://"):
            raisons.append(t(langue, "url.http")); score += 10
        if _hote_trompeur(hote):
            raisons.append(t(langue, "url.trompeur", hote=hote)); score += 35
        # « рaypal-secure.com » (р cyrillique) ou « paypa1.com » doivent quand même être reconnus
        compact = normaliser(_decoder_punycode(hote)).replace("-", "")
        for marque, officiels in MARQUES.items():
            if marque in compact and not _domaine_officiel(hote, officiels):
                raisons.append(t(langue, "url.marque", marque=marque))
                score += 40
                break
    return score, raisons


def analyser_en_tete(texte: str, langue: str = DEFAUT):
    """Si le courriel collé contient une ligne From:, compare le nom affiché et l'adresse."""
    m = re.search(r"^from:\s*\"?([^<\"\n]*)\"?\s*<([^>\s]+)>", texte, re.I | re.M)
    if not m:
        return 0, []
    nom = re.sub(r"[\s\-]", "", m.group(1).lower())
    domaine = m.group(2).split("@")[-1].lower()
    for marque, officiels in MARQUES.items():
        if marque in nom and not _domaine_officiel(domaine, officiels):
            return 40, [t(langue, "entete.marque", marque=marque, domaine=domaine)]
    return 0, []


def analyser_regles(texte: str, langue: str = DEFAUT):
    raisons, score = [], 0

    texte_norm = normaliser(texte)
    texte_simple = normaliser_simple(texte)
    camoufles = []

    for cat in MOTIFS:
        trouves = list(dict.fromkeys(m.group(0) for m in cat.motif.finditer(texte_norm)))
        if not trouves:
            continue
        mots = [cat.forme[f] for f in trouves]
        camoufles += [cat.forme[f] for f in trouves if not cat.simple[f].search(texte_simple)]
        raisons.append(expliquer(langue, cat.raison.texte(langue), mots)); score += cat.points

    if camoufles:
        raisons.append(avec_exemples(langue, "camoufle", dict.fromkeys(camoufles))); score += 25
    for r in caracteres_trompeurs(texte, langue):
        raisons.append(r); score += 25

    emojis = [c for c in texte.replace("\ufe0f", "") if c in EMOJIS_TOUS]
    for cat in DICO.emojis:
        vus = list(dict.fromkeys(e for e in emojis if e in cat.emojis))
        if vus:
            sep = " : " if langue == "fr" else ": "
            raisons.append(f"{cat.raison.texte(langue)}{sep}{' '.join(vus[:5])}"); score += cat.points
    if len(emojis) >= 5:
        raisons.append(t(langue, "emo.beaucoup", n=len(emojis))); score += 10

    s_url, r_url = analyser_urls(texte, langue)
    s_hdr, r_hdr = analyser_en_tete(texte, langue)
    score += s_url + s_hdr
    raisons += r_url + r_hdr

    # dédoublonne en gardant l'ordre
    raisons = list(dict.fromkeys(raisons))
    return min(100, score), raisons
