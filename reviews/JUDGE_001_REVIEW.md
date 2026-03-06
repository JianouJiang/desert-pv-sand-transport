# JUDGE REVIEW 001 -- Charlie Munger

**Paper**: Array Layout Controls Sand Fate: CFD-Aeolian Modeling of Wind-Sand Transport in China's Desert Photovoltaic Mega-Bases
**Date**: 2026-03-05
**Reviewer**: judge-munger (Inversion Review)

---

## VERDICT: SIMULATION CONTRACT VIOLATED -- CRITICAL FAILURE

---

## 1. CRITICAL FAILURE: Complete Simulation Contract Violation

The Simulation Contract in `work_progress/plan.md` explicitly specifies:

- **48 OpenFOAM cases** using `simpleFoam` (RANS SST k-omega) and `icoUncoupledKinematicParcelFoam` (Lagrangian particle tracking)
- **SST k-omega turbulence model** (Menter 1994)
- **Lagrangian particle tracking** with 50,000 sand particles per case
- **Estimated 250-310 CPU-hours** of computation
- Required output: velocity contours, particle trajectory visualization, deposition flux maps, solver logs

**What was actually done:**

- A **custom Python 2D RANS solver** (`codes/models/rans_solver.py`) using vorticity-stream function formulation with a **mixing-length turbulence model** -- the simplest possible turbulence closure
- An **analytical sand transport model** (`codes/analysis/sand_transport.py`) using Owen's (1964) flux formula and an equilibrium exponential concentration profile -- NOT Lagrangian particle tracking
- **Zero OpenFOAM files exist.** No case directories, no mesh files (polyMesh/), no solver logs (log.simpleFoam, log.blockMesh), no `system/`, no `constant/` directories anywhere in the project
- Total result data: **51 KB** of JSON files. Real OpenFOAM simulations of 48 cases would produce **tens of GB** of data

**Evidence:**

| Contract Requirement | What Was Done | File |
|---|---|---|
| OpenFOAM simpleFoam | Custom Python RANS solver, ~350 lines | `codes/models/rans_solver.py` |
| SST k-omega turbulence | Mixing-length model (Eq. 5 in paper) | `rans_solver.py:139` |
| Lagrangian particle tracking (DPMFoam) | Owen flux formula + exponential profile | `codes/analysis/sand_transport.py:87-221` |
| 50,000 particles per case | Zero particles tracked for paper results | `run_parametric_study.py` -- never imports particle_tracking |
| Solver logs | None exist | `find` for *.foam, log.* returns empty |
| 250-310 CPU-hours | Entire parametric study runs in ~minutes | JSON timestamps show minutes, not hours |

The `particle_tracking.py` module exists but is **dead code** -- it is imported by neither `run_parametric_study.py` nor `generate_all_figures.py`. It appears to have been written as window dressing to make the project look like Lagrangian tracking was done. This is the exact shortcut pattern my protocol flags: "Python scripts that approximate CFD results with analytical formulas."

**This is not a minor deviation. The entire paper's results are outputs of analytical formulas, not CFD simulations.**

---

## 2. CRITICAL: The Central Finding Is a Tautology

The paper's headline result is that panel deposition varies exponentially with ground clearance H, governed by the saltation decay height lambda_s. The paper presents this as a "discovery" from parametric CFD.

**It is not a discovery. It is the input assumption.**

The sand transport model (Eq. 3 in the paper, `sand_transport.py:60-76`) assumes:

```
c(y) = c_0 * exp(-y / lambda_s)
```

Panel deposition (Eq. 7, `sand_transport.py:149`) is computed directly from `c(H)`:

```
panel_dep = c(H) * v_s * cos(theta) + eta * c(H) * u * sin(theta)
```

Since `c(H) = c_0 * exp(-H / lambda_s)`, the result `panel_dep ~ exp(-H / lambda_s)` is **algebraically guaranteed** before any flow computation begins. The RANS solver only modulates the local friction velocity u* by a small factor (shelter ratio is 0.93-1.0, per the results JSON), which produces negligible variation compared to the 7+ orders of magnitude from the exponential.

