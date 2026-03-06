# STATISTICIAN REVIEW 001 -- Ronald Fisher

**Paper**: Array Layout Controls Sand Fate: CFD--Aeolian Modeling of Wind-Sand Transport in China's Desert Photovoltaic Mega-Bases
**Date**: 2026-03-05
**Reviewer**: statistician-fisher (Statistical Methods and Data Analysis Review)

---

## CONTEXT

The Worker is in transition: the Judge's review (2/10) identified that the original Python RANS + analytical model violated the simulation contract. The Worker has begun setting up the OpenFOAM pipeline (ABL precursor converged at 1755 iterations; test case meshed and decomposed). However, the current manuscript text has been rewritten to describe OpenFOAM methodology while the **actual results still come from the Python RANS solver** (`codes/models/rans_solver.py` + `codes/analysis/sand_transport.py`). The figures and numbers in the paper are generated from `codes/results/parametric_results.json`, which is the output of `codes/models/run_parametric_study.py` calling the Python solver.

This review evaluates the statistical and quantitative rigor of what exists. I do not penalize for incomplete sections, but I flag every quantitative deficiency that must be corrected before the paper can be considered statistically defensible.

---

## 1. CRITICAL: No Uncertainty Quantification Anywhere

**Not a single result in this paper has error bars, confidence intervals, or uncertainty bounds.**

Every quantitative claim -- panel deposition rates, shelter ratios, regime boundaries, erosion rates -- is reported as a bare point estimate. This is unacceptable for any computational study. Sources of uncertainty that must be propagated include:

1. **Input parameter uncertainty**: The sand grain diameter D_50 = 200 um is a population median. Real desert sand has a grain size *distribution* (typically log-normal with geometric standard deviation sigma_g = 1.5-2.0). The paper treats sand as monodisperse. At minimum, the sensitivity to D_50 should produce confidence bands, not isolated curves.

2. **Turbulence model uncertainty**: The paper acknowledges that k-epsilon may overpredict reattachment lengths. What is the quantitative impact on deposition predictions? The planned comparison of k-epsilon vs SST k-omega (Case 3 in the simulation contract) would partially address this but has not been done.

3. **Mesh discretization error**: No Grid Convergence Index (GCI) is reported (see Section 4 below).

4. **Empirical coefficient uncertainty**: Owen's sand flux formula uses C = 0.25. The literature reports C in the range 0.1-0.5 depending on conditions. How does this factor-of-5 uncertainty in C propagate to the deposition rates? Since panel deposition is linear in C (through c_0 in the concentration profile), the absolute deposition values carry at least a factor-of-2 uncertainty. This must be stated.

5. **Threshold friction velocity**: The Shao-Lu parameterization gives u_*t = 0.26 m/s for D = 200 um. Other formulations (Bagnold, Iversen-White) give values in the range 0.22-0.30 m/s. This 15% uncertainty in u_*t propagates non-linearly through the Owen flux formula.

**Recommendation**: Report all key results with uncertainty bounds. At minimum, propagate the grain size distribution (100-300 um sensitivity already computed) and Owen coefficient range to produce envelope curves on all figures.

---

## 2. CRITICAL: Shelter Ratio Is Invariant to Wind Speed -- Model Artifact

The sensitivity analysis results reveal that the shelter ratio is **identical to 10 significant figures** across all three wind speeds (u_ref = 8, 10, 14 m/s) for each H value:

| Regime | H | shelter (u=8) | shelter (u=10) | shelter (u=14) |
|--------|---|---------------|----------------|----------------|
| Capture | 0.1 | 0.9398947771 | 0.9398947771 | 0.9398947771 |
| Transitional | 0.3 | 0.9356333822 | 0.9356333822 | 0.9356333822 |
| Pass-through | 0.8 | 0.9073279093 | 0.9073279093 | 0.9073279093 |

This proves that **the RANS flow field does not depend on inlet wind speed** in the current implementation. This is a consequence of the vorticity-stream-function formulation with mixing-length turbulence, which produces a Reynolds-number-independent solution for the normalized velocity field. The shelter ratio is therefore a geometric property of the solver, not a physical prediction.

The practical consequence: all "wind speed sensitivity" in the paper is computed solely from the analytical sand flux formula (Q ~ u*^3), not from any flow-field change. The paper's claim that "Higher wind speeds increase u* and thus lambda_s, pushing the transition to higher H values" (Section 7.2, main.tex:353) is physically correct but computationally untested -- the CFD solver provides no evidence for it because the shelter pattern doesn't change.

