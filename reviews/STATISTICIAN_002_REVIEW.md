# STATISTICIAN REVIEW 002 -- Ronald Fisher

**Paper**: Array Layout Controls Sand Fate: CFD--Aeolian Modeling of Wind-Sand Transport in China's Desert Photovoltaic Mega-Bases
**Date**: 2026-03-06
**Reviewer**: statistician-fisher (Statistical Methods and Data Analysis Review)
**Previous review**: STATISTICIAN_001 (Score: 2/10)

---

## CONTEXT

The Worker has responded to both JUDGE_001 and STATISTICIAN_001 reviews with substantial effort. The Python mixing-length solver has been replaced by a real OpenFOAM k-epsilon pipeline. The sand transport model now uses CFD-derived friction velocity amplification factors applied to the design ABL u*, giving row spacing a physical pathway to influence deposition. GCI has been computed and reported. Uncertainty sources are discussed in the text. The manuscript has been significantly rewritten to reflect these changes.

This review evaluates the current statistical rigor against the same criteria as STATISTICIAN_001 and identifies remaining gaps.

---

## STATISTICIAN_001 ITEMS -- STATUS TRACKER

| # | STAT_001 Item | Status | Details |
|---|---|---|---|
| 1 | No uncertainty quantification | PARTIALLY ADDRESSED | Uncertainty sources (C, u*t, GCI) now discussed qualitatively in text (Sections 2, 6.1, 7.1). No uncertainty bands on figures yet. |
| 2 | Shelter ratio invariant to wind speed | RESOLVED BY DESIGN | Sensitivity analysis now honestly described as analytical (Section 4.3). The amplification factors are explicitly stated as Re-independent. |
| 3 | Row spacing effect <1.6% | RESOLVED | OpenFOAM Q_array now varies with S by a factor of 2-4x. The model has a physical pathway for S-dependence. |
| 4 | No GCI | RESOLVED | GCI computed (Table 1): u*_ref 4.3%, shelter_eff 9.7%, amp_max 5.7%. 2-level method with F_s=3.0. |
| 5 | H_panel definition wrong | RESOLVED | S values now use Hp = L*sin(theta). Verified from OpenFOAM results. |
| 6 | Convergence criteria inadequate | PARTIALLY ADDRESSED | Fields listed (p, Ux, Uz, k, eps), criterion 2e-4, iteration range stated. But 31/36 did not formally converge. |
| 7 | No validation with panels | NOT ADDRESSED | Still only flat-terrain ABL preservation test. |
| 8 | Precision concern (8 orders of magnitude) | ADDRESSED | Detection threshold of 10^-8 kg/(m*s) now defined in limitations. |
| 9 | Inter-row deposition identically zero | PARTIALLY ADDRESSED | The paper no longer reports inter-row deposition as an explicit metric. Row-by-row flux progression (F8) now shows physically meaningful shelter cascading. |
| 10 | Reattachment lengths all zero | ADDRESSED | Quantitative reattachment claims removed. F4 shows separation bubbles qualitatively from OpenFOAM contours. |
| 11 | Only 4 H values for regime transitions | NOT ADDRESSED | Still only 4 H values. Regime boundaries remain analytically imposed. |
| 12 | OAT sensitivity design | PARTIALLY ADDRESSED | Tornado chart (F11b) now shows relative parameter importance. Still OAT. |
| 13 | No reproducibility information | RESOLVED | Section 4.4: OpenFOAM-10, GCC 11.4, Ubuntu 22.04, Python 3.10. |

**Summary**: 6 resolved, 4 partially addressed, 3 not addressed. Substantial progress.

---

## NEW FINDINGS FROM THE UPDATED ANALYSIS

### 1. CRITICAL: Convergence Status Needs Clarification

The Judge's review states "31/36 cases did not converge" and reports Uz residuals at ~3.5e-4 and p at ~4e-4. However, my analysis of the actual final residuals in `openfoam_results.json` shows:

| Field | Typical final residual (unconverged cases) | Convergence criterion |
|-------|---------------------------------------------|----------------------|
| k | 7e-7 to 1e-6 | 2e-4 |
| epsilon | 4e-8 to 5e-7 | 2e-4 |
| p | 1.2e-5 to 7.2e-5 | 2e-4 |
| Uz | 3.6e-6 to 7.3e-6 | 2e-4 |

