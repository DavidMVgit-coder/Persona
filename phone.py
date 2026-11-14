"""Analyse d'un numéro de téléphone : validité, pays, type de ligne, liste noire."""
import csv
import phonenumbers
from phonenumbers import PhoneNumberType
from config import BLACKLIST_PATH

# Indicatifs régionaux nord-américains (hors Canada/É.-U.) souvent liés aux arnaques « un coup de sonnerie »
INDICATIFS_A_RISQUE = {"809", "829", "849", "876", "284", "473", "649", "664", "767", "784", "868", "869"}


def charger_blacklist():
    if not BLACKLIST_PATH.exists():
        return set()
    with open(BLACKLIST_PATH, newline="", encoding="utf-8") as f:
        return {row[0].strip() for row in csv.reader(f) if row and not row[0].startswith("#")}


def analyser_numero(num: str):
    raisons, score = [], 0
    try:
        p = phonenumbers.parse(num, "CA")
    except phonenumbers.NumberParseException:
        return 50, ["Format de numéro invalide"]

    e164 = phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.E164)

    if e164 in charger_blacklist():
        return 100, ["Numéro déjà signalé comme scam"]

    if not phonenumbers.is_valid_number(p):
        raisons.append("Numéro invalide"); score += 40

    if p.country_code != 1:
        raisons.append(f"Numéro international (+{p.country_code})"); score += 25
    else:
        indicatif = str(p.national_number)[:3]
        if indicatif in INDICATIFS_A_RISQUE:
            raisons.append(f"Indicatif {indicatif} souvent utilisé dans des arnaques"); score += 45

    t = phonenumbers.number_type(p)
    if t == PhoneNumberType.VOIP:
        raisons.append("Ligne VoIP (facile à usurper)"); score += 20
    elif t == PhoneNumberType.PREMIUM_RATE:
        raisons.append("Numéro surtaxé"); score += 40

    return min(100, score), raisons
