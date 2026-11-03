---
name: cv-adapt
description: Adapte un CV LaTeX existant (cv*.tex de ce dossier) à un appel d'offre / fiche de poste fourni en lien ou en fichier, puis génère le PDF via le MCP latex. Réorganise uniquement l'expérience pertinente et réécrit l'introduction, sans jamais inventer d'information absente du CV source. Déclencheurs : "adapter le CV", "CV pour cette offre", "cv-adapt", appel d'offre, fiche de poste, mission freelance.
---

# cv-adapt — CV ciblé sur un appel d'offre

Entrées attendues (demander si absentes) :
1. **Modèle LaTeX source** : un `cv*.tex` du dossier courant. Défaut : `cv.tex` (FR). Si l'offre est en anglais, proposer `cv.en.tex`.
2. **Appel d'offre** : URL (lire avec `WebFetch`) ou fichier local (`Read` ; PDF via `pages`).
3. Optionnel : slug de sortie (ex. `dotnet-azure`). Sinon le déduire de l'offre (2-3 mots, kebab-case).

Sortie : `cv.<slug>.tex` à la racine + `output/cv.<slug>.pdf`.

## Règle absolue : zéro invention

Le CV source est la **seule** source de vérité sur le candidat. L'offre sert uniquement à choisir l'ordre et l'accent.

- N'ajoute aucune technologie, outil, projet, client, chiffre, durée, taille d'équipe, certification, langue ou responsabilité absent du CV source.
- Une compétence demandée par l'offre mais absente du source reste absente. Elle est listée dans le rapport final comme « écart », jamais ajoutée.
- Pas de reformulation qui élargit un fait (« Docker » ne devient pas « Kubernetes », « mentorat de juniors » ne devient pas « management d'équipe », « Azure Functions » ne devient pas « architecture serverless à grande échelle »).
- Pas de nombre d'années d'expérience recalculé : reprendre celui du source (ex. « 10+ ans »).
- Ne corrige pas les incohérences du source (ex. versions Angular différentes entre titre et description). Signale-les dans le rapport.
- Exception connue : TF1 se termine en **Octobre 2026** (FR) / **October 2026** (EN), jamais « Présent ».

## Ce qui est autorisé

| Zone | Autorisé |
|---|---|
| Ligne de titre sous le nom (`{\large \color{primary} ...}`) | Réécrire avec des éléments présents dans le source, alignés sur l'intitulé de l'offre |
| Introduction (`minipage` sous l'en-tête) | Réécrire entièrement (4-6 lignes), mettre en `\textbf{}` les mots-clés de l'offre **qui existent dans le source** |
| Projets dans une même entreprise | Réordonner : le plus pertinent pour l'offre en premier |
| Puces (`\item`) d'un projet | Réordonner : les plus pertinentes en premier. Texte des puces inchangé |
| Expériences non pertinentes | Laisser en place, en fin de liste dans leur entreprise. Ne rien supprimer sauf demande explicite de l'utilisateur |
| Compétences | Réordonner les catégories et les éléments d'une catégorie. Aucun ajout |

Interdit : modifier le préambule, les couleurs, les coordonnées, les dates (hors exception TF1), l'éducation, le contenu des puces, des lignes « Environnement technique » et des descriptions de projet. L'ordre chronologique des entreprises reste inchangé.

## Structure du modèle (référence)

- Préambule : `article` 10pt A4, Helvetica, `geometry` 1.5cm, `titlesec`, `fontawesome5`, `needspace`, `fancyhdr` (pied « page / total »).
- En-tête `center` : nom `\Huge`, titre `\large\color{primary}`, contacts, `minipage` intro en `\small\color{darkgray}`.
- `\section*{EXPÉRIENCE}` : par entreprise, bloc `\needspace{11\baselineskip}` + ligne `\faBuilding` / `\faMapMarker` / `\faCalendar`, puis par projet :
  `\subsection*{<Rôle> --- Projet <Nom>}` + description + `itemize` + `\textit{Environnement technique~:} ...` + `\vspace{6pt}` (`\vspace{10pt}` entre entreprises).
- Bas de page : `tabularx` 2 colonnes (ÉDUCATION | LANGUES + COMPÉTENCES).
- Échapper `#`, `&`, `%`, `_` (`C\#`, `\&`). Espace insécable avant `:` en FR : `~:`.

Un bloc projet se déplace **en entier**, de `\subsection*` jusqu'au `\vspace{6pt}` qui le suit. Vérifier que le dernier projet d'une entreprise garde `\vspace{10pt}` avant l'entreprise suivante.

## Procédure

1. **Lire** le modèle source en entier et l'offre.
2. **Analyser l'offre** : intitulé, stack obligatoire, stack souhaitée, responsabilités, contexte (secteur, méthodo, séniorité), langue.
3. **Cartographier** chaque exigence vers les faits du source (projet + ligne). Classer : couvert / partiel / absent.
4. **Scorer** chaque projet par nombre et poids des exigences couvertes. Définir l'ordre des projets par entreprise et l'ordre des puces.
5. **Rédiger** titre + introduction uniquement à partir des faits cartographiés. Chaque affirmation de l'intro doit pointer vers une ligne du source.
6. **Écrire** `cv.<slug>.tex` (copie du source + modifications autorisées). Ne jamais écraser un fichier existant sans confirmation.
7. **Vérifier** avec le script :
   ```bash
   python3 .claude/skills/cv-adapt/scripts/check_facts.py <source.tex> cv.<slug>.tex
   ```
   Code de sortie non nul = contenu non présent dans le source. Corriger puis relancer jusqu'à `OK`.
8. **Compiler** avec `mcp__latex__compile_latex`. Le serveur tourne dans le conteneur Docker `mcp-content-creation` et ne voit pas ce dossier : `input_path` local échoue (« Input file not found ... /app »). Donc :
   - copier le `.tex` dans le volume monté : `cp cv.<slug>.tex ~/AppData/Projects/Sandbox/n8n-labs/outputs/mcp-content/cv-src/`, puis compiler avec `input_path: "outputs/mcp-content/cv-src/cv.<slug>.tex"` (`preview_pages: "all"`, `preview_dpi: 72`). À défaut, passer le contenu dans `content` ;
   - le résultat donne `container_path: /output/latex/<nom>.pdf`, qui correspond sur l'hôte à `~/AppData/Projects/Sandbox/n8n-labs/outputs/mcp-content/latex/<nom>.pdf` ;
   - copier ce fichier vers `output/cv.<slug>.pdf` (`cp`).
   Si le pied affiche `?? ` au lieu du nombre de pages (`\pageref{LastPage}`), recompiler une fois.
9. **Contrôler le rendu** (previews ou `mcp__latex__preview_pdf`) : pas de débordement, pas de titre de projet orphelin en bas de page, 5 pages max. Ajuster seulement les `\needspace` / `\newpage` si besoin. Page presque vide avant un bloc : retirer le `\newpage` ou le `\needspace` qui précède ce bloc (le `\needspace` avant Vinatech repousse tout à la page suivante). Le bloc ÉDUCATION/COMPÉTENCES (`tabularx`) ne se coupe pas.
10. **Relecture** : appliquer le skill `cv-check` sur `cv.<slug>.tex` (orthographe + mise en forme), sans toucher au fond.
11. **Rapport final** (court) :
    - chemins `.tex` et `.pdf` ;
    - ordre retenu des projets et pourquoi (1 ligne chacun) ;
    - écarts : exigences de l'offre absentes du CV (non ajoutées) ;
    - incohérences repérées dans le source.
