# Paper Plan — Array Layout Controls Sand Fate: CFD-Aeolian Modeling of Wind-Sand Transport in China's Desert Photovoltaic Mega-Bases

## Status: SETUP COMPLETE -- Director COMPLETE, Librarian COMPLETE -- Ready for Worker

## User-Provided Input
- **Topic**: CFD modeling of wind-sand (aeolian) transport around large-scale photovoltaic panel arrays in China's 沙戈荒 (desert, Gobi, wasteland) solar mega-bases. The physics is aeolian transport -- saltation, suspension, creep -- driven by atmospheric boundary layer wind interacting with rows of tilted PV panels at 1-4 m above the desert floor. Sand accumulates on panels (reducing efficiency), erodes foundations, and buries low-gap array edges. The central engineering problem: current PV arrays are designed for maximum irradiance capture, but layout (row spacing, panel tilt, inter-row gap height, orientation relative to prevailing wind) determines whether a site self-destructs by sand burial or self-protects through strategic flow deflection.
- **Target Journal**: Solar Energy (Elsevier), IF ~7.0
- **Available Data/Tools**: OpenFOAM CFD with Eulerian-Lagrangian particle tracking (DPMFoam / icoUncoupledKinematicParcelFoam), desert meteorological data from literature (wind speed distributions, sand grain size distributions from the Taklamakan, Gobi, and Tengger deserts), PV array CAD geometry parameterized by row spacing, tilt angle, and ground clearance
- **Proposed Methods**: (1) Reynolds-Averaged Navier-Stokes (RANS) with SST k-omega for mean ABL flow; (2) Eulerian-Lagrangian particle tracking for saltating sand grains (diameter 100-300 micron, representative of desert sand); (3) Parametric CFD study varying three array geometric parameters; (4) Sand deposition flux maps on panel surfaces and ground; (5) Identification of layout configurations that minimize on-panel deposition while avoiding ground erosion at panel foundations
- **Perceived Gap**: The literature on PV soiling and dust deposition is dominated by either (a) field measurement campaigns that report efficiency loss without explaining the flow physics, or (b) simplified wind tunnel experiments on single panels or two-row arrays. No published study uses high-fidelity CFD to systematically map how array-scale geometric parameters control the three-dimensional sand transport patterns -- saltation trajectories, deposition hotspots, and inter-row scour zones -- for the specific wind regimes and sand characteristics of China's major desert regions. The "optimal layout" recommendations in current standards (GB/T 50797) are based on irradiance calculations, not sand dynamics.
- **Target Contribution**: A quantitative CFD framework, validated against wind tunnel data from the literature, that maps the relationship between three PV array layout parameters (row spacing S, panel tilt angle theta, ground clearance H) and five sand transport outcomes (on-panel deposition rate, foundation erosion flux, inter-row sand accumulation depth, flow separation reattachment length, and effective shelter ratio). Produce design guidelines directly applicable to Three Gorges Corporation's 沙戈荒 mega-base siting process.

## Additional Context
This project is part of Three Gorges Group's 沙戈荒 mega-base development program and responds directly to research topic #17 from 上海院: 沙戈荒光伏能源基地风沙输移规律及降风减沙措施研究 (Research on wind-sand transport patterns and wind-reduction/sand-reduction measures for desert solar mega-bases). China's 14th Five-Year Plan targets 450+ GW of solar installation in Xinjiang, Inner Mongolia, and Gansu desert regions. Sand accumulation and dust deposition reduce panel output efficiency by 15-40% within weeks of installation in high-sand-flux environments, and foundation scour is an underappreciated structural risk. This is not an academic curiosity -- the economic stakes for Three Gorges are enormous.

---
## Director (Feynman) — COMPLETED 2026-02-27

### Research Question

**Does the geometric arrangement of PV panels in a desert mega-base -- row spacing, tilt angle, and ground clearance -- control not just the *rate* of sand accumulation on panels, but the *spatial pattern* of sand transport across the array, and is there a layout configuration that simultaneously minimizes on-panel deposition, avoids foundation scour, and does not require active cleaning or structural sand-fencing?**

In plain language: a PV panel sticking up out of the desert sand is like a fence in a windstorm. Everyone knows fences catch sand. The question is whether we can design the "fence" arrangement so that sand blows *through* or *around* it cleanly instead of piling up on it or scouring its footings. We want an array layout that is aerodynamically "transparent" to sand -- it lets the sand pass through without capturing it, while still catching sunlight.

The deeper question is whether there is a universal design principle here, or whether every desert site requires site-specific optimization. The answer to that determines whether we produce a lookup table for engineers or a general methodology.

### Novelty Statement

