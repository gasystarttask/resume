---
name: cv-check
description: Vérifie l'orthographe, la grammaire, la typographie (FR ou EN) et la mise en forme d'un CV LaTeX de ce dossier (cv*.tex) et de son PDF. Rapporte les problèmes avec numéro de ligne, puis corrige sur accord. Déclencheurs : "vérifier le CV", "relire le CV", "orthographe", "fautes", "mise en forme du CV", "cv-check", relecture avant envoi. À lancer aussi après cv-adapt.
---

# cv-check — relecture orthographe + mise en forme

Entrées : un `cv*.tex` (demander lequel si ambigu ; défaut : le dernier modifié). PDF associé optionnel : `output/<même nom>.pdf`.
Langue : FR si `\section*{EXPÉRIENCE}`, EN si `\section*{EXPERIENCE}`. L'utilisateur peut forcer `fr` / `en`.

## Règle : le fond ne change pas

Corriger la forme uniquement : orthographe, accords, conjugaison, ponctuation, typographie, LaTeX, mise en page.
Ne jamais ajouter, retirer ou reformuler un fait (techno, projet, chiffre, date, rôle). Si une correction toucherait au sens, la proposer sans l'appliquer.
Les incohérences de fond (ex. « Angular 8 » dans la description d'un projet titré « Angular 21 ») sont **signalées**, jamais tranchées seul : demander à l'utilisateur.
Exception connue : TF1 = « Juillet 2019 -- Octobre 2026 » / « July 2019 -- October 2026 ».

## Procédure

1. **Lint automatique** :
   ```bash
   python3 .claude/skills/cv-check/scripts/lint_cv.py <cv.tex> [--lang fr|en] [--pdf output/<cv>.pdf]
   ```
   Catégories : `ORTHO`, `TYPO-FR`/`TYPO-EN`, `LANGUE` (mot de l'autre langue), `DATE`, `LATEX` (caractère non échappé), `STRUCTURE`, `COHÉRENCE` (versions, ponctuation des puces), `PDF` (pages, `??`, titre orphelin, dernière page vide).
   Le script contrôle l'orthographe avec hunspell seulement si un dictionnaire est installé (`sudo pacman -S hunspell-fr hunspell-en_us`). Sinon il affiche `INFO` et l'étape 2 suffit.
   Un vrai terme technique signalé `ORTHO` : l'ajouter à `.claude/skills/cv-check/wordlist.txt`.

2. **Relecture manuelle** du `.tex` entier (le lint ne couvre pas tout) :
   - **FR** : accords (genre, nombre, participes passés), conjugaison, accents sur majuscules (« État », « Équipe »), élision, `~:` avant deux-points (aussi `~;` `~!` `~?`), guillemets « … », nombres (`99,9\%`), majuscules non anglaises (« Base de données », pas « Base De Données »), cohérence nominale des puces (noms ou infinitifs, pas les deux).
   - **EN** : orthographe US ou UK cohérente (« optimize » vs « optimise »), pas d'espace avant `:`, articles, temps (passé pour les missions finies, présent pour la mission en cours), « Present » seulement si mission en cours.
   - **Les deux** : mots répétés, coquilles, casse homogène des technos (`React.js`, `Node.js`, `.NET`, `C\#`, `PostgreSQL`, `TypeScript`, `GitHub`, `MS SQL Server` — jamais « MSSQL », « SQL Server » seul ni « Azure SQL » ; sur Azure : `MS SQL Server (Azure)`), même libellé partout pour une même techno, ponctuation finale homogène des puces, formats de date homogènes (`Mois AAAA -- Mois AAAA`).

3. **Mise en forme LaTeX** (référence : `cv.tex`) :
   - en-tête entreprise : `\needspace{11\baselineskip}` + `\noindent\textcolor{primary}{ \faBuilding\ ...}` + lieu + `\hfill` + date ;
   - projet : `\subsection*{<Rôle> --- Projet <Nom>}`, description, `itemize`, ligne `\textit{Environnement technique~:}` (EN : `\textit{Tech Stack:}`), puis `\vspace{6pt}` ; `\vspace{10pt}` entre entreprises ;
   - `---` entre rôle et projet, `--` pour les intervalles de dates ;
   - pas de `\\` pour espacer, pas de `\newpage` superflu, préambule identique au modèle.

4. **Rendu PDF** : si le PDF est absent ou plus ancien que le `.tex`, compiler comme dans `cv-adapt` étape 8 : copier le `.tex` vers `~/AppData/Projects/Sandbox/n8n-labs/outputs/mcp-content/cv-src/`, puis `mcp__latex__compile_latex` avec `input_path: "outputs/mcp-content/cv-src/<cv>.tex"` ; le PDF sort dans `~/AppData/Projects/Sandbox/n8n-labs/outputs/mcp-content/latex/`, à copier vers `output/`. Regarder les previews (`preview_pages: "all"`) :
   5 pages max, texte qui déborde, titre de projet isolé en bas de page, page presque vide, alignement des dates à droite, icônes manquantes, pied « x / y » correct. Relancer le lint avec `--pdf`.

5. **Rapport** : tableau `ligne | catégorie | avant | après`, groupé : à corriger / à confirmer (fond) / info.
   Appliquer les corrections de forme seulement après accord de l'utilisateur (ou directement si l'utilisateur l'a demandé). Puis relancer le lint et recompiler.
