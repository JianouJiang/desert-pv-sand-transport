# STATISTICIAN REVIEW 005 -- Ronald Fisher

**Paper**: Array Layout Controls Sand Fate: CFD--Aeolian Modeling of Wind-Sand Transport in China's Desert Photovoltaic Mega-Bases
**Date**: 2026-03-06
**Reviewer**: statistician-fisher (Statistical Methods and Data Analysis Review)
**Previous reviews**: STAT_001 (2/10), STAT_002 (5/10), STAT_003 (5/10), STAT_004 (6/10)

---

## CONTEXT

Since STATISTICIAN_004, three new reviews were posted (EDITOR_001 at 7.5/10, ILLUSTRATOR_001 at 8/10, JUDGE_004 at 5/10) and the manuscript has been substantially updated (07:33 UTC). The most significant change is the addition of a **panel-wake validation section** (Section 5.2) with a new figure (F3_validation_wake_profiles). Additionally, case 01's data integrity issue has been resolved, and case 34 now carries a convergence caveat where its extreme value is cited.

---

## STATUS OF STATISTICIAN_004 ITEMS

| # | STAT_004 Item | Priority | Status | Notes |
|---|---|---|---|---|
| 1 | Flag case 34 in manuscript | Tier 1 | **DONE** | Line 377: "this case did not formally converge; see Fig.~\ref{fig:heatmap} caption" |
| 2 | Fix case 01 data integrity | Tier 1 | **DONE** | JSON updated: case 01 now at 3000 iterations, shelter_eff = -0.113. 3000 time directory confirmed. |
| 3 | Correct "O(10^-4)" characterization | Tier 1 | **DONE** | Line 145 already separates case 34 as O(10^-3); remaining five at O(10^-4). Acceptable. |
| 4 | Experimental validation case | Tier 2 | **PARTIALLY** | Qualitative wake validation added (Section 5.2); no quantitative comparison with published data |
| 5 | Extend case 28 by 1000 iterations | Tier 2 | NOT DONE | Low priority |
| 6 | Fix check_convergence parser | Tier 3 | **DONE** | JSON now correctly reports case 01 at 3000 iterations |
| 7 | Run H=0.05m case | Tier 3 | NOT DONE | |

**Summary: 4 of 7 fully done, 1 partially done, 2 not done. All Tier 1 items resolved.**

---

## WAKE VALIDATION ASSESSMENT (New Section 5.2)

### What was added

Section 5.2 "Panel-wake structure" (main.tex:232--242) extracts vertical velocity profiles at x/Hp = 1, 2, 3 behind the first panel row of the S=6Hp reference case (H=0.5 m, theta=25 deg). The figure (F3_validation_wake_profiles) shows:

- **(a) Absolute velocity profiles**: upstream log-law (green circles) matches the analytical profile. At x/Hp = 1, the wake exhibits a pronounced velocity deficit in the panel zone (z = 0.5--1.35 m) with near-zero or negative velocities indicating recirculation. By x/Hp = 3, the minimum velocity is positive, indicating reattachment within 2--3 Hp.

- **(b) Normalized profiles (U/U_upstream)**: below the panel (z < H), all three downstream stations show U/U_upstream > 1 near the ground, confirming the Venturi acceleration mechanism that drives the friction velocity amplification.

### Statistical assessment

**Strengths:**

1. The figure demonstrates the solver captures four distinct flow physics modes: (i) separation behind the panel, (ii) recirculation in the immediate wake, (iii) wake recovery and reattachment, and (iv) sub-panel Venturi acceleration. These are the physical mechanisms that underpin the entire parametric study.

2. The normalized profiles (panel b) directly connect to the paper's central finding: U/U_upstream > 1 below the panel is the Venturi effect that drives the u* amplification factors and the Jensen inequality mechanism (Section 7.3). This provides visual evidence that the physics discussed in the paper is real.

3. The reattachment length (2--3 Hp) is stated to be "within the expected range for RANS k-epsilon models," which is a correct characterization based on the CFD literature.

**Limitations (acknowledged in the paper):**

1. **No comparison with published data.** The text explicitly states: "Quantitative comparison with published wind-tunnel data for PV panel arrays (Jubayer and Hangan, 2016) is not pursued because the geometry and boundary conditions differ." This is an honest statement but leaves the quantitative accuracy unbounded.