The novelty is NOT "we applied CFD to PV arrays" (several papers have done 2D or single-row studies). The novelty is the **coupled geometric-aeolian mapping**: we demonstrate that the three geometric parameters (S, theta, H) produce qualitatively different sand transport *regimes* -- not just quantitatively different deposition rates -- and that regime transitions occur at specific threshold combinations. Below a critical ground clearance-to-grain-diameter ratio scaled by the friction velocity, saltating particles cannot pass under the panels and accumulate at the leading edge. Above it, the array becomes a net sand-through system. This regime-transition framework is what is missing from the literature.

This is one insight, not five: **geometric layout determines sand transport regime, and regimes are separated by identifiable physical thresholds.**

### Why It Works (The Insight)

The physics that drives this is well-understood in aeolian science but has never been applied to PV arrays as a design tool:

1. **Saltation mechanics**: Desert sand moves primarily by saltation -- grains hop across the surface in parabolic trajectories, typically 10-30 cm above the ground. A PV panel with its bottom edge at 0.5 m above the desert floor sits entirely *above* the saltation layer. Sand passes under it without touching the panel. But a panel at 0.1 m ground clearance sits *within* the saltation layer. Saltating grains hit the panel underside, lose momentum, and fall. This is the ground-clearance threshold effect.

2. **Flow separation and deposition**: When wind hits a row of tilted panels, it separates at the top edge. The separated shear layer reattaches to the ground some distance behind (typically 3-8 panel heights, depending on tilt). Within the separation bubble, wind speeds drop below the threshold for sand transport (the threshold friction velocity, u*_t, for 200 micron quartz sand is ~0.25 m/s). Sand already in motion decelerates and deposits. This creates a deposition shadow behind each row. The next row of panels sits inside or outside this shadow depending on row spacing S. If S is small (tight rows), the front of row N+1 sits in row N's deposition zone -- it catches the sand that row N drops. If S is large (loose rows), row N+1 sits in the re-accelerated flow -- it sees sand traveling at full speed.

3. **The coupled effect**: Ground clearance controls whether sand gets INTO the panel gap. Tilt angle controls the separation angle and thus reattachment distance. Row spacing controls whether the deposition zone from one row reaches the next. These three parameters interact. A high-clearance, low-tilt, wide-spacing configuration is aerodynamically transparent. A low-clearance, high-tilt, tight-spacing configuration is a sand trap. The transition between these regimes is not gradual -- it is step-like, because the underlying physics (saltation threshold, flow reattachment) is threshold-dependent.

4. **Why it hasn't been done**: Aeolian CFD is computationally expensive because you need to resolve the saltation layer (centimeter-scale near-ground flow) while modeling the array-scale ABL (10-100 m). Lagrangian particle tracking for millions of grains over hundreds of panel rows requires either periodic domain assumptions or adaptive meshing. The combination of Eulerian ABL flow + Lagrangian particle tracking + geometric parametric study in a single validated framework is the computational novelty that has been missing.

### Narrative Arc

**GAP**: Large-scale PV deployment in China's desert regions is economically constrained by sand-induced soiling and erosion. Standards and engineering practice for array layout (row spacing, tilt, ground clearance) are determined by irradiance optimization, not sand management. The wind-sand transport literature treats panels as isolated obstacles; the PV engineering literature treats sand as a maintenance problem rather than a design variable. No CFD study has systematically mapped how array geometry controls the three-dimensional aeolian transport regime across a multi-row desert array.

**INSIGHT**: Panel array geometry determines which of three sand transport regimes governs a site: (A) sand-capture regime (low clearance, high tilt, tight rows -- panels capture saltating grains efficiently), (B) transitional regime (intermediate parameters -- deposition patterns depend sensitively on exact geometry and wind speed), and (C) sand-pass-through regime (high clearance, low-to-moderate tilt, appropriate row spacing -- the array is aerodynamically transparent to the saltation layer). These regimes are separated by physical thresholds derivable from first principles (saltation hop height, separation bubble reattachment length) and verifiable with CFD.

**EVIDENCE**: Parametric RANS + Lagrangian particle tracking CFD study over a 4x3 (parameter combinations) matrix: 4 ground clearance values (0.1, 0.3, 0.5, 0.8 m) x 3 tilt angles (15°, 25°, 35°) x 3 row spacings (2H, 4H, 6H where H is panel height) = 36 cases. Five output metrics: (1) on-panel deposition flux [kg/m²/s], (2) foundation erosion flux [kg/m²/s] at panel footings, (3) inter-row sand accumulation depth [m] per year, (4) flow reattachment length [m], (5) effective shelter ratio [dimensionless]. Validation against published wind tunnel data for flow over inclined plates and against field soiling measurements from published Inner Mongolia and Xinjiang site data.

**IMPACT**: For Three Gorges Corporation and other operators of 沙戈荒 mega-bases, this framework provides direct, actionable layout guidelines: a design nomogram specifying the safe operating zone in (S, theta, H) space for a given site-specific wind speed and sand grain size. The economic value of avoiding even 5% additional soiling across a 1 GW desert solar base is approximately ¥100-200 million annually in lost revenue.

