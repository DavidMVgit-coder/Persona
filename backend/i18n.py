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


def avec_exemples(langue: str, cle: str, mots, n: int = 3) -> str:
    return expliquer(langue, t(langue, cle), mots, n)
