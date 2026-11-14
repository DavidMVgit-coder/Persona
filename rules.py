"""Heuristiques : signaux explicites de scam dans un texte (SMS, courriel)."""
import re
from urllib.parse import urlparse

URGENCE = [
    "urgent", "immédiatement", "immediatement", "dernier avis", "compte suspendu",
    "24 heures", "48 heures", "sans délai", "act now", "final notice", "suspended",
]
ARGENT = [
    "virement", "carte cadeau", "carte-cadeau", "bitcoin", "gagnant", "remboursement",
    "prime", "héritage", "heritage", "frais de livraison", "payez", "gift card", "winner",
]
SENSIBLE = re.compile(
    r"mot de passe|\bnip\b|code de v[ée]rification|num[ée]ro d.assurance|"
    r"carte de cr[ée]dit|password|verification code|\bssn\b",
    re.I,
)

URL_RE = re.compile(r"https?://[^\s<>\"']+", re.I)
RACCOURCIS = ("bit.ly", "tinyurl.com", "t.co", "is.gd", "cutt.ly", "rb.gy")
TLD_SUSPECTS = (".xyz", ".top", ".click", ".icu", ".buzz", ".rest", ".monster")
IP_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")

# marque (sans tirets ni espaces) -> domaines officiels
MARQUES = {
    "desjardins": ("desjardins.com",),
    "revenuquebec": ("revenuquebec.ca",),
    "postescanada": ("postescanada.ca", "canadapost-postescanada.ca"),
    "canadapost": ("canadapost.ca", "canadapost-postescanada.ca"),
    "hydroquebec": ("hydroquebec.com",),
    "paypal": ("paypal.com",),
    "amazon": ("amazon.ca", "amazon.com"),
    "interac": ("interac.ca",),
    "netflix": ("netflix.com",),
}


def _hote(url: str) -> str:
    h = (urlparse(url).hostname or "").lower()
    return h[4:] if h.startswith("www.") else h


def _domaine_officiel(hote: str, officiels) -> bool:
    return any(hote == d or hote.endswith("." + d) for d in officiels)


def analyser_urls(texte: str):
    score, raisons = 0, []
    for url in URL_RE.findall(texte):
        hote = _hote(url)
        if not hote:
            continue
        if IP_RE.match(hote):
            raisons.append("Lien vers une adresse IP"); score += 30
        if hote in RACCOURCIS:
            raisons.append("Lien raccourci qui cache la destination"); score += 25
        if hote.endswith(TLD_SUSPECTS):
            raisons.append(f"Extension de domaine suspecte ({hote})"); score += 25
        if url.lower().startswith("http://"):
            raisons.append("Lien sans HTTPS"); score += 10
        compact = hote.replace("-", "")
        for marque, officiels in MARQUES.items():
            if marque in compact and not _domaine_officiel(hote, officiels):
                raisons.append(f"Imite le nom d'une organisation ({marque}) sur un domaine non officiel")
                score += 40
                break
    return score, raisons


def analyser_en_tete(texte: str):
    """Si le courriel collé contient une ligne From:, compare le nom affiché et l'adresse."""
    m = re.search(r"^from:\s*\"?([^<\"\n]*)\"?\s*<([^>\s]+)>", texte, re.I | re.M)
    if not m:
        return 0, []
    nom = re.sub(r"[\s\-]", "", m.group(1).lower())
    domaine = m.group(2).split("@")[-1].lower()
    for marque, officiels in MARQUES.items():
        if marque in nom and not _domaine_officiel(domaine, officiels):
            return 40, [f"Le nom affiché mentionne {marque} mais l'adresse vient de {domaine}"]
    return 0, []


def analyser_regles(texte: str):
    t = texte.lower()
    raisons, score = [], 0

    if any(m in t for m in URGENCE):
        raisons.append("Ton d'urgence ou de pression"); score += 20
    if any(m in t for m in ARGENT):
        raisons.append("Mention d'argent ou de paiement inhabituel"); score += 20
    if SENSIBLE.search(texte):
        raisons.append("Demande d'informations sensibles"); score += 30

    s_url, r_url = analyser_urls(texte)
    s_hdr, r_hdr = analyser_en_tete(texte)
    score += s_url + s_hdr
    raisons += r_url + r_hdr

    # dédoublonne en gardant l'ordre
    raisons = list(dict.fromkeys(raisons))
    return min(100, score), raisons
