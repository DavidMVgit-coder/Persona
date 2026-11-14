import { type Langue, enregistrerLangue, estCle, langueInitiale, traduire } from "./i18n.js";

type TypeContenu = "message" | "email" | "phone";
type Niveau = "faible" | "moyen" | "élevé";

interface ResultatAnalyse {
  score: number;
  niveau: Niveau;
  raisons: string[];
  alertes?: string[];
}

const NUMERO_EXEMPLE = "+1 809 555 0142";

let langue: Langue = langueInitiale();
// Dernière analyse affichée : relancée si on change de langue, pour traduire les raisons
let derniereAnalyse: { type: TypeContenu; contenu: string } | null = null;

const tr = (cle: Parameters<typeof traduire>[1], params?: Record<string, string | number>) =>
  traduire(langue, cle, params);

function $<T extends HTMLElement = HTMLElement>(id: string): T {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Élément #${id} introuvable`);
  return el as T;
}

const champTexte = $<HTMLTextAreaElement>("contenu-texte");
const champTel = $<HTMLInputElement>("contenu-tel");
const zoneResultat = $("resultat");
const btnAnalyser = $<HTMLButtonElement>("btn-analyser");

const typeCourant = (): TypeContenu =>
  document.querySelector<HTMLInputElement>('input[name="type"]:checked')!.value as TypeContenu;

const contenuCourant = (): string =>
  typeCourant() === "phone" ? champTel.value.trim() : champTexte.value.trim();

// ---------- Langue ----------

/** Traduit tout le texte statique de la page (attributs data-i18n*). */
function appliquerLangue(): void {
  document.documentElement.lang = langue;
  document.title = tr("titre.page");

  document.querySelectorAll<HTMLElement>("[data-i18n]").forEach((el) => {
    const cle = el.dataset.i18n!;
    if (estCle(cle)) el.textContent = tr(cle);
  });
  document.querySelectorAll<HTMLElement>("[data-i18n-aria]").forEach((el) => {
    const cle = el.dataset.i18nAria!;
    if (estCle(cle)) el.setAttribute("aria-label", tr(cle));
  });

  champTexte.placeholder = tr(typeCourant() === "email" ? "ph.email" : "ph.message");
  champTel.placeholder = tr("ph.tel");
  if (!btnAnalyser.disabled) btnAnalyser.textContent = tr("btn.analyser");

  document.querySelectorAll<HTMLButtonElement>("[data-langue]").forEach((btn) => {
    btn.setAttribute("aria-pressed", String(btn.dataset.langue === langue));
  });
}

document.querySelectorAll<HTMLButtonElement>("[data-langue]").forEach((btn) => {
  btn.addEventListener("click", () => {
    const choix = btn.dataset.langue as Langue;
    if (choix === langue) return;
    langue = choix;
    enregistrerLangue(langue);
    appliquerLangue();
    // Les raisons viennent du serveur : on relance l'analyse pour les avoir dans la nouvelle langue
    if (derniereAnalyse) void analyser(derniereAnalyse.type, derniereAnalyse.contenu);
    else zoneResultat.innerHTML = "";
  });
});

// ---------- Saisie ----------

// Affiche le bon champ selon le type choisi
document.querySelectorAll<HTMLInputElement>('input[name="type"]').forEach((radio) => {
  radio.addEventListener("change", () => {
    const tel = typeCourant() === "phone";
    $("zone-tel").hidden = !tel;
    $("zone-texte").hidden = tel;
    zoneResultat.innerHTML = "";
    derniereAnalyse = null;
    champTexte.placeholder = tr(typeCourant() === "email" ? "ph.email" : "ph.message");
  });
});

$("btn-exemple").addEventListener("click", () => {
  const t = typeCourant();
  if (t === "phone") champTel.value = NUMERO_EXEMPLE;
  else champTexte.value = tr(t === "email" ? "ex.email" : "ex.message");
});

btnAnalyser.addEventListener("click", () => {
  const contenu = contenuCourant();
  if (!contenu) {
    afficherErreur(tr("err.vide"));
    return;
  }
  void analyser(typeCourant(), contenu);
});

// ---------- Analyse ----------

