#!/usr/bin/env python3
"""Vérifie qu'un CV adapté n'invente rien par rapport au CV source.

Usage: check_facts.py <source.tex> <adapte.tex>

Contrôles :
1. Chaque ligne de contenu du CV adapté (\\item, Environnement technique,
   descriptions, \\subsection*) existe telle quelle dans le source.
   Seuls la ligne de titre et l'introduction (minipage d'en-tête) peuvent changer.
2. Les termes techniques de l'introduction et du titre (mots avec majuscule,
   chiffre ou symbole : .NET, C\\#, Azure, TDD...) existent dans le source.
3. Rien n'a été supprimé : chaque ligne de contenu du source est présente.
Exit 0 si OK, 1 sinon.
"""
import re
import sys

ALLOWED_DATE_FIXES = {
    "Juillet 2019 -- Présent": "Juillet 2019 -- Octobre 2026",
    "July 2019 -- Present": "July 2019 -- October 2026",
}


def norm(line: str) -> str:
    line = line.strip()
    for old, new in ALLOWED_DATE_FIXES.items():
        line = line.replace(old, new)
    return re.sub(r"\s+", " ", line)


def split(text: str):
    """Return (header_free_text, content_lines) where header = title + intro."""
    lines = text.splitlines()
    header, content = [], []
    in_intro = False
    in_doc = False
    for raw in lines:
        s = raw.strip()
        if s.startswith("\\begin{document}"):
            in_doc = True
            continue
        if not in_doc or not s or s.startswith("%"):
            continue
        if re.fullmatch(r"\\(newpage|clearpage|vspace\{[^}]*\}|needspace\{[^}]*\})", s):
            continue  # mise en page : ajustable
        if s.startswith("\\begin{minipage}{\\textwidth}"):
            in_intro = True
            continue
        if in_intro:
            if s.startswith("\\end{minipage}"):
                in_intro = False
            elif not s.startswith("\\small"):
                header.append(s)
            continue
        if s.startswith("{\\large \\color{primary}"):
            header.append(s)
            continue
        content.append(norm(s))
    return header, content


TERM = re.compile(r"[A-Za-z][\w.+#\\/-]*[A-Z0-9#+.][\w.+#\\/-]*|\.NET[\w.]*|C\\#")
STOP = {"Développeur", "Developer", "Senior", "Lead", "Full-Stack", "Expertise",
        "Expérience", "Experience", "Forte", "Compétences", "Pratiques", "Projet"}


def terms(text: str):
    out = set()
    # Every bolded keyword must exist verbatim in the source.
    for b in re.findall(r"\\textbf\{([^{}]*)\}", text):
        for part in re.split(r"\s*[/,]\s*|\s+(?:et|and|avec|with)\s+", b):
            part = part.strip(" .:;()~")
            if len(part) >= 2:
                out.add(part)
    text = re.sub(r"\\textbf\{|\\textit\{|\\emph\{|[{}~]", " ", text)
    for m in TERM.finditer(text):
        t = m.group(0).strip(".,;:()")
        if len(t) < 2 or t in STOP or t.startswith("\\"):
            continue
        before = text[: m.start()].rstrip()
        sentence_start = not before or before[-1] in ".:!?—-"
        plain = t[0].isupper() and t[1:].islower() and not re.search(r"[0-9#+.]", t)
        if plain and sentence_start:
            continue
        out.add(t)
    # Plain capitalised words mid-sentence (proper nouns: Kubernetes, Kafka...).
    for m in re.finditer(r"(?<=[a-zé,;(] )([A-Z][a-zé]{2,})\b", text):
        if m.group(1) not in STOP:
            out.add(m.group(1))
    return out


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        return 2
    src = open(sys.argv[1], encoding="utf-8").read()
    dst = open(sys.argv[2], encoding="utf-8").read()
    _, src_content = split(src)
    dst_header, dst_content = split(dst)
    src_set, dst_set = set(src_content), set(dst_content)
    src_flat = re.sub(r"\s+", " ", src).lower()

    errors = 0
    added = [l for l in dst_content if l not in src_set]
    for l in added:
        print(f"[AJOUT/MODIF] {l}")
    errors += len(added)

    removed = [l for l in src_content if l not in dst_set]
    for l in removed:
        print(f"[SUPPRIMÉ] {l}")
    errors += len(removed)

    for t in sorted(terms(" ".join(dst_header))):
        if t.lower() not in src_flat:
            print(f"[INTRO: terme absent du source] {t}")
            errors += 1

    if errors:
        print(f"ÉCHEC : {errors} problème(s).")
        return 1
    print("OK : aucun contenu inventé ni supprimé.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
