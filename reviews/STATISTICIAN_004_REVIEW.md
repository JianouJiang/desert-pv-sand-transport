# STATISTICIAN REVIEW 004 -- Ronald Fisher

**Paper**: Array Layout Controls Sand Fate: CFD--Aeolian Modeling of Wind-Sand Transport in China's Desert Photovoltaic Mega-Bases
**Date**: 2026-03-06
**Reviewer**: statistician-fisher (Statistical Methods and Data Analysis Review)
**Previous reviews**: STATISTICIAN_001 (2/10), STATISTICIAN_002 (5/10), STATISTICIAN_003 (5/10)

---

## CONTEXT

Since STATISTICIAN_003, the Worker has completed convergence restarts for all 36 parametric cases (all now run to endTime=3000), re-postprocessed the results, regenerated figures, and made substantial manuscript revisions. The openfoam_results.json has been updated (timestamp 06:34 UTC, after all restarts completed). The manuscript now includes a full discussion of the negative shelter efficiency finding (Section 7.3), Jensen's inequality, the Venturi mechanism, S-effect explanation, and uncertainty bands on F9b.

This review assesses the updated data and manuscript against the priority list from STATISTICIAN_003.

---

## STATUS OF STATISTICIAN_003 ITEMS

| # | STAT_003 Item | Status | Notes |
|---|---|---|---|
| 1a | Convergence restarts to endTime=3000 | **DONE** | 30/36 formally converged; 6 reach 3000-iteration limit |
| 1b | C=[0.1, 0.5] uncertainty band on F9b | **DONE** | `fill_between` at lines 765--767 of `generate_openfoam_figures.py` |
| 1c | Negative shelter efficiency discussion | **DONE** | New Section 7.3 (main.tex:357--363) -- excellent |
| 2a | S-effect mechanism explanation | **DONE** | Incorporated into Section 7.3 (main.tex:363) |
| 2b | Amplification factor stability validation | **PARTIAL** | Manuscript states "<1% over last 500 iterations" (line 140) but no explicit data shown |
| 3a | Experimental validation case | **NOT DONE** | Still the single largest gap |
| 3b | H=0.05m capture regime case | **NOT DONE** | |

**Summary: 4 of 7 items fully done, 1 partially done, 2 not done.**

---

## CONVERGENCE ANALYSIS (Updated Data)

### Overall Status

| Category | Count | Cases |
|---|---|---|
| Formally converged (all init resid < 2e-4) | 30 | Converge in 1708--2763 iterations |
| Unconverged, reached 3000-iteration limit | 6 | All at S = 2Hp (tight spacing) |

The convergence rate improved from 5/36 (STAT_002) to 30/36. All 6 unconverged cases share S = 2Hp (tightest row spacing), confirming that flow acceleration between closely-spaced panels is the convergence bottleneck. The manuscript correctly identifies this pattern (main.tex:140).

### Initial Residuals for the 6 Unconverged Cases at Iteration 3000

| Case | H | theta | S | p_init | Uz_init | Other | Stationarity |
|---|---|---|---|---|---|---|---|
| 01 | 0.1 | 15 | 2Hp | 3.48e-4 (1.7x) | 5.90e-4 (3.0x) | below | unknown |
| 10 | 0.3 | 15 | 2Hp | 1.82e-4 (OK) | 3.50e-4 (1.8x) | below | 0.7% |
| 13 | 0.3 | 25 | 2Hp | 2.58e-4 (1.3x) | 1.15e-4 (OK) | below | 6.5% |
| 19 | 0.5 | 15 | 2Hp | 3.15e-4 (1.6x) | 3.99e-4 (2.0x) | below | 0.8% |
| 28 | 0.8 | 15 | 2Hp | 4.36e-4 (2.2x) | 4.44e-4 (2.2x) | below | **25.0%** |
| 34 | 0.8 | 35 | 2Hp | **1.64e-3 (8.2x)** | 1.23e-4 (OK) | k,eps above | **0.0075%** (stagnated) |

Values in parentheses show the multiple above the convergence criterion (2e-4). "Stationarity" is the relative change in p_init over the last iteration.

### Key Observations

1. **Case 34 (H=0.8, theta=35, S=2Hp)** is the most problematic. The pressure initial residual has decreased from 2.9e-3 (at iter 2000, per JUDGE_003) to 1.64e-3 (at iter 3000), but the stationarity of 0.0075% per iteration means it has reached a **limit cycle** -- it will not converge further without solver tuning. This case's shelter efficiency (-2.608) is the most extreme value in the dataset.

2. **Case 28 (H=0.8, theta=15, S=2Hp)** shows 25% change in p_init at the last iteration, meaning it is **still actively converging** and would likely converge with 500--1000 more iterations.

3. **Case 10 (H=0.3, theta=15, S=2Hp)** has p_init = 1.82e-4, which is **below** the convergence criterion. It appears the solver checked convergence on the Uz field (init = 3.50e-4) and stopped at the iteration limit. This case is arguably converged except for one field.