**All final residuals are 1-2 orders of magnitude below the 2e-4 criterion.** The discrepancy likely arises because OpenFOAM's SIMPLE `residualControl` checks *initial* residuals (before the linear solver iteration for each field), not *final* residuals (after). The Initial residual for Uz may have been ~3.5e-4 while the Final residual was ~5e-6.

**Statistical impact**: If the final residuals are O(10^-5 to 10^-6), the solutions are likely well-converged for engineering purposes. But this needs verification:

1. The Worker should check whether the *initial* residuals (the ones SIMPLE uses for convergence control) are above or below 2e-4 at the last iteration.
2. If the initial residuals are slightly above 2e-4 while finals are well below, increasing endTime to 3000 (as the Judge recommends) should resolve this.
3. The manuscript should report which residual type is monitored and clarify the convergence status honestly.

**The medium mesh in the GCI study also did not converge** (3000 iterations, final residuals: p=5.0e-5, Uz=5.5e-6). This means the GCI calculation uses one converged mesh (coarse) and one unconverged mesh (medium). The medium-mesh u* values may not have fully stabilized, which introduces additional uncertainty into the GCI estimate.

**Recommendation**: Report final residual levels for ALL mesh levels and parametric cases. If initial residuals are the convergence bottleneck, report those too. Consider plotting residual convergence history for at least one representative case to demonstrate monotonic decrease.

---

### 2. CRITICAL: Negative Shelter Efficiency in 21/36 Cases -- Not Discussed

The shelter efficiency (defined as 1 - Q_array/Q_upstream) is **negative** for 21 of 36 cases:

| H | theta | S=2Hp | S=4Hp | S=6Hp |
|---|-------|-------|-------|-------|
| 0.1 | 15 | -0.11 | +0.43 | +0.63 |
| 0.1 | 25 | +0.26 | +0.66 | +0.76 |
| 0.1 | 35 | +0.40 | +0.68 | +0.76 |
| 0.3 | 15 | **-1.50** | -0.36 | +0.09 |
| 0.3 | 25 | **-1.07** | +0.16 | +0.47 |
| 0.3 | 35 | -0.58 | +0.29 | +0.51 |
| 0.5 | 15 | **-2.09** | **-1.29** | -0.59 |
| 0.5 | 25 | **-2.05** | -0.42 | +0.13 |
| 0.5 | 35 | **-1.66** | -0.15 | +0.24 |
| 0.8 | 15 | **-2.19** | **-1.76** | **-1.38** |
| 0.8 | 25 | **-2.45** | **-1.33** | -0.45 |
| 0.8 | 35 | **-2.66** | -0.82 | -0.17 |

A shelter efficiency of -2.66 means Q_array is 3.66 times Q_upstream -- the panels *amplify* ground-level sand flux.

**This is a physically significant and counterintuitive finding that the paper does not discuss.** The physical mechanism is clear: panels create Venturi-like flow acceleration at their leading edges (u* amplification up to 1.75x), and since Q ~ u*^3, even modest velocity peaks produce large flux amplification. The cubic nonlinearity means that the spatially averaged Q is dominated by the acceleration peaks, not the shelter troughs.

This is **Jensen's inequality** in action: E[u*^3] > (E[u*])^3 when u* has spatial variance. The mean u* within the array can be below the upstream value (ustar_amp_mean < 1.0) while the mean sand flux Q is above upstream (shelter_eff < 0). Example: H=0.5, theta=25, S=3.38:
- Mean u* amplification = 0.955 (5% reduction in mean wind)
- Q_array/Q_upstream = 1.42 (42% *increase* in mean sand flux)

**Why this matters**:
1. The paper discusses "shelter efficiency" as if the array reduces sand transport. For most configurations (especially tight spacing), the opposite is true at ground level.
2. The Q_array value enters directly into the panel deposition calculation (panel_dep = Q_array * deposition_fraction). Negative shelter means HIGHER deposition than expected from the analytical model alone.
3. This is actually a genuine finding of the CFD study that differentiates it from purely analytical predictions. The analytical model (no panels) predicts Q_upstream everywhere. The CFD reveals that panels amplify Q locally due to flow acceleration, and this amplification increases with tighter spacing.

