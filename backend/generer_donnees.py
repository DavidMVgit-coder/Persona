"""Fabrique des exemples d'entraînement réalistes (scams et messages légitimes), en français et en anglais.

Pourquoi : nos vrais exemples (data/data.csv) sont trop peu nombreux. Le générateur combine des
modèles de messages avec des marques, montants, liens, délais… tirés au hasard. Il fabrique surtout
des « pièges » légitimes (vraie notification de Postes Canada, vrai code de vérification, un proche
qui demande 20 $ pour le cinéma) pour que l'IA apprenne la différence, et pas juste « marque = scam ».

Usage : python generer_donnees.py      (affiche des exemples au hasard)
"""
import random
import re

GRAINE = 42

# ---------- ingrédients ----------

LIVREURS = ["Postes Canada", "Purolator", "FedEx", "DHL", "UPS", "Intelcom", "Canada Post"]
LIVREURS_EN = ["Canada Post", "FedEx", "DHL", "UPS", "USPS", "Purolator"]
BANQUES = ["Desjardins", "RBC", "TD", "BMO", "Banque Nationale", "Scotia", "Tangerine"]
BANQUES_EN = ["RBC", "TD", "BMO", "Scotiabank", "CIBC", "Tangerine"]
GOUV = ["ARC", "Agence du revenu du Canada", "Revenu Québec", "Service Canada", "SAAQ", "RAMQ"]
GOUV_EN = ["CRA", "Canada Revenue Agency", "Service Canada", "IRS"]
SERVICES = ["Netflix", "Spotify", "Disney+", "Amazon", "Apple", "PayPal", "Vidéotron", "Bell", "Fizz",
            "Hydro-Québec", "Rogers", "Telus", "Koodo"]
BOUTIQUES = ["Amazon", "Walmart", "Best Buy", "Simons", "IKEA", "Canadian Tire", "SAQ", "Costco"]
COMMERCES = ["Metro", "IGA", "Provigo", "Couche-Tard", "Jean Coutu", "Pharmaprix", "Tim Hortons", "Esso"]
PRENOMS = ["Julie", "Marc", "Sophie", "Alex", "Camille", "Mathieu", "Léa", "Olivier", "Emma", "Samuel",
           "Chloé", "Gabriel", "Sarah", "William", "Noémie"]
NOMS = ["Tremblay", "Gagnon", "Roy", "Côté", "Bouchard", "Gauthier", "Morin", "Lavoie", "Fortin", "Pelletier"]
PROCHES = ["maman", "papa", "grand-maman", "grand-papa", "ma tante", "mon oncle", "mamie"]
PROCHES_EN = ["mom", "dad", "grandma", "grandpa", "auntie"]
VILLES = ["Montréal", "Laval", "Québec", "Longueuil", "Sherbrooke", "Gatineau", "Trois-Rivières"]
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche", "demain", "ce soir"]
JOURS_EN = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "tomorrow", "tonight"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "septembre", "octobre", "novembre", "décembre"]
MOIS_EN = ["January", "February", "March", "April", "May", "June", "September", "October", "November", "December"]
MESSAGERIES = ["WhatsApp", "Telegram", "WeChat"]
CRYPTOS = ["bitcoin", "crypto", "USDT", "Ethereum"]

OFFICIELS = {
    "Postes Canada": "https://www.postescanada.ca/suivi", "Canada Post": "https://www.canadapost-postescanada.ca/track",
    "Purolator": "https://www.purolator.com/fr/suivi", "FedEx": "https://www.fedex.com/fr-ca/tracking.html",
    "Amazon": "https://www.amazon.ca/gp/your-account/order-history", "Desjardins": "https://www.desjardins.com",
    "RBC": "https://www.rbcroyalbank.com", "Netflix": "https://www.netflix.com/youraccount",
    "Hydro-Québec": "https://www.hydroquebec.com/espace-client", "Vidéotron": "https://videotron.com/espace-client",
}
EXTENSIONS_DOUTEUSES = [".xyz", ".top", ".info", ".live", ".click", ".online", ".site", ".shop", ".icu", ".com", ".net"]
MOTS_DOMAINE = ["suivi", "securite", "verification", "paiement", "livraison", "compte", "support", "login",
                "secure", "verify", "track", "client", "acces", "service", "remboursement", "renouvellement"]
RACCOURCISSEURS = ["bit.ly", "tinyurl.com", "cutt.ly", "rb.gy", "t.ly", "shorturl.at"]


def _slug(nom: str) -> str:
    nom = nom.lower().replace("é", "e").replace("è", "e").replace("ô", "o").replace("+", "plus")
    return re.sub(r"[^a-z0-9]+", "-", nom).strip("-")