**Recommendation**: When OpenFOAM simulations are complete, verify that the shelter ratio varies meaningfully with Re (i.e., with u_ref). If it does not (which is unlikely with a proper k-epsilon model), this must be explicitly stated as a model limitation.

---

## 3. CRITICAL: Row Spacing Has Near-Zero Effect (<1.6% Variation)

The parametric results confirm the Judge's finding quantitatively:

| H | theta | max variation in total_panel_dep across S |
|---|-------|-------------------------------------------|
| 0.1 | 15 | 0.08% |
| 0.1 | 25 | 0.54% |
| 0.1 | 35 | 0.12% |
| 0.3 | 15 | 1.38% |
| 0.3 | 25 | 0.36% |
| 0.5 | 15 | 1.62% |
| 0.8 | 15 | 0.86% |

The maximum variation of panel deposition across all three S values for any (H, theta) combination is **1.62%**. This is not a physically meaningful variation -- it is numerical noise from the solver.

The root cause is in `sand_transport.py:139`: `c_at_panel = saltation_concentration(y_panel, u_star_ref, max(q_ref, 1e-20), d_p)`. The concentration profile uses the **undisturbed reference u_star**, not the local u_star modified by the flow field. Since S changes the flow field between rows but does not change the reference u_star, S has essentially no pathway to influence panel deposition in this model.

**Statistical interpretation**: With 36 cases spanning a 3-parameter space, if one parameter (S) has zero explanatory power, the effective experimental design reduces to a 2-parameter study (12 unique H-theta combinations). The paper should not report S as a "studied parameter" if the model is structurally incapable of resolving its effects. This is not a physical finding -- it is a model limitation.

**Recommendation**: Either (a) fix the sand transport model to use local u_star (which would require proper Lagrangian tracking or at minimum evaluating the concentration profile with the local u_*), or (b) state explicitly that the current model cannot resolve inter-row effects and that S-dependence is a planned OpenFOAM investigation.

---

## 4. CRITICAL: No Grid Convergence Index (GCI) Reported

The manuscript describes a three-level mesh independence study (Section 5.2, main.tex:246-255) with coarse (~95k), medium (~300k), and fine (~600k) cells. However:

1. **No GCI values are computed or reported.** The standard practice for CFD papers (as required by ASME Journal of Fluids Engineering and recommended by all computational mechanics journals) is to report the GCI using the Richardson extrapolation method (Roache, 1994).

2. **No quantitative convergence metrics.** The manuscript says "relative metrics show mesh convergence at this resolution" without reporting any numerical comparison between grid levels.

3. **The mesh study appears to be for OpenFOAM, but the parametric results use the Python solver.** The Python RANS solver uses a fixed grid of ~200x60 = 12,000 cells (`run_parametric_study.py:50-51`). There is no mesh independence verification for this grid.

4. **The coarse grid is selected for the parametric study** (main.tex:248). Using the coarsest grid for a parametric study is defensible only if the GCI demonstrates that the quantities of interest are mesh-independent to within a stated tolerance. This demonstration is absent.

**Recommendation**:
- Compute GCI for at least two key quantities: ground friction velocity u* at a specific location, and the integrated panel deposition rate.
- Report GCI values with the fine-grid solution as the reference.
- If the coarse grid is used, state the estimated discretization error from the GCI.
- Formula: GCI_fine = (F_s * |f_2 - f_1|) / (r^p - 1), where r is the grid refinement ratio, p is the observed order of convergence, F_s = 1.25, and f_1, f_2 are solutions on fine and medium grids.

---

## 5. HIGH: H_panel Definition Inconsistency Between Code and Manuscript

The manuscript defines row spacing as S in {2Hp, 4Hp, 6Hp} where Hp = L*sin(theta) (main.tex:194). The progress report confirms this was corrected from the original wrong definition.

However, `codes/models/run_parametric_study.py:95` still uses:
```python
H_panel = H + L * np.sin(theta_rad)  # total panel height
```

Verification from the results confirms all 36 cases use the **old, incorrect** definition (S = factor * (H + L*sin(theta))). This means:

- For H=0.1, theta=15: S values are [1.235, 2.471, 3.706] m (old) instead of [1.035, 2.071, 3.106] m (correct)
- The discrepancy grows with H: for H=0.8, theta=15, the S values are too large by 0.8*factor m

**Impact**: All 36 parametric cases use wrong row spacings. The S values reported in the paper do not match the S values claimed. However, since S has near-zero effect in the current model (Section 3 above), this error is masked. It will become significant when the model is corrected to resolve inter-row interactions.

