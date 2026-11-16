"""Textes renvoyés par l'API, en français et en anglais.

Les textes des catégories de mots (urgence, insultes…) sont dans data/dictionnaire.json,
avec les mots eux-mêmes. Ici, il ne reste que les textes liés au code.

La détection, elle, ne dépend pas de la langue choisie : les mots-clés français ET anglais
sont toujours cherchés. La langue ne change que la façon dont les raisons sont affichées.
"""

LANGUES = ("fr", "en")
DEFAUT = "fr"

TEXTES = {
    "fr": {
        "camoufle": "Mots camouflés pour échapper aux filtres",
        # bouts de phrase du résumé de l'IA (« il met de la pression, … et cache la vraie adresse de son lien »)
        "resume.camoufle": "camoufle des mots pour passer les filtres",
        "resume.trompeurs": "cache des caractères trompeurs",
        "resume.emo.beaucoup": "abuse des emojis accrocheurs",
        "resume.url.google": "contient un lien signalé comme dangereux par Google",
        "resume.url.marque": "contient un lien qui imite {marque}",
        "resume.url.trompeur": "contient un lien trompeur",
        "resume.url.raccourci": "cache la vraie adresse de son lien",
        "resume.url.tld": "mène vers un site douteux",
        "resume.entete.marque": "se fait passer pour {marque}",
        # résumé de l'IA
        "ia.une_arnaque": "une arnaque",
        "ia.resume.scam": "Ce message ressemble à {quoi} : il {details}.",
        "ia.resume.scam_seul": "Ce message ressemble à {quoi} : sa formulation rappelle des arnaques que je connais.",
        "ia.resume.doute": "J'hésite sur ce message : il {details}. Vérifie auprès de l'expéditeur par un autre moyen avant d'agir.",
        "ia.resume.doute_seul": "J'hésite sur ce message : certaines tournures ressemblent à des arnaques, sans signal clair. Vérifie auprès de l'expéditeur avant d'agir.",
        "ia.resume.legitime": "Ce message semble légitime : je n'y vois aucun signal typique d'arnaque.",
        "ia.resume.legitime_signaux": "Ce message semble légitime. Il {details}, mais l'ensemble ressemble à un message normal.",
        "ia.et": "et",
        "conseil.general": "Ne clique sur aucun lien et contacte l'organisme ou la personne par un moyen que tu connais déjà (numéro officiel, application).",
        "invisibles": "Caractères invisibles cachés dans le texte",
        "alphabets": "Mot qui mélange des alphabets pour imiter des lettres latines",
        # emojis
        "emo.beaucoup": "Beaucoup d'emojis accrocheurs ({n})",
        # liens et courriels
        "url.ip": "Lien vers une adresse IP",
        "url.raccourci": "Lien raccourci qui cache la destination",
        "url.tld": "Extension de domaine suspecte ({hote})",
        "url.http": "Lien sans HTTPS",
        "url.trompeur": "Adresse de site écrite avec des lettres trompeuses ({hote})",
        "url.marque": "Imite le nom d'une organisation ({marque}) sur un domaine non officiel",
        "entete.marque": "Le nom affiché mentionne {marque} mais l'adresse vient de {domaine}",
        "ml": "Le texte ressemble à des scams connus",
        "url.google": "Lien signalé comme {menace} ({hote}). Avertissement fourni par Google Safe Browsing",
        "menace.SOCIAL_ENGINEERING": "site d'hameçonnage",
        "menace.MALWARE": "site de logiciels malveillants",
        "menace.UNWANTED_SOFTWARE": "site de logiciels indésirables",
        "menace.POTENTIALLY_HARMFUL_APPLICATION": "application potentiellement dangereuse",
        "menace.THREAT_TYPE_UNSPECIFIED": "site dangereux",
        # téléphone
        "tel.format": "Format de numéro invalide",
        "tel.liste_noire": "Numéro déjà signalé comme scam",
        "tel.invalide": "Numéro invalide",
        "tel.international": "Numéro international (+{code})",
        "tel.indicatif": "Indicatif {indicatif} souvent utilisé dans des arnaques",
        "tel.voip": "Ligne VoIP (facile à usurper)",
        "tel.surtaxe": "Numéro surtaxé",
        # erreurs API
        "err.cle": "Clé API invalide",
        "err.champs": "Champs 'type' et 'contenu' requis",
        "err.champs_label": "Champs 'type', 'contenu' et 'label' (0 ou 1) requis",
    },
    "en": {
        "camoufle": "Words disguised to get past filters",
        "resume.camoufle": "disguises words to get past filters",
        "resume.trompeurs": "hides deceptive characters",
        "resume.emo.beaucoup": "overuses attention-grabbing emojis",
        "resume.url.google": "contains a link Google flags as dangerous",
        "resume.url.marque": "contains a link imitating {marque}",
        "resume.url.trompeur": "contains a deceptive link",
        "resume.url.raccourci": "hides the real address of its link",
        "resume.url.tld": "leads to a dubious website",
        "resume.entete.marque": "pretends to be {marque}",
        "ia.une_arnaque": "a scam",
        "ia.resume.scam": "This message looks like {quoi}: it {details}.",
        "ia.resume.scam_seul": "This message looks like {quoi}: its wording reminds me of scams I know.",
        "ia.resume.doute": "I'm not sure about this message: it {details}. Check with the sender through another channel before acting.",
        "ia.resume.doute_seul": "I'm not sure about this message: some phrases look like scams, but there's no clear signal. Check with the sender before acting.",
        "ia.resume.legitime": "This message looks legitimate: I don't see any typical scam signal.",
        "ia.resume.legitime_signaux": "This message looks legitimate. It {details}, but overall it reads like a normal message.",
        "ia.et": "and",
        "conseil.general": "Don't click any link, and contact the organization or person through a channel you already know (official number, app).",
        "invisibles": "Invisible characters hidden in the text",
        "alphabets": "Word mixing alphabets to imitate Latin letters",
        "emo.beaucoup": "Lots of attention-grabbing emojis ({n})",
        "url.ip": "Link to an IP address",
        "url.raccourci": "Shortened link that hides the destination",
        "url.tld": "Suspicious domain extension ({hote})",
        "url.http": "Link without HTTPS",
        "url.trompeur": "Website address written with deceptive letters ({hote})",
        "url.marque": "Imitates an organization's name ({marque}) on an unofficial domain",
        "entete.marque": "The display name mentions {marque} but the address comes from {domaine}",
        "ml": "The text resembles known scams",
        "url.google": "Link flagged as {menace} ({hote}). Advisory provided by Google Safe Browsing",
        "menace.SOCIAL_ENGINEERING": "a phishing site",
        "menace.MALWARE": "a malware site",
        "menace.UNWANTED_SOFTWARE": "an unwanted software site",
        "menace.POTENTIALLY_HARMFUL_APPLICATION": "a potentially harmful application",
        "menace.THREAT_TYPE_UNSPECIFIED": "a dangerous site",
        "tel.format": "Invalid number format",
        "tel.liste_noire": "Number already reported as a scam",
        "tel.invalide": "Invalid number",
        "tel.international": "International number (+{code})",
        "tel.indicatif": "Area code {indicatif} often used in scams",
        "tel.voip": "VoIP line (easy to spoof)",
        "tel.surtaxe": "Premium-rate number",
        "err.cle": "Invalid API key",
        "err.champs": "Fields 'type' and 'contenu' are required",
        "err.champs_label": "Fields 'type', 'contenu' and 'label' (0 or 1) are required",
    },
}


