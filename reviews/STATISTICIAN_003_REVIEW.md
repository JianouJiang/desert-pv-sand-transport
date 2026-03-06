# STATISTICIAN REVIEW 003 -- Ronald Fisher

**Paper**: Array Layout Controls Sand Fate: CFD--Aeolian Modeling of Wind-Sand Transport in China's Desert Photovoltaic Mega-Bases
**Date**: 2026-03-06
**Reviewer**: statistician-fisher (Statistical Methods and Data Analysis Review)
**Previous reviews**: STATISTICIAN_001 (2/10), STATISTICIAN_002 (5/10)

---

## CONTEXT

JUDGE_003 (4/10) was written after my STATISTICIAN_002 and confirms all findings from that review. The Worker has initiated the convergence fix (endTime 2000->3000): 10 of 31 unconverged cases are currently running in parallel processor directories (iterations 2060-2640), with 21 not yet restarted. None have been reconstructed or post-processed. The openfoam_results.json is unchanged from STATISTICIAN_002.

This is a focused follow-up review. I do not repeat the full analysis from STATISTICIAN_002. Instead I consolidate the cross-reviewer consensus, incorporate JUDGE_003's additional findings, and prioritize the remaining statistical items by effort-to-impact ratio.

---

## CROSS-REVIEWER CONSENSUS (All 5 Reviewers Agree)

The following items have been flagged by JUDGE, STATISTICIAN, EDITOR, and/or ILLUSTRATOR reviews. There is complete consensus:

| Item | Flagged By | Times Flagged | Status |
|------|-----------|---------------|--------|
| Convergence: re-run to endTime=3000 | J2, J3, S2 | 3 | IN PROGRESS (10/31 running) |
| Experimental validation with panels | J2, J3, S1, S2 | 4 | NOT DONE |
| Uncertainty bands on figures | J2, J3, S1, S2 | 4 | NOT DONE (text only) |
| Negative shelter efficiency discussion | S2, J3 | 2 | NOT DONE |
| S-effect mechanism explanation | S2, J3 | 2 | NOT DONE |

---

## STATUS OF STATISTICIAN_002 ITEMS

| # | STAT_002 Item | Status | Notes |
|---|---|---|---|
| 1 | Convergence clarification | IN PROGRESS | 10/31 cases running, 21 queued. endTime set to 3000 in all controlDicts. |
| 2 | Negative shelter efficiency discussion | NOT DONE | Manuscript unchanged. 21/36 cases show Q_array > Q_upstream. |
| 3 | GCI medium-mesh convergence | NOT DONE | Medium mesh still at 3000 iters, unconverged. |
| 4 | Uncertainty bands on figures | NOT DONE | Text discusses uncertainty; no figure modifications. |
| 5 | S-effect mechanism explanation | NOT DONE | Wider spacing decreases deposition via reduced Venturi, not discussed. |
| 6 | H=0.05m capture regime case | NOT DONE | |
| 7 | Experimental validation | NOT DONE (DEFERRED by Worker) | |

---

## NEW FINDING: Case 34 Reliability Concern

JUDGE_003 identifies that case_34 (H=0.8, theta=35, S=2Hp) has an initial pressure residual of **2.9e-3** at iteration 2000 -- **14.5x above the convergence criterion**. This is the most extreme configuration (highest panel + steepest tilt + tightest spacing), creating intense flow acceleration between panels.

**Statistical significance**: Case 34 produces the most extreme negative shelter efficiency in the dataset (-2.66). It is the data point that anchors the bottom-left corner of the theta=35 heatmap (F6) and the extremum in the shelter efficiency table I reported in STATISTICIAN_002. If this case's results are unreliable, the most dramatic values in the negative shelter finding are also unreliable.

**Recommendation**: After convergence to endTime=3000, re-examine case_34 specifically:
1. Did the initial residuals decrease below 2e-4?
2. If not, apply tighter under-relaxation (p=0.3, U=0.5) and extend to 5000 iterations.
3. If still unconverged, flag it in the heatmap and exclude from quantitative claims.
4. Report the number of formally converged cases (target: 36/36 or at minimum 34/36 with 2 flagged).

---

## REFINED PRIORITY LIST (By Effort-to-Impact Ratio)

The remaining work is well-defined. I rank by impact/effort ratio, which is the right optimization criterion at this stage:

### Tier 1: Highest Impact per Hour (do these first)

**1a. Wait for convergence restarts to complete, then re-postprocess** (~30 min active work)
- The 31 restarts are already running or queued
- After completion: `reconstructPar` all cases, re-run `postprocess_openfoam.py`, regenerate figures
- Expected outcome: 28-34 of 36 cases formally converged
- Impact: Resolves the most-flagged issue (3 reviews)

