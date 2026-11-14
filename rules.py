"""Heuristiques : signaux explicites de scam dans un texte (SMS, courriel)."""
import re
from urllib.parse import urlparse

from i18n import DEFAUT, TEXTES, avec_exemples, t
import safebrowsing
from normalisation import caracteres_trompeurs, normaliser, normaliser_simple

# Mots-clés par catégorie : (clé du texte affiché dans i18n.py, points, liste de mots/expressions).
# La recherche se fait sur des mots entiers ("prime" ne déclenche pas sur "imprimer").
CATEGORIES = {
    "urgence": ("cat.urgence", 20, [
        "urgent", "urgence", "immédiatement", "immediatement", "sans délai", "sans delai",
        "dernier avis", "dernière chance", "derniere chance", "avis final", "rappel final",
        "24 heures", "48 heures", "24h", "48h", "aujourd'hui seulement", "expire aujourd'hui",
        "expire bientôt", "expirera", "dès maintenant", "dans les plus brefs délais",
        "action requise", "réponse requise", "agissez maintenant", "ne tardez pas",
        "compte suspendu", "compte bloqué", "compte bloque", "compte désactivé",
        "accès restreint", "accès limité", "sera supprimé", "sera fermé", "sera désactivé",
        "act now", "final notice", "last chance", "suspended", "immediately",
        "action required", "expires today", "account locked",
    ]),
    "argent": ("cat.argent", 20, [
        "virement", "virement interac", "transfert", "carte cadeau", "carte-cadeau",
        "cartes cadeaux", "bitcoin", "crypto", "cryptomonnaie", "usdt", "western union",
        "moneygram", "remboursement", "remboursé", "trop-perçu", "crédit d'impôt",
        "prime", "héritage", "heritage", "frais de livraison", "frais de douane",
        "frais de dédouanement", "frais de traitement", "petits frais", "payez", "payer maintenant",
        "réglez", "solde impayé", "facture impayée", "paiement en attente", "paiement refusé",
        "dépôt", "investissement", "rendement garanti", "argent facile",
        "gift card", "refund", "wire transfer", "payment pending", "unpaid",
    ]),
    "gain": ("cat.gain", 25, [
        "félicitations", "felicitations", "gagnant", "gagnante", "vous avez gagné",
        "tu as gagné", "vous avez été sélectionné", "sélectionné au hasard", "tirage",
        "loterie", "concours", "prix à réclamer", "réclamez", "réclamer votre",
        "cadeau gratuit", "récompense", "offre exclusive", "100% gratuit",
        "winner", "congratulations", "you have won", "claim your", "free gift", "reward",
    ]),
    "menace": ("cat.menace", 25, [
        "arrestation", "mandat d'arrêt", "mandat d'arrestation", "police", "gendarmerie",
        "grc", "poursuite", "poursuites judiciaires", "tribunal", "huissier", "amende",
        "pénalité", "penalite", "saisie", "fraude fiscale", "dossier criminel",
        "votre numéro d'assurance sociale a été", "nas suspendu", "déportation",
        "arrest", "warrant", "lawsuit", "legal action", "penalty",
    ]),
    "sextorsion": ("cat.sextorsion", 50, [
        "j'ai piraté", "j'ai pirate", "votre webcam", "ta webcam", "vidéo compromettante",
        "vidéos compromettantes", "photos intimes", "à tous vos contacts", "à tous tes contacts",
        "i hacked", "your webcam", "compromising video", "all your contacts",
    ]),
    "action": ("cat.action", 15, [
        "cliquez ici", "clique ici", "cliquez sur le lien", "cliquez le lien",
        "confirmez votre", "confirmer votre", "vérifiez votre", "vérifier votre",
        "validez votre", "valider votre", "mettez à jour", "mettre à jour vos",
        "réactivez", "réactiver votre", "débloquer votre", "connectez-vous",
        "identifiez-vous", "suivez ce lien", "répondez à ce message",
        "click here", "verify your", "confirm your", "update your", "log in to",
    ]),
}
SENSIBLE = re.compile(
    r"mot de passe|\bnip\b|code de v[ée]rification|code de s[ée]curit[ée]|"
    r"code d.acc[èe]s|code (?:à|a) usage unique|\bcvv\b|\bcvc\b|"
    r"num[ée]ro d.assurance sociale|\bnas\b|num[ée]ro de carte|carte de cr[ée]dit|"
    r"carte de d[ée]bit|date d.expiration|identifiants?|informations? bancaires?|"
    r"coordonn[ée]es bancaires|num[ée]ro de compte|question de s[ée]curit[ée]|"
    r"password|verification code|security code|one.time code|\bssn\b|"
    r"social insurance number|bank details|card number",
    re.I,
)


