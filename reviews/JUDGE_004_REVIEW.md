# JUDGE REVIEW 004 -- Charlie Munger

**Paper**: Array Layout Controls Sand Fate: CFD--Aeolian Modeling of Wind-Sand Transport in China's Desert Photovoltaic Mega-Bases
**Date**: 2026-03-06
**Reviewer**: judge-munger (Inversion Review)
**Previous reviews**: JUDGE_001 (2/10), JUDGE_002 (4/10), JUDGE_003 (4/10)

---

## VERDICT: GENUINE PROGRESS -- PAPER NOW IN MAJOR-REVISION TERRITORY

Since JUDGE_003, the paper has undergone substantive improvements: convergence restarts completed (30/36 formally converged, up from 5/36), a new Section 7.3 on the Jensen inequality / negative shelter mechanism (the paper's strongest physics contribution), uncertainty bands on F9b, explicit flagging of unconverged cases in F6 and the convergence paragraph, and expanded conclusions. The STATISTICIAN_004 review confirms the technical quality of these additions (score increased from 5 to 6).

This is the first review cycle where the CRITICAL items from previous rounds were actually addressed. I acknowledge the progress. The paper is no longer borderline reject; it is in major-revision territory. However, three significant gaps remain, and one (experimental validation) has been flagged by all five reviewers across eight reviews without action.

---

## JUDGE_003 CRITICAL ITEMS -- STATUS UPDATE

| # | JUDGE_003 Item | JUDGE_003 Status | Current Status | Change |
|---|---|---|---|---|
| C1 | Re-run 31 unconverged cases (endTime 3000) | NOT DONE | **DONE** | 30/36 converged |
| C2 | Experimental validation with panels | NOT DONE | **NOT DONE** | No change (4th consecutive review) |
| C3 | Discuss negative shelter efficiency finding | NOT DONE | **DONE** | New Section 7.3 -- excellent |
| H4 | Add uncertainty bands on key figures | PARTIALLY | **DONE** | F9b has C=[0.1, 0.5] band |
| H5 | Flag case 34 as unreliable | NOT FLAGGED | **PARTIALLY** | F6 caption flags it (line 296); convergence paragraph characterizes it (line 145) |
| H6 | Explain S-effect mechanism | NOT DONE | **DONE** | Section 7.3 (line 368) |
| M7 | Run one case at u_ref=14 m/s | NOT DONE | **NOT DONE** | No change |
| M8 | Run H=0.05m case | NOT DONE | **NOT DONE** | No change |

**Summary: 4 of 8 items fully addressed, 1 partially addressed, 3 not addressed. Two of three CRITICAL items resolved.**

---

## 1. CRITICAL (4th Consecutive Review): No Experimental Validation With Panels

This is now the most important remaining issue. It has been flagged by:
- JUDGE_001, JUDGE_002, JUDGE_003, JUDGE_004 (this review)
- STATISTICIAN_001, STATISTICIAN_002, STATISTICIAN_003, STATISTICIAN_004
- EDITOR, ILLUSTRATOR

**Every reviewer, every round.** The paper validates only flat-terrain ABL profile preservation (main.tex:221--230), which is trivially satisfied by the Richards-Hoxey inlet conditions. This does not validate the solver's ability to capture:

1. Flow separation behind tilted panels
2. Reattachment length and wake recovery
3. Turbulence intensification in the gap between panels and ground

Published data exists:
- **Jubayer & Hangan (2016)**: Wind tunnel velocity and turbulence profiles at x/H = 1, 3, 5 downstream of PV panel rows. Already cited in the manuscript (line 69).
- **Shademan et al. (2014)**: 3D panel array with Cp and velocity data. Also already cited.

The manuscript itself acknowledges this gap (limitation #8, main.tex:392): "Quantitative validation against multi-row array experiments with particle deposition is not available in the open literature." This is an honest statement about *particle deposition* validation. But *flow* validation IS available, and the paper does not attempt it.

**Why this matters**: The entire parametric study rests on the k-epsilon model's ability to predict the u* amplification factor around panel arrays. Without a single flow-validation case showing the model captures wake physics behind panels, the 36-case parametric results lack a credibility anchor. The analytical sand transport model (Owen flux + exponential profile) is standard and well-established; it is the CFD flow field that needs validation. One case comparing simulated velocity profiles downstream of a panel to Jubayer & Hangan (2016) data would:

1. Quantify the expected error (typically 20-40% for k-epsilon behind bluff bodies)
2. Demonstrate the solver captures the separation/reattachment physics
3. Provide a quantitative basis for the GCI uncertainties already reported

**Time estimate**: ~2 hours (30 min setup, 12 min run, 1 hour post-processing and figure).

**This is not a new request.** It has been the highest-ROI remaining improvement since JUDGE_002. I will not increase the score above 5.5/10 without it.

---

## 2. HIGH (Reiterated): Simulation Contract Deviation -- No Lagrangian Particle Tracking

The plan.md specifies Lagrangian particle tracking throughout:

- Line 8: "Eulerian-Lagrangian particle tracking (DPMFoam / icoUncoupledKinematicParcelFoam)"
- Line 9: "Eulerian-Lagrangian particle tracking for saltating sand grains"
- Line 43-51: Case schedule specifying Lagrangian tracking for all 48 cases
- Line 106: Figure F5 specified as "Lagrangian particle tracks colored by grain velocity"
- Line 277: Methodology section specifying "Lagrangian particle tracking (equations of motion: drag, gravity, Saffman lift)"

The manuscript instead uses an analytical Owen flux model with an exponential concentration profile (main.tex:164--174). Line 166 explicitly justifies the substitution: "Rather than tracking individual particles through the flow field, we employ an analytical sand transport model...This approach is standard in aeolian engineering and avoids the statistical noise inherent in Lagrangian tracking with limited particle numbers."

**Assessment**: This is a significant methodology deviation from the simulation contract, though the justification given is physically reasonable. The analytical approach IS standard in aeolian engineering, and the Owen flux formula IS the foundation of most field-scale sand transport modeling. The key physical insight of the paper (Jensen's inequality causing negative shelter efficiency) would not be different with Lagrangian tracking. However:

1. **The plan promised Lagrangian tracking as a differentiator** (plan.md line 199: "Lagrangian particle tracking capturing individual saltation hop mechanics for PV arrays: NOT DONE in a parametric study" -- listed as a gap this paper would fill).
2. **The codes/models/particle_tracking.py file exists** but is dead code -- never imported by any production script. This is a remnant of an abandoned implementation path.
3. **The Figure F5 specification** called for particle trajectory visualizations showing the capture vs. pass-through regimes. The current F5 (friction velocity profiles) is useful but different from the planned figure.

This is not CRITICAL because the analytical approach is scientifically defensible and the paper honestly describes what it does. But it should be acknowledged in the limitations section. Currently, the paper says "This approach is standard" (line 166) as if it were always the plan, rather than a deliberate simplification from the originally intended Lagrangian method. Adding one sentence noting that Lagrangian tracking would enable resolution of non-equilibrium saltation effects near the panel array (which the equilibrium analytical model cannot capture) would be more honest.

---

## 3. HIGH: Case 34 Flagging Is Incomplete

The manuscript now flags case 34 in two places:

1. **Convergence paragraph (line 145)**: "the sixth (H=0.8 m, theta=35, S=2Hp) exhibits persistent pressure oscillations with initial residual O(10^-3) and its quantitative results should be treated as approximate"
2. **F6 caption (line 296)**: "the red-bordered cell...exhibits persistent pressure oscillations and its result should be treated as approximate"

These are good additions. However, STATISTICIAN_004 identifies two remaining issues:

**a) The "O(10^-4)" characterization is misleading.** Line 145 states: "Five of these cases have initial residuals of O(10^-4)." STATISTICIAN_004 data shows case 01 has Uz_init = 5.90e-4 (3.0x above criterion), which is marginally O(10^-4) but arguably O(10^-3.2). The characterization should explicitly state that one case (case 34) has initial residuals of O(10^-3) while five have O(10^-4). The current text does separate case 34, which is good, but the "O(10^-4)" for the remaining five should acknowledge that some fields in some of these cases are 2-3x above the criterion.

**b) Case 01 data integrity.** STATISTICIAN_004 reports that case 01 has only a `2000` time directory despite running to iteration 3000. This means case 01's postprocessed results use iteration-2000 data. The impact is likely small (this case is in the transitional regime with shelter_eff = -0.114), but it is a data integrity issue that should be corrected.

**c) Case 34's shelter efficiency of -2.608 is the most extreme value in the dataset** and drives the bottom-left corner of the theta=35 heatmap. The red border in F6 is appropriate, but the Discussion's use of this value should include a caveat. Currently, Section 7.3 (line 364) states "for H=0.8 m, theta=35, and S=2Hp, the array-averaged flux is 3.7x the undisturbed upstream value" without noting this is from the unconverged case.

