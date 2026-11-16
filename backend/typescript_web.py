"""Sert les fichiers TypeScript de frontend/src au navigateur, traduits en JavaScript à la volée.

Le navigateur ne sait exécuter que du JavaScript. Plutôt que de garder des fichiers .js
dans le projet, on traduit chaque .ts en mémoire quand la page le demande
(avec le compilateur TypeScript installé par npm), et on garde le résultat
tant que le fichier .ts n'a pas changé.
"""
import subprocess

import config

SRC_DIR = config.FRONTEND_DIR / "src"

# Petit script Node : lit le TypeScript sur l'entrée standard, écrit le JavaScript sur la sortie
_TRADUCTEUR = """
const ts = require("typescript");
let src = "";
process.stdin.on("data", (d) => (src += d));
process.stdin.on("end", () => {
  const out = ts.transpileModule(src, {
    compilerOptions: { target: ts.ScriptTarget.ES2020, module: ts.ModuleKind.ES2020 },
  });
  process.stdout.write(out.outputText);
});
"""

_cache: dict[str, tuple[float, str]] = {}   # nom -> (date de modification du .ts, JavaScript)


class TypeScriptIntrouvable(FileNotFoundError):
    pass


def traduire(nom: str) -> str:
    """Renvoie le JavaScript de frontend/src/<nom>.ts (nom sans extension, ex. « app »)."""
    chemin = SRC_DIR / f"{nom}.ts"
    # Refuse « ../ » et autres chemins qui sortiraient de frontend/src
    if chemin.resolve().parent != SRC_DIR.resolve() or not chemin.is_file():
        raise TypeScriptIntrouvable(nom)

    date = chemin.stat().st_mtime
    if nom in _cache and _cache[nom][0] == date:
        return _cache[nom][1]

    resultat = subprocess.run(
        ["node", "-e", _TRADUCTEUR],
        input=chemin.read_text(encoding="utf-8"),
        capture_output=True, text=True, timeout=30,
        cwd=config.FRONTEND_DIR,   # pour que Node trouve le paquet « typescript » (node_modules)
    )
    if resultat.returncode != 0:
        raise RuntimeError(f"Traduction de {nom}.ts impossible : {resultat.stderr.strip()}")
    _cache[nom] = (date, resultat.stdout)
    return resultat.stdout
