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

---

## Addendum (2026-03-06): incorporate latest reviews + current draft state

This addendum reflects the updated manuscript and the new review set (`JUDGE_002_REVIEW.md`, `STATISTICIAN_002_REVIEW.md`, `ILLUSTRATOR_001_REVIEW.md`). I am not re-evaluating scientific validity; only presentation, LaTeX hygiene, and reference integrity.

### A) Items from EDITOR_001 now resolved

- **List-heavy writing cleaned up**: `itemize`/`description` are removed from the main narrative; Conclusions are now in tight prose. (A numbered list remains in Limitations; see “Remaining items”.)
- **`siunitx` fixes applied**: the earlier `\SI{}{\micro\metre}` misuse is gone; `\si{\micro\metre}` is used consistently in the current draft.
- **Submission boilerplate improved**: `\section*{Declaration of competing interest}` and `\section*{Data availability}` are now present.
- **References cleaned**: `references.bib` now contains **26 entries and all 26 are cited** (no orphans, no missing keys).
- **Reference existence spot-check**: I re-checked DOI resolution for **10 DOI-bearing entries**; all returned HTTP 302 at `doi.org` (OK).

### B) Remaining editor-facing issues (high priority)

1) **`hyperref` warnings persist**  
`manuscript/main.log` still shows repeated “Token not allowed in a PDF string (Unicode)” warnings. These usually come from author/title macros (e.g., `\corref`, footnote commands) leaking into PDF bookmarks/metadata. Clean bookmarks matter for submission polish.

2) **Template completeness still uncertain (Solar Energy / Elsevier)**  
Even with competing interest + data availability added, the manuscript still appears to lack:
  - **CRediT author contribution statement** (often expected).
  - **Highlights** / **Graphical abstract** (sometimes required depending on journal workflow).  
Confirm requirements against the target Solar Energy submission checklist and include the missing elements if mandated.

3) **Citations that may not support the claim as written**  
The text uses `\cite{dong2004flow}` to support a statement about panel wake reattachment length scaling with tilt angle. That cited paper (porous fences) may not support this specific claim; either replace with a more appropriate separation/reattachment reference for inclined plates/panels or rephrase to a claim that the cited work actually substantiates.

4) **Reference-key hygiene**  
The entry key `dong2004flow` has `year = {2007}`. Keys can be arbitrary, but year-mismatched keys confuse reviewers and collaborators; consider normalizing keys to `dong2007...` (or otherwise aligning key naming conventions).

### C) Figure/presentation polish (from Illustrator + editor scan)

I did not redesign figures, but several presentation issues are likely to draw reviewer attention:

- **Gridlines too prominent** across many plots (per Illustrator). Reduce grid alpha/linewidth or disable by default; turn on only where the grid is doing quantitative work.
- **Literal tildes in figure text** (e.g., `0.1~m`) appear in some Matplotlib labels. In plots, a tilde reads as a tilde, not a non-breaking space; replace with proper spacing.
- **Caption–figure consistency**: verify that captions match what is actually shown (Illustrator flagged at least one case where the caption implies numeric annotations that may not be present). This is an easy credibility win.
- **Float efficiency still a risk**: short-height figures (especially domain schematic / heatmaps) can create large post-float gaps in the Elsevier layout. Prefer figures that use the available vertical space (multi-panel stacking, insets, richer annotation) so each float “earns” its page area.

### D) Layout-report interpretation (do not overreact)

`manuscript/layout_report.md` has been regenerated (**2026-03-06 04:38**) and still flags ~90%+ “white%” as CRITICAL on nearly all pages. This metric/threshold remains **miscalibrated** for papers; use it cautiously and prioritize more specific defect signals (e.g., oversized float gaps) over the raw white-space percentage.

### E) Manuscript-claim precision (language/consistency)

The Judge/Statistician note potential discrepancies in how convergence is described (initial vs final residuals, formal vs practical convergence). As an editor-facing action: ensure the manuscript’s convergence claims are **precise, consistent, and audit-friendly** (define which residual is monitored and how “converged” is counted), so the narrative matches the actual logs/data.

Updated score (presentation only, given fixes observed): 7/10

---

