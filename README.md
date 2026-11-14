# Persona

Détecteur de scams (messages, courriels, numéros de téléphone).

```
backend/    API Flask + détection (Python), données, modèle, tests
frontend/   Page web : HTML, CSS, TypeScript (src/) compilé dans static/js/
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

Flask sert aussi la page web depuis `frontend/`.

## Frontend

```
cd frontend
npm install
npm run build               # src/*.ts -> static/js/*.js (ou `npm run watch`)
```