**Recommendation**: Fix `run_parametric_study.py:95` to `H_panel = L * np.sin(theta_rad)` before running the OpenFOAM parametric study.

---

## 6. HIGH: Convergence Criteria Inadequately Specified

### 6a. Python RANS solver
The Python solver uses `tol=1e-4` and `max_iter=400` (`run_parametric_study.py:54-55`). The convergence criterion is:
```python
res = sqrt(mean((u - u_prev)^2)) / max(mean(|u_prev|), 1e-10)
```
This is a relative L2-norm of the velocity change. Several issues:

1. **No separate monitoring of continuity residual.** The stream-function formulation satisfies continuity exactly, but the overall convergence of the iterative scheme is measured by a single scalar. It is unclear whether the vorticity field, pressure field, or turbulent viscosity are converged.

2. **400 iterations may be insufficient.** The solver prints convergence history but the paper does not report final residual levels or iteration counts for any case. Did all 36 cases converge to 1e-4?

3. **The under-relaxation factors (alpha_psi=0.4, alpha_u=0.3) are aggressive.** These may cause oscillatory convergence. No convergence history plots are provided.

### 6b. OpenFOAM (planned)
The manuscript states convergence when "all residuals fall below 10^-5, with a maximum of 3000 iterations" (main.tex:140). This is acceptable but:
- The paper should report actual iteration counts and final residual levels for representative cases.
- Which residuals? U_x, U_y, p, k, epsilon? All must be below 10^-5, or just the worst?

**Recommendation**: Include a convergence history plot for at least one representative case (e.g., the baseline H=0.5, theta=25, S=4Hp). Report the final residual level and iteration count for all 36 cases in a supplementary table.

---

## 7. HIGH: Validation Strategy Is Insufficient

### 7a. ABL profile preservation (the only validation done)
The ABL precursor test (Section 5.1) verifies that the log-law profile is preserved on a flat domain. This is a necessary but trivially achievable test -- it proves only that the boundary conditions are self-consistent. It says nothing about the solver's ability to predict flow separation, recirculation, or pressure distribution around obstacles.

The manuscript does not report the quantitative error from this test. The Judge's review mentions 11% mean relative error for the Python solver, which is poor for a self-preservation test.

### 7b. Missing experimental validation
The simulation contract specifies:
- Velocity profiles vs Jubayer & Hangan (2016) for flow over PV arrays: **NOT DONE**
- Particle deposition vs Jiang et al. (2011) for single panel: **NOT DONE**
- Field soiling rates vs Yue & Guo (2021) for Gobi Desert: **NOT DONE** (the previous calibration-disguised-as-validation in F12 was replaced)

### 7c. What constitutes adequate validation
For a CFD paper to be statistically defensible, the validation must include:
1. **Quantitative error metrics**: Report mean error, max error, RMSE, and R^2 for each validation comparison.
2. **Multiple independent validation cases**: At minimum, flow field (velocity profiles at 3+ locations downstream of panels) AND deposition (at least qualitative agreement with published single-panel data).
3. **Blind prediction**: The validation cases must not be used to calibrate model parameters. The Owen coefficient C = 0.25 and the saltation decay scale lambda_s = 2u*^2/g must be set a priori.

**Recommendation**: Before publishing any parametric results, validate the OpenFOAM flow field against at least one published experimental dataset with panels present. Report RMSE and correlation coefficient.

---

## 8. HIGH: Deposition Varies by 7-10 Orders of Magnitude -- Arithmetic Precision Concern

Panel deposition spans from ~10^-3 kg/(m*s) at H=0.1m to ~10^-11 kg/(m*s) at H=0.8m. This is:
- 0.1m: ~7.4e-4 to 1.0e-3
- 0.3m: ~5.5e-6 to 9.3e-6
- 0.5m: ~3.6e-8 to 6.8e-8
- 0.8m: ~2.0e-11 to 3.9e-11

The range spans **8 orders of magnitude**. The values at H=0.8m (O(10^-11)) are approaching machine precision limits for 64-bit float arithmetic (epsilon ~ 10^-16). Several concerns:

1. **Are the small values physically meaningful?** At H=0.8m with u_ref=8 m/s, the pass-through deposition is 1.9e-16 kg/(m*s). This is well within numerical noise. The paper should state a physical detection threshold below which deposition values are reported as "negligible" rather than as exact numbers.

2. **The exponential function exp(-H/lambda_s) at H=0.8, lambda_s=0.04 gives exp(-20) = 2.1e-9.** Values smaller than this (the 10^-16 result at u_ref=8) arise from the additional u*^3 factor. These values have no physical validity and should not be plotted or compared.