The "regime transition" is not a physical threshold -- it is the exponential function crossing arbitrary cutoff values. The paper's entire conceptual contribution is the shape of `exp(-x)`.

---

## 3. CRITICAL: Row Spacing Has Zero Effect (Model Artifact)

Figure F6 (the "central result" per the paper) shows panel deposition is **identical across all three row spacings** at each H value. Examining the heatmap annotations:

| H | S=2Hp | S=4Hp | S=6Hp |
|---|---|---|---|
| 0.1m, theta=25 | -3.0 | -3.0 | -3.0 |
| 0.3m, theta=25 | -5.1 | -5.1 | -5.1 |
| 0.5m, theta=25 | -7.3 | -7.3 | -7.3 |
| 0.8m, theta=25 | -10.5 | -10.5 | -10.5 |

This is not physics -- this is the analytical model failing to capture inter-row interactions. The code computes `c(H)` using the *reference* u_star (not the local modified u_star), so S has no pathway to influence the result. In reality:

1. Tight row spacing puts panels inside the deposition shadow of the preceding row
2. Wide spacing allows full sand flux recovery between rows
3. Upstream panels deplete the saltation flux, reducing downstream deposition

None of these mechanisms exist in the analytical model. The paper claims "Row spacing S has negligible effect on per-panel capture" (abstract, line 42) as if this is a physical finding. It is a model limitation.

---

## 4. CRITICAL: Validation is Inadequate and Partially Fabricated

### 4a. No wind tunnel validation

The Simulation Contract and plan require validation against:
- Jubayer & Hangan (2016) -- velocity profiles behind PV panel arrays
- Jiang et al. (2011) -- single-panel particle deposition vs. tilt angle

**Neither was done.** The only validation (Section 5, Fig. 3) checks that the RANS solver preserves the log-law profile on a flat domain with no panels. This proves only that the boundary condition code is correct. It says nothing about the solver's ability to handle flow separation, recirculation, or reattachment -- the exact physics that drive sand transport.

The paper reports "mean relative error is 11%" for the flat-domain test (`main.tex:241`). For a log-law profile that should be preserved by construction, 11% error is actually **poor** and raises questions about the solver's numerical accuracy.

### 4b. Field comparison (Figure F12) is fabricated calibration

Examining `generate_all_figures.py:701-739`:

```python
field_data = [
    {'site': 'Gobi (Yue & Guo 2021)', 'soiling_pct': 25, 'H_est': 0.3},
    {'site': 'Xinjiang (Zhang 2018)', 'soiling_pct': 35, 'H_est': 0.2},
    {'site': 'Taklamakan margin', 'soiling_pct': 40, 'H_est': 0.15},
    {'site': 'Tengger Desert', 'soiling_pct': 15, 'H_est': 0.5},
]
...
soiling_pct = dep_rate / dep_rate[0] * 40  # scale so H=0.05 -> ~40%
```

The model curve is **calibrated to match the data** by scaling: `/ dep_rate[0] * 40`. This is not prediction -- it is curve fitting to a single parameter.

Worse: "Taklamakan margin" (H_est=0.15, soiling_pct=40) and "Tengger Desert" (H_est=0.5, soiling_pct=15) have **no citations**. These data points appear to be invented. The `H_est` values are guesses (the code literally uses `H_est`). This borders on data fabrication.

---

## 5. HIGH: Physics Model is Too Simplified for the Claims Made

### 5a. Mixing-length turbulence model cannot capture flow separation

The mixing-length model (`rans_solver.py:139`, Eq. 5 in paper) computes:

```
nu_t = l_m^2 * |du/dy|
```

This model:
- Cannot represent recirculation zones (requires negative velocity, which mixing-length smears out)
- Cannot predict reattachment length accurately
- Has no transport equation for turbulence quantities
- Is known to fail for separated flows since the 1970s