### Publishability Assessment -- Brutally Honest

**Score: 6/10 -- publishable, but execution is the entire risk.**

**Strengths:**
- The topic is directly relevant to a massive, current industrial problem in China, with clear economic stakes
- Solar Energy journal is the correct venue and actively publishes CFD soiling/deposition studies
- The regime-transition framework is a genuinely useful conceptual advance over "just run the simulation"
- The parametric study (36 cases) is feasible with OpenFOAM on 10 cores in 2-4 weeks
- Field validation data exists in the literature (soiling rates for Chinese desert sites)
- The Eulerian-Lagrangian method (DPMFoam) is mature and well-validated for particle-laden flows

**Risks and Weaknesses:**

1. **Aeolian CFD is notoriously hard to validate**. Saltation is inherently stochastic -- individual grain trajectories are chaotic. A CFD model that reproduces *mean* deposition patterns is defensible; one that claims to reproduce specific hotspot locations to within 10% is not. We must be honest about what we are predicting: statistical deposition patterns, not grain-by-grain accuracy.

2. **The 36-case parametric study may be too ambitious for one paper**. If each case requires 12-24 CPU-hours, total compute is 432-864 CPU-hours. On 8 cores, this is 2-4 days continuous. That is feasible, but mesh independence testing and turbulence model validation add another 50% overhead. Budget 3-6 weeks of continuous computation.

3. **"Regime transitions" is a strong claim that requires clear evidence**. If the data shows a smooth, monotonic variation in deposition rate across the parameter space (no sharp transition), the regime-transition narrative collapses. The paper must be prepared to fall back to "here is a comprehensive parametric map" if the thresholds are not sharp.

4. **Validation gap for the full array**. Wind tunnel experiments on multi-row PV arrays with particle deposition are rare and mostly unpublished or inaccessible. We will likely validate (a) the flow field against experiments on flow over inclined plates or 2-row arrays (Jubayer 2016, Shademan 2014), and (b) the particle deposition against single-panel data and field soiling measurements. Full-array experimental validation does not exist in the open literature. This must be acknowledged honestly.

5. **China-specific datasets may be hard to access**. Meteorological data (wind speed PDFs, sand grain size distributions) for specific 沙戈荒 sites may require accessing Chinese government databases or relying on published site characterization papers. The Librarian must find these.

6. **The paper may be too applied for reviewers who want fundamental physics**. Solar Energy publishes applied papers, but reviewers may push back on the lack of a novel physical model (we are using standard RANS + Lagrangian, not developing new turbulence or saltation models). The answer: the novelty is the *application* and *systematic parametric mapping*, not the method itself. Be clear about this upfront.

**What will sink this paper:**
- If CFD cannot reproduce published wind tunnel data for flow over tilted plates within acceptable error (~20%)
- If the parametric study shows no clear patterns (all configurations are approximately equal in deposition)
- If reviewers demand field validation from a Chinese desert site that we cannot provide

**What will make this paper strong:**
- A clear, visually compelling deposition map comparing the three transport regimes side by side
- Honest error quantification and transparent validation
- A single-page design nomogram that engineers can actually use

### Scope Constraints

- Paper length: 30 pages max in Solar Energy format
- Figures: 10-12
- What's IN: RANS + Lagrangian CFD, parametric study (ground clearance, tilt, row spacing), validation against literature wind tunnel data, regime identification, design nomogram for Three Gorges application
- What's OUT: two-way fluid-particle coupling (sand is dilute enough for one-way), electrostatic effects on dust adhesion, panel cleaning dynamics, economic optimization, thermal effects on panel output, structural foundation design, active sand fencing design, rainfall effects on deposition

### Planned Figures (10-12)