## Addendum (2026-03-06, later): JUDGE\_003 + STATISTICIAN\_003 presentation implications

New reviews (`JUDGE_003_REVIEW.md`, `STATISTICIAN_003_REVIEW.md`) reiterate several *paper-credibility* gaps. I do not judge the physics, but these issues directly affect what the manuscript/figures “say” to a reader and therefore fall under presentation clarity:

### 1) Convergence language must match what SIMPLE actually checks

- The manuscript currently states that “most cases reach the convergence criterion within 1700--2500 iterations.” If many cases remain **formally unconverged in SIMPLE’s `residualControl` sense** (initial residuals), that sentence will read as misleading even if final (linear-solver) residuals are small.
- Editorial action: when the Worker updates results, ensure the paper clearly distinguishes **initial residuals** vs **final residuals**, and defines what “converged” means (and how many cases met it). Consider adding a one-line convergence summary (N/36) in the Results or an Appendix table.

### 2) “Shelter efficiency” terminology becomes confusing when negative

- STATISTICIAN\_003 reiterates the finding (from STATISTICIAN\_002) that many cases have **negative “shelter efficiency”** (i.e., net flux amplification). As-written, “efficiency” strongly implies a nonnegative benefit; the term risks confusing/irritating reviewers.
- Editorial action: rename the metric to something sign-agnostic (e.g., “flux modification ratio” or “array flux amplification factor”), and rewrite captions/axis labels accordingly so a negative value is not presented as a paradox.

### 3) Uncertainty must appear on at least one key figure (not only in text)

- JUDGE\_003 and STATISTICIAN\_003 both emphasize that uncertainty is currently discussed only in prose. From a presentation standpoint, **a single shaded band** on the flagship deposition-vs-clearance plot (e.g., coefficient range for Owen’s C) dramatically improves trust and reduces “false precision” optics.

### 4) Mechanism prose needed for the row-spacing trend

- The new reviews highlight that the observed row-spacing effect has a counterintuitive direction (wider spacing reducing deposition via reduced Venturi amplification rather than “more shelter”). Even if scientifically correct, *not explaining it* reads like a reporting error.
- Editorial action: add a short, plain-language mechanism paragraph in Discussion that reconciles the direction of the S-effect with the chosen metric definition and with the cubic dependence in the flux law.

### 5) Validation messaging

- Third reviewer round reiterates that a single obstacle-flow validation case (e.g., Jubayer & Hangan velocity profiles) would anchor credibility. This is primarily a methods/results issue, but it also affects presentation: without it, the paper must avoid language that implies validated predictive accuracy.
- Editorial action: keep claims calibrated (e.g., “screening-level guidance” vs “quantitative prediction”) until at least one validation comparison is shown.

Score note: I am keeping **7/10** for writing/LaTeX/reference hygiene as of the current draft; however, figure/narrative clarity will remain capped until (i) convergence reporting is made audit-friendly, (ii) the negative-shelter terminology is repaired, and (iii) at least one uncertainty band is plotted.

---

## Addendum (2026-03-06, latest): STATISTICIAN\_004 + current compiled artifacts

Since the prior addenda, a new review (`STATISTICIAN_004_REVIEW.md`, timestamped 2026-03-06) reports substantial progress: restarts to 3000 iterations, explicit negative-shelter discussion (Jensen/Venturi), S-effect mechanism prose, and an uncertainty band on the deposition-vs-clearance plot. I verified that the *current* working tree reflects these improvements in `manuscript/main.tex`, and that `manuscript/main.pdf`/`manuscript/main.log` were regenerated on **2026-03-06 06:57 UTC** (PDF now **31 pages**).

### What is now clearly resolved (presentation-facing)

- **Negative shelter efficiency is now acknowledged and explained**: Section titled “Flow amplification, spacing effects, and the Jensen inequality” is present and reads clearly; the abstract and conclusions also reflect this.
- **Row-spacing effect direction now has mechanism prose** (no longer reads like a sign error).
- **At least one key uncertainty visualization exists** (per STAT\_004, C-range band on the deposition-vs-clearance figure). This addresses the “text-only uncertainty” optics problem flagged in JUDGE\_002/JUDGE\_003.

### Remaining editor-facing issues to fix (still)