**Recommendation**:
1. Add a paragraph discussing the negative shelter efficiency phenomenon and its physical cause (Venturi acceleration + cubic flux nonlinearity).
2. Acknowledge Jensen's inequality explicitly: spatial averaging of u*^3 is not equivalent to (spatial average of u*)^3.
3. Reframe "shelter efficiency" or rename it (perhaps "flux modification ratio" = Q_array/Q_upstream) to avoid the misleading implication that the array always reduces sand transport.

---

### 3. HIGH: GCI Quality -- Medium Mesh Did Not Converge

The GCI is computed from the coarse-medium pair. The key concern:

- **Coarse**: converged at 1908 iterations (final p residual: 1.4e-5)
- **Medium**: did NOT converge at 3000 iterations (final p residual: 5.0e-5)
- **Fine**: did NOT converge at 3000 iterations (final p residual: 7.9e-5)

The coarse-medium GCI values (4.3%, 9.7%, 5.7%) are computed under the assumption that both solutions are adequately converged. If the medium solution has not stabilized, the GCI underestimates the true discretization error.

However, the final residuals for the medium mesh are all below 5e-5, which is well below the convergence criterion of 2e-4. The p-field initial residual may be the bottleneck (SIMPLE checks initial residuals). If the medium-mesh p field is oscillating at the 5e-5 level without fully converging, the u* values derived from it should be approximately correct.

**Recommendation**:
1. State explicitly that the medium mesh reached 3000 iterations with final residuals below 5e-5 but did not formally satisfy the SIMPLE convergence criterion.
2. Report whether the monitored quantities (u*, shelter efficiency) are stable over the last 500 iterations of the medium-mesh run (e.g., less than 1% change from iteration 2500 to 3000).
3. If they are stable, state this as evidence of practical convergence.

---

### 4. HIGH: Uncertainty Quantification Still Incomplete

The manuscript now discusses uncertainty sources in several places:
- Section 2: C = 0.1-0.5 (factor-of-5), u*t +/- 15% (main.tex:97)
- Section 6.1: "factor-of-two uncertainty from mesh resolution alone" (main.tex:298)
- Section 7.1: Tornado chart showing parameter importance (F11b)
- Limitations: detection threshold 10^-8 kg/(m*s) (main.tex:383)

This is a substantial improvement over STATISTICIAN_001 (which found zero uncertainty discussion). However, **no uncertainty bands appear on any figure**. The key figures (F6 heatmap, F9 regime plot, F10 nomogram) show point estimates only.

The tornado chart (F11b) is a step in the right direction -- it quantifies relative sensitivity. But it does not produce confidence bands on the regime boundaries or the nomogram.

**What is still missing**:
1. **Envelope curves on F9b** (deposition vs H): Show the band from C=[0.1, 0.5] and u*t +/- 15%. Since deposition is linear in C, this is trivial: the band is [dep/2.5, dep*2] centered on the C=0.25 value.
2. **GCI uncertainty on the nomogram** (F10): The 4.3-9.7% GCI translates to a shift in the regime boundaries. At minimum, state the implied H uncertainty: if shelter efficiency has 9.7% GCI and lambda_s has 4.3% GCI, the regime boundary H_crit = 10*lambda_s shifts by roughly 4.3%.
3. **Mesh uncertainty on the heatmap** (F6): The fine-mesh deposition is 2.5x the coarse-mesh value. This means each entry in the heatmap has an implicit uncertainty of at least +/- 0.4 log units. State this.

**Recommendation**: Add uncertainty bands to at least F9b (deposition vs H). This is the paper's central quantitative figure. A single shaded region showing the C=[0.1, 0.5] range would suffice. The regime boundaries are insensitive to C (correctly stated in the text), so the bands narrow to lines at the regime transitions.

---

### 5. HIGH: S-Effect Direction Is Physically Counterintuitive and Needs Explanation

The OpenFOAM results show that **wider spacing consistently decreases panel deposition**:

| H | theta | dep(S=2Hp) | dep(S=6Hp) | ratio |
|---|-------|------------|------------|-------|
| 0.1 | 25 | 1.14e-4 | 3.71e-5 | 3.1x |
| 0.3 | 25 | 2.24e-6 | 5.75e-7 | 3.9x |
| 0.5 | 25 | 2.34e-8 | 6.69e-9 | 3.5x |

