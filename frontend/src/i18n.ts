export type Langue = "fr" | "en";
export const LANGUES: Langue[] = ["fr", "en"];

const fr = {
  "titre.page": "Détecteur de scams",
  "titre": "Ce message est-il un scam ?",
  "intro": "Colle un texto, un courriel ou un numéro de téléphone. L’analyse te donne un niveau de risque et les raisons derrière.",
  "langue.groupe": "Langue",
  "types.groupe": "Type de contenu à analyser",
  "type.message": "Message",
  "type.email": "Courriel",
  "type.phone": "Téléphone",
  "label.texte": "Contenu à analyser",
  "label.tel": "Numéro de téléphone",
  "ph.message": "Colle le message ici",
  "ph.email": "Colle le courriel ici (objet et corps)",
  "ph.tel": "Ex. 514 555-0123",
  "btn.analyser": "Analyser",
  "btn.encours": "Analyse en cours…",
  "btn.exemple": "Essayer un exemple",
  "limite": "Le résultat est une estimation, pas une certitude. En cas de doute, ne clique sur aucun lien et contacte l’organisme directement avec le numéro officiel.",
  "verdict.faible": "Risque faible",
  "verdict.moyen": "Risque moyen, prudence",
  "verdict.élevé": "Scam probable",
  "verdict.inconnu": "Résultat",
  "score.aria": "Score de risque : {score} sur 100",
  "pourquoi": "Pourquoi",
  "aucune": "Aucun signal d’alerte précis n’a été relevé.",
  "alertes.titre": "Contenu offensant ou diffamatoire",
  "retour.question": "Est-ce que l’analyse était juste ?",
  "retour.scam": "C’était un scam",
  "retour.ok": "C’était légitime",
  "retour.merci": "Merci, ton retour est enregistré.",
  "retour.erreur": "Impossible d’enregistrer le retour pour le moment.",
  "ia.titre": "🤖 Analyse IA",
  "ia.verdict.scam": "🚨 Je pense que c’est une arnaque",
  "ia.verdict.doute": "🤔 J’hésite, prudence",
  "ia.verdict.legitime": "✅ Je pense que c’est légitime",
  "ia.confiance": "Confiance : {n} %",
  "ia.probabilite": "Probabilité d’arnaque : {n} %",
  "ia.type": "Type :",
  "ia.indices.suspects": "Mots suspects :",
  "ia.indices.rassurants": "Mots rassurants :",
  "ia.similaire": "Ressemble à ce scam connu ({n} %) :",
  "ia.conseil": "💡 Mon conseil :",
  "ia.etape1": "🤖 Je lis le message…",
  "ia.etape2": "🔍 Je cherche les signaux suspects…",
  "ia.etape3": "🧠 Je compare avec les arnaques que je connais…",
  "err.vide": "Ajoute un contenu à analyser avant de lancer l’analyse.",
  "err.serveur": "L’analyse a échoué. Vérifie que le serveur Flask est démarré, puis réessaie.",
  "ex.message": "Postes Canada : votre colis est en attente. Des frais de 2,99 $ sont requis dans les 24 heures sinon il sera retourné. Payez ici : http://postes-canada-suivi.xyz/paiement",
  "ex.email": "Objet : Dernier avis – compte suspendu\n\nBonjour, votre compte Desjardins sera suspendu immédiatement. Confirmez votre mot de passe et votre code de vérification ici : http://bit.ly/3xYzAbc",
};

type Cle = keyof typeof fr;

const en: Record<Cle, string> = {
  "titre.page": "Scam detector",
  "titre": "Is this message a scam?",
  "intro": "Paste a text message, an email or a phone number. The analysis gives you a risk level and the reasons behind it.",
  "langue.groupe": "Language",
  "types.groupe": "Type of content to analyze",
  "type.message": "Message",
  "type.email": "Email",
  "type.phone": "Phone",
  "label.texte": "Content to analyze",
  "label.tel": "Phone number",
  "ph.message": "Paste the message here",
  "ph.email": "Paste the email here (subject and body)",
  "ph.tel": "E.g. 514 555-0123",
  "btn.analyser": "Analyze",
  "btn.encours": "Analyzing…",
  "btn.exemple": "Try an example",
  "limite": "The result is an estimate, not a certainty. When in doubt, don’t click any link and contact the organization directly using its official number.",
  "verdict.faible": "Low risk",
  "verdict.moyen": "Medium risk, be careful",
  "verdict.élevé": "Likely scam",
  "verdict.inconnu": "Result",
  "score.aria": "Risk score: {score} out of 100",
  "pourquoi": "Why",
  "aucune": "No specific warning sign was found.",
  "alertes.titre": "Offensive or defamatory content",
  "retour.question": "Was the analysis right?",
  "retour.scam": "It was a scam",
  "retour.ok": "It was legitimate",
  "retour.merci": "Thanks, your feedback has been saved.",
  "retour.erreur": "Unable to save your feedback right now.",
  "ia.titre": "🤖 AI analysis",
  "ia.verdict.scam": "🚨 I think this is a scam",
  "ia.verdict.doute": "🤔 I’m not sure, be careful",
  "ia.verdict.legitime": "✅ I think this is legitimate",
  "ia.confiance": "Confidence: {n}%",
  "ia.probabilite": "Scam probability: {n}%",
  "ia.type": "Type:",
  "ia.indices.suspects": "Suspicious words:",
  "ia.indices.rassurants": "Reassuring words:",
  "ia.similaire": "Looks like this known scam ({n}%):",
  "ia.conseil": "💡 My advice:",
  "ia.etape1": "🤖 Reading the message…",
  "ia.etape2": "🔍 Looking for suspicious signals…",
  "ia.etape3": "🧠 Comparing with scams I know…",
  "err.vide": "Add some content to analyze before starting the analysis.",
  "err.serveur": "The analysis failed. Make sure the Flask server is running, then try again.",
  "ex.message": "Canada Post: your package is on hold. A fee of $2.99 is required within 24 hours or it will be returned. Pay here: http://canada-post-tracking.xyz/payment",
  "ex.email": "Subject: Final notice – account suspended\n\nHello, your RBC account will be suspended immediately. Confirm your password and verification code here: http://bit.ly/3xYzAbc",
};

const TEXTES: Record<Langue, Record<Cle, string>> = { fr, en };
const CLE_STOCKAGE = "langue";

export function langueInitiale(): Langue {
  const enregistree = localStorage.getItem(CLE_STOCKAGE);
  if (enregistree === "fr" || enregistree === "en") return enregistree;
  return navigator.language.toLowerCase().startsWith("fr") ? "fr" : "en";
}

export function enregistrerLangue(langue: Langue): void {
  localStorage.setItem(CLE_STOCKAGE, langue);
}

export function traduire(langue: Langue, cle: Cle, params: Record<string, string | number> = {}): string {
  return TEXTES[langue][cle].replace(/\{(\w+)\}/g, (_, nom: string) => String(params[nom] ?? ""));
}

export function estCle(cle: string): cle is Cle {
  return cle in fr;
}
