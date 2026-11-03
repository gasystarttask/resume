#!/usr/bin/env python3
"""Lint orthographe + mise en forme d'un CV LaTeX de ce dossier.

Usage: lint_cv.py <cv.tex> [--lang fr|en] [--pdf <cv.pdf>]

Langue auto-détectée (section EXPÉRIENCE vs EXPERIENCE) si --lang absent.
Sortie : une ligne par problème `L<ligne> [CATÉGORIE] message`.
Exit 0 si aucun problème, 1 sinon.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

MONTHS = {
    "fr": "Janvier Février Mars Avril Mai Juin Juillet Août Septembre Octobre Novembre Décembre".split(),
    "en": "January February March April May June July August September October November December".split(),
}
WRONG_LANG = {
    "fr": ["Present", "Experience", "Skills", "Education", "Languages", "Team of", "Technical environment"],
    "en": ["Présent", "Expérience", "Compétences", "Éducation", "Langues", "Équipe de", "Environnement technique"],
}
DICTS = {"fr": ["fr_FR", "fr"], "en": ["en_US", "en_GB"]}

issues = []


def add(n, cat, msg):
    issues.append((n, cat, msg))


def strip_latex(line: str) -> str:
    s = re.sub(r"(?<!\\)%.*", "", line)
    s = re.sub(r"\\href\{[^}]*\}\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\url\{[^}]*\}", "URL", s)
    s = re.sub(r"\\(begin|end|definecolor|usepackage|color|textcolor|vspace|hspace|needspace|setlength|rule)\*?(\[[^\]]*\])?(\{[^}]*\})*", " ", s)
    s = re.sub(r"\\fa[A-Za-z]+", " ", s)
    s = re.sub(r"\\[A-Za-z]+\*?", " ", s)
    s = s.replace("\\#", "#").replace("\\&", "&").replace("\\%", "%").replace("~", " ")
    return re.sub(r"[{}\[\]]", "", s)


def check_format(lines, lang):
    in_doc = False
    in_exp = False
    item_endings = []
    subsections = []
    for n, raw in enumerate(lines, 1):
        s = raw.rstrip("\n")
        if s.strip().startswith("\\begin{document}"):
            in_doc = True
        if not in_doc or s.lstrip().startswith("%"):
            continue
        if s.strip().startswith("\\section*"):
            in_exp = bool(re.search(r"EXP[ÉE]RIENCE", s))
        body = re.sub(r"(?<!\\)%.*", "", s)

        # Caractères spéciaux non échappés
        for ch in "&#%_":
            for m in re.finditer(r"(?<!\\)" + re.escape(ch), body):
                if ch == "&" and (body.strip() == "&" or re.search(r"tabular|\\\\\s*$", body)):
                    continue
                if ch == "%" and m.start() == len(body):
                    continue
                add(n, "LATEX", f"'{ch}' non échappé (utiliser \\{ch})")
        text = strip_latex(body)
        if re.search(r"\s[,.](\s|$)", text) and not re.search(r"\s\.NET", text):
            add(n, "PONCTUATION", "espace avant , ou .")
        # Ponctuation selon la langue
        if lang == "fr":
            if re.search(r"[^\s~]:(\s|$)", body) and "http" not in body and "mailto" not in body:
                add(n, "TYPO-FR", "« : » sans espace insécable avant (écrire ~:)")
            if re.search(r" :", body) and "~:" not in body:
                add(n, "TYPO-FR", "espace simple avant « : » (préférer ~:)")
            if '"' in body:
                add(n, "TYPO-FR", "guillemets droits, utiliser « … »")
        else:
            if re.search(r"(~| ):", body):
                add(n, "TYPO-EN", "pas d'espace avant « : » en anglais")
            if "«" in body or "»" in body:
                add(n, "TYPO-EN", "guillemets français dans un CV anglais")
        # Mots de l'autre langue
        for w in WRONG_LANG[lang]:
            if re.search(r"\b" + re.escape(w) + r"\b", body):
                add(n, "LANGUE", f"« {w} » appartient à l'autre langue")
        # Dates
        if "\\faCalendar" in body:
            span = re.sub(r".*\\faCalendar\\?\s*\}?\s*", "", body).rstrip("} ").strip()
            if re.search(r"\d{4}\s*-\s*\d{4}|\d{4}\s*—\s*", span) or re.search(r"[^-]-[^-]", span.replace("\\ ", "")) and "--" not in span:
                add(n, "DATE", "intervalle à écrire avec -- (tiret demi-cadratin)")
            for tok in re.findall(r"[A-Za-zÀ-ÿ]+", span):
                if tok.capitalize() in MONTHS["fr"] + MONTHS["en"] and tok not in MONTHS[lang]:
                    add(n, "DATE", f"mois « {tok} » mal orthographié ou dans l'autre langue")
            if re.search(r"Juillet 2019 -- Présent|July 2019 -- Present", span):
                add(n, "DATE", "TF1 : mission terminée en Octobre 2026 / October 2026")
        # Structure
        st = s.strip()
        if st.startswith("\\item") and in_exp:
            item_endings.append((n, st.endswith(".")))
        if st.startswith("\\subsection*"):
            subsections.append(n)
            if " --- " not in st and "Mainteneur" not in st and "Maintainer" not in st:
                add(n, "STRUCTURE", "titre de projet sans séparateur « --- »")
        if st.startswith("\\subsection*") and re.search(r"(?<!-)--(?!-)", body):
            add(n, "TYPO", "« -- » hors date : vérifier (« --- » pour séparer rôle et projet)")
        if re.search(r"\b(\w+) \1\b", text, re.I) and not re.search(r"\b(\d+) \1\b", text):
            add(n, "ORTHO", f"mot répété : {re.search(r'(\\b\\w+) \\1\\b', text, re.I).group(0)}")

    # Puces : ponctuation finale homogène
    with_dot = sum(1 for _, d in item_endings if d)
    if item_endings and 0 < with_dot < len(item_endings):
        major = with_dot * 2 >= len(item_endings)
        for n, d in item_endings:
            if d != major:
                add(n, "COHÉRENCE", "puce " + ("sans" if major else "avec") + " point final, contrairement à la majorité")

    # Chaque projet : un itemize et une ligne Environnement technique
    full = "".join(lines)
    blocks = re.split(r"\\subsection\*", full)[1:]
    env = "Environnement technique" if lang == "fr" else "Tech Stack"
    for start, blk in zip(subsections, blocks):
        blk = re.split(r"\\noindent\\textcolor|\\section\*", blk)[0]
        if "\\begin{itemize}" not in blk:
            add(start, "STRUCTURE", "projet sans liste de puces")
        if env not in blk and "Mainteneur" not in blk[:80] and "Maintainer" not in blk[:80] and "Open-source" not in blk[:120]:
            add(start, "STRUCTURE", f"projet sans ligne « {env} »")


def check_versions(lines):
    """Versions différentes pour un même projet (ex. Angular 8 vs Angular 21)."""
    full = "".join(lines)
    for blk in re.split(r"\\subsection\*", full)[1:]:
        blk = re.split(r"\\vspace\{(6|10)pt\}", blk)[0]
        title = blk.split("\n", 1)[0]
        line_no = full[: full.find(blk)].count("\n") + 1
        # Migrations « de .NET 4.7 vers .NET 10 » : versions multiples légitimes
        blk = re.sub(r"(de|from) \S+ [\d.]+\+? (vers|to) ", " ", blk)
        for tech in ("Angular", ".NET"):
            vers = {v.rstrip("+") for v in re.findall(re.escape(tech) + r" (\d+(?:\.\d+)?\+?)", blk)}
            if len(vers) > 1:
                add(line_no, "COHÉRENCE", f"{tech} : versions {sorted(vers)} dans « {title.strip('{} ')[:60]} »")


def find_dict(lang):
    if not shutil.which("hunspell"):
        return None
    out = subprocess.run(["hunspell", "-D"], capture_output=True, text=True, input="").stderr
    avail = set(re.findall(r"/([A-Za-z_]+)$", out, re.M))
    for d in DICTS[lang]:
        if d in avail:
            return d
    return None


def check_spelling(lines, lang):
    d = find_dict(lang)
    if not d:
        add(0, "INFO", f"aucun dictionnaire hunspell {lang} : orthographe à relire manuellement "
            f"(sudo pacman -S {'hunspell-fr' if lang == 'fr' else 'hunspell-en_us'})")
        return
    known = set()
    wl = os.path.join(HERE, "..", "wordlist.txt")
    if os.path.exists(wl):
        known |= {w.strip().lower() for w in open(wl, encoding="utf-8") if w.strip() and not w.startswith("#")}
    in_doc = False
    for n, raw in enumerate(lines, 1):
        if raw.strip().startswith("\\begin{document}"):
            in_doc = True
        if not in_doc or "Environnement technique" in raw or "Technical environment" in raw:
            continue  # lignes de stack : noms propres techniques
        text = strip_latex(raw)
        words = [w for w in re.findall(r"[A-Za-zÀ-ÿ'’-]{3,}", text)
                 if not re.search(r"[A-Z].*[A-Z]", w) and w.lower().strip("'’-") not in known]
        if not words:
            continue
        r = subprocess.run(["hunspell", "-d", d, "-l"], input="\n".join(words), capture_output=True, text=True)
        for w in sorted(set(r.stdout.split())):
            add(n, "ORTHO", f"mot inconnu : {w}")


def check_pdf(pdf):
    if not shutil.which("pdftotext"):
        return
    txt = subprocess.run(["pdftotext", "-layout", pdf, "-"], capture_output=True, text=True).stdout
    pages = txt.split("\f")
    if "??" in txt:
        add(0, "PDF", "« ?? » dans le PDF : référence non résolue (recompiler)")
    real = [p for p in pages if p.strip()]
    if len(real) > 5:
        add(0, "PDF", f"{len(real)} pages : 5 max")
    for i, p in enumerate(real[:-1], 1):
        tail = [l.strip() for l in p.strip().splitlines() if l.strip()]
        # Ligne de pied « x / y » ignorée ; titre isolé en bas de page = orphelin
        tail = [l for l in tail if not re.fullmatch(r"\d+ / \d+", l)]
        if tail and (" — " in tail[-1] or " --- " in tail[-1] or tail[-1].isupper()):
            add(0, "PDF", f"page {i} : titre orphelin en bas de page « {tail[-1][:60]} »")
    if len(real) and len(real[-1].strip().splitlines()) < 6:
        add(0, "PDF", "dernière page presque vide : resserrer les espacements")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tex")
    ap.add_argument("--lang", choices=["fr", "en"])
    ap.add_argument("--pdf")
    a = ap.parse_args()
    lines = open(a.tex, encoding="utf-8").readlines()
    lang = a.lang or ("en" if any("\\section*{EXPERIENCE}" in l for l in lines) else "fr")
    print(f"Langue : {lang}")
    check_format(lines, lang)
    check_versions(lines)
    check_spelling(lines, lang)
    if a.pdf:
        check_pdf(a.pdf)
    for n, cat, msg in sorted(issues):
        print(f"L{n} [{cat}] {msg}")
    real = [i for i in issues if i[1] != "INFO"]
    print(f"{len(real)} problème(s).")
    return 1 if real else 0


if __name__ == "__main__":
    sys.exit(main())