2. **Self-validation only.** The profiles are from the paper's own simulation -- they demonstrate internal consistency and qualitative correctness, not predictive accuracy against independent measurements.

3. **No error metrics.** There is no RMSE, R^2, or any quantitative comparison metric. The reader cannot judge *how accurate* the solver is, only that it captures the *right physics*.

### Is the geometry-mismatch justification valid?

The paper argues that quantitative comparison with Jubayer & Hangan (2016) is not pursued because "the geometry and boundary conditions differ." This is partially valid:

- Jubayer & Hangan used 3D panels (not 2D baffles), different panel dimensions, and a wind tunnel ABL (not Richards-Hoxey)
- Exact replication would require building a new mesh with their geometry

However, the standard approach in computational wind engineering is to replicate published cases (even with different geometry) to demonstrate model competence. The AIJ guidelines (already cited in the paper) explicitly recommend validating against benchmark datasets. The fact that the geometry differs is the *reason* for validation, not a reason to avoid it -- a 2D k-epsilon model's ability to predict wake structure behind a flat inclined plate is precisely what needs bounding.

**Net assessment**: The qualitative wake validation is a significant improvement over the previous state (no panel-flow validation at all). It demonstrates solver competence for the relevant physics. However, it does not bound the quantitative error. For a parametric screening study (which this paper now honestly frames itself as), qualitative validation is arguably sufficient. For a paper claiming quantitative design guidance (nomogram with specific H values), quantitative validation would strengthen the credibility substantially.

I credit this as approximately half of what was requested: it addresses the "does the solver capture wake physics?" question but not the "how accurately?" question.

---

## CASE 01 DATA INTEGRITY: RESOLVED

The openfoam_results.json (timestamp 06:56 UTC) now reports case 01 at 3000 iterations with shelter_eff = -0.113 (was -0.114 from iteration-2000 data). The 3000 time directory now exists. The change in shelter efficiency is 0.001 (< 1%), confirming the practical convergence claim.

This closes my STAT_004 Tier 1 item #2.

---

## CASE 34 CAVEAT: PROPERLY INTEGRATED

Line 377 now reads: "for H=0.8 m, theta=35 deg, and S=2Hp, the array-averaged flux is 3.7x the undisturbed upstream value (this case did not formally converge; see Fig.~\ref{fig:heatmap} caption)."

This is exactly the parenthetical caveat I recommended. The reader is now explicitly warned that the most extreme value in the dataset comes from a case with convergence limitations.

---

## ADDITIONAL MANUSCRIPT IMPROVEMENTS (NEW SINCE STAT_004)

1. **Tight-spacing warning propagated to design recommendation** (line 354): "tight row spacing (S=2Hp) should be avoided even in the pass-through regime, because the Venturi-induced flow acceleration amplifies ground-level sand flux (Section 7.3), increasing both foundation erosion risk and soiling of downstream rows." This directly addresses STAT_004's suggestion and JUDGE_004's HIGH item #3.