---

## 4. HIGH (New): Section 7.3 Needs to Inform the Design Recommendation

Section 7.3 is the paper's strongest physics contribution. The Venturi-Jensen mechanism is clearly explained, the connection between spatial u* variability and net flux amplification is correct, and the link to the S-effect is well-drawn. However, the finding that 21/36 cases show NEGATIVE shelter efficiency has implications for the design recommendation that are not fully propagated.

The current design guidance (line 342): "Configurations with H < 0.15 m should be avoided entirely at sites with active sand transport." But the negative shelter data shows that even at H = 0.5-0.8 m with S = 2Hp, the panels AMPLIFY ground-level transport. This means:

1. **Tight spacing should be explicitly warned against**, not just for panel soiling but for ground erosion. The nomogram (F10) shows contours in (H, theta) space but does not include a spacing axis or annotation.
2. **The term "shelter efficiency" remains misleading.** It is negative for 21/36 cases. Consider defining it more carefully the first time it appears (line 333: "shelter efficiency (defined as 1 - Q_array/Q_upstream, negative when the array amplifies flux)") -- which the manuscript already does, but only in Section 7.1. In the abstract, the shelter efficiency is introduced without this clarification.

These are refinements, not fundamental problems. The core physics is sound.

---

## 5. MEDIUM: Sensitivity Claims Rest Entirely on Analytical Curves