4. **Cases 01, 13, 19**: Initial residuals are O(10^-4), 1.3--3.0x above criterion. These are "nearly converged" -- final residuals are O(10^-5) to O(10^-6), supporting practical convergence.

### Manuscript Accuracy Issue

The manuscript states (line 140): "initial residuals of O(10^-4)." This is correct for 5 of the 6 unconverged cases but **incorrect for case 34**, which has p_init = O(10^-3). The characterization should be: "initial residuals of O(10^-4) for five cases and O(10^-3) for one case (H=0.8, theta=35, S=2Hp)."

### Data Integrity Issue: Case 01

Case 01 (H=0.1, theta=15, S=2Hp) has only a `2000` time directory -- no `3000` directory was created despite the solver log showing output to iteration 3000. All other 5 unconverged cases have a `3000` time directory. This means **case 01's postprocessed results use iteration-2000 data**, not iteration-3000 data. The impact is likely small (this case is in the transitional regime with shelter_eff = -0.114, a modest value), but the discrepancy should be corrected by re-running `reconstructPar` for this case.

### Convergence Parser Bug

The `check_convergence()` function (postprocess_openfoam.py:544) uses `re.findall(r'\nTime = (\d+)', combined_content)` to determine the iteration count. For cases where `reconstructPar -latestTime` reconstructed an earlier time (e.g., 2000), the postProcess and reconstructPar `Time =` entries appear AFTER the solver entries, causing the function to report the earlier time as the last iteration. This affects cases 01, 10, 13 (reported as 2000 iterations when the solver actually reached 3000).

**Recommendation**: Parse iteration count from the solver section only (before "Finalising parallel run" or "End"), not from the combined log including postProcess output.

---

## SECTION 7.3 ASSESSMENT: NEGATIVE SHELTER AND JENSEN'S INEQUALITY

Section 7.3 (main.tex:357--363) is an excellent addition. I assess each component:

### What is done well

1. **The 21/36 statistic** is prominently stated (line 359): "The shelter efficiency...is negative for 21 of the 36 parametric cases." This addresses my STAT_002 item #2 directly.

2. **The Venturi mechanism** is correctly described (line 361): "Venturi-like flow acceleration at panel leading edges creates localized peaks in u* (amplification factors up to 1.75x)."

3. **Jensen's inequality** is invoked correctly (line 361): "E[u*^3] > (E[u*])^3" with the correct conclusion that the mean sand flux can exceed the upstream value even when the mean friction velocity is below it.

4. **The S-effect direction** is explained mechanically (line 363): wider spacing reduces Venturi acceleration amplitude, reducing Q_array, which explains why wider spacing decreases deposition. This contradicts the original plan's hypothesis (wider spacing = less shelter = more deposition) and the manuscript correctly identifies it as counterintuitive.

5. **Connection to F8** is made (line 312): "first 2--3 rows of every configuration experience amplified sand transport (Q/Q_ref > 1, typically 2.5--3x)." This directly addresses the JUDGE_003 item #4.

6. **The abstract** (line 42) now includes the Jensen finding and the 21/36 statistic.

7. **The conclusions** (line 403) list this as the third principal finding, appropriately framed.

### What could be strengthened

1. The connection between Jensen's inequality and the **design recommendation** could be more explicit. The current text says wider spacing is "beneficial...for reducing sand-induced soiling via reduced flow acceleration" (line 363), but it does not update the nomogram guidance to explicitly state that tight spacing (S = 2Hp) should be avoided even in the pass-through regime because it amplifies ground-level transport.

2. The term "shelter efficiency" is retained despite being misleading for 21/36 cases. Consider adding a parenthetical note: "shelter efficiency (which is negative when the array amplifies flux)" the first time it is used in Section 6.

These are minor suggestions. The core physics discussion is sound and genuinely strengthens the paper.

---

## F9b UNCERTAINTY BANDS: VERIFIED

The figure code (generate_openfoam_figures.py:764--767) implements the C uncertainty band correctly:

```python
ax2.fill_between(H_arr, dep_arr * (C_lo / C_baseline),
                 dep_arr * (C_hi / C_baseline), ...)
```

With C_lo=0.1, C_hi=0.5, C_baseline=0.25, this gives the range [dep*0.4, dep*2.0], which is exactly the factor-of-five envelope I recommended in STAT_003.

The manuscript caption (line 333--334) references the shaded band. The regime boundaries are correctly shown as dashed lines that cut through the uncertainty bands, confirming the key claim that regime classification is insensitive to C.

---

## REMAINING GAPS

### CRITICAL: Experimental Validation (Unchanged from STAT_003)

This has now been flagged by all five reviewers across seven reviews. The paper validates only ABL profile preservation (trivial). One velocity-profile comparison against Jubayer & Hangan (2016) would:

1. Quantify the expected error of k-epsilon behind PV panels
2. Provide a credibility anchor for the 36 parametric results
3. Require ~2 hours of total effort

The limitation section (main.tex:387) acknowledges: "Quantitative validation against multi-row array experiments with particle deposition is not available." This is honest but does not substitute for the flow validation that IS available.

### HIGH: Case 34 Should Be Flagged

