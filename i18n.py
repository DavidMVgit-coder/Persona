"""Textes renvoyés par l'API, en français et en anglais.

La détection, elle, ne dépend pas de la langue choisie : les mots-clés français ET anglais
sont toujours cherchés. La langue ne change que la façon dont les raisons sont affichées.
"""

LANGUES = ("fr", "en")
DEFAUT = "fr"

TEXTES = {
    "fr": {
        # catégories de mots-clés (rules.py)
        "cat.urgence": "Ton d'urgence ou de pression",
        "cat.argent": "Mention d'argent ou de paiement inhabituel",
        "cat.gain": "Promesse de gain ou de cadeau trop belle pour être vraie",
        "cat.menace": "Menace ou intimidation (police, poursuite, amende)",
        "cat.sextorsion": "Chantage typique de sextorsion (webcam piratée, vidéo intime)",
        "cat.action": "Demande de cliquer, confirmer ou mettre à jour vos informations",
        "sensible": "Demande d'informations sensibles",
        "sensible.mot": "informations sensibles",
        "camoufle": "Mots camouflés pour échapper aux filtres",
        "invisibles": "Caractères invisibles cachés dans le texte",
        "alphabets": "Mot qui mélange des alphabets pour imiter des lettres latines",
        # emojis
        "emo.alerte": "Emojis d'alerte ou d'urgence",
        "emo.argent": "Emojis d'argent ou de cadeau",
        "emo.action": "Emojis qui poussent à cliquer",
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
        # contenu offensant (abus.py)
        "abus.insultes": "Insultes ou langage injurieux",
        "abus.vulgaire": "Langage vulgaire, obscène ou haineux",
        "abus.menaces": "Menaces ou harcèlement",
        "abus.diffamation": "Propos possiblement diffamatoires (accusation grave contre une personne)",
        "abus.propagation": "Appel à faire circuler le message (rumeur, chaîne)",
        "abus.accusation": "Accusation grave présentée comme un fait",
        # erreurs API
        "err.cle": "Clé API invalide",
        "err.champs": "Champs 'type' et 'contenu' requis",
        "err.champs_label": "Champs 'type', 'contenu' et 'label' (0 ou 1) requis",
    },
    "en": {
        "cat.urgence": "Urgent or pressuring tone",
        "cat.argent": "Unusual mention of money or payment",
        "cat.gain": "Promise of a prize or gift that is too good to be true",
        "cat.menace": "Threat or intimidation (police, lawsuit, fine)",
        "cat.sextorsion": "Typical sextortion blackmail (hacked webcam, intimate video)",
        "cat.action": "Asks you to click, confirm or update your information",
        "sensible": "Asks for sensitive information",
        "sensible.mot": "sensitive information",
        "camoufle": "Words disguised to get past filters",
        "invisibles": "Invisible characters hidden in the text",
        "alphabets": "Word mixing alphabets to imitate Latin letters",
        "emo.alerte": "Alarm or urgency emojis",
        "emo.argent": "Money or gift emojis",
        "emo.action": "Emojis pushing you to click",
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
        "abus.insultes": "Insults or abusive language",
        "abus.vulgaire": "Vulgar, obscene or hateful language",
        "abus.menaces": "Threats or harassment",
        "abus.diffamation": "Possibly defamatory statements (serious accusation against a person)",
        "abus.propagation": "Asks to spread the message (rumor, chain letter)",
        "abus.accusation": "Serious accusation presented as fact",
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


def avec_exemples(langue: str, cle: str, mots, n: int = 3) -> str:
    separateur = " : " if langue_valide(langue) == "fr" else ": "
    return t(langue, cle) + separateur + citer(langue, mots, n)
