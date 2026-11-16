"""Heuristiques : signaux explicites de scam dans un texte (SMS, courriel).

Chaque règle produit un Signal : un code stable, des points, la raison affichée et un bout de
phrase pour le résumé de l'IA. Une seule détection (detecter) sert à deux choses :
- analyser_regles() : score et raisons, pour l'affichage
- signaux_ia()      : les mêmes signaux sous forme de nombres, donnés à l'IA (ia.py)
"""
import re
from dataclasses import dataclass
from urllib.parse import urlparse

import safebrowsing
from dictionnaire import DICO, Raison
from i18n import DEFAUT, TEXTES, avec_exemples, expliquer, separateur, t
from normalisation import motif_mots, normaliser, normaliser_simple, trompeurs

URL_RE = re.compile(r"https?://[^\s<>\"']+", re.I)
PONCTUATION_FIN = ".,;:!?)]}»"
IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")

# Les mots, emojis et domaines viennent de data/dictionnaire.json
RACCOURCIS = DICO.raccourcis
TLD_SUSPECTS = DICO.extensions_suspectes
MARQUES = DICO.marques            # marque (sans tirets ni espaces) -> domaines officiels

# Adresses écrites sans « http:// » (« bit.ly/abc », « fizz-reactivation.com »). On ne reconnaît que
# des extensions connues, pour ne pas prendre « M.Tremblay » ou « etc. » pour un site.
_TLD_CONNUS = sorted({"com", "ca", "net", "org", "info", "io", "co", "me", "ly", "gl", "gd", "at", "cc",
                      "id", "us", "app", "dev", "fr", "uk", "biz"} | {e.lstrip(".") for e in TLD_SUSPECTS},
                     key=len, reverse=True)
DOMAINE_NU_RE = re.compile(
    r"(?<![@\w.\-/])(?:[a-z0-9](?:[a-z0-9\-]*[a-z0-9])?\.)+(?:" + "|".join(_TLD_CONNUS) + r")(?![\w\-])"
    r"(?:/[^\s<>\"']*)?", re.I)

# Un mot-clé juste après une négation ne compte pas : « aucune action requise », « pas urgent », « no action required »
NEGATIONS = {"aucune", "aucun", "pas", "sans", "jamais", "nul", "no", "not", "never", "without"}
DERNIER_MOT_RE = re.compile(r"(\w+)\W*$")

MONTANT_RE = re.compile(r"\d[\d\s.,]*\s?(?:\$|€|dollars?\b)|[$€]\s?\d", re.I)
TELEPHONE_RE = re.compile(r"(?<!\d)(?:\+?1[\s.\-]?)?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}(?!\d)")


@dataclass(frozen=True)
class Signal:
    code: str           # identifiant stable : « cat.urgence », « url.marque », « camoufle », « emo.alerte »…
    points: int
    raison: str         # texte affiché dans « Pourquoi » (déjà traduit)
    resume: str = ""    # bout de phrase pour le résumé de l'IA (déjà traduit) ; vide = pas dans le résumé


@dataclass(frozen=True)
class Motif:
    """Une catégorie du dictionnaire, prête à chercher dans un texte normalisé."""
    nom: str
    raison: Raison
    resume: Raison | None
    points: int
    motif: re.Pattern       # toutes les formes normalisées (camouflage défait, sans accents)
    forme: dict             # forme normalisée -> mot tel qu'écrit dans le dictionnaire
    simple: dict            # forme normalisée -> motif du mot écrit normalement (pour repérer le camouflage)


def _preparer(categorie) -> Motif:
    forme = {normaliser(m): m for m in reversed(categorie.mots)}     # le premier mot du fichier gagne
    simple = {normaliser(m): motif_mots([normaliser_simple(m)]) for m in categorie.mots}
    return Motif(categorie.nom, categorie.raison, categorie.resume, categorie.points,
                 motif_mots(forme), forme, simple)


MOTIFS = [_preparer(c) for c in DICO.scam]
EMOJIS_TOUS = frozenset().union(*(c.emojis for c in DICO.emojis))


# ---------- liens ----------

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


def extraire_liens(texte: str) -> list[str]:
    """Liens du texte. Ceux écrits sans « http:// » sont rendus sous la forme « //bit.ly/abc »."""
    # « …/paiement. » : le point final fait partie de la phrase, pas du lien
    liens = [u.rstrip(PONCTUATION_FIN) for u in URL_RE.findall(texte)]
    reste = URL_RE.sub(" ", texte)          # pour ne pas retrouver « www.x.com » dans « https://www.x.com »
    liens += ["//" + m.group(0).rstrip(PONCTUATION_FIN) for m in DOMAINE_NU_RE.finditer(reste)]
    return liens


def _defauts_lien(url: str, langue: str) -> list[Signal]:
    hote = _hote(url)
    if not hote:
        return []
    signaux = []
    if IP_RE.match(hote):
        signaux.append(Signal("url.ip", 30, t(langue, "url.ip"), t(langue, "resume.url.trompeur")))
    if hote in RACCOURCIS:
        signaux.append(Signal("url.raccourci", 25, t(langue, "url.raccourci"), t(langue, "resume.url.raccourci")))
    if hote.endswith(TLD_SUSPECTS):
        signaux.append(Signal("url.tld", 25, t(langue, "url.tld", hote=hote), t(langue, "resume.url.tld")))
    if url.lower().startswith("http://"):
        signaux.append(Signal("url.http", 10, t(langue, "url.http")))
    if _hote_trompeur(hote):
        signaux.append(Signal("url.trompeur", 35, t(langue, "url.trompeur", hote=hote),
                              t(langue, "resume.url.trompeur")))
    # « рaypal-secure.com » (р cyrillique) ou « paypa1.com » doivent quand même être reconnus
    compact = normaliser(_decoder_punycode(hote)).replace("-", "")
    for marque, officiels in MARQUES.items():
        if marque in compact and not _domaine_officiel(hote, officiels):
            signaux.append(Signal("url.marque", 40, t(langue, "url.marque", marque=marque),
                                  t(langue, "resume.url.marque", marque=marque)))
            break
    return signaux


