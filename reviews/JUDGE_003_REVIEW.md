# JUDGE REVIEW 003 -- Charlie Munger

**Paper**: Array Layout Controls Sand Fate: CFD--Aeolian Modeling of Wind-Sand Transport in China's Desert Photovoltaic Mega-Bases
**Date**: 2026-03-06
**Reviewer**: judge-munger (Inversion Review)
**Previous reviews**: JUDGE_001 (2/10), JUDGE_002 (4/10)

---

## VERDICT: STALLED -- JUDGE_002 CRITICAL ITEMS NOT ADDRESSED

Since JUDGE_002, the manuscript has received cosmetic improvements (abstract S-effect wording corrected, uncertainty paragraph added to Section 6, F11 tornado chart) but the three CRITICAL items from JUDGE_002 remain substantially unaddressed. The Statistician_002 review identified a major new finding (negative shelter efficiency in 21/36 cases) that the paper ignores. This review does NOT repeat the full audit from JUDGE_002 -- it focuses on what has changed and what has not.

---

## JUDGE_002 CRITICAL ITEMS -- STATUS UPDATE

| # | JUDGE_002 Item | JUDGE_002 Status | Current Status | Change |
|---|---|---|---|---|
| C1 | Re-run 31 unconverged cases (endTime 2000→3000) | CRITICAL | **NOT DONE** | No change |
| C2 | Add experimental validation with panels (Jubayer 2016) | CRITICAL | **NOT DONE** | No change |
| C3 | Add uncertainty bounds on figures | CRITICAL | **PARTIALLY** | Text discusses uncertainty; tornado chart added (F11b); no envelope curves on F9b |
| H4 | Correct abstract S-effect wording | HIGH | **DONE** | "negligible" → "modest but measurable (factor 2-3)" |
| H5 | Run Lagrangian tracking for 3 cases | HIGH | **NOT DONE** | No change |
| H6 | Discuss fine-mesh anomaly prominently | HIGH | **DONE** | main.tex:297 states "factor-of-two uncertainty from mesh resolution alone" |
| M7 | Run one additional wind speed | MEDIUM | **NOT DONE** | No change |
| M8 | Add intermediate H values (0.15, 0.4m) | MEDIUM | **NOT DONE** | No change |

**Summary: 2 of 8 items fully addressed, 1 partially addressed, 5 not addressed. Zero CRITICAL items fully resolved.**

---

## 1. CRITICAL (Reiterated): 31/36 Cases Still Unconverged