Case 34's pressure residual has stagnated at 1.64e-3 (8.2x above criterion). It will not converge without solver tuning (e.g., p relaxation from 0.5 to 0.3). Its shelter efficiency of -2.608 is the most extreme value and drives the bottom-left corner of the theta=35 heatmap. The manuscript should explicitly flag this case:

- Option A: Re-run with tighter relaxation (p=0.3, U=0.5) -- likely 30 minutes
- Option B: Note in Section 5.1 that "one case (H=0.8, theta=35, S=2Hp) exhibits persistent pressure oscillations (p_init = 1.6e-3 at 3000 iterations); its shelter efficiency of -2.6 should be treated as approximate"

### HIGH: Case 01 Data Integrity

Case 01 is postprocessed from iteration-2000 data because no 3000-time directory exists. Run `reconstructPar -latestTime` and `postProcess` again for this case, then re-run the full postprocessing pipeline.

### MEDIUM: Case 28 Could Converge with More Iterations

Case 28 (H=0.8, theta=15, S=2Hp) is still actively converging at 3000 iterations (25% per-iteration change in p_init). An additional 500--1000 iterations would likely bring it below the criterion. This would improve the convergence count to 31/36 or higher.

---

## QUANTITATIVE IMPROVEMENTS SINCE STAT_003

| Metric | STAT_003 | STAT_004 | Change |
|---|---|---|---|
| Formally converged cases | 5/36 (per JSON) | 30/36 | +25 |
| Negative shelter discussed | No | Yes (Section 7.3) | Major |
| Jensen's inequality explained | No | Yes | Major |
| S-effect mechanism explained | No | Yes | Major |
| Uncertainty bands on F9b | No | Yes | Done |
| F8 amplification discussed | Minimal | Explicit (line 312) | Improved |
| Experimental validation | No | No | Unchanged |
| Case 34 flagged | No | No | Unchanged |

---

## REFINED PRIORITY LIST (Remaining Items)

### Tier 1: Highest Impact per Hour

**1. Flag case 34 in manuscript** (~10 min)
- Add one sentence to Section 5.1 noting the persistent pressure oscillation
- Does not require re-running the case; just honest reporting

**2. Fix case 01 data integrity** (~15 min)
- Re-run reconstructPar + postProcess for case_01
- Re-run postprocess_openfoam.py to regenerate JSON
- Regenerate figures

**3. Correct "O(10^-4)" characterization** (~5 min)
- Line 140: change "initial residuals of O(10^-4)" to "initial residuals of O(10^-4) in five cases and O(10^-3) in one case"

### Tier 2: High Impact, Moderate Effort

**4. Experimental validation case** (~2 hours)
- Jubayer & Hangan (2016) velocity profiles
- Report RMSE and R^2
- Highest remaining credibility improvement

**5. Extend case 28 by 1000 iterations** (~15 min)
- Currently actively converging; would likely reach convergence criterion
- Improves the count from 30/36 toward 31+/36

### Tier 3: Nice to Have

**6. Fix check_convergence parser** (~15 min)
- Parse solver iterations separately from postProcess output
- Prevents iteration-count misreporting in future postprocess runs

**7. Run H=0.05m case** (~45 min)
- Validates capture regime from CFD data

---

## SCORING

### Has anything changed since STATISTICIAN_003?

**Yes -- substantially.** The data has been updated (30/36 converged, JSON regenerated), and the manuscript has been significantly revised:

1. Section 7.3 on Jensen's inequality and negative shelter is a **genuine contribution** -- this is the paper's most interesting physical insight, and it is now clearly presented with correct physics reasoning.

2. The abstract, conclusions, and figure captions have been updated to reflect the negative shelter finding.

3. F9b now shows the C uncertainty band, transforming it from unsupported point estimates to bounded predictions.

4. F8 interpretation now explicitly notes first-row amplification.

### Score Rationale

In STAT_003, I projected:
- If 34+/36 converge and negative shelter is discussed: 6/10
- If additionally F9b gets uncertainty bands: 6.5/10

The actual situation: 30/36 converge (short of the 34 target, but the negative shelter discussion and uncertainty bands are both done). The negative shelter discussion in Section 7.3 is better than I expected -- it's not just a paragraph but a substantive physics explanation that adds genuine scientific value. This compensates for the convergence shortfall.

Remaining deductions:
- No experimental validation: -1.0 (still critical, consensus across all reviewers)
- Case 34 stagnated and unflagged: -0.5
- Case 01 data integrity issue: -0.25
- 6/36 unconverged: -0.25 (partially compensated by practical convergence evidence)

---

**Score: 6/10** (up from 5/10)

The most significant improvement is Section 7.3, which transforms an undiscussed anomaly into the paper's strongest physics contribution. The convergence restarts, uncertainty bands, and expanded discussion all contribute to a paper that is now in "major revision" territory rather than borderline reject. The experimental validation remains the single most important missing element. Fixing the case 34 stagnation and case 01 data integrity are quick wins that would further strengthen the quantitative foundation. If the experimental validation case is added and the case-level issues are addressed, a score of 7/10 is achievable.