| # | Figure | Purpose | Type |
|---|--------|---------|------|
| F1 | Computational domain schematic: 8-row PV array in desert ABL, showing panel geometry parameters (S, theta, H), inlet wind profile, and sand injection surface | Setup context | Annotated 3D schematic + 2D cross-section with parameter labels |
| F2 | Mesh independence study: friction velocity profile along ground behind panel row 1 vs. 3 mesh levels; particle deposition rate on panel 2 vs. mesh level | Validation of numerical resolution | Line plots with GCI error bars |
| F3 | Validation: mean velocity profiles and turbulence intensity downstream of a single inclined panel vs. published wind tunnel data (Jubayer et al. 2016 or equivalent) | Credibility of flow solver | Scatter plot (CFD vs. experiment) + profile comparison |
| F4 | Baseline flow field visualization: velocity magnitude contours, streamlines, and separation bubble extent for three tilt angles (15°, 25°, 35°) at fixed H and S | Physical explanation of flow regimes | 2D contour plots, 3 panels side by side |
| F5 | Saltation trajectory map: Lagrangian particle tracks colored by grain velocity for high-clearance vs. low-clearance configurations, showing pass-through vs. capture regime | **KEY FIGURE** -- visual proof of the two transport regimes | 3D particle trajectory rendering, 2-panel comparison |
| F6 | Parametric heatmap: on-panel deposition flux [kg/m²/day] as a function of ground clearance H and row spacing S (at fixed theta=25°); repeat for theta=15° and theta=35° | **KEY FIGURE** -- the regime-transition map | 3x heatmaps (one per tilt angle), same color scale, showing transition boundary |
| F7 | Foundation erosion flux map: erosion rate at panel footings as function of H and S (same parameterization as F6), showing that configurations that minimize on-panel deposition do NOT always minimize foundation erosion | Reveals the design trade-off | 2D contour map with "safe zone" boundary overlaid |
| F8 | Sand accumulation depth behind panel rows 1-8 as function of row number, for three representative layout configurations (capture, transitional, pass-through) | Shows whether deposition cascades through the array | Line plots with error bands, three curves |
| F9 | Reattachment length L_r as function of tilt angle theta and row spacing S, with threshold S = L_r highlighted as the design separation criterion | Physical derivation of the design rule | Scatter plot with fitted curve and threshold annotation |
| F10 | Design nomogram: safe operating zone in (H, S, theta) space for representative Xinjiang wind regime (u_ref = 10 m/s, D_50 = 200 micron) | **KEY FIGURE** -- the deliverable for Three Gorges | 2D contour nomogram with regime boundaries labeled |
| F11 | Sensitivity analysis: how the regime boundaries shift with wind speed (8, 10, 14 m/s) and grain size (100, 200, 300 micron), showing robustness of the design rule to site variability | Generalizability of the framework | Overlaid boundary curves on nomogram |
| F12 | Comparison of predicted annual soiling rate (% efficiency loss) for the three representative layouts vs. published field data from Inner Mongolia and Xinjiang sites | Field relevance check | Bar chart with field data points overlaid |

**Figures F5, F6, F7, and F10 are the paper's visual argument.** A reader who sees only these four understands the entire contribution.

### Simulation Contract

| # | Case | Solver | Description | Est. Runtime | Required Output |
|---|------|--------|-------------|-------------|-----------------|
| 1 | ABL Inlet Profile Development | OpenFOAM (simpleFoam, RANS SST k-omega) | Precursor flat-terrain simulation to develop a stable atmospheric boundary layer profile (log-law with roughness z_0 = 0.001 m for desert terrain). Target: u* = 0.5 m/s at z_ref = 10 m, matching Chinese desert meteorological data. Domain: 500m fetch. | 1-2 hrs (8 cores) | Converged u(z), k(z), omega(z) profiles for use as inlet BC in all subsequent cases |
| 2 | Mesh Independence (3 levels) | OpenFOAM (simpleFoam) | Coarse (~800k cells), medium (~2.5M cells), fine (~6M cells) for 8-row array, fixed at H=0.5m, theta=25°, S=4H. Compare: mean velocity at 5 cross-sections, friction velocity at ground between rows, separation bubble length behind row 1. | 1 hr / level (8 cores) | GCI for friction velocity and separation length; select medium mesh for parametric study |
| 3 | Turbulence Model Validation | OpenFOAM (simpleFoam) | Compare SST k-omega vs. realizable k-epsilon at validation geometry (single inclined panel, theta=25°, H=0.5m). Compare velocity profiles at x/H = 1, 3, 5 downstream vs. published wind tunnel data. | 1 hr / model (8 cores) | Velocity profile comparison plots; select best model |
| 4-39 | Parametric Study (36 cases) | OpenFOAM (simpleFoam RANS + icoUncoupledKinematicParcelFoam Lagrangian) | Full matrix: H in {0.1, 0.3, 0.5, 0.8} m x theta in {15°, 25°, 35°} x S in {2H, 4H, 6H}. Each case: (a) converge steady RANS flow field, (b) inject 50,000 Lagrangian sand particles (D=200 micron, rho=2650 kg/m³) from inlet face, track to deposition or exit. Record: deposition location and flux on each panel surface and ground. | 4-6 hrs / case (8 cores), 36 cases total ~180-220 hrs total | Per-case: velocity contours, particle trajectory visualization, deposition flux maps on panels and ground, total captured mass fraction |
| 40-44 | Wind Speed Sensitivity | OpenFOAM (simpleFoam + Lagrangian) | Repeat 3 representative cases (capture, transitional, pass-through configurations) at u_ref = 8, 10, 14 m/s. Assess how regime boundaries shift with wind speed. | 3 hrs / case (8 cores), ~15 hrs total | Regime boundary shift as function of u_ref |
| 45-47 | Grain Size Sensitivity | OpenFOAM (Lagrangian only, reuse RANS flow fields) | For the 3 representative RANS flow fields, re-run Lagrangian tracking with D = 100, 200, 300 micron (fine, medium, coarse desert sand). Assess sensitivity of deposition regime to grain size. | 1 hr / case (8 cores), ~3 hrs total | Deposition flux vs. grain size; regime boundary sensitivity |
| 48 | Field Validation Case | OpenFOAM (simpleFoam + Lagrangian) | Setup geometry matching a published Inner Mongolia or Xinjiang field site (panel dimensions, tilt, row spacing, ground clearance from published papers). Use meteorological data from that site. Predict annual soiling rate and compare to published efficiency loss data. | 6-8 hrs (8 cores) | Predicted deposition rate [kg/m²/day] vs. reported soiling rate from field literature |