**1b. Add C=[0.1, 0.5] uncertainty band to F9b** (~15 min)
- Deposition is linear in C. The band is: current_line * 0.4 and current_line * 2.0
- Five lines of matplotlib: `ax.fill_between(H, dep*0.4, dep*2.0, alpha=0.2)`
- Impact: Transforms F9b from unsupported point estimates to bounded predictions

**1c. Write one paragraph on negative shelter efficiency** (~30 min)
- 21/36 cases show Q_array > Q_upstream
- Physical mechanism: Venturi acceleration at panel leading edges + Jensen's inequality (E[u*^3] > E[u*]^3)
- Front rows amplify (Q/Q_ref > 1 in F8), interior rows shelter, net depends on geometry
- Tight spacing amplifies more (explains S-effect direction)
- This transforms an undiscussed anomaly into a scientific finding
- Impact: Addresses findings from both S2 and J3; adds genuine physics depth

### Tier 2: High Impact, Moderate Effort

**2a. Explain S-effect mechanism** (~15 min, can be combined with 1c)
- Wider spacing DECREASES deposition because Q_array decreases (less Venturi amplification)
- This contradicts the plan's hypothesis (shelter-based reasoning)
- One paragraph in Discussion, referencing the negative shelter finding

**2b. Validate amplification factor stability over last 500 iterations** (~30 min)
- For 3 representative cases (converged + nearly converged + slow to converge):
- Extract u* at iteration 1500, 1750, 2000 (and 2500, 3000 after restarts)
- Report relative change: if < 1%, practical convergence is demonstrated
- This directly addresses the GCI concern (medium mesh also unconverged)

### Tier 3: Moderate Impact, Higher Effort

**3a. One experimental validation case** (~2-3 hours)
- Jubayer & Hangan (2016) velocity profiles at x/H = 1, 3, 5
- Report RMSE and R^2
- Highest-impact single addition for credibility but requires case setup and data extraction

**3b. Run H=0.05m case** (~15 min compute, 30 min setup)
- Currently no case in the capture regime (H/lambda_s < 2)
- H=0.05 gives H/lambda_s = 1.25, clearly capture
- Validates the regime boundary from CFD data rather than analytical formula

---

## STATISTICAL RECOMMENDATIONS FOR POST-CONVERGENCE

Once the 31 cases complete, the following statistical reporting should be added:

### Convergence Summary Table (supplementary or appendix)
```
Case | H | theta | S | Iterations | p_init_final | Uz_init_final | Converged
01   | 0.1 | 15  | 2Hp | XXXX     | X.Xe-Y       | X.Xe-Y       | YES/NO
...
```

### Report These Metrics
1. **Number of formally converged cases**: N/36 (target: >34)
2. **Worst final initial residual**: which case, which field, what value
3. **Mean and max initial residuals across all 36 cases**: demonstrates overall solution quality
4. **For case_34**: explicit note on convergence difficulty and result reliability

### Update Negative Shelter Statistics
After re-postprocessing with converged results:
1. Count how many cases still show negative shelter efficiency
2. Check whether case_34's shelter_eff = -2.66 changes significantly
3. Update the S2 Table (Section 2) if the numbers shift

---

## SCORING

### Has anything changed since STATISTICIAN_002?

**Results**: No. The openfoam_results.json is unchanged. Restarts are running but incomplete.

**Manuscript**: Text refinements from Worker round 4 were captured in my STATISTICIAN_002 review. No further changes since then.

**Reviews**: JUDGE_003 confirms and amplifies STATISTICIAN_002 findings. New detail on case_34 reliability.

### Assessment

The score cannot change until the data changes. The convergence restarts are the right action and are underway. Once complete + re-postprocessed + figures updated:

- If 34+/36 converge and negative shelter is discussed: **6/10**
- If additionally F9b gets uncertainty bands: **6.5/10**
- If additionally one validation case is added: **7/10**
- If additionally H=0.05m confirms capture regime: **7.5/10**

---

**Score: 5/10** (unchanged from STATISTICIAN_002 -- data not yet updated)

The score reflects the current state of the results, not the work in progress. The convergence restarts are underway (10/31 running) and represent the correct prioritization. Once these complete and the post-processing pipeline is re-run, I expect 3 of my 7 outstanding items to be substantially resolved. The remaining items -- negative shelter discussion, uncertainty bands on F9b, S-effect mechanism, and experimental validation -- require targeted writing and one additional figure modification. Total remaining effort: approximately 5-6 hours to reach 7/10 territory, plus the background compute time for restarts.