At first glance, wider spacing should mean MORE sand reaches interior panels (less shelter). But the opposite occurs because:
- Tight spacing (S=2Hp) creates high Q_array due to Venturi acceleration between closely-spaced panels
- Wide spacing (S=6Hp) allows more flux recovery but also more flow deceleration between rows, lowering Q_array
- The panel deposition = Q_array * deposition_fraction, and Q_array dominates the S-effect

This finding contradicts the plan's original hypothesis that "If S is small (tight rows), the front of row N+1 sits in row N's deposition zone -- it catches the sand that row N drops" (plan.md). The plan predicted that tight spacing would be FAVORABLE (sand captured by upstream rows doesn't reach downstream ones). The CFD shows tight spacing is UNFAVORABLE (higher Q_array due to acceleration).

**Recommendation**: Discuss this reversal explicitly. The CFD result is more physically nuanced than the original hypothesis: the dominant mechanism is not inter-row shelter but flow acceleration. This is a genuine value-add of the CFD over simple analytical reasoning.

---

### 6. MEDIUM: Regime Classification Still Has Only 4 H Data Points

Unchanged from STATISTICIAN_001 item #11. The regime boundaries (H/lambda_s = 2 and 10) are imposed from the analytical concentration profile, not resolved from the CFD data. With only 4 H values:
- H = 0.1m (H/lambda_s = 2.5 -- just inside transitional)
- H = 0.3m (H/lambda_s = 7.5 -- mid-transitional)
- H = 0.5m (H/lambda_s = 12.5 -- just inside pass-through)
- H = 0.8m (H/lambda_s = 20 -- deep pass-through)

None of these falls in the capture regime (H/lambda_s < 2). The capture regime is only represented by the H=0.1 case, which is already transitional (H/lambda_s = 2.5). The paper's abstract states "capture regime (H < 2*lambda_s ~ 0.08m)" -- but no simulation uses H < 0.1m.

**Recommendation**: Run at least one case at H = 0.05m (H/lambda_s = 1.25, clearly in the capture regime) to confirm that the analytical prediction holds. Additionally, H = 0.15m and H = 0.4m would add resolution to the two transition zones.

---

### 7. MEDIUM: No Experimental Validation With Panels (Reiteration)

Unchanged from STATISTICIAN_001 item #7 and JUDGE_002 item #3. This remains the single highest-value-added task for the paper's statistical credibility. The ABL precursor validation (flat terrain) demonstrates boundary condition consistency but says nothing about the solver's ability to predict flow around obstacles.

The k-epsilon model is known to overpredict separation bubble length behind bluff bodies by 20-50%. Without at least one comparison to published wind tunnel data (Jubayer & Hangan 2016 or equivalent), the quantitative accuracy of the flow predictions -- and therefore the sand transport predictions that depend on them -- is unknown.

**Recommendation**: One validation case against published velocity profiles downstream of a PV panel, with RMSE and R^2 reported. This is the highest-ROI improvement remaining.

---

## WHAT HAS IMPROVED (Credit Where Due)

The statistical quality of this paper has improved significantly:

1. **GCI with proper methodology**: 2-level Roache (1994) with F_s=3.0, reported in a table with all three mesh levels. The fine-mesh wall-function issue is honestly noted. This is a proper mesh convergence assessment.

2. **S-dependence is real**: Factor of 2-4x variation in panel deposition across S values, entering through the CFD-modulated Q_array. This validates the 3-parameter experimental design.

3. **Uncertainty sources enumerated**: C uncertainty (factor 5), u*t uncertainty (15%), mesh uncertainty (factor 2-2.5), all discussed in the text. Not yet propagated to figures, but acknowledged.

4. **Sensitivity analysis honestly framed**: Section 4.3 explicitly states that amplification factors are Re-independent and sensitivities are evaluated analytically. No more disguised-as-computational claims.

5. **Reproducibility information provided**: Software versions, hardware, solver settings all specified.

6. **Detection threshold defined**: 10^-8 kg/(m*s) below which values are "negligible."

7. **Row-by-row flux progression is physical**: F8 shows dramatic shelter cascading through the array -- 95% flux depletion by row 3 for H=0.1m. This is a genuine CFD finding.

---

## SCORING

### Methodology (50%): 5/10
- OpenFOAM k-epsilon with proper ATM BCs is a legitimate CFD solver (+3 from 2/10)
- GCI computed and reported properly (+1)
- Sand transport model now uses CFD-derived Q_array, giving S a physical pathway (+1)
- Still no validation against experiments with panels (-2)
- 31/36 cases formally unconverged (though final residuals appear adequate) (-1)
- Medium mesh in GCI also unconverged (-0.5)