F11a shows exp(-H/lambda_s) for three wind speeds. These are ANALYTICAL curves computed from the formula lambda_s = 2*u*^2/g. No additional OpenFOAM cases were run at different wind speeds. The paper states (line 210): "The amplification factors from the u_ref = 10 m/s simulations are applied to other wind speeds."

This assumption (Re-independence of amplification factors) is reasonable for the RANS equations but has not been verified. Running ONE case at u_ref = 14 m/s would confirm or refute the assumption in 12 minutes. This was flagged in JUDGE_002 and remains unaddressed. It is low-effort, moderate-impact.

---

## 6. MEDIUM: The 36-Case Parametric Space Has a Gap at the Capture Regime

The parametric study covers H in {0.1, 0.3, 0.5, 0.8} m. The capture regime is defined as H < 2*lambda_s = 0.08 m. No case samples this regime -- H = 0.1 m is already in the transitional regime. Running one case at H = 0.05 m would directly sample the capture regime and validate the regime boundary from CFD data. This was flagged by STATISTICIAN_002 and remains unaddressed.

---

## WHAT HAS GENUINELY IMPROVED SINCE JUDGE_003

1. **Convergence**: 5/36 → 30/36 formally converged. The remaining 6 cases are at S=2Hp (tight spacing), which is physically the most challenging configuration. The manuscript correctly identifies and explains this pattern.