class Generateur:
    def __init__(self, graine: int = GRAINE):
        self.r = random.Random(graine)

    def c(self, liste):
        return self.r.choice(liste)

    # --- petits morceaux aléatoires ---

    def montant(self, petit=False, en=False):
        v = self.r.choice([1.75, 1.99, 2.49, 2.99, 3.50, 4.95]) if petit else self.r.choice(
            [48, 64.2, 86.2, 120, 187.43, 249.99, 350, 412.5, 532.18, 850, 1200, 1500, 2000])
        if en:
            return f"${v:,.2f}" if v % 1 else f"${int(v):,}"
        texte = f"{v:,.2f}".replace(",", " ").replace(".", ",") if v % 1 else f"{int(v):,}".replace(",", " ")
        return f"{texte} $"

    def tel(self):
        return f"1-8{self.r.choice('0345678')}{self.r.choice('0345678')}-555-0{self.r.randint(100, 199)}"

    def code(self):
        return str(self.r.randint(100000, 999999))

    def suivi(self):
        return " ".join(str(self.r.randint(1000, 9999)) for _ in range(3))

    def heure(self):
        return f"{self.r.randint(8, 20)} h" + self.c(["", " 30", " 15"])

    def heure_en(self):
        return f"{self.r.randint(1, 11)}:{self.c(['00', '30', '15'])} {self.c(['AM', 'PM'])}"

    def date(self):
        return f"{self.r.randint(1, 28)} {self.c(MOIS)}"

    def delai(self, en=False):
        if en:
            return self.c(["", " within 24 hours", " today", " immediately", " before midnight", " within 48h"])
        return self.c(["", " dans les 24 heures", " aujourd'hui", " immédiatement", " avant minuit", " d'ici 48 h",
                       " sous 24h"])

    def lien_scam(self, marque=None):
        """Faux lien : marque collée à un mot rassurant sur un domaine douteux, ou lien raccourci."""
        if self.r.random() < 0.25:
            return f"https://{self.c(RACCOURCISSEURS)}/{self.r.choice(['x', 'p', 'c'])}{self.r.randint(10, 99)}" \
                   f"{self.c(['abc', 'Kq', 'zT', 'verif', 'colis'])}"
        base = _slug(marque) if marque and self.r.random() < 0.8 else self.c(["mon", "ca", "canada", "client", "info"])
        domaine = f"{base}-{self.c(MOTS_DOMAINE)}{self.c(EXTENSIONS_DOUTEUSES)}"
        chemin = self.c(["", "/", "/login", "/paiement", "/verification", "/suivi", "/maj", "/ca"])
        schema = self.c(["https://", "http://", "https://", ""])       # parfois écrit sans http://
        return f"{schema}{domaine}{chemin}"

    def lien_officiel(self, marque):
        return OFFICIELS.get(marque, f"https://www.{_slug(marque)}.ca")

    # --- variations appliquées après coup ---

    def camoufler(self, texte):
        remplacements = {"payez": "p@yez", "compte": "c0mpte", "colis": "c0lis", "virement": "vir3ment",
                         "urgent": "urg3nt", "mot de passe": "m0t de p@sse", "gagné": "g@gné", "frais": "fr@is",
                         "account": "acc0unt", "password": "p@ssword", "verify": "ver1fy", "bitcoin": "b1tcoin"}
        for mot, camoufle in self.r.sample(list(remplacements.items()), len(remplacements)):
            if mot in texte.lower():
                return re.sub(re.escape(mot), camoufle, texte, count=1, flags=re.I)
        return texte

    def sans_lien(self, texte):
        """Remplace le lien final par un appel à l'action sans lien (« Appelez le… », « Répondez OUI »)."""
        m = re.search(r"\s*:?\s*(?:https?:)?(?://)?[\w.-]+\.[a-z]{2,}(?:/\S*)?\s*\S?$", texte)
        if not m or "." not in m.group(0):
            return texte
        anglais = re.search(r"\b(your|you|the|has|have|is|now)\b", texte, re.I)
        fin = self.c([f". Call {self.tel()}.", ". Reply YES to continue.", " using the link below.", "."] if anglais
                     else [f". Appelez le {self.tel()}.", ". Répondez OUI pour continuer.",
                           " en cliquant sur le lien ci-dessous.", ".", " par texto en répondant à ce message."])
        return texte[: m.start()] + fin

    def decorer_scam(self, texte):
        if self.r.random() < 0.35:
            texte = self.sans_lien(texte)
        x = self.r.random()
        if x < 0.12:
            texte = self.camoufler(texte)
        elif x < 0.22:
            texte = f"{self.c(['🚨', '⚠️', '❗', '🎁', '💰', '📦'])} {texte} {self.c(['👉', '⏰', '', '🔒'])}".strip()
        elif x < 0.28:
            texte = re.sub(r"^[^:]+", lambda m: m.group(0).upper(), texte, count=1)
        return texte

    def decorer_legit(self, texte):
        marques = [m for m in OFFICIELS if m in texte]
        if marques and "http" not in texte and self.r.random() < 0.35:
            texte = f"{texte.rstrip('.')} : {self.lien_officiel(marques[0])}"
        if self.r.random() < 0.12:
            texte = f"{texte} {self.c(['😊', '😂', '❤️', '👍', '🎉', '🙏', '😅'])}"
        return texte

    # ---------- scams ----------

    def scam(self):
        modele = self.c(SCAMS)
        return self.decorer_scam(modele(self)), 1

    # ---------- légitimes ----------

    def legit(self):
        modele = self.c(LEGITS)
        return self.decorer_legit(modele(self)), 0