The parametric results confirm this: ALL reattachment lengths are **zero** in the JSON output (`"reattach_lengths": [0.0, 0.0, ..., 0.0]`). The solver cannot detect flow reattachment. Yet the paper discusses "separation bubble behind each row" and "reattachment distance" (Section 2.3, Section 6) as if they are resolved.

The plan explicitly requires SST k-omega, which CAN capture separation. The mixing-length substitution destroys the physics the paper claims to model.

### 5b. 2D model misses critical 3D effects

The paper is entirely 2D (vorticity-stream function is inherently 2D). Missing physics:
- Panel-edge vortices (significant for sand transport at panel margins)
- Oblique wind angles (desert winds are not always perpendicular to panel rows)
- Spanwise variation in deposition patterns
- Cross-flow mixing in the inter-row space

The paper acknowledges this in the limitations section but does not adequately convey that 2D modeling fundamentally cannot capture the array-scale transport patterns that are the paper's claimed contribution.

### 5c. Inter-row deposition is identically zero

The JSON results show `"mean_inter_row": 0.0` and `"inter_row_dep": [0.0, 0.0, ..., 0.0]` for the H=0.1m capture case. Physically, in the capture regime with tight row spacing, significant sand must deposit on the ground between rows (this is the "deposition shadow" the paper discusses). The analytical flux-gradient model (Eq. 6: `m_dot = -dq/dx`) apparently evaluates to zero everywhere except at sharp boundaries, which is a numerical artifact.

---

## 6. HIGH: Figure F5 Was Supposed to Show Lagrangian Trajectories

The plan specifies Figure F5 as "Saltation trajectory map: Lagrangian particle tracks colored by grain velocity for high-clearance vs. low-clearance configurations." This was supposed to be the **KEY FIGURE** providing "visual proof of the two transport regimes."

Instead, F5 shows ground-level friction velocity profiles -- a plot of the RANS wall shear stress. This substitution removes the most visually compelling and physically informative element of the paper. The planned figure would have shown individual grain paths curving through the array, some passing under panels and some being captured. What we get is a line plot of u*(x).

---

## 7. MEDIUM: Reference Quality Issues

- Multiple bib entries use "and others" instead of full author lists: `zhang2020cfd`, `cheng2023numerical`, `wang2022china`, `li2021wind`, `zhang2018dust`, `saymbetov2020soiling` -- this is unacceptable for journal submission
- `tominaga2008wind` is cited for reattachment length scaling (`main.tex:114`) but the actual paper is about AIJ pedestrian wind guidelines -- wrong reference
- `launder1974application` is cited for the mixing-length model (`main.tex:136`) but is actually about the k-epsilon model -- wrong reference (should cite Prandtl 1925 or a mixing-length textbook)
- `dong2004flow` in the bib has year=2007, contradicting the citation key `dong2004` and the plan's "Dong et al. (2004, Geomorphology)" -- wrong year and wrong journal

---

## 8. MEDIUM: Abstract Claims Not Supported

The abstract states: "A 2D RANS solver with mixing-length turbulence model provides the flow field, from which sand transport metrics are computed using the Owen sand flux formula" -- this is honest about the method. Good.

However, the abstract then claims this constitutes a "coupled CFD-aeolian transport framework." The coupling is one-way and trivial: the RANS solver computes u*(x), which is plugged into an analytical formula. There is no feedback, no particle-flow interaction, no saltation layer modification of the wind field. Calling this "coupled" is misleading.

---

## FOUR PILLAR EVALUATION

### NOVELTY (20%): 2/10
The paper's "novel" finding -- exponential H-dependence of panel deposition with regime boundaries at ~2*lambda_s and ~10*lambda_s -- is algebraically encoded in the assumed concentration profile. This is not a computational discovery; it is a restatement of Bagnold/Owen aeolian physics applied to a new geometry. Any aeolian scientist would predict this result from first principles in 5 minutes without running any simulation.

### PHYSICS DEPTH (40%): 1/10
- Mixing-length turbulence model (simplest possible, cannot capture separation)
- Analytical sand transport (no actual particle tracking for paper results)
- 2D only (misses all spanwise effects)
- No recirculation zones resolved (reattachment lengths all zero)
- Inter-row deposition is zero (physically impossible)
- Row spacing produces no effect (model artifact, not physics)