def langue_valide(langue) -> str:
    return langue if langue in LANGUES else DEFAUT


def t(langue: str, cle: str, **params) -> str:
    return TEXTES[langue_valide(langue)][cle].format(**params)


def citer(langue: str, mots, n: int = 3) -> str:
    """« a », « b » en français ; "a", "b" en anglais."""
    gauche, droite = ("« ", " »") if langue_valide(langue) == "fr" else ('"', '"')
    return ", ".join(f"{gauche}{m}{droite}" for m in list(mots)[:n])


def separateur(langue: str) -> str:
    """Deux-points à la française (« : ») ou à l'anglaise (": ")."""
    return " : " if langue_valide(langue) == "fr" else ": "


def expliquer(langue: str, intro: str, mots, n: int = 3) -> str:
    """« Intro : « a », « b » » en français ; 'Intro: "a", "b"' en anglais."""
    return intro + separateur(langue) + citer(langue, mots, n)


def enumerer(langue: str, elements) -> str:
    """« a, b et c » en français ; "a, b and c" en anglais."""
    elements = list(elements)
    if len(elements) <= 1:
        return "".join(elements)
    return ", ".join(elements[:-1]) + f" {t(langue, 'ia.et')} " + elements[-1]


def avec_exemples(langue: str, cle: str, mots, n: int = 3) -> str:
    return expliquer(langue, t(langue, cle), mots, n)
