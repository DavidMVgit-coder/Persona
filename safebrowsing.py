"""Vérifie des liens auprès de Google Safe Browsing (API Lookup v4).

- Optionnel : sans GOOGLE_SAFE_BROWSING_KEY, ne fait rien.
- Seuls les liens trouvés dans le message sont envoyés à Google, jamais le texte du message.
- Si Google ne répond pas (réseau, quota, clé invalide), l'analyse continue sans ce signal.
- Les réponses sont gardées en cache le temps indiqué par Google (cacheDuration).

Doc : https://developers.google.com/safe-browsing/v4/lookup-api
Conditions : usage non commercial, et l'avertissement doit indiquer qu'il vient de Google.
"""
import json
import logging
import time
import urllib.error
import urllib.request

import config

ENDPOINT = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
TYPES_MENACES = ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"]
CACHE_SAIN = 300        # secondes : durée de cache pour un lien que Google ne signale pas
MAX_URLS = 500          # limite de l'API par requête

log = logging.getLogger(__name__)
_cache: dict[str, tuple[float, str | None]] = {}   # url -> (expiration, type de menace ou None)


def actif() -> bool:
    return bool(config.GOOGLE_SAFE_BROWSING_KEY)


def _duree(cache_duration: str | None) -> float:
    # Google renvoie une durée comme "300s"
    try:
        return float((cache_duration or "").rstrip("s"))
    except ValueError:
        return CACHE_SAIN


def _interroger(urls: list[str]) -> dict[str, tuple[str, float]]:
    corps = {
        "client": {"clientId": "detecteur-scams", "clientVersion": "1.0"},
        "threatInfo": {
            "threatTypes": TYPES_MENACES,
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": u} for u in urls],
        },
    }
    requete = urllib.request.Request(
        f"{ENDPOINT}?key={config.GOOGLE_SAFE_BROWSING_KEY}",
        data=json.dumps(corps).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(requete, timeout=config.SAFE_BROWSING_TIMEOUT) as rep:
        reponse = json.load(rep)
    # Réponse vide {} = aucun lien dangereux
    return {
        m["threat"]["url"]: (m["threatType"], _duree(m.get("cacheDuration")))
        for m in reponse.get("matches", [])
    }


def verifier(urls: list[str]) -> dict[str, str]:
    """Renvoie {url: type de menace} pour les liens que Google signale comme dangereux."""
    if not actif() or not urls:
        return {}

    maintenant = time.time()
    urls = list(dict.fromkeys(urls))[:MAX_URLS]
    a_demander = [u for u in urls if _cache.get(u, (0, None))[0] <= maintenant]

    if a_demander:
        try:
            trouves = _interroger(a_demander)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError, KeyError) as e:
            # Google indisponible ou clé refusée : on continue sans ce signal
            log.warning("Safe Browsing indisponible : %s", e)
            trouves = None
        if trouves is not None:
            for u in a_demander:
                if u in trouves:
                    menace, duree = trouves[u]
                    _cache[u] = (maintenant + duree, menace)
                else:
                    _cache[u] = (maintenant + CACHE_SAIN, None)

    return {u: _cache[u][1] for u in urls if u in _cache and _cache[u][1]}
