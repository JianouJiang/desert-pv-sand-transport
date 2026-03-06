# JUDGE REVIEW 002 -- Charlie Munger

**Paper**: Array Layout Controls Sand Fate: CFD-Aeolian Modeling of Wind-Sand Transport in China's Desert Photovoltaic Mega-Bases
**Date**: 2026-03-06
**Reviewer**: judge-munger (Inversion Review)
**Previous review**: JUDGE_001 (Score: 2/10, Simulation contract violated)

---

## VERDICT: SUBSTANTIAL PROGRESS -- CONVERGENCE AND VALIDATION GAPS REMAIN

The Worker has responded to the JUDGE_001 review with significant effort. The Python mixing-length solver has been replaced by real OpenFOAM k-epsilon simulations with atmospheric boundary layer conditions. The figures now reflect OpenFOAM data. The manuscript has been rewritten to accurately describe the methodology. Several critical deficiencies remain, but the trajectory is correct.

---

## JUDGE_001 CRITICAL ITEMS -- STATUS TRACKER

| # | JUDGE_001 Item | Status | Details |
|---|---|---|---|
| 1 | Execute OpenFOAM simulations | PARTIALLY DONE | 36 cases run, but only 5/36 converged. ABL precursor converged. Mesh independence completed. |
| 2 | Validate against published experimental data | NOT DONE | Still only flat-terrain ABL test. No Jubayer & Hangan (2016) or Jiang et al. (2011) comparison. |
| 3 | Remove fabricated field data from F12 | DONE | F12 now references Lu & Zhang (2019) and Tang et al. (2021) with honest metric-mismatch annotation. |
| 4 | Run Lagrangian particle tracking | NOT DONE | Analytical Owen model still used, but now applied to OpenFOAM-derived u* fields. |
| 5 | Restore F5 as particle trajectories | NOT DONE (but improved) | F5 now shows OpenFOAM u* amplification with panel markers. Informative, but not the planned Lagrangian tracks. |
| 6 | Fix bib entries | PARTIALLY DONE | Some improvements; detailed audit deferred to Editor. |

---

## 1. WHAT HAS IMPROVED (Credit Where Due)

### 1a. OpenFOAM k-epsilon is running and producing real physics

The Worker has built a complete OpenFOAM pipeline:
- `codes/openfoam/setup_case.py`: blockMesh + topoSet (STL panels) + createBaffles baffle workflow
- k-epsilon with ATM BCs (`atmBoundaryLayerInletK`, `atmBoundaryLayerInletEpsilon`)
- SIMPLE with GAMG/PBiCGStab, proper solver settings
- 4-process parallel decomposition via Scotch
- `codes/analysis/postprocess_openfoam.py`: extracts u* from wallShearStress field, computes sand metrics

This is a genuine CFD pipeline, not a toy solver. The `setup_case.py` correctly implements the memory-documented OpenFOAM-10 baffle workflow (STL in `constant/geometry/`, `searchableSurfaceToFaceZone`, createBaffles, write BCs AFTER baffle creation).

### 1b. Flow physics are dramatically improved

Figure F5 (friction velocity amplification) now shows:
- Clear flow acceleration at panel leading edges (u*/u*_ref peaks at 1.5-1.9)
- Pronounced sheltering troughs behind panels (u*/u*_ref drops to 0.2-0.4)
- For H=0.1m, u* collapses to near-zero after row 2-3, far below u*_t -- genuine capture regime
- For H=0.8m, u* oscillates but remains above u*_t throughout -- pass-through regime
- Panel locations are marked with grey bands

This is REAL flow physics from a REAL CFD solver. The qualitative difference between H=0.1m and H=0.8m is no longer an analytical assumption -- it is a computed result.

### 1c. Row spacing S now has measurable effect

The heatmap (F6) now shows visible S-variation:
- At H=0.1m, theta=25: S=2Hp gives -3.9, S=6Hp gives -4.4 (~0.5 log units, factor of ~3)
- At H=0.3m: S-variation is ~0.4-0.6 log units
- At H=0.5m: S-variation is ~0.5 log units

This is modest but physically meaningful: wider spacing allows partial sand flux recovery between rows. The old Python solver showed zero S-effect; the OpenFOAM solver shows a factor-of-3 variation. This is a genuine improvement.

### 1d. Row-by-row flux progression is physically realistic

Figure F8 now shows dramatic row-by-row flux depletion:
- H=0.1m: flux drops from ~2.5x at row 1 to ~0.05x by row 3 (95% depletion in 3 rows)
- H=0.3m: flux drops from ~2.9x to ~0.1x by row 5
- H=0.5m: gradual decline, flux still at ~0.2x by row 8
- H=0.8m: flux remains above reference (~0.8x) through all 8 rows

