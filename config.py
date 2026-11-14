import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _charger_env(chemin: Path) -> None:
    """Lit un fichier .env (CLE=valeur). Les variables déjà exportées dans le terminal gagnent."""
    if not chemin.exists():
        return
    for ligne in chemin.read_text(encoding="utf-8").splitlines():
        ligne = ligne.strip()
        if not ligne or ligne.startswith("#") or "=" not in ligne:
            continue
        cle, valeur = ligne.split("=", 1)
        os.environ.setdefault(cle.strip(), valeur.strip().strip("\"'"))


_charger_env(BASE_DIR / ".env")
MODEL_PATH = BASE_DIR / "model.joblib"
DATA_PATH = BASE_DIR / "data" / "data.csv"
FEEDBACK_PATH = BASE_DIR / "data" / "feedback.csv"
BLACKLIST_PATH = BASE_DIR / "data" / "blacklist.csv"
DICTIONNAIRE_PATH = BASE_DIR / "data" / "dictionnaire.json"
LDNOOBW_DIR = BASE_DIR / "data" / "ldnoobw"

API_KEY = os.getenv("API_KEY", "")
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "5000"))

# Google Safe Browsing (optionnel) : sans clé, la vérification des liens auprès de Google est sautée
GOOGLE_SAFE_BROWSING_KEY = os.getenv("GOOGLE_SAFE_BROWSING_KEY", "")
SAFE_BROWSING_TIMEOUT = 3   # secondes : on n'attend pas plus longtemps que ça pour Google

MAX_LEN = 5000          # longueur max du contenu analysé
SEUIL_ELEVE = 70
SEUIL_MOYEN = 40
