import sys
from pathlib import Path

# Rend les modules du projet (rules, abus, config…) importables depuis les tests
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
