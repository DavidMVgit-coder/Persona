# Persona

Détecteur de scams (messages, courriels, numéros de téléphone).

```
backend/    API Flask + détection (Python), données, modèle, tests
frontend/   Page web : HTML, CSS, TypeScript (src/)
```

## Backend

```
cd backend
pip install -r requirements.txt
cp .env.example .env        # optionnel
python train.py             # optionnel : entraîne model.joblib
python app.py               # http://127.0.0.1:5000
python -m pytest
```

Flask sert aussi la page web depuis `frontend/` : compile le TypeScript avant (voir plus bas).

## Frontend

```
cd frontend
npm install
npm run build               # src/*.ts -> static/js/*.js (ou `npm run watch`)
```

Le code du frontend s'écrit uniquement en TypeScript (`src/`). Les navigateurs n'exécutent
que du JavaScript : `static/js/` est généré par `npm run build` et n'est pas versionné.
À refaire après chaque modification de `src/` (ou laisser `npm run watch` tourner).