**Recommendation**: Define a physical detection limit (e.g., 10^-8 kg/(m*s) or equivalently a soiling rate below 0.01% per year) below which deposition is reported as "below detection threshold." This avoids implying false precision.

---

## 9. HIGH: Inter-Row Deposition Is Identically Zero in All 36 Cases

The `mean_inter_row` field is 0.0 for every case in `parametric_results.json`. The `inter_row_dep` arrays are all-zero vectors.

Physically, for the capture regime (H=0.1m), sand must deposit on the ground between panels. The deposition shadow behind inclined panels is a well-documented phenomenon in aeolian science (Dong et al. 2004). Zero inter-row deposition is physically impossible in the capture regime.

The cause: the sand flux gradient dq/dx (Eq. 6, main.tex:166) evaluates to zero or negative everywhere because the Python RANS solver's u_star_local varies smoothly. The `np.maximum(dep_rate, 0)` filter in `sand_transport.py:114` then clips all negative values to zero.

**Statistical impact**: One of the paper's five claimed output metrics is "inter-row sand accumulation depth." This metric is identically zero for all 36 cases. The paper cannot credibly claim to have studied this quantity.

**Recommendation**: This metric must produce non-zero, physically reasonable values before it can be reported. Either the Lagrangian particle tracking or a corrected Eulerian model is required.

---

## 10. MEDIUM: Reattachment Lengths Are All Zero

All 288 reattachment length values (36 cases x 8 rows) are 0.0 in the results. The RANS solver's detection algorithm (`rans_solver.py:334-335`) looks for the first grid point where `u_gnd > 0.05 * u_ref` downstream of the trailing edge. If u never drops below this threshold (because the mixing-length model cannot produce reversed flow), the reattachment length defaults to the search distance or zero.

The paper discusses "flow separation" and "reattachment distance" extensively (Sections 2.3, 6, 7) without disclosing that the solver cannot resolve these features. The planned Figure F9 (reattachment length vs tilt angle) cannot be populated with the current model.

**Recommendation**: When switching to OpenFOAM k-epsilon, re-extract reattachment lengths. Until then, remove all quantitative claims about reattachment from the manuscript.

---

## 11. MEDIUM: Sample Size for Regime Identification

The paper claims to identify three "distinct" transport regimes based on 36 cases. With only 4 values of H (the controlling parameter), the regime boundaries are determined by exactly one data point per transition:

- Capture to transitional: between H=0.1m and H=0.3m (one interval)
- Transitional to pass-through: between H=0.3m and H=0.5m (one interval)

This is insufficient to characterize a transition. Is it sharp or gradual? Where exactly is the boundary? With only 4 H values, the "regime boundaries at 2*lambda_s and 10*lambda_s" cannot be statistically resolved from the CFD data alone -- they are derived from the analytical formula.

**Recommendation**: Add at least 2-3 intermediate H values (e.g., 0.05, 0.15, 0.2, 0.4, 0.6 m) to characterize the transition region. This does not require more theta or S values -- just additional H slices at one (theta, S) combination.

---

## 12. MEDIUM: Sensitivity Analysis Is a One-at-a-Time (OAT) Design

The sensitivity study varies wind speed and grain size independently at three representative configurations. This is a one-factor-at-a-time design that:

1. **Cannot detect interaction effects** between wind speed and grain size.
2. **Uses only 3 configurations** (capture, transitional, pass-through) instead of sampling the full parameter space.
3. **Reports no sensitivity indices** (e.g., Sobol indices, Morris screening, or even simple partial derivatives).

For a paper that claims to identify "regime transitions," the sensitivity analysis should quantify:
- How the regime boundaries shift as functions of (u_ref, D_50) jointly
- Whether the boundary location H_crit is more sensitive to wind speed or grain size
- The confidence band on the design nomogram given realistic ranges of input uncertainty

**Recommendation**: At minimum, compute and report the local sensitivity dlog(dep)/d(H/lambda_s) and compare it to the analytical gradient from the exponential model. This would quantify how much additional information the CFD provides beyond the analytical formula.

---

## 13. MEDIUM: No Reproducibility Information

The paper does not specify:
- Software version for the Python solver (NumPy, SciPy versions)
- OpenFOAM version (mentioned as "OpenFOAM-10" in the text but not formally in the methodology)
- Random seeds (relevant if Lagrangian tracking is added later)
- Compute hardware specifications
- Whether results are bit-for-bit reproducible across different machines