# Chaque modèle est une fonction g -> texte (g = Generateur). Regroupés par type d'arnaque.
SCAMS = [
    # colis
    lambda g: (lambda l: f"{l} : votre colis est en attente de livraison. Des frais de {g.montant(True)} sont requis{g.delai()}. "
                         f"{g.c(['Payez ici', 'Réglez-les ici', 'Paiement'])} : {g.lien_scam(l)}")(g.c(LIVREURS)),
    lambda g: (lambda l: f"{l} : nous n'avons pas pu livrer votre colis {g.suivi()}. Confirmez votre adresse{g.delai()} : "
                         f"{g.lien_scam(l)}")(g.c(LIVREURS)),
    lambda g: f"Votre colis est retenu à la douane. Réglez les frais de dédouanement de {g.montant(True)} ici : {g.lien_scam()}",
    lambda g: (lambda l: f"{l} : votre envoi sera retourné à l'expéditeur. Reprogrammez la livraison{g.delai()} : "
                         f"{g.lien_scam(l)}")(g.c(LIVREURS)),
    lambda g: f"Dernière tentative de livraison pour votre colis. Mettez à jour vos informations : {g.lien_scam()}",
    lambda g: (lambda l: f"{l}: your package is on hold. A {g.montant(True, True)} fee is required{g.delai(True)}. "
                         f"Pay here: {g.lien_scam(l)}")(g.c(LIVREURS_EN)),
    lambda g: (lambda l: f"{l}: we were unable to deliver your parcel. Update your address{g.delai(True)}: "
                         f"{g.lien_scam(l)}")(g.c(LIVREURS_EN)),
    # banque
    lambda g: (lambda b: f"{b} : activité inhabituelle détectée sur votre compte. {g.c(['Confirmez', 'Vérifiez', 'Validez'])} "
                         f"votre {g.c(['mot de passe', 'NIP', 'identité', 'code de vérification'])}{g.delai()} : {g.lien_scam(b)}")(g.c(BANQUES)),
    lambda g: (lambda b: f"{b} : votre accès en ligne a été {g.c(['bloqué', 'suspendu', 'désactivé'])}. Pour le réactiver, "
                         f"connectez-vous ici : {g.lien_scam(b)}")(g.c(BANQUES)),
    lambda g: (lambda b: f"Alerte {b} : un virement de {g.montant()} est en attente. Si ce n'est pas vous, annulez-le ici : "
                         f"{g.lien_scam(b)}")(g.c(BANQUES)),
    lambda g: f"Interac : vous avez reçu un virement de {g.montant()}. Pour accepter le dépôt, sélectionnez votre institution : "
              f"{g.lien_scam('interac')}",
    lambda g: f"{g.c(BANQUES)} : votre carte a été {g.c(['bloquée', 'suspendue'])} par mesure de sécurité. Appelez immédiatement le {g.tel()}",
    lambda g: (lambda b: f"{b}: unusual activity detected on your account. Verify your {g.c(['password', 'identity', 'PIN'])} "
                         f"now: {g.lien_scam(b)}")(g.c(BANQUES_EN)),
    lambda g: f"Interac e-Transfer: you received {g.montant(en=True)}. Click to deposit: {g.lien_scam('interac')}",
    # faux proche
    lambda g: f"Salut {g.c(PROCHES)}, c'est moi. {g.c(['J’ai changé de numéro', 'Mon téléphone est brisé, je t’écris d’un nouveau numéro', 'J’ai perdu mon cell', 'Mon cell est tombé dans l’eau, c’est mon nouveau numéro'])}. "
              f"{g.c(['Peux-tu me faire un virement Interac de {m} ? C’est urgent', 'J’ai une facture à payer aujourd’hui, peux-tu m’envoyer {m} ?', 'Peux-tu m’aider ? J’ai besoin de {m} pour ce soir, je te rembourse demain', 'Envoie-moi {m} par Interac s’il te plaît, je t’explique plus tard'])}".format(m=g.montant()),
    lambda g: f"{g.c(PROCHES).capitalize()}, c'est {g.c(['ton petit-fils', 'ta petite-fille', 'ton fils', 'ta fille'])}. "
              f"{g.c(['J’ai eu un accident', 'Je suis au poste de police', 'Je suis à l’hôpital', 'J’ai des problèmes avec la police'])}. "
              f"J'ai besoin de {g.montant()} rapidement, {g.c(['n’en parle pas à papa', 'ne le dis à personne', 'garde ça entre nous', 'ne dis rien à maman'])}.",
    lambda g: f"Hi {g.c(PROCHES_EN)}, it's me. {g.c(['This is my new number', 'My phone broke, this is my new number', 'I lost my phone'])}. "
              f"{g.c(['Can you send me {m}? It’s urgent', 'Can you help me with {m} today? I’ll pay you back tomorrow'])}".format(m=g.montant(en=True)),
    lambda g: f"{g.c(['Grandma', 'Grandpa'])}, it's your {g.c(['grandson', 'granddaughter'])}. I was in an accident and I need "
              f"{g.montant(en=True)} for bail. Please don't tell {g.c(['mom', 'dad'])}.",
    # gouvernement
    lambda g: f"{g.c(GOUV)} : vous avez droit à un remboursement de {g.montant()}. Réclamez-le{g.delai()} : {g.lien_scam(g.c(GOUV))}",
    lambda g: f"{g.c(GOUV)} : un mandat d'arrestation a été émis à votre nom pour fraude fiscale. Appelez le {g.tel()} immédiatement.",
    lambda g: f"{g.c(GOUV)} : votre numéro d'assurance sociale a été suspendu. Contactez-nous au {g.tel()} pour éviter des poursuites.",
    lambda g: f"SAAQ : vous avez une contravention impayée de {g.montant()}. Payez{g.delai()} pour éviter la suspension de votre "
              f"permis : {g.lien_scam('saaq')}",
    lambda g: f"{g.c(GOUV)} : vous avez un solde impayé de {g.montant()}. Payez en cartes-cadeaux pour éviter l'arrestation.",
    lambda g: f"{g.c(GOUV_EN)}: you are eligible for a tax refund of {g.montant(en=True)}. Claim it{g.delai(True)}: {g.lien_scam('cra')}",
    lambda g: f"{g.c(GOUV_EN)} final notice: a warrant has been issued for your arrest. Call {g.tel()} immediately to settle your debt.",
    # prix
    lambda g: f"{g.c(['Félicitations !', 'Bravo !', 'FÉLICITATIONS !'])} Vous avez été sélectionné pour gagner "
              f"{g.c(['un iPhone 16', 'une PlayStation 5', 'une carte-cadeau de 500 $', 'un voyage dans le Sud'])}. "
              f"Réclamez votre prix{g.delai()} : {g.lien_scam()}",
    lambda g: f"Votre numéro a été tiré au sort ! Il ne reste que {g.montant(True)} de frais de livraison à payer pour recevoir "
              f"votre cadeau : {g.lien_scam()}",
    lambda g: f"Congratulations! You have won {g.c(['a $1000 gift card', 'an iPhone 16', 'a free cruise'])}. Claim your reward"
              f"{g.delai(True)}: {g.lien_scam()}",
    # investissement
    lambda g: f"Investissez {g.montant()} en {g.c(CRYPTOS)} et recevez {g.montant()} en {g.c(['une semaine', '7 jours', '48 heures'])}. "
              f"Rendement garanti !",
    lambda g: f"J'ai fait {g.montant()} cette semaine avec une plateforme de {g.c(['trading', 'crypto'])}. Écris-moi sur "
              f"{g.c(MESSAGERIES)} pour que je te montre.",
    lambda g: f"Opportunité unique : doublez votre argent en {g.c(['7 jours', 'un mois'])} grâce à notre robot de trading. "
              f"Places limitées : {g.lien_scam()}",
    lambda g: f"I made {g.montant(en=True)} this week trading crypto. Message me on {g.c(MESSAGERIES)} and I'll show you how.",
    lambda g: f"{g.c(['Crypto opportunity', 'Investment alert', 'Limited offer'])}: {g.c(['double your money', 'triple your savings'])} "
              f"in {g.c(['7 days', '48 hours', 'one month'])}, guaranteed returns. {g.c(['Send USDT to this wallet', 'Deposit now', 'Join our VIP group'])}.",
    lambda g: f"Invest {g.montant(en=True)} in {g.c(CRYPTOS)} today and get {g.montant(en=True)} back next week. 100% guaranteed profit!",
    # emploi
    lambda g: f"Offre d'emploi : gagnez {g.c(['300 $', '500 $', '800 $'])} par jour depuis la maison, aucune expérience requise. "
              f"Contactez-nous sur {g.c(MESSAGERIES)}.",
    lambda g: f"Bonjour, nous avons consulté votre CV. Poste à temps partiel : {g.c(['250 $', '400 $'])} par jour, "
              f"{g.c(['1 h', '2 h'])} de travail. Écrivez-nous sur {g.c(MESSAGERIES)}.",
    lambda g: f"Hiring now: earn {g.c(['$300', '$500'])} per day working from home, no experience needed. Text us on {g.c(MESSAGERIES)}.",
    # support technique
    lambda g: f"Alerte {g.c(['Microsoft', 'Windows', 'Apple'])} : votre ordinateur est infecté par {g.r.randint(2, 7)} virus. "
              f"Appelez le soutien technique au {g.tel()} immédiatement.",
    lambda g: f"{g.c(['Microsoft', 'Apple'])} Security Alert: {g.r.randint(2, 7)} viruses detected on your computer. Call support at {g.tel()} now.",
    # abonnement
    lambda g: (lambda s: f"{s} : votre paiement a été refusé. Mettez à jour vos informations de paiement{g.delai()} : "
                         f"{g.lien_scam(s)}")(g.c(SERVICES)),
    lambda g: (lambda s: f"{s} : votre {g.c(['abonnement', 'compte', 'forfait'])} est suspendu. Réactivez-le ici : {g.lien_scam(s)}")(g.c(SERVICES)),
    lambda g: (lambda s: f"{s} : votre compte sera fermé{g.delai()}. Confirmez votre identité : {g.lien_scam(s)}")(g.c(SERVICES)),
    lambda g: (lambda s: f"{s}: your payment was declined. Update your billing details{g.delai(True)}: {g.lien_scam(s)}")(g.c(SERVICES)),
    # sextorsion
    lambda g: f"J'ai piraté votre {g.c(['ordinateur', 'téléphone', 'webcam'])}. J'ai des vidéos de vous. Envoyez {g.montant()} en "
              f"bitcoin{g.delai()} sinon je les envoie à tous vos contacts.",
    lambda g: f"I hacked your {g.c(['computer', 'phone', 'webcam'])}. Send {g.montant(en=True)} in bitcoin{g.delai(True)} or I will "
              f"send the video to all your contacts.",
    # romance / mauvais numéro
    lambda g: f"Bonsoir, j'ai vu ton profil et je te trouve {g.c(['magnifique', 'très charmant', 'super belle'])} 😘 "
              f"Écris-moi sur {g.c(MESSAGERIES)}",
    lambda g: f"Salut, désolée je pense que je me suis trompée de numéro... mais tu as l'air gentil, on peut jaser sur "
              f"{g.c(MESSAGERIES)} ?",
    lambda g: f"Hi, sorry wrong number... but you seem nice. Can we chat on {g.c(MESSAGERIES)}?",
    # héritage / avance de frais
    lambda g: f"Bonjour, je suis {g.c(['Maître', 'Dr', 'M.'])} {g.c(NOMS)}. Un héritage de {g.c(['2,5 millions', '850 000 $'])} "
              f"vous revient. Envoyez vos informations personnelles pour le recevoir.",
    lambda g: f"I am {g.c(['Mr.', 'Barrister', 'Dr.'])} {g.c(NOMS)} from the {g.c(['UN compensation fund', 'World Bank'])}. "
              f"You have been awarded {g.c(['$1.5 million', '$850,000'])}. Send your full name and bank details.",
    # rappel : « appelez ce numéro » (aucun lien)
    lambda g: f"{g.c(['Amazon', 'PayPal', 'Apple', 'Best Buy', 'Walmart'])} : commande {g.c(['suspecte', 'inhabituelle', 'de'])} "
              f"de {g.montant()} sur votre compte. Si ce n'est pas vous, appelez le {g.tel()} pour l'annuler.",
    lambda g: f"{g.c(['Amazon', 'PayPal', 'Apple'])}: a purchase of {g.montant(en=True)} was made on your account. "
              f"If you did not authorize it, call {g.tel()} immediately.",
    lambda g: f"{g.c(BANQUES)} : une transaction de {g.montant()} a été refusée. Pour la débloquer, rappelez notre service "
              f"de fraude au {g.tel()} et donnez votre NIP à l'agent.",
    # avance de frais : « aidez-moi à transférer des fonds »
    lambda g: f"Bonjour, je suis {g.c(['un prince', 'un diplomate', 'un ingénieur', 'une veuve', 'un banquier'])} "
              f"{g.c(['en exil', 'en mission à l’étranger', 'malade', 'à la retraite'])}. J'ai besoin d'un partenaire de confiance pour "
              f"{g.c(['transférer des fonds', 'sortir {s} du pays', 'recevoir {s}'])}. Vous recevrez {g.c(['10', '15', '30'])} % "
              f"de la somme.".format(s=g.c(["4,5 millions", "un héritage", "2 millions de dollars"])),
    lambda g: f"Dear friend, I am {g.c(['a widow', 'a bank manager', 'a diplomat'])} and I need your help to transfer "
              f"{g.c(['$4.5 million', 'my late husband’s funds'])} out of the country. You will receive {g.c(['20', '30'])}% for your help.",
    # prix sans lien
    lambda g: f"{g.c(['Félicitations', 'Bravo'])}, vous êtes l'heureux gagnant de {g.c(['notre tirage', 'notre concours'])} ! "
              f"Pour recevoir {g.c(['votre prix', 'vos 1 000 $', 'votre voiture'])}, payez les frais de {g.montant(True)} par "
              f"{g.c(['carte de crédit', 'virement Interac', 'carte-cadeau'])}.",
    # message vocal / divers
    lambda g: f"Vous avez un message vocal en attente. Écoutez-le ici : {g.lien_scam()}",
    lambda g: f"URGENT !!! Votre compte bancaire sera FERMÉ aujourd'hui. Appelez immédiatement le {g.tel()}",
]

