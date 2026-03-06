# Worker Progress Report

**Last updated:** 2026-03-06 10:00 (Round 10 — STAT_005 quantitative reattachment)
**Status:** COMPLETE — Quantitative reattachment length added to Section 5.2, manuscript recompiled

## Reviews Addressed This Round (Round 10)

### STATISTICIAN_005_REVIEW (7/10)
- [DONE] **Quantitative reattachment length (Option B)**: Extracted reattachment point from wake profiles — Lr = 2.6 Hp (2.2 m). Compared against AIJ guidelines (Tominaga et al., 2008): RANS k-epsilon overpredicts by 30-50%, implying true Lr ~ 1.7-2.0 Hp. Added to Section 5.2.
- [DONE] **Ground-level acceleration quantified**: Added specific numbers to Section 5.2: +31% at x/Hp=1, +15% at x/Hp=2, +1% at x/Hp=3.
- [NOTED] **Shelter efficiency rename**: MEDIUM priority. Term already clearly defined with sign convention at first use (Section 7.1, line 345) and in Section 7.3 (line 377). Abstract avoids the term entirely, using sign-agnostic language. Current wording is adequate.
- [NOTED] **Additional parametric cases**: LOW priority. H=0.05m and u_ref=14 m/s remain deferred.

### STAT_005 Path to Higher Score
- Current: 7/10 → 7.5/10 with reattachment length comparison (DONE this round)
- 7.5/10 → 8/10: requires full quantitative validation (Jubayer & Hangan) OR u_ref=14 sensitivity + rename shelter efficiency

## Previous Rounds Summary

| Review | Initial | Latest | Key Actions |
|--------|---------|--------|-------------|
| JUDGE_001 | 2/10 | -- | OpenFOAM pipeline |
| JUDGE_002 | 4/10 | -- | Convergence restarts, uncertainty discussion |
| JUDGE_003 | 4/10 | -- | 30/36 converged, negative shelter, Jensen's inequality |
| JUDGE_004 | 5/10 | -- | Flow validation figure, design warning, case_34 caveat |
| STAT_001 | 2/10 | -- | GCI table, uncertainty documentation |
| STAT_002 | 5/10 | -- | F9b uncertainty bands, S-effect mechanism |
| STAT_003 | 5/10 | -- | Consensus items |
| STAT_004 | 6/10 | -- | Case_34 flagged, case_01 fixed, case_28 extended, parser fix |
| STAT_005 | 7/10 | -- | Quantitative reattachment length, ground-level acceleration numbers |
| EDITOR_001 | 6/10 | 7.5/10 | LaTeX fixes, CRediT, hyperref, dong2004flow |
| ILLUSTRATOR_001 | 6/10 | 8/10 | F2(b) GCI, F6 hatching+legend, F9b bands |
| FALLBACK | -- | -- | False positives verified |

## Simulation Status
- **36/36 cases complete**
- **30/36 formally converged** (all initial residuals < 2×10^-4)
- **6 unconverged**: all S=2Hp; case_34 visually flagged with red border in F6

## Manuscript Status
- **34 pages**, 13 figures (12 original + F3 validation)
- **0 undefined refs, 0 BibTeX warnings, 0 hyperref warnings**
- 25 bib entries, all cited
- CRediT statement present
- Section 5.2: Quantitative reattachment length (Lr = 2.6 Hp) + AIJ comparison + ground-level acceleration numbers
- Section 7.3: Jensen's inequality + negative shelter mechanism
- F2(b): GCI error bars + Richardson extrapolation
- F3: Panel-wake velocity profiles (validation)
- F6: hatching legend + case_34 red border
- F9b: C-uncertainty bands
- Compiles cleanly

## Outstanding Items (Deferred)
1. Jubayer & Hangan (2016) full experimental validation case (~2-3 hrs effort)
2. H=0.05m capture-regime confirmation case (~30 min)
3. One additional wind speed (u_ref=14 m/s) for Re-independence check (~15 min)
4. Dedicated amplification map figure (Illustrator nice-to-have)
5. Highlights / Graphical abstract (if required by Solar Energy submission)