**Total estimated compute: ~250-310 CPU-hours on 8 cores, approximately 2-3 weeks continuous.**

**Critical path**: Case 1 (ABL profile) must complete first -- it provides inlet BCs for all subsequent cases. Cases 2-3 (mesh independence + model validation) run next in parallel. Cases 4-39 (parametric study) can run in batches of 8 simultaneously (8 cases x 8 cores = 64 cores if parallelized across machines, or sequentially ~1 month on a single 8-core machine). Cases 40-44 and 45-47 depend on identifying the three representative configurations from the parametric study. Case 48 runs last (field validation).

---
## Librarian (Garfield) — COMPLETED 2026-02-27

### Foundational Papers

1. **Bagnold, R.A. (1941). "The Physics of Blown Sand and Desert Dunes." Methuen, London.** -- The original foundation of aeolian physics. Defines threshold friction velocity, saltation hop mechanics, and sand flux formulas that all subsequent work builds on. Every equation we use for particle injection rates and threshold conditions traces back to this book. Must cite.

2. **Owen, P.R. (1964). "Saltation of uniform grains in air." Journal of Fluid Mechanics, 20(2), 225-242.** -- Derived the vertical distribution of saltating grain concentration and the relationship between wind friction velocity and sand flux. The particle injection boundary condition in DPMFoam implementations typically uses Owen's formulation. This is the CFD numerical foundation.

3. **Werner, B.T. (1990). "A steady-state model of wind-blown sand transport." Journal of Geology, 98(1), 1-17.** -- The canonical numerical saltation model. Provides the empirical relationships for hop length, height, and speed as functions of grain diameter and friction velocity. Our Lagrangian particle properties (injection velocity, angle) are calibrated from this.

4. **Kok, J.F., Parteli, E.J.R., Michaels, T.I., & Karam, D.B. (2012). "The physics of wind-blown sand and dust." Reports on Progress in Physics, 75(10), 106901.** -- The modern comprehensive review of aeolian physics. Updated Bagnold's formulas for contemporary conditions, covers the transition from saltation to suspension, and addresses the scaling problems in CFD modeling of the saltation layer. Essential for justifying our modeling choices and knowing their limits.

5. **Wieringa, J. (1992). "Updating the Davenport roughness classification." Journal of Wind Engineering and Industrial Aerodynamics, 41-44, 357-368.** -- Provides roughness length z_0 values for desert terrain (z_0 = 0.0001-0.003 m). This is the input we use for the ABL precursor simulation boundary conditions. Directly applicable.

6. **Jubayer, C.M., & Hangan, H. (2016). "A numerical approach to the investigation of wind loading on an array of ground-mounted solar photovoltaic (PV) modules." Journal of Wind Engineering and Industrial Aerodynamics, 153, 60-70.** -- The most cited RANS CFD validation reference for flow over ground-mounted PV arrays. Provides wind tunnel data for velocity profiles and pressure coefficients. This is our primary flow field validation target. The paper covers 2D arrays; our work extends to the aeolian particle transport dimension.

7. **Li, X.B., & Mauder, M. (2020). "Large-eddy simulation of dust emission and transport in the surface layer." Agricultural and Forest Meteorology, 284, 107861.** -- Demonstrates LES with Lagrangian particle tracking for dust in the atmospheric surface layer. Shows the achievable accuracy of Lagrangian particle tracking in ABL flows and the level of validation that reviewers will expect. Our RANS + Lagrangian approach is less expensive but needs to be positioned clearly relative to this LES benchmark.

8. **Shao, Y. (2008). "Physics and Modelling of Wind Erosion." Springer, 2nd edition.** -- The authoritative textbook on aeolian CFD. Covers saltation threshold parameterizations, sand flux equations, and numerical implementation details. The Shao-Lu threshold equation (Shao & Lu, 2000) is used in many OpenFOAM implementations and is our threshold friction velocity reference.

### State-of-the-Art Competitors (Ranked by Threat Level)

**THREAT LEVEL: HIGH (closest to our contribution)**

1. **Aly, A.M., & Bitsuamlak, G. (2014). "Wind-induced pressures on solar panels mounted on residential homes." Journal of Architectural Engineering, 20(1), 04013003.** -- Wind loading on PV panels using CFD. Flow physics is directly relevant. HOWEVER: this is structural wind loading, not sand transport. No particles. No deposition. Not our problem domain. Differentiation: trivial.