For computational reproducibility, the solver settings (under-relaxation factors, convergence tolerance, grid parameters) should be tabulated.

---

## SUMMARY OF FINDINGS

| # | Severity | Issue | Impact |
|---|----------|-------|--------|
| 1 | CRITICAL | No uncertainty quantification on any result | All numerical claims are unsupported point estimates |
| 2 | CRITICAL | Shelter ratio invariant to wind speed (solver artifact) | Wind speed sensitivity is purely analytical, not computational |
| 3 | CRITICAL | Row spacing effect <1.6% (model limitation, not physics) | One-third of the parametric space is ineffective |
| 4 | CRITICAL | No GCI for mesh convergence | Discretization error is unknown |
| 5 | HIGH | H_panel definition wrong in code vs manuscript | All 36 S values are incorrect |
| 6 | HIGH | Convergence criteria inadequately specified/reported | Solution quality unverified |
| 7 | HIGH | No validation against experiments with panels | Zero credibility for flow predictions around obstacles |
| 8 | HIGH | 8 orders of magnitude range -- precision concern | Small values may be numerical noise |
| 9 | HIGH | Inter-row deposition identically zero (all 36 cases) | One of five claimed metrics is non-functional |
| 10 | MEDIUM | Reattachment lengths all zero | Key flow physics not resolved |
| 11 | MEDIUM | Only 4 H values to characterize 2 regime transitions | Transition boundaries are analytically imposed, not resolved |
| 12 | MEDIUM | OAT sensitivity design | Cannot quantify interaction effects or confidence bands |
| 13 | MEDIUM | No reproducibility information | Standard omission, easily fixable |

---

## SCORING

### Methodology (50%): 2/10
- Equations are correctly stated but the solver (Python mixing-length) cannot solve them
- The analytical sand transport model bypasses the flow field for the dominant variable (H)
- Row spacing has no pathway to influence results due to model structure
- No mesh convergence study with GCI
- Convergence criteria and residual levels unreported

### Results (30%): 1/10
- Zero uncertainty quantification on any result
- No error bars on any figure
- Inter-row deposition and reattachment lengths are non-functional metrics (identically zero)
- Shelter ratio is a geometric constant of the solver, not a physical prediction
- 8 orders of magnitude range with no discussion of meaningful precision limits

### Experimental Design (20%): 3/10
- The 36-case parametric matrix is well-structured in principle
- The sensitivity study covers wind speed and grain size
- However: only 4 H values to resolve 2 transitions, OAT design, no interaction effects
- H_panel definition error means S values don't match manuscript claims

---

## ACTIONABLE ITEMS (Priority Order)

### CRITICAL (Must fix before submission)
1. **Add uncertainty quantification** to all results. At minimum: propagate grain size range (100-300 um) and Owen coefficient range (C = 0.1-0.5) to produce uncertainty bands.
2. **Compute and report GCI** for the mesh independence study. Report for u* at ground and panel deposition rate.
3. **Fix the row spacing model** so S has a physical pathway to influence deposition (requires Lagrangian tracking or using local u_* in concentration profile).
4. **Validate against published experimental data** with panels present. Report RMSE and R^2.

### HIGH (Must fix for submission)
5. **Fix H_panel = L*sin(theta)** in `run_parametric_study.py:95` before running OpenFOAM cases.
6. **Report convergence metrics**: iteration counts, final residual levels, convergence history for representative cases.
7. **Define a physical detection threshold** for deposition rates below which values are reported as negligible.
8. **Fix inter-row deposition** to produce physically reasonable non-zero values.
9. **Remove reattachment length claims** until the solver can resolve separation.

### MEDIUM (Recommended)
10. **Add intermediate H values** (0.05, 0.15, 0.2, 0.4 m) to resolve regime transitions from CFD data rather than analytical formula.
11. **Compute local sensitivity indices** (dlog(dep)/d(H/lambda_s)) to quantify CFD value-add over analytical model.
12. **Report reproducibility information**: software versions, hardware, grid parameters in a table.

---

**Score: 2/10**

The paper reports 36 parametric cases with five output metrics, but the quantitative foundations are absent. No result has uncertainty bounds. No grid convergence index is reported. No validation against experiments with panels exists. Two of five output metrics (inter-row deposition, reattachment length) are identically zero in all cases. Row spacing -- one of three studied parameters -- has no measurable effect (<1.6%). The shelter ratio is invariant to wind speed, revealing that the sensitivity analysis is purely analytical. The transition from the Python solver to OpenFOAM (in progress) should resolve many of these issues, but the paper in its current state cannot make defensible quantitative claims.