### Results (30%): 4/10
- S-dependence now real (factor 2-4x) (+2 from 1/10)
- Row-by-row flux depletion is a genuine finding (+1)
- Uncertainty sources discussed qualitatively but no envelope curves on figures (-1)
- Negative shelter efficiency (21/36 cases) is not discussed (-1)
- Jensen's inequality effect on Q averaging not acknowledged (-0.5)
- H-dependence remains analytically dominated (-0.5)

### Experimental Design (20%): 5/10
- 36-case parametric matrix is well-structured (+1 from 3/10)
- H_panel definition fixed, S values now correct (+1)
- Tornado chart shows parameter importance ranking (+0.5)
- Still only 4 H values for regime transitions (no data in capture regime) (-1)
- OAT sensitivity design (-0.5)

---

## SUMMARY OF REMAINING FINDINGS

| # | Severity | Issue | Status vs STAT_001 |
|---|----------|-------|-------------------|
| 1 | CRITICAL | Convergence status needs clarification (31/36 unconverged but finals are O(10^-5)) | NEW FINDING |
| 2 | CRITICAL | Negative shelter efficiency in 21/36 cases undiscussed | NEW FINDING |
| 3 | HIGH | GCI uses one unconverged mesh (medium at 3000 iters) | NEW FINDING |
| 4 | HIGH | No uncertainty bands on figures (text discusses but no propagation) | PARTIALLY ADDRESSED from STAT_001 #1 |
| 5 | HIGH | S-effect direction contradicts original hypothesis -- needs discussion | NEW FINDING |
| 6 | MEDIUM | Only 4 H values, no cases in capture regime (H < 0.08m) | UNCHANGED from STAT_001 #11 |
| 7 | MEDIUM | No experimental validation with panels | UNCHANGED from STAT_001 #7 |

---

## ACTIONABLE ITEMS (Priority Order)

### CRITICAL
1. **Clarify convergence status**: Check initial residuals for the 31 "unconverged" cases. If final residuals are all below 2e-4 (as the data suggests), the solutions may be practically converged. Either increase endTime to 3000 to achieve formal convergence, or demonstrate that the monitored quantities are stable over the last 500 iterations.

2. **Discuss the negative shelter efficiency finding**: 21/36 cases show the panels AMPLIFY ground-level sand flux. This is physically important (Venturi acceleration + Jensen's inequality on the cubic flux law) and must be acknowledged. It is also a genuine value-add of the CFD over purely analytical predictions.

### HIGH
3. **Add uncertainty bands to F9b** (deposition vs H): Show the C=[0.1, 0.5] envelope. This is the minimum credible uncertainty visualization -- one shaded band on one figure.

4. **Discuss the S-effect mechanism**: Explain why wider spacing DECREASES deposition (lower Q_array due to less flow acceleration) rather than increases it (less shelter). This reversal of the original hypothesis is scientifically interesting.

5. **Validate the medium-mesh practical convergence** for the GCI study: Show that u* and shelter efficiency are stable over the last 500 iterations at 3000 steps.

### MEDIUM
6. **Add H = 0.05m** to confirm capture regime behavior (currently unsampled).

7. **Add one experimental validation case** with panels. The highest-ROI statistical improvement remaining.

---

**Score: 5/10**

Increased from 2/10 (STATISTICIAN_001). The paper now has a legitimate CFD pipeline (OpenFOAM k-epsilon), a proper GCI assessment, physical S-dependence through CFD-modulated Q_array, and honest framing of the analytical sensitivity approach. The improvements are substantial and genuine.

Three gaps prevent a higher score: (1) the convergence status of 31/36 cases needs clarification -- the final residuals suggest practical convergence but formal convergence was not reached; (2) the negative shelter efficiency in 21/36 cases is an important and counterintuitive finding that the paper ignores; and (3) uncertainty sources are discussed qualitatively but not propagated to any figure as envelope curves. Additionally, no experimental validation with panels exists (unchanged from STATISTICIAN_001). If the convergence issue is resolved, uncertainty bands are added to at least one key figure, and the negative shelter phenomenon is discussed, this paper could reach 6-7/10 territory.