2. **Lagrangian deviation acknowledged** (limitation #4): "Lagrangian particle tracking would resolve the transient saltation response to the rapidly varying flow field within the array, including overshoot/undershoot effects near panel edges, but at substantially greater computational cost." This addresses JUDGE_004's MEDIUM item #7.

3. **CRediT authorship statement** added (line 427). This addresses EDITOR_001's submission checklist item.

4. **Limitation #8 updated** to reference the new wake validation section: "The flow validation (Section 5.2) confirms qualitative wake structure but does not include a quantitative point-by-point comparison."

---

## CROSS-REVIEWER CONSENSUS CHECK

All five reviewers have now posted at least one review. The consensus picture:

| Issue | JUDGE | STAT | EDITOR | ILLUSTR | Status |
|---|---|---|---|---|---|
| Convergence (30/36) | Addressed | Addressed | Noted | -- | RESOLVED |
| Negative shelter discussion | Excellent | Excellent | Good | Good | RESOLVED |
| Jensen's inequality | Excellent | Excellent | -- | -- | RESOLVED |
| Uncertainty on F9b | Done | Done | Done | Done | RESOLVED |
| Case 34 flagged | Done | Done | -- | Partial | RESOLVED |
| Panel-wake validation | Partial | Partial | -- | -- | **QUALITATIVE ONLY** |
| Quantitative validation (RMSE) | NOT DONE | NOT DONE | Noted | -- | **OPEN** |
| Shelter efficiency terminology | Recommended | -- | Recommended | -- | **OPEN** |
| F2(b) convergence plot upgrade | -- | -- | -- | Noted | OPEN (minor) |
| u_ref=14 / H=0.05 cases | NOT DONE | NOT DONE | -- | -- | OPEN (minor) |

The paper has resolved its critical structural deficiencies. The remaining open items are either enhancement-level (terminology, additional cases) or the quantitative validation that would elevate it from "adequate" to "strong."

---

## REMAINING GAPS (REFINED)

### HIGH: Quantitative Flow Validation (Downgraded from CRITICAL)

The qualitative wake validation (Section 5.2) is sufficient to demonstrate solver competence for the relevant physics. However, the paper could still be strengthened by:

1. **Option A (preferred, ~2 hours)**: Replicate the Jubayer & Hangan (2016) geometry in a separate validation case. Extract velocity profiles at their measurement stations. Report RMSE for U/U_ref at each station. This provides an independent credibility anchor.

2. **Option B (acceptable, ~30 min)**: Extract the reattachment length from the current wake profiles (define as the x-distance where the minimum U in the panel zone first becomes positive). Compare this value against published correlations for inclined flat plates (e.g., Fage & Johansen 1927 for normal plates, or the Tominaga 2008 compilation for bluff-body RANS). Report the comparison quantitatively: "the simulated reattachment length of X Hp falls within / above / below the range Y--Z Hp reported for similar configurations."

Option B requires no new simulations and provides a quantitative number that bounds the solver's accuracy for the key flow feature.

### MEDIUM: Rename "Shelter Efficiency" (Unchanged from EDITOR)

Still recommended by EDITOR_001 and JUDGE_004. When 21/36 cases have negative "efficiency," the term creates unnecessary confusion. Consider "flux modification factor" or simply use Q_array/Q_upstream with appropriate annotation.

### LOW: Additional Parametric Cases

Running one case at u_ref=14 m/s and one at H=0.05 m would strengthen the sensitivity analysis and capture regime, respectively. These are ~15 minutes each but are not critical for the paper's core claims.

---

## SCORING

### Improvements Since STAT_004

| Change | Impact |
|---|---|
| Wake validation section (qualitative) | +0.5 (half of the +1.0 for quantitative) |
| Case 01 data integrity fixed | +0.15 |
| Case 34 caveat in Section 7.3 | +0.15 |
| Tight-spacing warning in design section | +0.10 |
| Lagrangian deviation in limitations | +0.10 |

### Score Trajectory

| Review | Score | Key Driver |
|---|---|---|
| STAT_001 | 2/10 | Python solver, no simulation data |
| STAT_002 | 5/10 | OpenFOAM pipeline, 36 cases, but 31 unconverged and no discussion of negative shelter |
| STAT_003 | 5/10 | Stalled -- restarts pending, key discussion missing |
| STAT_004 | 6/10 | 30/36 converged, Jensen's inequality, uncertainty bands, S-effect mechanism |
| STAT_005 | **7/10** | Qualitative wake validation, case fixes, discussion refinements |

### Path to Higher Scores

- **7/10 -> 7.5/10**: Add a quantitative reattachment-length comparison (Option B above, ~30 min). This requires no new simulations and provides a number that bounds the model's accuracy.
- **7.5/10 -> 8/10**: Full quantitative validation against published data (Option A, ~2 hours), OR run the u_ref=14 m/s sensitivity case plus rename "shelter efficiency" to a sign-agnostic term.

---

**Score: 7/10**

The paper has crossed the threshold from "major revision" to "minor revision with specific requirements." The qualitative wake validation demonstrates solver competence for the relevant physics (separation, reattachment, Venturi acceleration). The case-level data integrity issues are resolved. The discussion section is now one of the paper's strengths, with the Jensen inequality mechanism properly explained and the design implications correctly propagated. The quantitative accuracy of the flow field remains unbounded, but the paper honestly frames itself as a screening study rather than a precision prediction tool. A 30-minute reattachment-length comparison would close the last significant gap.
