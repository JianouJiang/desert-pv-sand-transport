# EDITOR_001 Review (Quality, Formatting, Presentation)

**Scope reviewed** (read-only): `manuscript/main.tex`, `manuscript/references.bib`, `manuscript/main.log`, `manuscript/main.pdf`, `manuscript/layout_report.md`, `manuscript/figures/*`.

## 1) Programmatic layout inspection (status + interpretation)

- **Blocked tools**: `layout_analyzer.py` and `figure_inspector.py` are not present in this project directory, so I could not re-run them. However, an existing `manuscript/layout_report.md` (generated **2026-03-05 21:28**) is available and reviewed.
- **Page count**: `pdfinfo manuscript/main.pdf` reports **29 pages**. `layout_report.md` reports “Total pages: 30” but its table lists pages 1–29 only. This discrepancy suggests the layout tool/report pipeline needs a quick sanity check.
- **White-space flags look miscalibrated**: `layout_report.md` flags **92–98% “white%”** as CRITICAL on essentially every page. For a normal text-heavy manuscript, pixel-level background percentage will be high; the **30% threshold appears inappropriate** (likely tuned for slide-like layouts, not papers). Treat these “CRITICAL 88” defects as **likely false positives** until thresholds/metrics are revised.
- **Actionable layout risk that *does* look real** (even without page-image viewing): multiple figures have **very short PDF bounding boxes** (see Section 3). When placed with `[t]` floats, these can create visibly large blank regions and post-float gaps in an Elsevier preprint layout.

## 2) Template compliance (Elsevier `elsarticle`)

- `\documentclass[preprint,12pt,review]{elsarticle}`: this is close to Elsevier’s template, but the combination of `preprint` + `review` should be **intentional** (double-spacing for review vs. preprint formatting). Decide the target build mode and keep the class options minimal and consistent.
- **Journal-required statements likely missing** for Solar Energy/Elsevier submission packages (confirm with the journal’s “Your Paper Your Way” checklist):
  - Graphical abstract (if required)
  - Highlights (commonly required)
  - Declaration of competing interest
  - Data availability statement
  - CRediT author contribution statement
- `hyperref` produces bookmark-string warnings around the author/corresponding-author commands (see `manuscript/main.log`). Not fatal, but cleanable for a polished submission.

## 3) Figure placement, sizing, and float hygiene (presentation-level)

I did not evaluate scientific content or aesthetics; this is purely layout/presentation.

- Several figure PDFs are **extremely short relative to page height**, which increases the risk of large blank areas when floated:
  - `F1_domain_schematic.pdf`: **~491 × 113 pt** (notably thin strip).
  - `F6_parametric_heatmap_panel_deposition.pdf`: **~492 × 201 pt**.
  - `F7_foundation_erosion_map.pdf`: **~491 × 201 pt**.
- In `main.tex`, many figures use `[t]` and are inserted immediately after first mention (good), but **short-height figures at top-of-page** can still leave half-page gaps. Consider redesigning F1 (and possibly F6/F7) to occupy more vertical space (e.g., stacked panels, inset zooms, richer annotations) so each float “earns” its page real estate.
- `manuscript/figure_report.md` is missing (and the inspector script is missing), so there is no automated figure-quality audit output in this project yet.

## 4) Writing style (Strunk: omit needless lists; avoid “AI voice”)

The prose is generally strong and specific, but the draft repeatedly falls back to list structures that read “generated”:

- **Avoid list-heavy exposition**:
  - `\begin{itemize}` in “Geometry and parameter space” and “Reference conditions”.
  - `\begin{description}` for regime definitions.
  - `\begin{enumerate}` in “Limitations” and “Conclusions”.
- **Remove boldface list starters** in Conclusions (`\textbf{...}` at the start of each enumerated item). This is a common LLM tell and is visually heavy in Elsevier preprint.
- One sentence reads slightly colloquial/imperative for journal tone: “the practical recommendation is simple: raise the panels.” Prefer a precise engineering phrasing (e.g., “increase ground clearance to …”).

## 5) LaTeX / typography issues that need tightening

- **`siunitx` misuse**: multiple occurrences of `\SI{}{\micro\metre}` (unit without a number) appear alongside a numeric value in math mode (e.g., `D_{50} = 200$~\SI{}{\micro\metre}`). Prefer either:
  - `\SI{200}{\micro\metre}` (number + unit), or
  - `200~\si{\micro\metre}` (unit-only macro).
- **Math-mode glitch**: in the regime description, patterns like `$\sim$$10^{-4}$` introduce back-to-back math shifts. Use a single math expression (e.g., `$\sim 10^{-4}$`).
- `hyperref` warnings in `manuscript/main.log` indicate some macros are being stripped from PDF strings. Addressing this improves metadata/bookmarks cleanliness.

## 6) Reference integrity (anti-hallucination audit)

### Cross-reference integrity
- `references.bib` contains **45** entries; `main.tex` cites **26** unique keys.
- **No “cited but missing from .bib”** keys detected.
- **19 entries are currently uncited**; consider pruning to reduce review burden and avoid “padding”.

### DOI verification (existence check)
I spot-checked DOI resolution for the first **20 DOI-bearing entries** in `references.bib` via `https://doi.org/<doi>`; **all returned HTTP 302 (OK)**, including (examples): Owen (1964), Kok et al. (2012), Richards & Hoxey (1993), Jubayer & Hangan (2016), Zhang et al. (2024), and others.

### Suspect / needs correction
- **`conceicao2019soiling`** (titled “Review of the soiling effect on solar energy systems”, RSE Reviews 117:109459 (2019)) has **no DOI field** and I could not verify the specific record:
  - The natural DOI guess `10.1016/j.rser.2019.109459` returns **HTTP 404** at doi.org.
  - Crossref search for “109459” does not return any RSE Reviews item.
  - Recommendation: **verify and correct this entry**, or replace with a verifiable soiling review (for example, DOI `10.1016/j.rser.2022.112434` resolves).
- **Missing DOI fields where a DOI likely exists**:
  - `yue2021sand` (Aeolian Research 53, 100741 (2021)) likely corresponds to DOI `10.1016/j.aeolia.2021.100741` (resolves).
  - `anderson1991review` appears to have a Crossref DOI for the chapter version (`10.1007/978-3-7091-6706-9_2`); confirm the correct publication type (chapter vs. journal supplement) and add DOI if appropriate.

## Requested next fixes (for the Worker)

1) Replace list-heavy sections with tight prose (especially Conclusions), and remove boldface list openers.  
2) Fix `siunitx` usage and the `$\sim$$...$` math shifts.  
3) Redesign/re-export short-height figures (notably `F1_domain_schematic.pdf`) to reduce float-induced whitespace.  
4) Add missing Elsevier/Solar Energy submission statements (highlights, competing interests, data availability, CRediT) as required by the target submission route.  
5) Verify/fix `conceicao2019soiling`; add missing DOIs where available; prune uncited bib entries.

Score: 6/10

