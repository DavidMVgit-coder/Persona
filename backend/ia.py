"""« IA » maison du détecteur de scams.

Un classifieur (régression logistique) entraîné par train.py. Il lit chaque message de trois façons :
- les mots et paires de mots du texte décamouflé (« compte suspendu », p@y3z -> payez)
- des morceaux de 2 à 5 lettres, pour reconnaître les variantes (« paiement », « payez », « payer »)
- les signaux des règles (lien qui imite une marque, urgence, camouflage, emojis, montant…)
et apprend lui-même combien chaque indice pèse. Il en tire :
- une probabilité d'arnaque, combinée aux règles pour le score final
- un verdict (scam / doute / légitime), le type d'arnaque et un conseil adapté
- un résumé en une phrase et les mots qui ont pesé dans sa décision
- le scam connu le plus ressemblant
"""
import re
from dataclasses import dataclass

import joblib
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import FeatureUnion, Pipeline

import config
import generer_donnees
import rules
from dictionnaire import DICO
from i18n import DEFAUT, enumerer, langue_valide, t
from normalisation import motif_mots, normaliser

VERSION = 2

# Réglages choisis par validation croisée (voir train.py)
POIDS_SIGNAUX = 0.5         # importance des signaux des règles face aux mots
C = 25.0                    # peu de régularisation : l'IA colle à ses exemples (choisi par validation croisée)
MARGE_REGLES = 30           # les règles seules peuvent imposer un score de (score des règles - MARGE)
SEUIL_SIMILAIRE = 0.40      # similarité minimale pour citer un scam connu (au-dessus : même famille de scam)

# Petits mots sans intérêt à montrer comme « indice » (le modèle les utilise quand même)
MOTS_VIDES = set("""
le la les un une des de du d l a au aux et ou en est ce cet cette ces je tu il elle on nous vous ils
mon ma mes ton ta tes son sa ses notre votre nos vos leur leurs que qui quoi dans sur pour par pas ne
plus avec ici ai as avez se s y c j n m t qu ca vers peux te me moi toi lui sont etre suis fait
faire avoir peut veux dire aller voir tout tous bien tres aussi donc alors mais comme sous entre
apres avant deja encore cela ceci quand comment oui non bonjour salut
the a an and or to of in on at for is are be your you my me it this that with from by as we our
was were will can has have i its im http https www com html
not but just so if do does did been get got all any hi hey
""".split())


# Prénoms et noms : jamais montrés comme indices (« roy » n'est pas un mot suspect)
NOMS_PROPRES = {normaliser(n) for n in generer_donnees.PRENOMS + generer_donnees.NOMS}


class SignauxRegles(BaseEstimator, TransformerMixin):
    """Transforme chaque texte en vecteur des signaux des règles (voir rules.signaux_ia)."""

    def fit(self, X, y=None):
        self.fit_transform(X)
        return self

    def fit_transform(self, X, y=None):
        lignes = [rules.signaux_ia(x) for x in X]
        self.noms_ = sorted(set().union(*lignes))
        return self._matrice(lignes)

    def transform(self, X):
        return self._matrice([rules.signaux_ia(x) for x in X])

    def _matrice(self, lignes):
        return csr_matrix(np.array([[l.get(n, 0.0) for n in self.noms_] for l in lignes], dtype=float))

    def get_feature_names_out(self, input_features=None):
        return np.array(self.noms_, dtype=object)


def creer_modele(poids_signaux: float = POIDS_SIGNAUX, c: float = C) -> Pipeline:
    return Pipeline([
        ("features", FeatureUnion([
            ("mots", TfidfVectorizer(preprocessor=normaliser, ngram_range=(1, 2), sublinear_tf=True)),
            ("lettres", TfidfVectorizer(preprocessor=normaliser, analyzer="char_wb",
                                        ngram_range=(2, 5), sublinear_tf=True)),
            ("signaux", SignauxRegles()),
        ], transformer_weights={"mots": 1.0, "lettres": 1.0, "signaux": poids_signaux})),
        ("clf", LogisticRegression(max_iter=3000, class_weight="balanced", C=c)),
    ])


def score_final(probabilite: float, signaux: list) -> int:
    """Score 0-100 : l'avis de l'IA, sauf si les règles à elles seules sont très sûres d'elles."""
    score = max(100 * probabilite, rules.score_regles(signaux) - MARGE_REGLES)
    if any(s.code == "url.google" for s in signaux):
        score = max(score, 90)          # un lien que Google classe dangereux est décisif
    return int(round(min(100, score)))


def verdict(score: int) -> str:
    if score >= config.SEUIL_ELEVE:
        return "scam"
    if score >= config.SEUIL_MOYEN:
        return "doute"
    return "legitime"


@dataclass
class AvisIA:
    probabilite: float          # avis du modèle seul, 0 à 1
    score: int                  # score final 0-100 (modèle + règles)
    verdict: str                # « scam », « doute » ou « legitime »
    confiance: int              # % de certitude dans le verdict
    raisons: list               # raisons détaillées (règles + modèle)
    resume: str                 # une phrase qui explique la décision
    indices: list               # mots qui ont le plus pesé
    indices_vers_scam: bool     # True : ces mots ont poussé vers « scam » ; False : ils ont rassuré
    type: dict | None           # {"nom": …, "conseil": …} ou None
    conseil: str | None
    similaire: dict | None      # {"texte": …, "similarite": %} ou None


# Types d'arnaque du dictionnaire, prêts à chercher dans un texte normalisé
_TYPES = [(typ, motif_mots({normaliser(m) for m in typ.mots})) for typ in DICO.types]