The cases have NOT been re-run. My analysis of the INITIAL residuals (which is what SIMPLE's `residualControl` checks) at iteration 2000 shows:

| Category | Count | Description |
|---|---|---|
| Formally converged | 5 | All initial residuals < 2e-4 |
| Nearly converged (all init < 3e-4) | ~11 | Would converge with 500-1000 more iterations |
| Moderately unconverged (some init 3-5e-4) | ~12 | Need 1000+ more iterations |
| Clearly unconverged (any init > 5e-4) | ~8 | May need solver tuning or relaxation adjustment |

**Worst case**: case_34 (H=0.8, T35, S2Hp) has p_init = **2.9e-3** at iteration 2000 -- this is **14.5x above the convergence criterion**. The results from this case are unreliable.

The Statistician_002 correctly notes that the FINAL residuals (post linear-solver) are O(10^-5 to 10^-6), well below the criterion. This is reassuring for most cases. However, the initial residuals (what SIMPLE actually monitors) show that:
- The pressure field in many cases has not stabilized
- The discrepancy between initial and final residuals indicates the linear solver is working hard each iteration, which signals incomplete outer-loop convergence
- **Extending endTime to 3000 is a 12-minute wall-time fix per case** (the coarse mesh runs at ~0.36 s/iteration on 4 procs). Total: ~6 hours for 31 cases. This is trivial.

**This is the single easiest fix with the highest impact on paper credibility.** I reiterate: do it.

---

## 2. CRITICAL (Reiterated): No Experimental Validation With Panels

Third consecutive review flagging this. The Statistician_002 also flags it as MEDIUM priority #7, the Editor_001 notes it, and the Illustrator_001 suggests showing validation comparison. This is now the consensus across ALL reviewers.

The manuscript's limitation #8 acknowledges: "Quantitative validation against multi-row array experiments with particle deposition is not available in the open literature" (main.tex:379). This is honest but does not excuse the absence of FLOW validation.

Published velocity profiles behind PV arrays DO exist:
- **Jubayer & Hangan (2016)**: Wind tunnel, multiple panel rows, velocity and turbulence profiles at x/H = 1, 3, 5 downstream
- **Shademan et al. (2014)**: 3D panel array, Cp and velocity

The paper validates only ABL profile preservation on flat terrain (trivial). One case comparing velocity profiles downstream of a single panel row to Jubayer & Hangan (2016) data would:
1. Demonstrate the k-epsilon solver captures separation physics
2. Quantify the expected error (typically 20-40% for k-epsilon behind bluff bodies)
3. Provide a credibility anchor for all 36 parametric results

**Time estimate**: 1 case setup (~30 min), 1 run (~12 min), 1 figure (~1 hour). Total: <2 hours. This is the highest-ROI improvement remaining in the paper.

---

## 3. CRITICAL (New, from Statistician_002): Negative Shelter Efficiency Undiscussed

The Statistician_002 identified that **21 of 36 cases show negative shelter efficiency** -- meaning the panel array AMPLIFIES ground-level sand flux rather than reducing it. Example:

- H=0.5, theta=25, S=4Hp: shelter efficiency = -0.42 (Q_array is 1.42x Q_upstream)
- H=0.8, theta=35, S=2Hp: shelter efficiency = -2.66 (Q_array is 3.66x Q_upstream)

**The paper does not discuss this finding.** The implications are profound:

1. **The word "shelter" is misleading.** The paper uses "shelter efficiency" and "shelter ratio" as if panels always reduce sand transport. For 58% of configurations tested, they INCREASE it.

2. **The mechanism is physically significant.** Panels create Venturi-like flow acceleration at their leading edges (u* amplification peaks of 1.5-1.9x visible in F5). Since Q ~ u*^3 (Owen flux), a 1.75x velocity peak produces a 5.4x flux peak. The spatial average of Q is dominated by these peaks (Jensen's inequality: E[u*^3] > E[u*]^3 when u* varies spatially). The mean wind speed can decrease while the mean sand flux increases.

3. **This is a genuine CFD finding** that cannot be obtained from analytical models. The analytical model assumes uniform u* everywhere. The CFD reveals that panels create localized acceleration zones that amplify net sand flux. This is arguably the paper's most interesting physical insight, and it is completely absent from the discussion.

4. **It affects the design recommendation.** The paper says "configurations with H < 0.15m should be avoided" (main.tex:337). But the negative shelter data shows that even at H = 0.5-0.8m with S = 2Hp, the panels amplify ground-level transport. This means tight row spacing is problematic even in the "pass-through" regime -- not for panel soiling, but for ground erosion.

**Recommendation**: Add a subsection to the Discussion (Section 7) titled "Flow amplification and the Jensen effect" (or similar). Explain:
- Why 21/36 cases show Q_array > Q_upstream (Venturi acceleration + cubic nonlinearity)
- That "shelter" is not universal -- it depends on spacing and clearance
- How the design nomogram should account for this (wider spacing reduces amplification)
- The physical cause: localized acceleration peaks dominate the spatial average of Q because of the u*^3 nonlinearity

This transforms a model limitation into a scientific finding.

---

## 4. HIGH (New): F8 Shows Q/Q_ref > 1 for Most Cases -- Not Acknowledged

Figure F8 shows that the normalized sand flux Q/Q_ref EXCEEDS 1.0 for the first 1-3 rows at ALL ground clearance values:

| H | Q/Q_ref at row 1 | Q/Q_ref at row 8 |
|---|---|---|
| 0.1m | ~2.5 | ~0.05 |
| 0.3m | ~2.9 | ~0.05 |
| 0.5m | ~2.8 | ~0.1 |
| 0.8m | ~2.9 | ~0.8 |

The text (main.tex:312) says "Per-row flux variations reflect local flow acceleration and sheltering effects" -- this is a correct but anodyne description of a dramatic result. The first 2-3 rows of EVERY configuration experience AMPLIFIED sand transport (2.5-3x the undisturbed level). Only further into the array does sheltering dominate.

**This finding directly supports the Statistician's negative shelter efficiency observation** -- the front rows amplify while interior rows shelter, and the net effect depends on which dominates.

**Recommendation**: State explicitly that the first 2-3 rows act as flux amplifiers due to flow acceleration, while interior rows experience sheltering. The cross-over row number depends on H and S. This row-resolved picture is more informative than the array-averaged "shelter efficiency" metric.

---

## 5. HIGH: Case 34 Has Clearly Unreliable Results

Case 34 (H=0.8, theta=35, S=2Hp) has a pressure initial residual of **2.9e-3** at the 2000th iteration -- 14.5x above the convergence criterion. This is not "nearly converged"; it indicates an ongoing convergence difficulty, possibly related to the tight spacing combined with large panels at high tilt creating strong flow acceleration.

This case's results are included in the heatmap (F6, bottom-left cell of the theta=35 panel) and the shelter efficiency data. Its shelter efficiency of -2.66 is the most extreme value in the parametric study and drives the Statistician's finding.

**Recommendation**: Either re-run this case with tighter relaxation factors (p=0.3, U=0.5) and extended iterations, or flag it as unconverged and exclude it from quantitative analysis. Report which cases met the convergence criterion and which did not.

---

## 6. HIGH (Reiterated): No Uncertainty Bands on Key Figures

The text now discusses uncertainty qualitatively (C factor-of-5, u*t +/-15%, mesh factor-of-2). The F11b tornado chart is a useful addition showing relative parameter importance. But:

- **F9b** (panel deposition vs H -- the central quantitative figure) still shows single lines with no error bands
- **F10** (design nomogram) shows regime boundaries as crisp lines with no uncertainty width
- **F6** (parametric heatmap) values carry unacknowledged +/-0.4 log units mesh uncertainty

The Statistician_002 states: "The regime boundaries are insensitive to C (correctly stated in the text), so the bands narrow to lines at the regime transitions." This is exactly right -- the REGIME boundaries are robust, but the DEPOSITION VALUES at each point carry factor-of-5 uncertainty. The figures should show this.

At minimum: add a shaded band to F9b showing the C=[0.1, 0.5] range (deposition is linear in C, so the band is simply the current line x0.4 and x2.0). This is ~5 lines of matplotlib code.

---

## 7. MEDIUM: S-Effect Mechanism Not Explained

The Statistician_002 identified that the S-effect direction CONTRADICTS the original plan's hypothesis:

- **Plan predicted**: Tight spacing → more shelter → less deposition downstream (favorable)
- **CFD shows**: Tight spacing → more Venturi acceleration → higher Q_array → MORE deposition (unfavorable)

The paper reports the result (F6 shows wider spacing decreases deposition) but does not explain the mechanism. This is scientifically interesting: the dominant S-effect pathway is NOT inter-row shelter but rather flow acceleration amplitude, which increases with tighter spacing.

**Recommendation**: One paragraph in the Discussion explaining why wider spacing DECREASES panel deposition despite providing less inter-row shelter. The acceleration effect (amplified Q_array at tight S) overwhelms the shelter effect (reduced Q_array at wide S) because Q ~ u*^3.

---

## 8. MEDIUM: Sensitivity Study Is Purely Analytical Curves

F11a shows exp(-H/lambda_s) for three wind speeds. These are ANALYTICAL curves, not CFD results. The sensitivity to wind speed is entirely captured by the formula lambda_s = 2*u*^2/g. No additional OpenFOAM cases were run at different wind speeds.

This was flagged in JUDGE_002 (item M7) and remains unchanged. While the analytical approach is justified (the shelter amplification pattern is approximately Re-independent), running ONE case at u_ref=14 m/s to confirm this assumption would take 12 minutes and substantially strengthen the sensitivity claim.

---

## WHAT HAS GENUINELY IMPROVED SINCE JUDGE_002

1. **Abstract S-effect wording corrected**: "negligible" → "modest but measurable (factor of 2-3)" -- accurate and honest.

2. **Section 6 analytical-vs-CFD attribution**: "The H-dependence is driven primarily by the analytical concentration profile (exp(-H/lambda_s)), while the CFD contributes the shelter-modified ground flux Q_array" (main.tex:286). This is the exact statement I recommended in JUDGE_002 item #5. Good.

3. **Uncertainty paragraph in Section 6**: Discusses GCI 4.3-9.7%, fine-mesh factor-of-2 discrepancy, Owen C factor-of-5. States these "affect absolute deposition rates but not regime classification." This is accurate and important.

4. **F11b tornado chart**: Shows parameter importance ranking visually. H dominates by 4+ log units; C uncertainty is ~1.3 log units; theta and S are ~0.5 each. Informative.

5. **"and others" removed from references**: Bib entries now have full author lists.

6. **Limitations section comprehensive**: 8 items, including the key admission "Quantitative validation against multi-row array experiments with particle deposition is not available."

---

## FOUR PILLAR EVALUATION

### NOVELTY (20%): 4/10
Unchanged from JUDGE_002. The regime-transition framework has CFD backing from the OpenFOAM shelter patterns. The negative shelter efficiency finding (21/36 cases) would be a GENUINELY novel insight if discussed -- the Venturi-Jensen mechanism is not in the aeolian PV literature. Currently undiscussed, so no novelty credit.

### PHYSICS DEPTH (40%): 4/10
Unchanged from JUDGE_002:
- k-epsilon resolves separation and acceleration patterns (F5)
- Row-by-row flux depletion shows real shelter cascading (F8)
- S-dependence enters through CFD-modulated Q_array
- But: 31/36 cases formally unconverged (case_34 clearly unreliable)
- No Lagrangian particle tracking
- No experimental validation of flow around panels
- Negative shelter finding not discussed (a physics insight being wasted)

### CONTRIBUTION (30%): 4/10
Unchanged. The design nomogram is backed by real CFD through amplification factors. Uncertainty is discussed textually but not propagated to figures. The paper provides actionable guidance (H > 0.4m) but quantitative accuracy is unvalidated. The negative shelter finding could significantly strengthen the contribution if incorporated.

### RELEVANCY (10%): 7/10
Unchanged. Topic directly relevant to Solar Energy.

---

## ACTIONABLE ITEMS -- FINAL PRIORITY LIST

The paper has been through 3 judge reviews and 2 statistician reviews. The remaining items are well-defined and finite. Here is the consolidated priority list:

### CRITICAL (3 items -- all previously identified, none resolved)

1. **Re-run 31 unconverged cases with endTime=3000** (~6 hours total compute). Flag case_34 for solver tuning. Report convergence status for all 36 cases.

2. **Add one experimental validation case** against Jubayer & Hangan (2016) velocity profiles. Report RMSE. (~2 hours total effort.)

3. **Discuss the negative shelter efficiency finding.** 21/36 cases show Q_array > Q_upstream. Explain the Venturi-Jensen mechanism. Rename "shelter efficiency" to "flux modification ratio" or similar. This transforms a gap into a finding.

### HIGH (3 items)

4. **Add uncertainty band to F9b** (deposition vs H): shaded region for C=[0.1, 0.5]. ~5 lines of code.

5. **Explain the S-effect mechanism**: wider spacing decreases deposition because it reduces Venturi acceleration (lower Q_array), not because it increases inter-row shelter. One paragraph.

6. **Discuss F8 amplification finding**: first 2-3 rows amplify flux (Q/Q_ref > 1) for all configurations. Interior rows shelter. Cross-over row depends on geometry.

### MEDIUM (2 items)

7. **Run one case at u_ref=14 m/s** to validate Re-independence of amplification factors. 12 minutes.

8. **Run one case at H=0.05m** to confirm capture regime behavior (currently unsampled).

---

## SUMMARY

The paper has made genuine progress since JUDGE_001 (2/10 → 4/10 in JUDGE_002). Since JUDGE_002, improvements are limited to text refinements (abstract, uncertainty paragraph, tornado chart). The three CRITICAL items from JUDGE_002 -- convergence, validation, uncertainty bands -- remain unaddressed.

The Statistician_002 review identified a major new finding that the paper misses entirely: 21/36 cases show NEGATIVE shelter efficiency (panels amplify sand flux due to Venturi acceleration + Jensen's inequality on u*^3). This is the paper's most interesting physical insight, and it sits unused in the post-processed data.

The remaining work is well-defined and tractable:
- Convergence fix: ~6 hours compute (background)
- Validation case: ~2 hours
- Negative shelter discussion: ~1 hour of writing
- Uncertainty band on F9b: ~30 minutes
- S-effect explanation: ~30 minutes

Total estimated effort: ~10 hours. The paper currently sits at the boundary of "reject" and "major revision." These fixes would push it solidly into "major revision" territory.

---

**Score: 4/10**

Unchanged from JUDGE_002. The text improvements are appreciated but cosmetic. The structural deficiencies (convergence, validation, negative shelter, uncertainty) are unchanged. The score will increase when the CRITICAL items are addressed -- specifically, when the 31 cases are reconverged, the validation case is added, and the negative shelter efficiency finding is discussed. Each of these alone could add 0.5-1.0 points.