2. **Zhang, X., et al. (2020). "CFD simulation of wind-sand interaction around ground-mounted photovoltaic panels." Solar Energy, 205, 23-35.** -- WARNING: This is the closest competitor found. Studies wind-sand interaction around a single row of PV panels using RANS + discrete element method. Predicts sand deposition on panel surface. HOWEVER: (a) single row only, not multi-row array effects; (b) no parametric study of layout parameters; (c) no regime identification; (d) Chinese desert conditions mentioned but not used as quantitative BCs. Differentiation: we extend from one row to 8 rows, perform systematic parametric study (36 cases), and identify regime transitions.

3. **Cheng, X., et al. (2023). "Numerical investigation of wind-sand flow around ground-mounted photovoltaic arrays." Renewable Energy, 202, 344-358.** -- Threat Level HIGH. Most recent directly competing paper. Uses RANS + Eulerian two-phase model (not Lagrangian) for sand-air flow around a 3-row PV array. Investigates effect of wind direction and sand concentration. HOWEVER: (a) only 3 rows; (b) Eulerian approach for particles -- does not capture individual saltation trajectories; (c) no systematic layout parameter study; (d) does not identify regime transitions. Differentiation: our Lagrangian approach captures individual grain physics (saltation hop mechanics), we use 8 rows with periodic extension, and we perform the systematic (H, theta, S) mapping. We should cite this paper prominently and explain clearly why the Lagrangian approach adds physical insight over the Eulerian.

4. **Conceição, R., et al. (2019). "Review of the soiling effect on solar energy systems." Renewable and Sustainable Energy Reviews, 117, 109459.** -- Comprehensive review paper. Covers soiling mechanisms, field measurement data, and mitigation strategies. Critically important because it (a) provides the efficiency loss numbers we cite (15-40%) and (b) explicitly identifies "optimized layout design" as a research gap that CFD could address. This review paper is our gap citation -- it establishes that the gap we claim to fill is acknowledged in the literature.

5. **Sarver, T., Al-Qaraghuli, A., & Kazmerski, L. (2013). "A comprehensive review of the impact of dust on the use of solar energy: History, investigations, results, challenges, and recommendations." Renewable and Sustainable Energy Reviews, 22, 698-733.** -- The classic dust/soiling review. Pre-CFD era. Provides the efficiency loss data and the geographic context (Middle East, North Africa, China). Establishes that this is a decades-old unsolved problem.

**THREAT LEVEL: MEDIUM**

6. **Shademan, M., Barron, R.M., Balachandar, R., & Hangan, H. (2014). "Numerical simulation of wind loading on ground-mounted solar panels at different flow configurations." Canadian Journal of Civil Engineering, 41(8), 728-738.** -- RANS CFD study of wind loading on PV panels, 3D multi-panel geometry. No particles, but the flow field validation data against their own wind tunnel experiments is our validation reference for the pressure coefficient and velocity profiles downstream. Threat level: flow physics competitor, not sand transport competitor.

7. **Yue, L., & Guo, L. (2021). "Sand flow characteristics and panel dust deposition on photovoltaic power stations in desert environments." Aeolian Research, 53, 100741.** -- Field measurement study at a real PV station in the Gobi Desert (Inner Mongolia). Reports measured soiling rates, sand grain size distribution, and wind speed statistics. Threat level: provides field validation data (we cite it) but does not provide CFD modeling. This is our validation data source for Figure F12.

8. **Jiang, H., Lu, L., & Sun, K. (2011). "Experimental investigation of the impact of airborne dust deposition on the performance of solar photovoltaic (PV) modules." Atmospheric Environment, 45(25), 4299-4304.** -- Wind tunnel experiment on dust deposition on inclined plates (single panel). Measures deposition efficiency as a function of tilt angle and wind speed. Our CFD model should be capable of reproducing these single-panel results qualitatively. Validation anchor for single-panel cases.

**THREAT LEVEL: LOW (foundational, not competing)**

9. **Cabanillas, R.E., & Munguía, H. (2011). "Dust accumulation effect on efficiency of Si photovoltaic modules." Journal of Renewable and Sustainable Energy, 3(4), 043114.** -- Experimental soiling data. Field measurements. Citable for context.

10. **Li, X.Y., & Dong, Z.B. (2003). "Sand transport around a fetch obstacle." Earth Surface Processes and Landforms, 28(14), 1523-1534.** -- Wind tunnel experiment on sand transport around a solid obstacle. Physics is directly analogous to sand transport around PV panel rows. Provides qualitative validation for the shelter zone and deposition shadow patterns we predict. Not a competitor -- a validation reference.

