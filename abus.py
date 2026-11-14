"""Contenu offensant : insultes, propos diffamatoires, menaces et harcèlement.

Ces signaux ne changent PAS le score de scam : ils sont renvoyés à part (champ « alertes »),
parce qu'un message peut être insultant sans être une arnaque, et l'inverse.
"""
import re
from pathlib import Path

from i18n import DEFAUT, avec_exemples
from normalisation import normaliser

LDNOOBW_DIR = Path(__file__).resolve().parent / "data" / "ldnoobw"

# Mots des listes LDNOOBW qu'on ignore : double sens courant, termes médicaux ou jurons
# si fréquents qu'ils noieraient les vrais signaux.
EXCLUSIONS_LDNOOBW = {
    # français
    "baiser", "bander", "bordel", "bourré", "bourrée", "branler", "caca", "chatte", "chier", "con",
    "cul", "déconne", "déconner", "emmerdant", "emmerder", "folle", "foutre", "gerbe", "gerber",
    "gueule", "jouir", "merde", "meuf", "pédale", "péter", "pipi", "pisser", "putain", "ramoner",
    "suce", "tanche", "tapette", "trique", "turlute",
    # anglais : double sens
    "ass", "bareback", "big black", "blonde action", "brunette action", "cock", "coon", "coons",
    "cum", "domination", "escort", "girl on", "hard core", "hardcore", "hot chick", "huge fat",
    "jelly donut", "lolita", "mong", "panties", "panty", "pleasure chest", "poof", "santorum",
    "scat", "scissoring", "shrimping", "skeet", "snatch", "snowballing", "suck", "sucks",
    "tainted love", "taste my", "tied up", "tight white", "tongue in a", "twinkie", "xx",
    # anglais : termes médicaux ou d'actualité
    "anal", "anus", "butt", "clitoris", "ejaculation", "erotic", "erotism", "eunuch", "fecal",
    "genitals", "homoerotic", "incest", "intercourse", "lovemaking", "nipple", "nipples", "nude",
    "nudity", "penis", "rectum", "sadism", "semen", "sex", "sexual", "sexually", "sexuality",
    "sexy", "vagina", "vulva",
    # anglais : jurons très courants (« fuck you » reste détecté comme insulte)
    "bullshit", "fuck", "fuckin", "fucking", "god damn", "shit", "shitty",
}


def _charger_ldnoobw() -> list[str]:
    mots = []
    for fichier in ("fr.txt", "en.txt"):
        chemin = LDNOOBW_DIR / fichier
        if not chemin.exists():
            continue
        for ligne in chemin.read_text(encoding="utf-8").splitlines():
            mot = ligne.strip()
            if mot and not mot.startswith("#") and mot.lower() not in EXCLUSIONS_LDNOOBW:
                mots.append(mot)
    return mots

INSULTES = [
    "connard", "connasse", "conne", "salaud", "salope", "pute", "enculé", "encule",
    "fils de pute", "fdp", "ntm", "nique ta mère", "nique ta mere", "ferme ta gueule",
    "va te faire foutre", "va chier", "imbécile", "imbecile", "crétin", "cretin", "débile",
    "abruti", "abrutie", "idiot", "idiote", "attardé", "attardée", "trou de cul",
    "tête de cul", "gros tas", "grosse vache", "sale chien", "espèce d'ordure", "pourriture",
    "minable", "sous-merde", "sac à merde",
    "fuck you", "fuck off", "asshole", "bitch", "bastard", "moron", "stupid", "loser", "piece of shit", "son of a bitch", "dumbass", "jackass", "whore", "slut",
]

# Accusation grave formulée comme un fait : « X est un voleur », « c'est une fraudeuse »
ACCUSATIONS = [
    "voleur", "voleuse", "escroc", "arnaqueur", "arnaqueuse", "fraudeur", "fraudeuse",
    "menteur", "menteuse", "criminel", "criminelle", "pédophile", "pedophile", "pédo", "pedo",
    "violeur", "agresseur", "agresseuse", "prédateur", "predateur", "dealer", "trafiquant",
    "drogué", "droguée", "alcoolique", "corrompu", "corrompue", "raciste", "nazi", "terroriste",
    "thief", "scammer", "fraud", "liar", "criminal", "pedophile", "rapist", "predator", "abuser",
]
ACCUSATION_RE = re.compile(
    r"(?<!\w)(?:est|c'est|etait|c'etait|sont|un vrai|une vraie|is a|is an|was a|are)\s+"
    r"(?:un |une |des |le |la |les |a |an |)?(?:vrai |vraie |gros |grosse |sale |)"
    rf"({'|'.join(re.escape(normaliser(m)) for m in ACCUSATIONS)})(?!\w)"
)

DIFFAMATION = [
    "il a volé", "elle a volé", "il a fraudé", "elle a fraudé", "il a agressé", "elle a agressé",
    "il a violé", "il bat sa femme", "elle bat ses enfants", "il trompe sa femme",
    "elle trompe son mari", "ne faites pas confiance à", "méfiez-vous de", "dénoncez-le",
    "dénoncez-la", "tout le monde doit savoir", "voici son adresse", "voici son numéro",
    "honte à", "boycottez",
]

PROPAGATION = [
    "faites tourner", "faites circuler", "partagez massivement", "partagez au maximum",
    "partagez avant que", "partage avant que", "avant que ce soit supprimé",
    "envoie à 10", "envoyez à 10", "transférez à tous vos contacts", "share before",
    "spread the word", "make this go viral",
]

MENACES = [
    "je vais te tuer", "je vais vous tuer", "je vais te retrouver", "on va te retrouver",
    "je sais où tu habites", "je sais ou tu habites", "je sais où tu restes", "tu vas le regretter",
    "tu vas souffrir", "fais attention à toi", "je vais publier tes photos",
    "je vais tout dire", "je vais te détruire", "je vais ruiner ta vie",
    "suicide-toi", "tue-toi", "va mourir", "i will kill you", "i know where you live",
    "you will regret", "kill yourself", "kys",
]


def _motif(mots):
    """Motif sur la forme normalisée + table pour réafficher le mot avec ses accents."""
    forme = {normaliser(m): m for m in reversed(mots)}
    alt = "|".join(sorted((re.escape(f) for f in forme), key=len, reverse=True))
    return re.compile(rf"(?<!\w)(?:{alt})(?!\w)"), forme


# Mots LDNOOBW pas déjà classés comme insultes
_deja = {normaliser(m) for m in INSULTES}
VULGAIRE = [m for m in _charger_ldnoobw() if normaliser(m) not in _deja]

CATEGORIES = [
    ("abus.insultes", *_motif(INSULTES)),
    *([("abus.vulgaire", *_motif(VULGAIRE))] if VULGAIRE else []),
    ("abus.menaces", *_motif(MENACES)),
    ("abus.diffamation", *_motif(DIFFAMATION)),
    ("abus.propagation", *_motif(PROPAGATION)),
]


def analyser_abus(texte: str, langue: str = DEFAUT) -> list[str]:
    t = normaliser(texte)
    alertes = []
    for raison, motif, forme in CATEGORIES:
        trouves = list(dict.fromkeys(forme[m.group(0)] for m in motif.finditer(t)))
        if trouves:
            alertes.append(avec_exemples(langue, raison, trouves))

    accusations = list(dict.fromkeys(m.group(0) for m in ACCUSATION_RE.finditer(t)))
    if accusations:
        alertes.append(avec_exemples(langue, "abus.accusation", accusations))
    return alertes
