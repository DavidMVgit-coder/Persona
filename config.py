import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "model.joblib"
DATA_PATH = BASE_DIR / "data" / "data.csv"
FEEDBACK_PATH = BASE_DIR / "data" / "feedback.csv"
BLACKLIST_PATH = BASE_DIR / "data" / "blacklist.csv"

API_KEY = os.getenv("API_KEY", "")
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "5000"))

MAX_LEN = 5000          # longueur max du contenu analysé
SEUIL_ELEVE = 70
SEUIL_MOYEN = 40