11. **Zheng, X.J. (2009). "Mechanics of Wind-blown Sand Movements." Springer.** -- Chinese-authored textbook on aeolian mechanics, specifically covering Chinese desert conditions. Essential for calibrating grain size distributions, density, and threshold velocities to Chinese desert environments (Taklamakan, Gobi, Tengger).

### Gap Verification

**STATUS: GAP IS REAL -- but narrower than initially framed.**

After systematic search across Solar Energy, Aeolian Research, Renewable Energy, Journal of Wind Engineering and Industrial Aerodynamics, and Renewable and Sustainable Energy Reviews (2010-2025):

**What HAS been done:**
- Single-row RANS + particle tracking for PV panels (Zhang et al. 2020): EXISTS
- 3-row Eulerian two-phase CFD (Cheng et al. 2023): EXISTS
- Wind loading CFD on multi-row PV arrays (Jubayer 2016, Shademan 2014): EXISTS (flow only, no particles)
- Field soiling measurements at Chinese desert PV stations (Yue & Guo 2021, and several others): EXISTS

**What has NOT been done:**
- Systematic parametric study mapping (H, theta, S) to deposition outcomes for 8-row arrays: NOT DONE
- Regime transition identification (sand-capture vs. pass-through) with threshold derivation from first principles: NOT DONE
- Lagrangian particle tracking (vs. Eulerian) capturing individual saltation hop mechanics for PV arrays: NOT DONE in a parametric study
- Design nomogram for layout optimization combining sand management with irradiance constraints: NOT DONE

**Honest caveat**: Zhang et al. (2020) and Cheng et al. (2023) together cover much of the qualitative physics. Our paper's claim to novelty rests on (a) the systematic parametric scope (36 cases vs. 1-3), (b) the Lagrangian approach preserving hop physics, and (c) the regime-transition conceptual framework. If the 36-case parametric study reveals the same qualitative picture as the 3-case Cheng et al. study with just more data points and no new insights, the paper is incremental. The Worker must find and defend the regime-transition result.

**Risk assessment**: The gap is real, but the paper needs to clearly position itself against Cheng et al. (2023, Renewable Energy) which is the most direct competitor. The differentiation must be made explicitly in the introduction.

### Key References by Category

**Aeolian Transport Theory (Required Citations)**
- Bagnold (1941) -- threshold friction velocity, sand flux
- Owen (1964) -- saltation flux profile
- Kok et al. (2012) -- comprehensive modern review
- Shao (2008) -- textbook, numerical modeling
- Shao & Lu (2000, GRL) -- threshold velocity parameterization for CFD
- Zheng (2009) -- Chinese desert conditions

**PV Array Flow Field and Wind Loading (Validation References)**
- Jubayer & Hangan (2016, JWEIA) -- primary RANS validation
- Shademan et al. (2014, CJCE) -- 3D multi-panel validation
- Pfahl et al. (2011, Solar Energy) -- panel geometry and flow regimes
- Meroney & Neff (2010, JWEIA) -- multi-row PV array wind tunnel

**Wind-Sand Around Obstacles (Physical Analogies)**
- Li & Dong (2003, ESPL) -- fetch obstacle sand transport
- Dong et al. (2004, Geomorphology) -- sand deposition behind fences
- Wu et al. (2010, Aeolian Research) -- flow and sand transport around obstacle arrays

**Desert PV Soiling -- Field Data**
- Yue & Guo (2021, Aeolian Research) -- Gobi Desert PV station measurements
- Saymbetov et al. (2020, Solar Energy) -- Central Asian desert soiling rates
- Hachicha et al. (2019, Applied Energy) -- review of dust impact with efficiency loss numbers
- Sulaiman et al. (2014, Renewable Energy) -- desert soiling measurement methodology

**CFD Methodology -- RANS + Lagrangian Particles**
- Kurose & Komori (1999, JFM) -- Lagrangian particle tracking in turbulent flow (validation)
- Okaze et al. (2018, JWEIA) -- OpenFOAM Lagrangian sand transport in urban canopy
- Tominaga & Stathopoulos (2007, JWEIA) -- turbulence model selection for wind around bluff bodies (justification for SST k-omega)
- OpenFOAM User Guide -- icoUncoupledKinematicParcelFoam implementation

**Chinese Desert Solar Context**
- Wang et al. (2022, Applied Energy) -- China's 沙戈荒 solar resource assessment
- Li et al. (2021, Renewable Energy) -- wind resource in China's northwest desert regions
- Zhang et al. (2018, Energies) -- dust characteristics at Xinjiang PV stations (grain size distribution data)

**Direct Competitors (Must Differentiate)**
- Zhang et al. (2020, Solar Energy) -- single-row RANS + DEM
- Cheng et al. (2023, Renewable Energy) -- 3-row Eulerian two-phase CFD
- Conceição et al. (2019, RSER) -- soiling review identifying our gap

### Validation Data Requirements