async function analyser(type: TypeContenu, contenu: string): Promise<void> {
  btnAnalyser.disabled = true;
  btnAnalyser.textContent = tr("btn.encours");

  try {
    const rep = await fetch("/analyser", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type, contenu, langue }),
    });
    if (!rep.ok) throw new Error("HTTP " + rep.status);
    derniereAnalyse = { type, contenu };
    afficherResultat((await rep.json()) as ResultatAnalyse, type, contenu);
  } catch {
    afficherErreur(tr("err.serveur"));
  } finally {
    btnAnalyser.disabled = false;
    btnAnalyser.textContent = tr("btn.analyser");
  }
}

function liste(items: string[]): HTMLUListElement {
  const ul = document.createElement("ul");
  items.forEach((txt) => {
    const li = document.createElement("li");
    li.textContent = txt; // textContent : évite d'injecter du HTML
    ul.append(li);
  });
  return ul;
}

function afficherResultat(r: ResultatAnalyse, type: TypeContenu, contenu: string): void {
  zoneResultat.innerHTML = "";

  const carte = document.createElement("div");
  carte.className = "carte";
  carte.dataset.niveau = r.niveau;

  const verdict = document.createElement("div");
  verdict.className = "verdict";
  const titre = document.createElement("strong");
  const cleVerdict = `verdict.${r.niveau}`;
  titre.textContent = tr(estCle(cleVerdict) ? cleVerdict : "verdict.inconnu");
  const score = document.createElement("span");
  score.className = "score";
  const valeur = document.createElement("b");
  valeur.textContent = String(r.score);
  score.append(valeur, " / 100");
  verdict.append(titre, score);

  const jauge = document.createElement("div");
  jauge.className = "jauge";
  jauge.setAttribute("role", "img");
  jauge.setAttribute("aria-label", tr("score.aria", { score: r.score }));
  const rempli = document.createElement("div");
  jauge.append(rempli);

  const h2 = document.createElement("h2");
  h2.textContent = tr("pourquoi");
  carte.append(verdict, jauge, h2);

  if (r.raisons && r.raisons.length) {
    carte.append(liste(r.raisons));
  } else {
    const p = document.createElement("p");
    p.className = "aucune";
    p.textContent = tr("aucune");
    carte.append(p);
  }

  // Contenu offensant : affiché à part, ne compte pas dans le score de scam
  if (r.alertes && r.alertes.length) {
    const bloc = document.createElement("div");
    bloc.className = "alertes";
    const h = document.createElement("h2");
    h.textContent = tr("alertes.titre");
    bloc.append(h, liste(r.alertes));
    carte.append(bloc);
  }

  // Retour utilisateur (pour réentraîner le modèle plus tard)
  const retour = document.createElement("div");
  retour.className = "retour";
  const q = document.createElement("p");
  q.textContent = tr("retour.question");
  const btnScam = document.createElement("button");
  btnScam.type = "button";
  btnScam.className = "ghost";
  btnScam.textContent = tr("retour.scam");
  const btnOk = btnScam.cloneNode() as HTMLButtonElement;
  btnOk.textContent = tr("retour.ok");
  btnScam.addEventListener("click", () => envoyerRetour(retour, type, contenu, 1));
  btnOk.addEventListener("click", () => envoyerRetour(retour, type, contenu, 0));
  retour.append(q, btnScam, btnOk);
  carte.append(retour);

  zoneResultat.append(carte);
  requestAnimationFrame(() => {
    rempli.style.width = `${Math.max(2, r.score)}%`;
  });
  carte.scrollIntoView({ block: "nearest", behavior: "smooth" });
}

async function envoyerRetour(
  conteneur: HTMLElement,
  type: TypeContenu,
  contenu: string,
  label: 0 | 1,
): Promise<void> {
  const message = (cle: "retour.merci" | "retour.erreur") => {
    const p = document.createElement("p");
    p.textContent = tr(cle);
    conteneur.replaceChildren(p);
  };
  try {
    const rep = await fetch("/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type, contenu, label, langue }),
    });
    if (!rep.ok) throw new Error("HTTP " + rep.status);
    message("retour.merci");
  } catch {
    message("retour.erreur");
  }
}

function afficherErreur(msg: string): void {
  derniereAnalyse = null;
  zoneResultat.innerHTML = "";
  const div = document.createElement("div");
  div.className = "erreur";
  div.setAttribute("role", "alert");
  div.textContent = msg;
  zoneResultat.append(div);
}

appliquerLangue();