def _type_arnaque(texte_norm: str):
    """Le type dont le plus de mots différents apparaissent ; en cas d'égalité, le premier du fichier."""
    meilleur, n_max = None, 0
    for typ, motif in _TYPES:
        n = len({m.group(0) for m in motif.finditer(texte_norm)})
        if n > n_max:
            meilleur, n_max = typ, n
    return meilleur


def _sans_article(titre: str) -> str:
    """« une arnaque au colis » -> « Arnaque au colis »."""
    titre = re.sub(r"^(une?|an?|l')\s*", "", titre, flags=re.I)
    return titre[:1].upper() + titre[1:]


@dataclass
class IA:
    modele: Pipeline
    connus: list                # vrais scams connus, pour « ressemble à… »
    matrice_connus: object      # leurs vecteurs (morceaux de lettres)
    version: int = VERSION

    @classmethod
    def entrainer(cls, textes, labels, poids=None, scams_connus=(), **reglages) -> "IA":
        modele = creer_modele(**reglages)
        modele.fit(list(textes), list(labels), clf__sample_weight=poids)
        connus = list(dict.fromkeys(scams_connus))
        matrice = cls._vec_lettres(modele).transform(connus) if connus else None
        return cls(modele, connus, matrice)

    @staticmethod
    def _vec_lettres(modele):
        return modele.named_steps["features"].transformer_list[1][1]

    def probabilite(self, texte: str) -> float:
        return float(self.modele.predict_proba([texte])[0][1])

    # ---------- explications ----------

    def _indices(self, texte: str, vers_scam: bool, n: int = 5) -> list[str]:
        """Mots du message qui ont le plus poussé vers « scam » (ou vers « légitime »)."""
        vec = self.modele.named_steps["features"].transformer_list[0][1]
        poids = self.modele.named_steps["clf"].coef_[0][: len(vec.vocabulary_)]
        x = vec.transform([texte]).tocoo()
        noms = vec.get_feature_names_out()
        signe = 1 if vers_scam else -1
        contributions = sorted(((signe * poids[j] * v, noms[j]) for j, v in zip(x.col, x.data)), reverse=True)

        # Réaffiche les mots tels qu'écrits dans le message (avec leurs accents)
        originaux = {}
        for mot in re.findall(r"\w+", texte):
            originaux.setdefault(normaliser(mot), mot.lower())

        indices = []
        for c, terme in contributions:
            if c <= 0 or len(indices) == n:
                break
            mots = terme.split()
            if any(m in MOTS_VIDES or m in NOMS_PROPRES or len(m) < 3 or m.isdigit() for m in mots):
                continue
            affiche = " ".join(originaux.get(m, m) for m in mots)
            # « votre colis » et « colis » : on ne garde pas un mot déjà compris dans un autre indice
            if not any(affiche in deja or deja in affiche for deja in indices):
                indices.append(affiche)
        return indices

    def _similaire(self, texte: str):
        if self.matrice_connus is None:
            return None
        sims = (self._vec_lettres(self.modele).transform([texte]) @ self.matrice_connus.T).toarray()[0]
        i = int(sims.argmax())
        if sims[i] < SEUIL_SIMILAIRE:
            return None
        return {"texte": self.connus[i], "similarite": int(round(100 * sims[i]))}

    @staticmethod
    def _resume(langue: str, verdict_: str, typ, signaux) -> str:
        details = []
        for s in sorted(signaux, key=lambda s: -s.points):       # les signaux les plus forts d'abord
            if s.resume and s.resume not in details:
                details.append(s.resume)
        details = enumerer(langue, details[:3])
        if verdict_ == "scam":
            quoi = typ.titre.texte(langue) if typ else t(langue, "ia.une_arnaque")
            return t(langue, "ia.resume.scam" if details else "ia.resume.scam_seul", quoi=quoi, details=details)
        if verdict_ == "doute":
            return t(langue, "ia.resume.doute" if details else "ia.resume.doute_seul", details=details)
        return t(langue, "ia.resume.legitime_signaux" if details else "ia.resume.legitime", details=details)

    # ---------- analyse complète ----------

    def analyser(self, texte: str, langue: str = DEFAUT, reseau: bool = True) -> AvisIA:
        langue = langue_valide(langue)
        signaux = rules.detecter(texte, langue, reseau=reseau)
        p = self.probabilite(texte)
        score = score_final(p, signaux)
        v = verdict(score)

        raisons = rules.raisons(signaux)
        if p >= 0.6:
            raisons.append(t(langue, "ml"))

        typ = _type_arnaque(normaliser(texte)) if v != "legitime" else None
        conseil = None
        if v != "legitime":
            conseil = typ.conseil.texte(langue) if typ else t(langue, "conseil.general")

        return AvisIA(
            probabilite=p,
            score=score,
            verdict=v,
            confiance=min(99, score if v != "legitime" else 100 - score),    # jamais sûre à 100 %
            raisons=raisons,
            resume=self._resume(langue, v, typ, signaux),
            indices=self._indices(texte, vers_scam=v != "legitime"),
            indices_vers_scam=v != "legitime",
            type={"nom": _sans_article(typ.titre.texte(langue)), "conseil": typ.conseil.texte(langue)} if typ else None,
            conseil=conseil,
            similaire=self._similaire(texte) if v != "legitime" else None,
        )


def charger(chemin=None):
    """L'IA entraînée (model.joblib), ou None si absente ou trop ancienne."""
    chemin = chemin or config.MODEL_PATH
    if not chemin.exists():
        return None
    ia = joblib.load(chemin)
    if not isinstance(ia, IA) or getattr(ia, "version", 0) != VERSION:
        print("model.joblib vient d'une ancienne version de l'IA : relance `python train.py`.")
        return None
    return ia