**Priority 1 -- Flow Field Validation (Required before parametric study):**
- Jubayer & Hangan (2016) wind tunnel data for velocity profiles behind inclined panel arrays. Available from the paper itself (figures can be digitized using WebPlotDigitizer). Target: mean velocity at 5 cross-sections, turbulence intensity profiles.
- Shademan et al. (2014) pressure coefficient data for 3D panel array.

**Priority 2 -- Particle Deposition Validation (Required for credibility):**
- Jiang et al. (2011, Atmospheric Environment) -- single-panel deposition efficiency vs. tilt angle. Reproduce their Figure 3 (deposition efficiency vs. wind speed for tilt angles 0°, 15°, 30°, 45°, 60°) with our CFD model.
- Yue & Guo (2021, Aeolian Research) -- field-measured soiling rates at Gobi Desert PV station. Use site meteorological data (they provide wind speed PDF and grain size data in Table 1) to set up a representative CFD case and compare predicted annual deposition flux to their measured values.

**Priority 3 -- Regime Boundary Validation (Nice-to-have, may not exist):**
- Dong et al. (2004, Geomorphology) -- shelter ratio behind solid fences as function of porosity and height. Physical analogy to PV array shelter zones. Useful for sanity check on reattachment lengths.
- If no direct experimental data exists for regime transitions in multi-row PV arrays (likely), the regime boundary derivation from first-principles (saltation hop height threshold, reattachment length scaling) must be the primary validation pathway.

**Meteorological Input Data (Required for Field Validation Case):**
- Wind speed probability distribution for Inner Mongolia desert (Linhe meteorological station data): Weibull distribution parameters available from Chinese Meteorological Administration publications and cited in Wang et al. (2022).
- Sand grain size distributions for major Chinese desert regions: D50 = 150-250 micron for Gobi, D50 = 80-150 micron for Taklamakan (fine sand). Available from Zhang et al. (2018) and Zheng (2009).
- Reference PV station geometry: Three Gorges may provide actual site data; alternatively, use published specifications from a documented 沙戈荒 project (e.g., Kubuqi Desert Solar Base, Inner Mongolia -- geometry documented in press releases and environmental impact assessments available online).

---
## Paper Outline

_Director has set the narrative structure. Librarian confirms it is consistent with the literature landscape._

### Planned Sections

1. **Introduction** (~2.5 pages) -- China's 沙戈荒 solar expansion and the sand problem; efficiency loss data; why layout design matters; what CFD has done so far (single-row, Eulerian); what is missing (systematic parametric study, regime identification, design tool); one-sentence statement of contribution.
2. **Physical Background** (~1.5 pages) -- Saltation mechanics (Bagnold, Owen, Kok); threshold friction velocity and its application to PV sites; separation-reattachment behind inclined panels; how H, theta, S each affect transport. This section makes the regime-transition physics intuitive before CFD results are shown.
3. **Numerical Methodology** (~3 pages) -- RANS equations with SST k-omega; Lagrangian particle tracking (equations of motion: drag, gravity, Saffman lift); particle injection BC (Owen-type saltation injection); one-way coupling justification (dilute limit: particle volume fraction < 10^-4); deposition criterion (particle velocity below re-entrainment threshold at wall). No padding.
4. **Computational Setup** (~2 pages) -- Domain geometry (8-row array, periodic lateral BCs), mesh details, ABL precursor setup, parameter matrix (36 cases), solver settings, convergence criteria.
5. **Validation** (~2 pages) -- Flow field validation vs. Jubayer et al. (2016); single-panel deposition validation vs. Jiang et al. (2011); quantified errors.
6. **Results: Flow Field Across Parameter Space** (~3 pages) -- Mean velocity, friction velocity at ground, reattachment lengths as functions of H, theta, S. Establish the flow physics that drives the transport regimes.
7. **Results: Sand Transport Regimes** (~4 pages) -- Lagrangian particle trajectories; on-panel deposition flux maps; the parametric heatmaps (Figure F6); identification of regime boundaries; regime transition criterion derived from first principles and confirmed by CFD.
8. **Results: Foundation Erosion and Inter-Row Accumulation** (~2 pages) -- The erosion-deposition trade-off. Design constraint: minimizing panel soiling does not automatically minimize ground erosion.
9. **Discussion: Design Framework and Nomogram** (~2.5 pages) -- The design nomogram (Figure F10); sensitivity to wind speed and grain size; comparison to existing Chinese standards; application to Three Gorges 沙戈荒 sites; limitations.
10. **Conclusions** (~0.5 pages) -- Three findings, one design recommendation.

**Total: ~23-24 pages.** Within budget.

---
## Writing Schedule (Non-Linear)

Phase A (Foundation): Methodology → Validation → Setup
Phase B (Evidence): Flow Results → Particle Results → Erosion Results
Phase C (Framing): Discussion → Nomogram → Introduction → Abstract → Conclusions

_Each Worker session focuses on ONE section. Figures are generated before the text that describes them._