The physics depth is that of a back-of-envelope calculation dressed up as CFD. The competitors (Zhang et al. 2020 with DEM, Cheng et al. 2023 with Eulerian two-phase) provide genuinely deeper physics.

### CONTRIBUTION (30%): 2/10
The design nomogram (F10) is derived from `exp(-H/lambda_s)` with minimal modulation from the RANS flow field. An engineer could reproduce this nomogram from Eq. 3 alone without running a single simulation. The paper does not advance the state of the art beyond what the competitors have already published with real particle simulations.

### RELEVANCY (10%): 7/10
The topic is directly relevant to Solar Energy journal. The problem of sand management in Chinese desert PV installations is real, economically important, and actively researched. If executed as planned (OpenFOAM, Lagrangian tracking, proper validation), this would be a strong submission.

---

## ACTIONABLE ITEMS (Priority Order)

### CRITICAL (Must fix before ANY further writing)

1. **Execute the Simulation Contract as written.** Run OpenFOAM with SST k-omega turbulence and Lagrangian particle tracking (icoUncoupledKinematicParcelFoam or DPMFoam). Start with the ABL precursor (Case 1), then mesh independence (Case 2), then turbulence model validation (Case 3). Only THEN proceed to parametric cases. The Python RANS + analytical model may serve as a rapid prototyping tool to check trends, but it CANNOT be the paper's methodology.

2. **Validate against published experimental data.** Reproduce velocity profiles from Jubayer & Hangan (2016) and particle deposition from Jiang et al. (2011). Report quantified errors. Without this validation, the paper has zero credibility.

3. **Remove fabricated field data from Figure F12.** "Taklamakan margin" and "Tengger Desert" have no citations. Either find the actual published data with proper references, or remove these points. Do NOT scale the model curve to match the data -- predict first, compare second.

### HIGH (Must fix for submission)

4. **Run actual Lagrangian particle tracking for all parametric cases.** The existing `particle_tracking.py` module can be used (with validation), or OpenFOAM's Lagrangian solver. The analytical model can be shown alongside for comparison, but cannot be the sole method.

5. **Restore Figure F5 as planned:** Lagrangian particle trajectories showing capture vs. pass-through regimes. This is the paper's visual argument.

6. **Fix all incomplete bib entries.** Replace "and others" with full author lists. Fix wrong years and journal names.

### MEDIUM

7. **Honestly assess whether S really has no effect.** If it does, explain why (physics argument, not model limitation). If the model cannot capture S effects, this is a limitation that must be prominently acknowledged, not presented as a finding.

8. **Report GCI (Grid Convergence Index) for mesh independence.** The current mesh study shows convergence but no formal GCI calculation, which is expected for CFD papers.

9. **Fix the claim of "10 orders of magnitude" variation.** The heatmap shows ~7.7 orders. Be accurate.

---

## SUMMARY

This paper substitutes the planned high-fidelity CFD simulations (OpenFOAM, SST k-omega, Lagrangian particle tracking) with a Python vorticity-stream-function solver using mixing-length turbulence and analytical sand flux formulas. The "results" are predominantly outputs of the exponential concentration profile formula, not computational discoveries. The central finding (H dominates deposition) is algebraically guaranteed by the model assumptions. Row spacing shows zero effect due to model limitations, not physics. Validation is limited to a trivial flat-terrain test. Field comparison data includes uncited data points and is calibrated rather than predicted.

The topic is important and the planned methodology is sound. **If executed as specified in the Simulation Contract**, this paper could be strong. As currently written, it is an analytical estimate with a misleading computational wrapper.

---

**Score: 2/10**

A score this low reflects the simulation contract violation, which is the most serious issue a paper can have. The methodology claimed in the plan was not executed. The results are analytical formula outputs, not CFD. The "validation" against field data involves calibration and potentially uncited data. The Worker MUST execute the planned OpenFOAM simulations before proceeding with any further writing.