LEGITS = [
    # colis
    lambda g: f"{g.c(LIVREURS)} : votre colis {g.suivi()} a été livré{g.c(['', ' dans votre boîte aux lettres', ' à votre porte', ' au point de retrait'])}.",
    lambda g: (lambda l: f"{l} : votre colis arrivera {g.c(JOURS)} entre {g.heure()} et {g.heure()}. Suivez-le sur "
                         f"{g.lien_officiel(l)}")(g.c(["Postes Canada", "Purolator", "FedEx"])),
    lambda g: f"Ton colis {g.c(BOUTIQUES)} a été livré à ta porte. Bonne journée !",
    lambda g: f"Votre colis a été livré {g.c(['aujourd’hui', 'ce matin'])} à {g.heure()}. Aucune action n'est requise de votre part.",
    lambda g: f"Votre commande {g.c(BOUTIQUES)} a été expédiée. Numéro de suivi : {g.suivi()}.",
    lambda g: f"{g.c(LIVREURS_EN)}: your package {g.suivi()} was delivered{g.c(['', ' to your mailbox', ' at your front door'])}.",
    lambda g: f"Your {g.c(BOUTIQUES)} order has shipped and will arrive {g.c(JOURS_EN)}. Track it in the app.",
    # banque
    lambda g: f"{g.c(BANQUES)} : votre relevé de {g.c(MOIS)} est disponible dans votre espace client.",
    lambda g: f"{g.c(BANQUES)} : un virement Interac de {g.montant()} de {g.c(PRENOMS)} {g.c(NOMS)} a été déposé automatiquement "
              f"dans votre compte.",
    lambda g: f"Ton code de vérification {g.c(BANQUES)} est {g.code()}. Ne le communique à personne, même pas à un employé.",
    lambda g: f"Votre code de sécurité est {g.code()}. Il expire dans 10 minutes. Ne le partagez avec personne.",
    lambda g: f"Alerte {g.c(BANQUES)} : achat de {g.montant()} chez {g.c(COMMERCES)} le {g.date()}. Si vous ne reconnaissez pas "
              f"cette transaction, appelez le numéro au dos de votre carte.",
    lambda g: f"{g.c(BANQUES)} : votre paiement de {g.montant()} à {g.c(['Hydro-Québec', 'Vidéotron', 'Bell'])} a été effectué.",
    lambda g: f"Rappel {g.c(BANQUES)} : le paiement minimum de votre carte de crédit est dû le {g.date()}.",
    lambda g: f"Your {g.c(BANQUES_EN)} statement for {g.c(MOIS_EN)} is ready in online banking.",
    lambda g: f"Your verification code is {g.code()}. Don't share it with anyone.",
    lambda g: f"{g.c(BANQUES_EN)} alert: a purchase of {g.montant(en=True)} was made on your card at {g.c(COMMERCES)}. If this "
              f"wasn't you, call the number on the back of your card.",
    # proches (dont des demandes d'argent normales et de vrais changements de numéro)
    lambda g: f"Salut {g.c(PROCHES)}, je vais arriver vers {g.heure()} avec les enfants.",
    lambda g: f"{g.c(PROCHES).capitalize()}, peux-tu venir me chercher après {g.c(['l’école', 'le hockey', 'le travail', 'la pratique'])} ?",
    lambda g: f"{g.c(PROCHES).capitalize()}, peux-tu me prêter {g.c(['10 $', '20 $', '30 $'])} pour {g.c(['le cinéma', 'la pizza', 'mon lunch'])} ? "
              f"Je te rembourse {g.c(JOURS)}.",
    lambda g: f"Merci {g.c(PROCHES)} pour le cadeau, je t'aime !",
    lambda g: f"J'ai changé de numéro, voici le nouveau. Enregistre-le ! — {g.c(PRENOMS)}",
    lambda g: f"{g.c(PROCHES).capitalize()}, j'ai oublié mes clés, es-tu à la maison ?",
    lambda g: f"{g.c(PROCHES).capitalize()}, je t'ai fait le virement pour {g.c(['l’épicerie', 'le souper', 'les billets'])}, "
              f"{g.c(['25 $', '40 $', '60 $'])}.",
    lambda g: f"Hi {g.c(PROCHES_EN)}, I'll be home around {g.heure_en()}.",
    lambda g: f"{g.c(PROCHES_EN).capitalize()}, can you lend me {g.c(['$10', '$20'])} for {g.c(['the movies', 'lunch'])}? "
              f"I'll pay you back {g.c(JOURS_EN)}.",
    lambda g: f"New number, save it! - {g.c(PRENOMS)}",
    # gouvernement
    lambda g: f"{g.c(['Revenu Québec', 'ARC'])} : votre avis de cotisation est disponible dans {g.c(['Mon dossier', 'Mon dossier ARC'])}.",
    lambda g: f"SAAQ : votre rendez-vous est confirmé le {g.date()} à {g.heure()} au centre de {g.c(VILLES)}.",
    lambda g: f"Service Canada : votre passeport est prêt. Vous pouvez le récupérer au bureau de {g.c(VILLES)}.",
    lambda g: f"{g.c(['Revenu Québec', 'ARC'])} : votre remboursement de {g.montant()} a été déposé dans votre compte.",
    lambda g: f"Votre remboursement de {g.montant()} chez {g.c(BOUTIQUES)} a été traité. Il apparaîtra sur votre relevé d'ici "
              f"{g.c(['3 à 5', '5 à 10'])} jours ouvrables.",
    lambda g: f"Your refund of {g.montant(en=True)} from {g.c(BOUTIQUES)} has been processed. It will appear on your statement "
              f"in 3-5 business days.",
    lambda g: f"{g.c(BOUTIQUES)} : votre commande de {g.montant()} est confirmée. Merci pour votre achat !",
    lambda g: f"CRA: your notice of assessment is now available in My Account.",
    # « gagné », « félicitations » dans la vraie vie
    lambda g: f"Félicitations pour {g.c(['ta promotion', 'ton diplôme', 'le bébé', 'ton nouvel emploi'])} ! On fête ça {g.c(JOURS)} ?",
    lambda g: f"Bravo, tu as gagné {g.c(['le tournoi', 'ta partie', 'le concours de dessin'])} ! Je suis fière de toi",
    lambda g: f"Tu as gagné ton pari, je te dois {g.c(['une pizza', 'une bière', 'un café'])} 😂",
    lambda g: f"Congrats on {g.c(['the new job', 'your graduation', 'the baby'])}! Let's celebrate {g.c(JOURS_EN)}.",
    # argent / placements normaux
    lambda g: "As-tu vu le prix du bitcoin aujourd'hui ? Ça descend encore.",
    lambda g: f"Votre rencontre avec votre conseiller {g.c(BANQUES)} pour le REER est confirmée le {g.date()} à {g.heure()}.",
    # emploi
    lambda g: f"Merci pour votre candidature au poste de {g.c(['caissier', 'commis', 'analyste', 'technicienne'])}. "
              f"Nous vous contacterons pour une entrevue.",
    lambda g: f"Ton quart de travail de {g.c(JOURS)} est confirmé de {g.heure()} à {g.heure()}.",
    lambda g: f"Urgent : on a besoin de quelqu'un pour remplacer {g.c(PRENOMS)} {g.c(JOURS)}, es-tu disponible ?",
    lambda g: f"Thanks for applying to the {g.c(['cashier', 'analyst', 'developer'])} position. We'll be in touch.",
    # abonnements et factures
    lambda g: f"{g.c(SERVICES)} : votre paiement de {g.montant()} a été traité avec succès. Merci !",
    lambda g: f"{g.c(SERVICES)} : votre abonnement sera renouvelé le {g.date()}.",
    lambda g: f"Votre facture {g.c(['Hydro-Québec', 'Vidéotron', 'Bell'])} de {g.montant()} est disponible dans votre espace client.",
    lambda g: f"{g.c(SERVICES)}: your payment of {g.montant(en=True)} was successful. Thanks for being a member.",
    lambda g: f"Votre ordinateur est prêt à être récupéré chez {g.c(['Best Buy', 'Bureau en Gros', 'Microplus'])}.",
    # des noms de famille aussi dans les vrais messages (sinon l'IA apprend « Roy » = arnaque)
    lambda g: f"Rappel : votre rendez-vous avec {g.c(['Dre', 'Dr', 'Me'])} {g.c(NOMS)} est {g.c(JOURS)} à {g.heure()}.",
    lambda g: f"Bonjour, ici {g.c(PRENOMS)} {g.c(NOMS)} de l'école. La sortie de {g.c(JOURS)} est confirmée.",
    lambda g: f"{g.c(PRENOMS)} {g.c(NOMS)} vous a envoyé une demande de paiement de {g.montant()} pour {g.c(['le souper', 'les billets', 'le cadeau de groupe'])}.",
    lambda g: f"Merci {g.c(PRENOMS)}! Mme {g.c(NOMS)} a bien reçu ton travail.",
    # quotidien
    lambda g: f"Salut, on se voit {g.c(JOURS)} au {g.c(['café', 'resto', 'gym', 'parc'])} ?",
    lambda g: f"La réunion de {g.c(JOURS)} est déplacée à {g.heure()}.",
    lambda g: f"Rappel : votre rendez-vous chez {g.c(['le dentiste', 'le médecin', 'l’optométriste', 'le vétérinaire'])} est "
              f"{g.c(JOURS)} à {g.heure()}. Pour annuler, appelez le 450-555-0{g.r.randint(100, 199)}.",
    lambda g: f"Peux-tu acheter {g.c(['du lait', 'du pain', 'des oeufs', 'du café'])} en revenant ?",
    lambda g: f"Merci pour {g.c(['le souper', 'ton aide', 'la soirée', 'le lift'])}, c'était super !",
    lambda g: f"{g.c(PRENOMS)}, as-tu reçu mon courriel pour {g.c(['le projet', 'la présentation', 'le rapport'])} ?",
    lambda g: f"La garderie sera fermée {g.c(JOURS)} pour une journée pédagogique.",
    lambda g: f"Voici le lien pour la réunion de {g.heure()} : https://teams.microsoft.com/l/meetup-join/{g.code()}",
    lambda g: f"Les photos du party sont ici : https://photos.app.goo.gl/{g.c(['aB3', 'Xy9', 'Qp2'])}{g.code()}",
    lambda g: f"Hey, are we still on for {g.c(['lunch', 'dinner', 'the game'])} {g.c(JOURS_EN)}?",
    lambda g: f"Reminder: the team meeting moved to {g.heure_en()}.",
    lambda g: f"Can you send me the {g.c(['slides', 'notes', 'pictures'])} from today?",
]


def generer(n_par_classe: int = 600, graine: int = GRAINE) -> list[tuple[str, int]]:
    """Exemples (texte, label) : n_par_classe scams et autant de messages légitimes, sans doublons."""
    g = Generateur(graine)
    exemples, vus = [], set()
    for fabrique in (g.scam, g.legit):
        produits, essais = 0, 0
        while produits < n_par_classe and essais < n_par_classe * 20:
            essais += 1
            texte, label = fabrique()
            if texte not in vus:
                vus.add(texte)
                exemples.append((texte, label))
                produits += 1
    return exemples


if __name__ == "__main__":
    exemples = generer()
    print(f"{len(exemples)} exemples générés. Échantillon :\n")
    for texte, label in random.Random().sample(exemples, 12):
        print(f"[{'SCAM' if label else 'ok  '}] {texte}")