def _motif(formes):
    alt = "|".join(sorted({re.escape(f) for f in formes}, key=len, reverse=True))
    return re.compile(rf"(?<!\w)(?:{alt})(?!\w)")


# Chaque mot-clé est comparé au texte normalisé (camouflage défait, sans accents).
# On garde aussi sa forme « simple » pour savoir s'il était écrit normalement ou camouflé.
MOTIFS = {}
for _cle, (_raison, _pts, _mots) in CATEGORIES.items():
    _forme = {normaliser(m): m for m in reversed(_mots)}          # forme normalisée -> mot affiché
    _simple = {normaliser(m): _motif([normaliser_simple(m)]) for m in _mots}
    MOTIFS[_cle] = (_raison, _pts, _motif(_forme), _forme, _simple)

# Emojis typiques des scams. Un seul emoji ne pèse pas lourd ; c'est l'accumulation qui compte.
EMOJIS = {
    "alerte": ("emo.alerte", 10, set("🚨⚠❗‼⁉⏰⏳⌛🔴🆘📢⛔🚫🔔")),
    "argent": ("emo.argent", 10, set("💰💵💶💷💸💲🤑🎁🏆🥇💎🪙💳🏦")),
    "action": ("emo.action", 10, set("👉👇➡⬇🔗📲🖱☝")),
}
EMOJIS_TOUS = set().union(*(e for _, _, e in EMOJIS.values()))

URL_RE = re.compile(r"https?://[^\s<>\"']+", re.I)
PONCTUATION_FIN = ".,;:!?)]}»"
RACCOURCIS = ("bit.ly", "tinyurl.com", "t.co", "is.gd", "cutt.ly", "rb.gy", "ow.ly",
              "shorturl.at", "tiny.cc", "s.id", "rebrand.ly", "goo.gl", "t.ly")
TLD_SUSPECTS = (".xyz", ".top", ".click", ".icu", ".buzz", ".rest", ".monster", ".live",
                ".shop", ".online", ".site", ".info", ".cfd", ".sbs", ".support", ".link")
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
    "rbc": ("rbc.com", "rbcroyalbank.com"),
    "bmo": ("bmo.com",),
    "scotiabank": ("scotiabank.com",),
    "tdbank": ("td.com", "tdcanadatrust.com"),
    "banquenationale": ("bnc.ca",),
    "nationalbank": ("bnc.ca",),
    "saaq": ("saaq.gouv.qc.ca",),
    "servicecanada": ("canada.ca",),
    "videotron": ("videotron.com",),
    "purolator": ("purolator.com",),
    "fedex": ("fedex.com",),
    "dhl": ("dhl.com", "dhl.ca"),
    "apple": ("apple.com",),
    "icloud": ("icloud.com", "apple.com"),
    "microsoft": ("microsoft.com", "live.com", "office.com"),
    "facebook": ("facebook.com",),
    "instagram": ("instagram.com",),
}


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

    for raison, pts, motif, forme, simple in MOTIFS.values():
        trouves = list(dict.fromkeys(m.group(0) for m in motif.finditer(texte_norm)))
        if not trouves:
            continue
        mots = [forme[f] for f in trouves]
        camoufles += [forme[f] for f in trouves if not simple[f].search(texte_simple)]
        raisons.append(avec_exemples(langue, raison, mots)); score += pts

    if SENSIBLE.search(texte_norm):
        raisons.append(t(langue, "sensible")); score += 30
        if not SENSIBLE.search(texte_simple):
            camoufles.append(t(langue, "sensible.mot"))

    if camoufles:
        raisons.append(avec_exemples(langue, "camoufle", dict.fromkeys(camoufles))); score += 25
    for r in caracteres_trompeurs(texte, langue):
        raisons.append(r); score += 25

    emojis = [c for c in texte.replace("\ufe0f", "") if c in EMOJIS_TOUS]
    for raison, pts, ensemble in EMOJIS.values():
        vus = list(dict.fromkeys(e for e in emojis if e in ensemble))
        if vus:
            sep = " : " if langue == "fr" else ": "
            raisons.append(f"{t(langue, raison)}{sep}{' '.join(vus[:5])}"); score += pts
    if len(emojis) >= 5:
        raisons.append(t(langue, "emo.beaucoup", n=len(emojis))); score += 10

    s_url, r_url = analyser_urls(texte, langue)
    s_hdr, r_hdr = analyser_en_tete(texte, langue)
    score += s_url + s_hdr
    raisons += r_url + r_hdr

    # dédoublonne en gardant l'ordre
    raisons = list(dict.fromkeys(raisons))
    return min(100, score), raisons