The old version showed flat, uniform deposition across all rows (within 3%). The new version shows physically meaningful shelter cascading. This IS the inter-row interaction physics that was missing.

### 1e. F12 field comparison is honest

F12 now shows Lu & Zhang (2019) deposition gradient data and Tang et al. (2021) sand inhibition range (35-89%). The annotation explicitly states "shelter efficiency = -42% (different metric; not directly comparable)." This is honest scientific communication.

### 1f. Limitations section is thorough

The manuscript now acknowledges 8 specific limitations including: 2D RANS, k-epsilon overprediction, horizontal homogeneity decay, equilibrium saltation profile, Owen coefficient uncertainty, no electrostatic/humidity effects, detection threshold, and lack of multi-row experimental validation. This is commendably honest.

---

## 2. CRITICAL: 31 of 36 Cases Did Not Converge

Only 5 of 36 parametric cases reached the convergence criterion (all residuals below 2e-4):
- case_04 (H=0.1, T25, S2Hp): CONVERGED at 1708 iterations
- case_07 (H=0.1, T35, S2Hp): CONVERGED
- case_16 (H=0.3, T35, S2Hp): CONVERGED
- case_23 (H=0.5, T25, S4Hp): CONVERGED
- case_25 (H=0.5, T35, S2Hp): CONVERGED

The remaining 31 cases reached the 2000-iteration endTime limit with Uz residual at ~3.5e-4 and p at ~4e-4 (approximately 2x above the convergence criterion).

**Impact on paper claims**: The heatmap (F6) plots results from ALL 36 cases, including 31 unconverged ones. The manuscript states "Typical cases converge in 1500-2000 SIMPLE iterations" (`main.tex:140`) -- this is misleading since only 14% of cases actually converged.

**The fix is straightforward**: Increase `endTime` from 2000 to 3000 in `setup_case.py`. The memory file documents that "Coarse mesh converges ~1900 iterations (~12 min wall time on 4 procs)" and "endTime 3000 (mesh independence)." The parametric cases use endTime=2000, which is insufficient for some geometries. The residual trends show monotonic decrease -- these cases WILL converge with more iterations.

**Recommendation**: Re-run all 31 unconverged cases with endTime=3000. Report the actual convergence status for all 36 cases (converged/iterations/final residuals) in a supplementary table. Do not claim "typical convergence in 1500-2000" when 86% of cases did not converge within that range.

---

## 3. CRITICAL: Still No Experimental Validation With Panels Present

The Simulation Contract specifies validation against:
- Jubayer & Hangan (2016): velocity profiles behind PV arrays (wind tunnel data)
- Jiang et al. (2011): single-panel deposition efficiency vs tilt angle

Neither has been done. The validation section (`main.tex:216-254`) contains only:
1. ABL profile preservation (flat terrain, no panels) -- necessary but trivial
2. Mesh independence study with GCI -- good, but tests numerical convergence, not physical accuracy

**Without experimental validation against flow data around obstacles, the solver has not demonstrated it can predict flow separation behind PV panels.** The ABL test only proves the boundary conditions are self-consistent.

The F5 flow patterns (acceleration peaks, shelter troughs) are qualitatively plausible, but their quantitative accuracy is unknown. The k-epsilon model is known to overpredict separation bubble length behind bluff bodies (as the paper acknowledges in the limitations). How much? By 20%? By 100%? Without experimental comparison, this cannot be assessed.

**Recommendation**: Add one validation case against Jubayer & Hangan (2016) velocity profiles at x/H = 1, 3, 5 downstream of a single panel row. Report RMSE and correlation coefficient. This can be done with a single additional OpenFOAM case and would substantially strengthen the paper.

---

## 4. CRITICAL: No Uncertainty Quantification (Statistician's Finding Confirmed)

Not a single result has error bars, confidence intervals, or uncertainty bounds. The Statistician's review (2/10) identified this as CRITICAL item #1 and it remains unaddressed. Key uncertainty sources:

1. **Owen coefficient C**: literature range 0.1-0.5 (paper uses 0.25). Panel deposition is linear in C. The paper mentions this in the limitations but does not propagate it as error bands.
2. **Threshold friction velocity u*_t**: +-15% between parameterizations. Non-linear propagation through Owen flux formula.
3. **Grain size distribution**: Real desert sand is polydisperse. The sensitivity analysis covers D=100-300um but reports single curves, not uncertainty bands.
4. **Discretization error**: GCI is 4.3-9.7% (Table 1) but is not propagated to the heatmap or nomogram.

**Recommendation**: At minimum, add envelope curves to F9b and F11 showing the uncertainty band from C=[0.1, 0.5] and u*_t +/- 15%. State the GCI-estimated discretization uncertainty for key reported metrics. The regime BOUNDARIES (H/lambda_s = 2, 10) are insensitive to C (they derive from the concentration profile, not the flux magnitude), which is a strength -- state this explicitly.