2. **Section 7.3 (Jensen's inequality and negative shelter)**: This is an excellent addition -- the paper's most interesting physics contribution. The Venturi-Jensen mechanism is clearly articulated, the 21/36 statistic is prominently stated, and the connection to the S-effect is well-drawn. This transforms an undiscussed anomaly into a genuine scientific finding. STATISTICIAN_004 rates it "excellent."

3. **Abstract updated**: Now includes the Jensen finding (line 47): "panel arrays amplify ground-level sand flux in the majority of configurations (21/36)." This is honest and striking.

4. **Conclusions expanded**: Four principal findings (up from three), with the Jensen/amplification finding as the third. This appropriately elevates the new physics contribution.

5. **F6 hatching and flagging**: Unconverged cases are hatched; case 34 is red-bordered. This is good visual practice for parametric studies.

6. **F8 discussion enhanced**: Line 317 now explicitly states "first 2-3 rows of every configuration experience amplified sand transport (Q/Q_ref > 1, typically 2.5-3x)." This addresses JUDGE_003 item #4.

7. **F9b uncertainty bands**: The C=[0.1, 0.5] envelope transforms this from unsupported point estimates to bounded predictions. Correctly implemented per STATISTICIAN_004.

8. **Convergence reporting**: Line 145 provides detailed convergence characterization including iteration ranges, the S=2Hp pattern, case 34 flagging, and the <1% stationarity claim. This is thorough.

---

## FOUR PILLAR EVALUATION

### NOVELTY (20%): 5/10 (up from 4/10)
The Jensen inequality / negative shelter finding is genuinely novel. The aeolian PV literature does not contain this insight: that arrays can AMPLIFY net sand flux through the Venturi-u*^3 nonlinearity. This is a CFD finding that cannot be obtained analytically. However, it is an observation from the simulations, not a new model or theoretical framework. It would be strengthened by experimental confirmation.

### PHYSICS DEPTH (40%): 5/10 (up from 4/10)
- k-epsilon RANS resolves separation and acceleration patterns (F4, F5)
- Row-by-row flux progression shows real shelter cascading and front-row amplification (F8)
- Jensen's inequality mechanism correctly identified and explained (Section 7.3)
- S-effect mechanism explained through Venturi acceleration amplitude
- 30/36 cases formally converged (up from 5/36)
- BUT: No flow validation around panels (ABL-only validation is trivial)
- No Lagrangian tracking (significant plan deviation, though justified)
- Case 34 stuck in limit cycle, still included in quantitative claims (with caveat)
- No fine-mesh resolution of near-panel flow (fine mesh itself unconverged)

### CONTRIBUTION (30%): 5/10 (up from 4/10)
- Design nomogram backed by real CFD through amplification factors
- Three-regime framework (capture/transitional/pass-through) is actionable
- Uncertainty quantified and propagated to F9b
- Negative shelter finding has genuine practical implications for array design
- BUT: Quantitative accuracy unvalidated (no panel-flow validation)
- Nomogram does not integrate the tight-spacing warning from the Jensen finding
- 48 planned cases reduced to 36 (no wind speed or grain size sensitivity runs)

### RELEVANCY (10%): 7/10 (unchanged)
Topic directly relevant to Solar Energy. The Chinese desert PV context is timely and commercially important.

---

## ACTIONABLE ITEMS -- PRIORITY LIST

### CRITICAL (1 item -- 4th consecutive flagging)

1. **Add one experimental validation case** against Jubayer & Hangan (2016) velocity profiles downstream of PV panels. Compare simulated u/u_ref profiles at x/H = 1, 3, 5 to wind tunnel data. Report RMSE and R^2. This is the single highest-ROI improvement remaining. (~2 hours total effort.)

### HIGH (3 items)

2. **Fix case 01 data integrity**: Re-run `reconstructPar -latestTime` and `postProcess` for case_01 to ensure iteration-3000 data is used, then re-run the full postprocessing pipeline. (~15 minutes.)

3. **Propagate the tight-spacing warning to the design recommendation**: Add one sentence to Section 7.1 (near line 342) noting that S=2Hp configurations should be avoided in desert installations because tight spacing amplifies ground-level transport even in the pass-through regime (Section 7.3). The nomogram should include an annotation or note about the spacing dimension.

4. **Add caveat to case 34's extreme value in Section 7.3**: Line 364 states "the array-averaged flux is 3.7x the undisturbed upstream value" for the case flagged as unconverged. Add a parenthetical: "(from the approximately-converged case flagged in Table/Fig. X)."

### MEDIUM (3 items)

5. **Run one case at u_ref = 14 m/s** to verify Re-independence of amplification factors. 12 minutes of compute. Strengthens the analytical sensitivity analysis.

6. **Run one case at H = 0.05 m** to sample the capture regime. Currently no parametric case sits in H < 2*lambda_s. 15 minutes of compute + setup.

7. **Acknowledge the Lagrangian deviation in limitations**: Add one sentence to the limitations section noting that Lagrangian particle tracking would resolve non-equilibrium saltation effects near the panel array that the equilibrium analytical model cannot capture.

---

## SCORING TRAJECTORY

| Review | Score | Key Driver |
|--------|-------|------------|
| JUDGE_001 | 2/10 | Simulation contract violated (Python solver, no OpenFOAM) |
| JUDGE_002 | 4/10 | OpenFOAM pipeline built, but 31/36 unconverged, no validation |
| JUDGE_003 | 4/10 | Stalled -- cosmetic improvements only, critical items unaddressed |
| JUDGE_004 | **5/10** | 30/36 converged, Section 7.3 Jensen finding, uncertainty bands, S-effect explained |

The score increases by 1.0 point, reflecting genuine structural improvements:
- +0.5 for convergence (30/36 vs 5/36)
- +0.5 for Section 7.3 (negative shelter + Jensen mechanism)
- +0.25 for uncertainty bands on F9b
- +0.25 for explicit convergence reporting and case flagging
- -0.5 for no experimental validation (4th consecutive round)

### Path to Higher Scores

- **5/10 → 6/10**: Add the experimental validation case (Jubayer & Hangan 2016). This alone would add ~1.0 points.
- **6/10 → 6.5/10**: Fix case 01 data integrity, add caveat to case 34 in Section 7.3, propagate tight-spacing warning to design recommendation.
- **6.5/10 → 7/10**: Run u_ref=14 m/s and H=0.05 m cases, acknowledge Lagrangian deviation in limitations.

---

## SUMMARY

The paper has made its most significant progress since JUDGE_001→002 (Python→OpenFOAM transition). The Section 7.3 Jensen inequality discussion is a genuine scientific contribution that elevates the paper beyond a parametric screening study. The convergence improvements, uncertainty quantification, and honest case flagging demonstrate methodological rigor.

The single most important remaining action is the experimental validation case. It has been flagged unanimously by all reviewers for four consecutive rounds. The data exists (Jubayer & Hangan 2016, already cited in the paper), the effort is modest (~2 hours), and the impact on credibility is high. Every other issue is secondary to this.

---

**Score: 5/10**

The paper crosses from "reject" into "major revision with specific requirements" territory. The Jensen inequality finding gives it genuine scientific novelty. The convergence improvements give it adequate numerical rigor. What it lacks is the validation anchor that would make a reviewer trust the CFD results enough to accept the parametric study's quantitative conclusions. One validation case transforms this paper from "interesting framework, unvalidated" to "validated framework with genuine findings."