def _signaux_google(liens: list[str], langue: str) -> list[Signal]:
    """Liste de sites dangereux de Google (seulement si une clé est configurée)."""
    absolus = {("http:" + u if u.startswith("//") else u): u for u in liens}
    signaux = []
    for url, menace in safebrowsing.verifier(list(absolus)).items():
        cle = f"menace.{menace}" if f"menace.{menace}" in TEXTES[DEFAUT] else "menace.THREAT_TYPE_UNSPECIFIED"
        signaux.append(Signal("url.google", 60, t(langue, "url.google", hote=_hote(url), menace=t(langue, cle)),
                              t(langue, "resume.url.google")))
    return signaux


def _en_tete(texte: str, langue: str) -> list[Signal]:
    """Si le courriel collé contient une ligne From:, compare le nom affiché et l'adresse."""
    m = re.search(r"^from:\s*\"?([^<\"\n]*)\"?\s*<([^>\s]+)>", texte, re.I | re.M)
    if not m:
        return []
    nom = re.sub(r"[\s\-]", "", m.group(1).lower())
    domaine = m.group(2).split("@")[-1].lower()
    for marque, officiels in MARQUES.items():
        if marque in nom and not _domaine_officiel(domaine, officiels):
            return [Signal("entete.marque", 40, t(langue, "entete.marque", marque=marque, domaine=domaine),
                           t(langue, "resume.entete.marque", marque=marque))]
    return []


# ---------- détection ----------

def _apres_negation(texte_norm: str, debut: int) -> bool:
    m = DERNIER_MOT_RE.search(texte_norm[max(0, debut - 25):debut])
    return bool(m) and m.group(1) in NEGATIONS


def detecter(texte: str, langue: str = DEFAUT, reseau: bool = True) -> list[Signal]:
    """Tous les signaux de scam du texte. reseau=False : sans interroger Google Safe Browsing."""
    signaux = []
    texte_norm = normaliser(texte)
    texte_simple = normaliser_simple(texte)
    camoufles = []

    for cat in MOTIFS:
        trouves = list(dict.fromkeys(m.group(0) for m in cat.motif.finditer(texte_norm)
                                     if not _apres_negation(texte_norm, m.start())))
        if not trouves:
            continue
        mots = [cat.forme[f] for f in trouves]
        camoufles += [cat.forme[f] for f in trouves if not cat.simple[f].search(texte_simple)]
        signaux.append(Signal(f"cat.{cat.nom}", cat.points, expliquer(langue, cat.raison.texte(langue), mots),
                              cat.resume.texte(langue) if cat.resume else ""))

    if camoufles:
        signaux.append(Signal("camoufle", 25, avec_exemples(langue, "camoufle", dict.fromkeys(camoufles)),
                              t(langue, "resume.camoufle")))
    for code, mots in trompeurs(texte):
        raison = avec_exemples(langue, code, mots) if mots else t(langue, code)
        signaux.append(Signal(code, 25, raison, t(langue, "resume.trompeurs")))

    emojis = [c for c in texte.replace("️", "") if c in EMOJIS_TOUS]
    for cat in DICO.emojis:
        vus = list(dict.fromkeys(e for e in emojis if e in cat.emojis))
        if vus:
            signaux.append(Signal(f"emo.{cat.nom}", cat.points,
                                  f"{cat.raison.texte(langue)}{separateur(langue)}{' '.join(vus[:5])}"))
    if len(emojis) >= 5:
        signaux.append(Signal("emo.beaucoup", 10, t(langue, "emo.beaucoup", n=len(emojis)),
                              t(langue, "resume.emo.beaucoup")))

    liens = extraire_liens(texte)
    if reseau:
        signaux += _signaux_google(liens, langue)
    for url in liens:
        signaux += _defauts_lien(url, langue)
    signaux += _en_tete(texte, langue)
    return signaux


def score_regles(signaux: list[Signal]) -> int:
    return min(100, sum(s.points for s in signaux))


def raisons(signaux: list[Signal]) -> list[str]:
    return list(dict.fromkeys(s.raison for s in signaux))       # dédoublonne en gardant l'ordre


def analyser_regles(texte: str, langue: str = DEFAUT):
    signaux = detecter(texte, langue)
    return score_regles(signaux), raisons(signaux)


def signaux_ia(texte: str) -> dict[str, float]:
    """Ce que l'IA reçoit en plus des mots : chaque signal des règles (0 ou 1) et quelques mesures."""
    signaux = detecter(texte, DEFAUT, reseau=False)
    v = {s.code: 1.0 for s in signaux}
    v["score_regles"] = score_regles(signaux) / 100
    v["lien"] = 1.0 if extraire_liens(texte) else 0.0
    v["montant"] = 1.0 if MONTANT_RE.search(texte) else 0.0
    v["telephone"] = 1.0 if TELEPHONE_RE.search(texte) else 0.0
    v["exclamations"] = min(texte.count("!"), 3) / 3
    lettres = [c for c in texte if c.isalpha()]
    # Proportion de majuscules (« URGENT !!! VOTRE COMPTE SERA FERMÉ ») ; ignorée sur les textes très courts
    v["majuscules"] = sum(c.isupper() for c in lettres) / len(lettres) if len(lettres) >= 15 else 0.0
    return v