---

## 5. HIGH: The Analytical Deposition Model Remains the Core Limitation

The `postprocess_openfoam.py:444-455` computes panel deposition as:

```python
deposition_fraction = np.exp(-H / lambda_s) - np.exp(-(H + Hp) / lambda_s)
Q_array = np.mean(Q[mask_array])
panel_deposition = Q_array * deposition_fraction
```

The OpenFOAM now provides a physically meaningful `Q_array` (the spatially-averaged ground flux within the array, modulated by real flow acceleration and sheltering). This is a genuine improvement: `Q_array` varies across cases because the k-epsilon flow field varies. The S-dependence enters through `Q_array` because wider spacing allows more flux recovery.

However, the H-dependence is still dominated by `deposition_fraction = exp(-H/lambda_s)`, which is analytical. The CFD contributes the Q_array factor (varies by ~2-3x across S at fixed H) while the exponential contributes 7+ orders of magnitude across H. The paper's headline conclusion -- "H dominates" -- is partly a model artifact of this multiplicative structure.

**This is no longer a fatal flaw** (the CFD now genuinely modulates the result through Q_array), but it is a significant limitation that should be acknowledged more explicitly. The paper should state: "The H-dependence is driven primarily by the analytical concentration profile; the CFD contributes the shelter-modified ground flux which produces the S- and theta-dependence."

---

## 6. HIGH: Abstract Contradicts Heatmap on S-Effect

The abstract states: "Row spacing S has negligible effect on per-panel capture" (`main.tex:42`).

The updated heatmap (F6) shows S-variation of ~0.4-0.5 log units (factor of 2.5-3x) at each H value. A factor of 3 is NOT "negligible." The paper text in Section 6 (`main.tex:286`) now says "varying by a factor of 2-3 across the S range at fixed H" -- which is correct.

**The abstract must be corrected** to reflect the actual results. Suggested revision: "Row spacing S produces modest but measurable variation in per-panel deposition (factor of 2-3), secondary to the dominant H effect."

---

## 7. HIGH: Fine-Mesh Convergence Is Non-Monotonic

Figure F2b shows panel deposition INCREASING from coarse to fine mesh (non-monotonic):
- Coarse: ~1.0e-8
- Medium: ~1.2e-8
- Fine: ~2.5e-8

The GCI table reports that the fine-grid y+ ~ 49 approaches wall-function validity limits and the pressure residual didn't converge. The paper correctly uses 2-level GCI with F_s = 3.0. However:

1. **Non-monotonic convergence means the observed order p cannot be reliably estimated.** The assumed p=2 may be wrong.
2. **The fine-grid shelter efficiency is -2.228 vs medium -0.469** -- a 5x change, suggesting the fine grid resolves fundamentally different physics (or wall-function breakdown).
3. **The coarse grid is used for the parametric study.** If the fine-grid solution is 2.5x different, the coarse-grid results carry substantial uncertainty.

**Recommendation**: Acknowledge this more prominently. The current footnote is adequate for the GCI table, but the discussion should note that the deposition predictions carry at least a factor-of-2 uncertainty from mesh resolution alone. Consider running the medium mesh for a subset of key cases (e.g., the 3 representative configurations) to assess how the parametric trends change.

---

## 8. HIGH: Lagrangian Particle Tracking Still Missing (Simulation Contract)

The plan specifies `icoUncoupledKinematicParcelFoam` with 50,000 particles per case. This has not been attempted. The `codes/models/particle_tracking.py` module is still dead code.

The paper now honestly states: "Rather than tracking individual particles through the flow field, we employ an analytical sand transport model" (`main.tex:161`). This is transparently described. However:

1. The plan's F5 was supposed to show Lagrangian trajectories -- the visual proof of capture vs pass-through regimes.
2. Lagrangian tracking would capture non-equilibrium saltation adjustment (particles entering the array don't instantly follow the local concentration profile), which the analytical model cannot.
3. The Cheng et al. (2023) competitor uses Eulerian two-phase modeling. Without Lagrangian tracking, this paper does not advance particle-level physics beyond the competitor.

**Recommendation**: This is a significant scope reduction from the plan. If time constraints prevent Lagrangian tracking for all 36 cases, run it for at LEAST 3 representative cases (capture, transitional, pass-through) to: (a) generate the planned F5 trajectory visualization, (b) validate the analytical deposition model against Lagrangian deposition, (c) quantify the non-equilibrium error.

---

## 9. MEDIUM: Sensitivity Analysis Is Purely Analytical

The manuscript states: "sensitivities to wind speed and grain size are evaluated analytically" (`main.tex:205`). The CFD amplification factors are extracted once at u_ref=10 m/s and applied to other conditions. This is mathematically consistent (the RANS shelter pattern is approximately Re-independent) but means the sensitivity study adds no new CFD data.

The Statistician flagged this as "shelter ratio invariant to wind speed (solver artifact)." The current approach is honest about it, but it means the paper's sensitivity analysis is a one-line formula application, not a computational investigation.

**Recommendation**: Run at least one additional wind speed (u_ref=14 m/s) for a representative case to verify that the amplification factors don't change significantly. This would take ~15 min and would validate the analytical sensitivity approach.

---

## FOUR PILLAR EVALUATION

### NOVELTY (20%): 4/10
The regime-transition framework (capture / transitional / pass-through) now has genuine CFD support from the OpenFOAM shelter patterns and row-by-row flux depletion (F8). The H/lambda_s thresholds are still analytically imposed, but the Q_array modulation from CFD adds real value. The paper is incrementally novel over Zhang et al. (2020) and Cheng et al. (2023), but the lack of Lagrangian tracking limits the physics depth relative to those competitors.

### PHYSICS DEPTH (40%): 4/10
Major improvement from 1/10:
- k-epsilon resolves separation and shelter (F5 shows real wake structures)
- Flow acceleration peaks at leading edges (1.5-1.9x amplification)
- Row-by-row flux depletion through the array (F8)
- S-dependence now enters through CFD-modulated Q_array

Still limited by:
- 2D only (no edge vortices, oblique wind)
- Analytical deposition model (no Lagrangian physics)
- 31/36 cases unconverged
- No experimental validation with panels

### CONTRIBUTION (30%): 4/10
The design nomogram (F10) now has CFD backing through the amplification factors. The shelter efficiency varies meaningfully with geometry. The paper provides actionable guidance (H > 0.4m for pass-through regime) supported by real simulations. However, the quantitative accuracy is unvalidated, and the dominant H-effect is still analytically driven.

### RELEVANCY (10%): 7/10
Unchanged from JUDGE_001. The topic is directly relevant to Solar Energy journal.

---

## ACTIONABLE ITEMS (Priority Order)

### CRITICAL (Must fix before submission)

1. **Re-run 31 unconverged cases with endTime=3000.** The residuals are close to criterion; they just need more iterations. Correct the manuscript claim about "typical convergence in 1500-2000." Report convergence status for all cases.

2. **Add one experimental validation case with panels.** Compare velocity profiles to Jubayer & Hangan (2016) at x/H = 1, 3, 5. Report RMSE. This is the single highest-value-added task remaining.

3. **Add uncertainty bounds.** Propagate C=[0.1, 0.5] and u*_t +/- 15% as envelope curves on F9b and F11. State GCI uncertainty on key reported metrics.

### HIGH (Must fix for submission)

4. **Correct abstract**: "negligible S effect" contradicts the heatmap showing factor-of-3 variation.

5. **Run Lagrangian tracking for 3 representative cases** to generate the planned F5 particle trajectories and validate the analytical model. If this is impractical, explicitly acknowledge the departure from the simulation contract and justify the analytical approach.

6. **Discuss fine-mesh anomaly** more prominently: factor-of-2 mesh uncertainty in deposition should be stated in the results discussion, not just the GCI footnote.

### MEDIUM

7. **Run one additional wind speed** (u_ref=14 m/s) for one case to validate the analytical sensitivity approach.

8. **Add intermediate H values** (0.15, 0.2, 0.4 m) at one (theta, S) combination to resolve regime transitions from CFD data rather than analytical formula.

9. **Report per-case convergence data** in a supplementary table: case ID, iterations, final residuals, converged status.

---

## SUMMARY

The paper has improved dramatically since JUDGE_001. The core methodology is now a legitimate OpenFOAM k-epsilon simulation that resolves real flow physics (separation, shelter cascading, flow acceleration). The figures reflect actual CFD data, S-dependence is now visible, and the row-by-row flux progression shows physically meaningful shelter effects. The limitations section and field comparison are honest.

Three critical gaps prevent publication: (1) 31/36 cases are unconverged and need more iterations, (2) no experimental validation against flow data around panels, and (3) no uncertainty quantification on any result. These are all fixable within a reasonable timeframe.

The Lagrangian tracking omission is a significant departure from the simulation contract. The current RANS + analytical approach is defensible for a screening study, but the paper should be positioned as such and should not claim to capture individual saltation physics.

---

**Score: 4/10**

Increased from 2/10 (JUDGE_001). The simulation contract is partially fulfilled: OpenFOAM flow solver with k-epsilon is operational, but Lagrangian tracking is absent and 31/36 cases are unconverged. The physics depth has improved substantially (real separation, shelter, S-dependence). The three critical gaps (convergence, validation, uncertainty) are all tractable. If addressed, this paper could reach 6-7/10 territory.