1) **“Shelter efficiency” naming still clashes with negative values**  
Even with the new Section 7.3, the term “shelter efficiency” is still used for a quantity that can be negative by design. Strong recommendation remains: switch to a sign-agnostic term (e.g., “flux modification ratio” or “array flux amplification factor”) and keep “shelter” for strictly attenuating quantities.

2) **Case-level reliability disclosures** (reader trust)  
STAT\_004 reports: 30/36 formally converged; 6 tight-spacing cases did not; case\_34 stagnates at `p_init ~ O(10^{-3})`; case\_01 appears to have a postprocessing/time-directory integrity issue. These are not just “methods”: they affect how a reviewer interprets the extremes shown in heatmaps/summary metrics. Ensure the manuscript explicitly flags:
  - the set of non-formally-converged cases (and how treated in figures), and
  - the special status of case\_34 if it drives an extremum.

3) **Persistent `hyperref` PDF-string warnings**  
`manuscript/main.log` still shows repeated “Token not allowed in a PDF string (Unicode)” warnings. Clean these for submission polish; they typically come from author/corresponding-author macros entering bookmarks.

4) **Elsevier front-matter completeness still missing**  
I still do not see:
  - **CRediT author contribution statement**, or
  - **Highlights** / **Graphical abstract** environments.  
Whether these are mandatory depends on Solar Energy’s submission route, but if required, their absence is an avoidable desk-reject risk.

5) **Layout report inconsistencies**  
`manuscript/layout_report.md` generated **2026-03-06 06:59 UTC** reports **32 pages**, while `pdfinfo manuscript/main.pdf` reports **31 pages**. The tool also continues to treat ~90%+ page “white%” as CRITICAL, which appears miscalibrated for papers. Use the report for *relative*/specific defect detection, not the headline CRITICAL count, until the metric is corrected.

Updated score (presentation only, current compiled state): 7.5/10

---

## Addendum (2026-03-06, most recent): JUDGE\_004 + STATISTICIAN\_005 + updated front matter

New reviews (`JUDGE_004_REVIEW.md`, `STATISTICIAN_005_REVIEW.md`) and the latest compiled artifacts (PDF regenerated **2026-03-06 07:45 UTC**) indicate additional substantive progress that affects presentation/completeness.

### Newly resolved items (since the last editor addendum)

- **CRediT statement added**: `\section*{CRediT authorship contribution statement}` now exists in `manuscript/main.tex`. This closes a front-matter completeness gap.
- **`hyperref` warnings appear resolved**: the prior “Token not allowed in a PDF string” warnings no longer appear in the latest `manuscript/main.log` (based on grep check). Good submission polish improvement.
- **Flow validation section added (qualitative)**: STAT\_005 reports a new Section 5.2 and a new wake-profile figure (`F3_validation_wake_profiles`). Even without a point-by-point wind-tunnel comparison, this materially improves narrative credibility and helps readers connect the Jensen/Venturi discussion to an observable wake structure.
- **Case integrity/caveats improved**: STAT\_005 reports case\_01 integrity fixed and case\_34 now has an explicit convergence caveat where its extreme value is cited.

### Remaining editor-facing issues (still worth fixing)

1) **Highlights / Graphical abstract**  
I still do not see `highlights` or `graphicalabstract` environments in `manuscript/main.tex`. Whether mandatory depends on Solar Energy’s workflow, but these are common Elsevier submission requirements; confirm and include if required.

2) **Terminology: “shelter efficiency” vs negative values**  
Even with the strong Section 7.3 discussion, the phrase “shelter efficiency” remains semantically awkward for a metric that is negative in many cases. Renaming to a sign-agnostic term would reduce reviewer friction and improve readability.

3) **Page-count optics and tool mismatch**  
`pdfinfo manuscript/main.pdf` now reports **34 pages**, while `manuscript/layout_report.md` reports **35 total pages** and **29 content pages excluding references** (references start at page 30). Content length looks comfortably within a 35-page (excl. refs) ceiling, but the persistent PDF-vs-report mismatch suggests the layout tool’s page counting should be checked before relying on it for hard limits.

Updated score (presentation only, given the added CRediT + resolved hyperref warnings + wake-validation figure): 8/10
