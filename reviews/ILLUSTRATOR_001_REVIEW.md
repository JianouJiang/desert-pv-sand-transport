# ILLUSTRATOR_001 — Figure Quality & Data Visualization Review (Tufte)

Date: 2026-03-06  
Scope: Current figures in `manuscript/figures/` (F1–F12) and their usage/captions in `manuscript/main.tex`.  
Reviewer stance: **Reviewer only** (no edits, no script execution).

## 0) Constraint & missing-standard gaps (important)

1) The agent spec asks to run `python3 figure_inspector.py {paper_dir}` first, but:
   - I cannot run scripts under the explicit “NEVER run scripts” constraint in this task.
   - `figure_inspector.py` is not present in this repo (search returned none).

2) The spec asks to read `related_papers/FIGURE_QUALITY_STANDARDS.md`, but `related_papers/` currently only contains `README.md` (no standards file, no competitor examples).

**Net effect:** I relied on **programmatic image/PDF metadata inspection** (resolution, PDF creator, color counts) + **selective visual checks** of each PNG.

## Addendum (2026-03-06) — incorporate new reviews + latest figure state

New reviews observed since ILLUSTRATOR_001 was written: `reviews/JUDGE_002_REVIEW.md`, `reviews/STATISTICIAN_002_REVIEW.md`, `reviews/EDITOR_001_REVIEW.md`.

### Corrections to my earlier review (factual)

1) **Grid default:** `codes/utils/plotting_utils.py` currently sets `"axes.grid": False` (not True). Any visible grids are therefore being enabled figure-by-figure (or via other rcParams), and should be removed/softened at the figure level.

2) **F6 numeric annotations:** The current `F6_parametric_heatmap_panel_deposition.png` *does* show per-cell numbers; my earlier note reflected the prior version.

3) **F12 mixed-metric axis:** The current `F12_field_comparison.png` is now split into two panels and explicitly states metric non-comparability (this is a major improvement; see below).

### What improved materially (credit)

- **F12 is now scientifically and visually honest:** two-panel layout separates Lu & Zhang (row-wise deposition gradient) from Tang et al. (field inhibition band) and adds an explicit “different metric; not directly comparable” note for this-study shelter efficiency. This removes the most serious “lie factor” risk.
- **F5 now marks panel locations** (grey bands), making the wake-cascade structure immediately legible.
- **F2(b) upgraded from a bar chart to a convergence plot** vs `1/sqrt(N_cells)`; better than bars, but still needs a stronger convergence narrative (order/extrapolation/uncertainty).
- **Label typography improved**: the visible “`~`” LaTeX artifacts in legends/titles appear largely removed in the latest figures (e.g., F11 now uses “m/s” with normal spacing).

### Remaining high-impact figure work (aligned with JUDGE_002 + STATISTICIAN_002 + EDITOR_001)

1) **Add uncertainty bands to at least one central quantitative figure (minimum: F9b).**
   - STATISTICIAN_002 is right: the paper discusses uncertainty sources, but the figures still present point estimates without envelopes.
   - Minimum credible step: show the `C ∈ [0.1, 0.5]` multiplicative band (±0.4…0.3 in `log10`, depending on definition) on deposition vs `H`, plus an additional band for the mesh factor (~2.5× from coarse→fine implies ±0.4 in `log10`).

2) **Make convergence “status” visible in F6 heatmap.**
   - JUDGE_002 notes only 5/36 cases formally converged. If unconverged cases remain in the heatmap, encode that (e.g., hatched cells, desaturated alpha, or a marker in each cell) so readers can see which values are less trustworthy.

3) **F2(b) needs observed-order/GCI logic in the graphic, not only in table text.**
   - Current F2(b) is a line+markers with “GCI: …” text. Add: (i) extrapolated value line, (ii) observed `p` annotation, (iii) percent changes coarse→medium→fine in a small inset, or (iv) include GCI as error bars.

4) **Revisit float/space efficiency for short-height wide figures (EDITOR_001 concern).**
   - Even if the PDF page sizes are not “thin strips”, the *visual content* in F1/F6/F7 is still horizontally dominant. Add vertical information density: insets, contour overlays, or stacking (e.g., one shared colorbar and a bottom strip showing regime boundary lines).

### Concrete implementation outline: uncertainty envelopes for F9(b) / deposition vs H (30+ lines)

```python
import numpy as np
from utils.plotting_utils import plt, COLORS

def plot_deposition_vs_H_with_uncertainty(H, Q_panel, lambda_s,
                                         C0=0.25, C_range=(0.1, 0.5),
                                         mesh_factor=2.5, ut_rel=0.15):
    """
    H: array [m]
    Q_panel: array, baseline panel deposition rate (kg/(m*s)) at C0, nominal u*_t, nominal mesh
    lambda_s: scalar [m] for regime boundary lines (or array if varying)
    """
    H = np.asarray(H)
    Q0 = np.asarray(Q_panel)

    fig, ax = plt.subplots(1, 1, figsize=(6.6, 3.6))

    # Baseline curve (log y)
    ax.semilogy(H, Q0, color=COLORS["primary"], lw=1.8, label="Baseline")

    # 1) Owen coefficient uncertainty: Q ∝ C (linear)
    C_lo, C_hi = C_range
    scale_lo = C_lo / C0
    scale_hi = C_hi / C0
    Q_C_lo = Q0 * scale_lo
    Q_C_hi = Q0 * scale_hi
    ax.fill_between(H, Q_C_lo, Q_C_hi, color=COLORS["primary"], alpha=0.18,
                    label=r"$C\\in[0.1,0.5]$ envelope")

    # 2) Mesh uncertainty: treat as multiplicative (e.g., factor 2.5 between coarse and fine)
    # Show as an additional, lighter band around the baseline (can be combined multiplicatively).
    Q_mesh_lo = Q0 / mesh_factor
    Q_mesh_hi = Q0 * mesh_factor
    ax.fill_between(H, Q_mesh_lo, Q_mesh_hi, color=COLORS["octonary"], alpha=0.10,
                    label=r"Mesh factor $\u00d7/\,\u00d7$%.1f" % mesh_factor)

    # Optional: combined envelope (C and mesh), if you want one band instead of two
    Q_comb_lo = Q0 * scale_lo / mesh_factor
    Q_comb_hi = Q0 * scale_hi * mesh_factor
    ax.fill_between(H, Q_comb_lo, Q_comb_hi, color=COLORS["secondary"], alpha=0.08,
                    label="Combined envelope")

    # 3) u*_t uncertainty affects regime thresholds (H/\u03bbs lines) more than absolute Q
    # If using \u03bbs = 2*u_*^2/g and u* scales with u*_t, then \u03bbs shifts ~ (1±ut_rel)^2.
    # Represent as a horizontal band in H for the regime boundaries.
    lam_lo = lambda_s * (1 - ut_rel)**2
    lam_hi = lambda_s * (1 + ut_rel)**2
    H2_lo, H2_hi = 2*lam_lo, 2*lam_hi
    H10_lo, H10_hi = 10*lam_lo, 10*lam_hi

    ax.axvspan(H2_lo, H2_hi, color='r', alpha=0.10, lw=0)
    ax.axvspan(H10_lo, H10_hi, color='g', alpha=0.08, lw=0)
    ax.axvline(2*lambda_s, color='r', ls='--', lw=1.2)
    ax.axvline(10*lambda_s, color='g', ls='--', lw=1.2)
    ax.text(2*lambda_s, 0.95, r"$H=2\\lambda_s$", transform=ax.get_xaxis_transform(),
            ha='left', va='top', fontsize=8, color='r')
    ax.text(10*lambda_s, 0.95, r"$H=10\\lambda_s$", transform=ax.get_xaxis_transform(),
            ha='left', va='top', fontsize=8, color='g')

    ax.set_xlabel(r"Ground clearance $H$ [m]")
    ax.set_ylabel(r"Panel deposition [kg/(m$\u00b7$s)]")
    ax.set_title("Deposition vs clearance with uncertainty envelopes")
    ax.legend(frameon=False, loc="lower left", fontsize=8)
    ax.grid(False)
    fig.tight_layout()
    return fig
```

This directly addresses STATISTICIAN_002’s “minimum credible uncertainty visualization” without changing the underlying model.

## Addendum (2026-03-06, later) — incorporate JUDGE_003 + STATISTICIAN_003

New reviews observed after the prior addendum: `reviews/JUDGE_003_REVIEW.md`, `reviews/STATISTICIAN_003_REVIEW.md`.

### New/strengthened figure requirements (consensus items)

1) **Convergence must be visible in the figures (not buried in text).**
   - JUDGE_003 reiterates that a large fraction of cases are not formally converged at the iteration cutoff and highlights at least one “worst-case” geometry.
   - From a visualization standpoint: if F6 (and any derived map/nomogram) includes unconverged cases, it must **encode solution status** (e.g., hatch overlay, alpha desaturation, or a small corner marker per cell). Otherwise the heatmap communicates false certainty.

2) **Negative “shelter efficiency” (flux amplification) needs a dedicated visual.**
   - JUDGE_003 emphasizes that many configurations show **Q-array amplification** (negative shelter in their sign convention). This is not a footnote; it changes interpretation and naming.
   - Recommendation: upgrade the current “shelter” storyline from a single curve to a **parameter-space map** (small multiples by `θ`) showing shelter sign and magnitude.

3) **Uncertainty bands: minimum deliverable remains F9(b) envelope.**
   - STATISTICIAN_003 reiterates: text-only uncertainty discussion is not enough. A shaded envelope on a central plot is the quickest credibility gain.

### Concrete implementation outline: “negative shelter” small-multiples map (30+ lines)

```python
import numpy as np
from utils.plotting_utils import plt, COLORS
from matplotlib.colors import TwoSlopeNorm

def plot_shelter_efficiency_map(H_vals, S_vals, theta_vals, shelter_eff):
    """
    H_vals: array shape (nH,)
    S_vals: array shape (nS,) (numeric, even if labels are 2Hp/4Hp/6Hp)
    theta_vals: array shape (nT,)
    shelter_eff: array shape (nT, nH, nS)
        Use the paper's sign convention; if negative means amplification, keep that.
    """
    nT = len(theta_vals)
    fig, axes = plt.subplots(1, nT, figsize=(7.2, 3.0), sharey=True)
    if nT == 1:
        axes = [axes]

    # Diverging map centered at 0: shelter ↔ amplification
    vmax = np.nanpercentile(np.abs(shelter_eff), 95)
    norm = TwoSlopeNorm(vmin=-vmax, vcenter=0.0, vmax=vmax)
    cmap = "RdBu_r"  # diverging, colorblind-check recommended; can swap to 'coolwarm'/'PuOr'

    for j, th in enumerate(theta_vals):
        ax = axes[j]
        Z = shelter_eff[j, :, :]  # (nH, nS)
        im = ax.imshow(Z, origin="lower", aspect="auto",
                       extent=[S_vals.min(), S_vals.max(), H_vals.min(), H_vals.max()],
                       cmap=cmap, norm=norm)
        ax.set_title(rf"$\theta={th:.0f}^\circ$")
        ax.set_xlabel(r"Row spacing $S$")
        if j == 0:
            ax.set_ylabel(r"Ground clearance $H$ [m]")

        # Overlay sign markers to make amplification unmissable in grayscale print
        # (e.g., '+' for shelter, '×' for amplification) at cell centers.
        for iH, H in enumerate(H_vals):
            for iS, S in enumerate(S_vals):
                val = Z[iH, iS]
                if np.isnan(val):
                    continue
                marker = "+" if val >= 0 else "×"
                ax.text(S, H, marker, ha="center", va="center",
                        fontsize=9, color="k", alpha=0.75)

        ax.grid(False)

    cbar = fig.colorbar(im, ax=axes, fraction=0.046, pad=0.03)
    cbar.set_label("Shelter efficiency (negative = amplification)")

    # Optional inset: histogram of shelter_eff across all cases (information-dense, 1 inset total)
    ax_in = axes[-1].inset_axes([1.05, 0.10, 0.28, 0.35])
    flat = shelter_eff.reshape(-1)
    flat = flat[np.isfinite(flat)]
    ax_in.hist(flat, bins=12, color=COLORS["octonary"], alpha=0.75)
    ax_in.axvline(0, color="k", lw=1.0)
    ax_in.set_title("All cases", fontsize=8)
    ax_in.set_yticks([])
    ax_in.set_xlabel("eff.", fontsize=8)
    ax_in.tick_params(axis="x", labelsize=7)
    ax_in.grid(False)

    fig.tight_layout()
    return fig
```

This figure would (i) make the “amplification” region visually obvious, (ii) provide a mechanism hook for the S-effect discussion, and (iii) prevent the term “shelter” from misleading readers.

## Addendum (2026-03-06, latest) — incorporate STATISTICIAN_004 + updated figure set

New reviews observed after the prior addendum: `reviews/STATISTICIAN_004_REVIEW.md` (and `reviews/EDITOR_001_REVIEW.md` updated).

### What is now fixed in the figures (measurable improvements)

1) **Uncertainty is finally plotted (key credibility win).**
   - `F9_shelter_and_regime.png` panel (b) now includes shaded envelopes around the deposition-vs-$H$ curves (consistent with the required “show the band, not just prose” standard).

2) **Convergence-status encoding has started (correct direction).**
   - `F6_parametric_heatmap_panel_deposition.png` now uses **hatched overlays** on selected cells, aligning with the reviewer consensus that unconverged/less-trustworthy cases must be visually flagged.

3) **Negative shelter / amplification is visible, not hidden.**
   - `F9_shelter_and_regime.png` panel (a) shows shelter efficiency crossing zero with $H$, reinforcing the need for sign-agnostic terminology and clear narrative.

### Remaining figure-level issues to address (still outstanding)

1) **F6 hatching needs a legend/caption key.**
   - Currently, hatched cells are not self-explaining in the graphic itself. Add a small legend item (“hatched = not formally converged at residualControl threshold” or “hatched = flagged/limit-cycle case(s)”) and ensure the caption uses the same wording.

2) **Case 34 (limit cycle) should be singled out graphically wherever it drives extrema.**
   - STATISTICIAN_004 identifies case 34 as a persistent outlier with $p_{init}=O(10^{-3})$ and extreme shelter amplification. If this point anchors extremes in any map/nomogram, mark it explicitly (e.g., “⚠” marker on the corresponding heatmap cell, and/or an asterisk note in the caption). Do not let it silently define the dynamic range.

3) **F2(b) remains an underpowered “convergence story”.**
   - The move from bars → a curve is good, but journal readers expect at least one of:
     - observed order $p$ annotation and an extrapolated value line,
     - GCI/error bars on the scalar,
     - or a compact inset showing percent-change shrinkage.
   - Without that, F2(b) still reads like “a plot was made” rather than “convergence was demonstrated.”

4) **A dedicated “amplification map” is still missing.**
   - Even with the improved narrative, the most information-dense way to communicate the negative-shelter phenomenon is still a small-multiples map (see prior addendum’s code outline). Consider promoting that to a main figure panel or supplement.

### Quick visual check notes on updated figures

- `F9_shelter_and_regime.png`: uncertainty shading is visually subtle and does not overwhelm the curves (good). Consider adding a legend entry clarifying what the band represents (e.g., $C$ range only vs combined).
- `F6_parametric_heatmap_panel_deposition.png`: hatching is visible but ambiguous (needs key). Numeric annotations remain legible.


## 1) Inventory (what exists)

Figures present (both `.pdf` and `.png`): `F1` … `F12`. All PDFs were created by Matplotlib (v3.10.8), dated Thu Mar 5, 2026 (per `pdfinfo`).

Programmatic PNG info (WxH):

| Fig | PNG size |
|---|---|
| F1 | 2047×1470 |
| F2 | 2083×989 |
| F3 | 2040×990 |
| F4 | 1975×1924 |
| F5 | 2040×990 |
| F6 | 2043×990 |
| F7 | 2043×990 |
| F8 | 2039×990 |
| F9 | 2039×990 |
| F10 | 1590×1290 |
| F11 | 2039×990 |
| F12 | 2040×1140 |

## 2) Global visual language (cross-figure consistency)

### What is already good
- **Vector outputs exist** for all figures (`.pdf`), which is the right default for journals.
- Baseline typography appears consistent with a serif family and large, readable labels.
- Panel labels `(a)`, `(b)`, `(c)` appear in multiple multi-panel figures and are generally consistent.

### Problems to fix early (high leverage)

1) **Gridlines are too prominent and too frequent** across most plots (F2, F3, F5, F8, F9, F10, F11, F12). This violates the “data-ink” principle: the grid is competing with the signal.  
   - If `codes/utils/plotting_utils.py` is the global style source, it currently sets `"axes.grid": True` and a non-trivial grid linewidth. Consider turning grids off by default and enabling only when they carry quantitative meaning (or reduce alpha further and use major ticks only).

2) **Legend/label typography contains literal tildes** like `0.1~m`, `u_ref = 10~m/s` (F5, F11, F12). In Matplotlib text this reads as a tilde, not a non-breaking space; it looks like a LaTeX artifact, not a professional label.

3) **Color semantics drift across figures.**
   - The repo defines a colorblind-friendly palette in `codes/utils/plotting_utils.py` (`COLORS`), but at least one figure uses saturated “pure red” markers/lines (F12) that do not appear to come from that palette.
   - Several figures use multi-hue colormaps for fields/heatmaps (F4, F6, F7). Without explicit “same scale, same colormap, same endpoints” across comparable panels, readers cannot compare panels accurately.

4) **Redundancy and “AI-lazy” chart forms appear in several figures.**  
   - A reviewer at JFM / PoF would expect richer encodings than standalone bar charts (F2b) and basic line/scatter summaries without uncertainty (F8, F9b, F12).

## 3) Per-figure review (what to keep / what to upgrade)

### F1 — `F1_domain_schematic`
**Purpose/story:** Strong: communicates geometry parameters and CFD domain in one figure.  
**What works:** Clear separation (a) schematic and (b) boundary conditions; annotations for `H`, `θ`, `S` are legible.  
**Issues:**
- Panel lines are thick; they dominate the schematic more than needed.
- “Saltation layer” is a thin stripe with a small label at far right; it reads as decoration unless you quantify its thickness/height range (even a single number).
- There are many distinct colors (blue panels, red/green/purple annotations, orange layer, brown ground text). This risks looking “PowerPoint-ish”.
**Recommendation:** Keep the structure but simplify ink: slightly thinner panel strokes, fewer hues (use 2–3 semantic colors total), and consider a small inset showing the saltation-layer scale (e.g., `λ_s` height).

### F2 — `F2_mesh_independence` (**AI-lazy risk**)
**Purpose/story:** Mesh convergence; crucial credibility figure.  
**Issues (major):**
- Panel (b) is a **bar chart** with no uncertainty, no convergence order, no GCI visualization. This is a classic “AI-lazy” form.
- Panel (a) curves show strong oscillations for the “fine” case; without indicating panel locations/geometry along `x`, the plot is hard to interpret physically.
**Upgrade target:** A convergence graphic that *shows the data and the convergence logic*, not just three bars.

**Concrete redesign (Python outline, 30+ lines):**
```python
import numpy as np
from matplotlib.gridspec import GridSpec
from utils.plotting_utils import plt, COLORS

def plot_mesh_independence(mesh_results, panel_x_regions, ustar_t):
    # mesh_results: list of dicts with keys: level, n_cells, dx_min, ustar_profile(x,u*),
    #              and scalars: deposition_rate, shelter_eff, ustar_max
    fig = plt.figure(figsize=(7.2, 4.2))
    gs = GridSpec(2, 2, figure=fig, height_ratios=[2.2, 1.0], width_ratios=[2.2, 1.0])
    ax_prof = fig.add_subplot(gs[0, 0])      # u*(x)
    ax_conv = fig.add_subplot(gs[0, 1])      # convergence plot (Richardson)
    ax_err  = fig.add_subplot(gs[1, :])      # relative error / GCI summary strip

    # (a) u*(x) with panel-row shading for physical context
    for (x0, x1) in panel_x_regions:
        ax_prof.axvspan(x0, x1, color='k', alpha=0.05, lw=0)
    color_map = {"coarse": COLORS["primary"], "medium": COLORS["secondary"], "fine": COLORS["tertiary"]}
    for mr in mesh_results:
        x = np.asarray(mr["ustar"]["x"])
        u = np.asarray(mr["ustar"]["ustar"])
        ax_prof.plot(x, u, lw=1.6, color=color_map[mr["mesh_level"]], label=f'{mr["mesh_level"]} ({mr["n_cells"]:,} cells)')
    ax_prof.axhline(ustar_t, ls='--', lw=1.0, color='0.2')
    ax_prof.set_xlabel(r'$x$ [m]')
    ax_prof.set_ylabel(r'$u_*$ [m/s]')
    ax_prof.set_title('(a) Friction velocity with panel locations')
    ax_prof.legend(frameon=False, loc='lower right')
    ax_prof.grid(False)  # keep ink for data

    # (b) Convergence: plot key scalar vs grid spacing h (or N^{-1/2})
    # choose one scalar shown in paper (e.g., panel deposition) and show Richardson extrapolation
    levels = ["coarse", "medium", "fine"]
    h = np.array([mr["h_char"] for mr in mesh_results])  # define consistently, e.g., min cell size or (1/sqrt(N))
    q = np.array([mr["sand_transport"]["panel_deposition"] for mr in mesh_results])
    ax_conv.plot(h, q, 'o-', color=COLORS["octonary"], lw=1.2)
    ax_conv.set_xlabel(r'Characteristic grid size $h$')
    ax_conv.set_ylabel(r'Panel deposition [kg/m/s]')
    ax_conv.set_title('(b) Convergence (not bars)')
    ax_conv.invert_xaxis()  # finer to the right, typical in CFD papers
    ax_conv.grid(False)

    # estimate observed order p and extrapolated value q_ext (simple 3-grid approach)
    # (guard against missing fine convergence; if fine invalid, explicitly annotate)
    if len(q) == 3:
        r21 = h[0] / h[1]
        r32 = h[1] / h[2]
        # simplified p estimate (assume r21≈r32); otherwise use iterative method
        p = np.log(abs((q[0]-q[1])/(q[1]-q[2]))) / np.log(r21)
        q_ext = q[2] + (q[2]-q[1])/(r32**p - 1.0)
        ax_conv.axhline(q_ext, color=COLORS["secondary"], ls='--', lw=1.2)
        ax_conv.text(0.98, 0.05, rf'$p\\approx{p:.2f}$'+'\n'+rf'$q_{{ext}}\\approx{q_ext:.2e}$',
                     transform=ax_conv.transAxes, ha='right', va='bottom', fontsize=8)

    # (c) Error strip: percent change coarse→medium, medium→fine, and reported GCI
    def pct(a, b): return 100.0*(b-a)/b
    deltas = []
    labels = []
    if len(q) >= 2:
        deltas.append(abs(pct(q[0], q[1]))); labels.append('coarse→medium')
    if len(q) == 3:
        deltas.append(abs(pct(q[1], q[2]))); labels.append('medium→fine')
    ax_err.bar(labels, deltas, color='0.6')
    ax_err.set_ylabel('Δ [%]')
    ax_err.set_title('Relative changes (should shrink with refinement)')
    ax_err.grid(False)
    fig.tight_layout()
    return fig
```
This replaces a decorative bar chart with a convergence narrative: **profiles + physical context + observed order + extrapolation + error shrinkage**.

### F3 — `F3_validation_loglaw`
**Purpose/story:** Validates ABL equilibrium preservation.  
**What works:** Two-panel logic is correct; data vs analytical line is clear.  
**Issues:**
- Caption claims “three downstream positions”, but the plot/legend reads like a single “outlet” dataset (visually I only see one series of points). Ensure caption matches figure content.
- Gridlines again are louder than needed.
**Recommendation:** If you truly have 3 stations, plot all 3 with subtle color/marker variations and direct labels at curve ends; otherwise correct the caption.

### F4 — `F4_flow_field_tilt_comparison`
**Purpose/story:** Flow field changes with tilt angle.  
**Issues (major):**
- Three **separate colorbars** repeat ink; readers must compare across panels but can’t be sure scales match visually.
- Colormap is multi-hue; consider a perceptually uniform sequential map for speed magnitude (e.g., `cividis`/`viridis`) unless the current map is rigorously chosen.
- There is substantial white space between panels; the flow region is a thin strip, so maximize data area.
**Recommendation:** Use a single shared colorbar, consistent `vmin/vmax`, add streamline overlay or a few quiver arrows to show direction changes, and annotate separation/reattachment lengths (key story).

### F5 — `F5_friction_velocity_regimes` (**borderline AI-lazy**)
**Purpose/story:** Ground friction velocity amplification along x, for multiple H.  
**Issues:**
- No explicit indication of **where rows are located** along `x`; the repeated wakes would be much clearer with row markers/spans.
- Legend uses `H = 0.1~m` etc (tilde artifact).
- Large title; could be reduced and replaced by in-plot direct labeling.
**Recommendation:** Add subtle vertical bands for each row (LE→TE), then directly label each curve near the downstream end to remove the legend.

### F6 — `F6_parametric_heatmap_panel_deposition`
**Purpose/story:** Central parametric result (H vs S, three θ).  
**What works:** Small multiples by θ are appropriate; clear axis labeling.  
**Issues:**
- Caption: “Numbers indicate log10 values” but I do **not** see value annotations in the current plot. Either add the numbers or remove that claim.
- Three separate colorbars consume a lot of ink; if scales are the same, use **one shared colorbar**.
- Colormap choice emphasizes aesthetics; ensure it is perceptually ordered and colorblind-safe. (The current looks like a “YlOrRd-ish” map; acceptable, but confirm monotonic luminance.)
**Recommendation:** Add contour lines at regime-relevant levels (e.g., `10^-6`, `10^-8`) and annotate the `H=2λ_s` and `H=10λ_s` lines directly on each panel.

### F7 — `F7_foundation_erosion_map`
**Purpose/story:** Trade-off map for foundation erosion.  
**Issues:**
- Colorbar label reads `u_*/u_*t - 1` (dimensionless), but caption says “erosion rate at footings.” Ensure the plotted quantity matches the narrative; otherwise readers will suspect inconsistency.
- Same small-multiples + multiple colorbar ink issue as F6.
**Recommendation:** If this is truly an erosion proxy, label it as such and state mapping in caption; if it’s actually `u_*` exceedance, title/caption should match that.

### F8 — `F8_accumulation_by_row` (**AI-lazy risk**)
**Purpose/story:** Row-by-row normalized flux progression.  
**Issues (major):**
- Simple multi-line plot with a legend; no uncertainty; no depiction of quasi-periodic “interior rows” claim beyond prose.
- Curves cross and the message is not immediate (“what should I see in 5 seconds?”).
**Upgrade target:** A compact visualization showing stabilization after row ~3 (e.g., slope/ΔQ per row; or heatmap row×H with an inset showing convergence).

**Concrete redesign (Python outline, 30+ lines):**
```python
import numpy as np
from utils.plotting_utils import plt, COLORS
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

def plot_row_progression(Q_by_H, rows=np.arange(1, 9)):
    # Q_by_H: dict {H_value: array(len(rows))} of Q/Q_ref
    H_vals = np.array(sorted(Q_by_H.keys()))
    Q = np.vstack([Q_by_H[H] for H in H_vals])  # shape: (nH, nRows)

    fig, (ax_hm, ax_slope) = plt.subplots(1, 2, figsize=(7.2, 3.6), gridspec_kw={"width_ratios":[1.35, 1.0]})

    # (a) Heatmap: row vs H reveals stabilization patterns immediately
    im = ax_hm.imshow(Q, aspect='auto', origin='lower',
                      extent=[rows.min()-0.5, rows.max()+0.5, H_vals.min(), H_vals.max()],
                      cmap='cividis')
    ax_hm.set_xlabel('Row number')
    ax_hm.set_ylabel(r'Ground clearance $H$ [m]')
    ax_hm.set_title('(a) $Q/Q_{ref}$ across array')
    cbar = fig.colorbar(im, ax=ax_hm, fraction=0.046, pad=0.03)
    cbar.set_label(r'$Q/Q_{ref}$')
    ax_hm.grid(False)

    # annotate “interior rows” region
    ax_hm.axvspan(3.5, rows.max()+0.5, color='w', alpha=0.08, lw=0)
    ax_hm.text(0.98, 0.06, 'Interior rows', transform=ax_hm.transAxes,
               ha='right', va='bottom', fontsize=8, color='w')

    # (b) Stabilization metric: |ΔQ| per row, aggregated over H
    dQ = np.diff(Q, axis=1)  # (nH, nRows-1)
    dQ_abs = np.abs(dQ)
    mean_dQ = dQ_abs.mean(axis=0)
    p90_dQ = np.quantile(dQ_abs, 0.9, axis=0)
    x = rows[1:]
    ax_slope.plot(x, mean_dQ, '-o', color=COLORS["primary"], label='mean |ΔQ|')
    ax_slope.fill_between(x, mean_dQ, p90_dQ, color=COLORS["primary"], alpha=0.2, label='to 90th pct')
    ax_slope.set_xlabel('Row number')
    ax_slope.set_ylabel(r'Mean $|\\Delta(Q/Q_{ref})|$')
    ax_slope.set_title('(b) Stabilization indicator')
    ax_slope.legend(frameon=False)
    ax_slope.grid(False)

    # inset: show one representative H curve with direct labeling (no legend)
    ax_in = inset_axes(ax_slope, width="45%", height="45%", loc='upper right', borderpad=1.0)
    H0 = H_vals[len(H_vals)//2]
    ax_in.plot(rows, Q_by_H[H0], '-o', color=COLORS["secondary"], lw=1.2)
    ax_in.axhline(1.0, color='0.2', ls='--', lw=0.9)
    ax_in.set_title(rf'$H={H0:.1f}$ m', fontsize=8)
    ax_in.set_xticks([1, 4, 8])
    ax_in.set_yticks([0, 1, 2, 3])
    ax_in.grid(False)

    fig.tight_layout()
    return fig
```

### F9 — `F9_shelter_and_regime` (**AI-lazy risk in panel b**)
**Purpose/story:** (a) shelter efficiency vs H; (b) regime classification map.  
**Issues:**
- Panel (b) is essentially a categorical scatter plot. It is readable, but it is low information density relative to the physics; it repeats what F10 later does more richly.
- The legend in (b) obscures data and repeats labels that could be direct-annotated.
**Recommendation:** Either (i) merge F9(b) into F10 as a simplified overlay, or (ii) upgrade F9(b) to show decision boundaries as continuous curves/surfaces (e.g., `H/λ_s` contours) and plot points on top.

### F10 — `F10_design_nomogram`
**Purpose/story:** Integrates regimes into a design chart.  
**What works:** Background zones + threshold lines + markers is a coherent story.  
**Issues:**
- This is close to a “poster” graphic: large background fills + gridlines consume ink while only ~9 points carry data.
- If you have underlying continuous deposition predictions, consider showing **contours of log10(deposition)** (not just zones) to justify the term “nomogram” and increase information density.
**Recommendation:** Replace large flat fills with light contour bands (few levels), label contours, and keep only the boundaries that matter (H=2λ_s, H=10λ_s).

### F11 — `F11_sensitivity_analysis`
**Purpose/story:** (a) boundary shift with wind; (b) parameter influence.  
**Issues:**
- Panel (b) is a tornado chart; it’s acceptable, but add uncertainty (even qualitative) or show it as distributions across cases rather than a single delta.
- Again, tilde artifacts in text (e.g., `200~μm`).
**Recommendation:** Consider a dot+interval (“forest plot”) instead of bars: central estimate with a range across cases.

### F12 — `F12_field_comparison` (**AI-lazy + narrative mismatch**)
**Purpose/story:** Validate trends vs literature.  
**Issues (major):**
- The y-axis reads “Deposition rate [%] or sand flux metric” — mixing units/metrics in one axis is not defensible. It tells the reader you’re forcing unlike quantities into one plot.
- The green dashed “This study (… shelter=-42%)” line is drawn at a negative value (~ -8.5 visually). If that number is percent, it should not be negative; if it’s “shelter efficiency” (dimensionless), it does not belong on the same axis as deposition percent.
- Color choice uses pure red squares/line (not consistent with the repo palette).
**Upgrade target:** Separate metrics into separate panels with explicit normalization.

**Concrete redesign (Python outline, 30+ lines):**
```python
import numpy as np
from utils.plotting_utils import plt, COLORS

def plot_literature_comparison(rows, lu_dep_pct, lu_err=None,
                               tang_inhib_range=(0.35, 0.89),
                               this_dep_pct=None, this_shelter=None):
    fig, (ax_dep, ax_inhib) = plt.subplots(1, 2, figsize=(7.2, 3.4), gridspec_kw={"width_ratios":[1.35, 1.0]})

    # (a) Row-wise deposition (%): Lu&Zhang vs this-study prediction (same units)
    ax_dep.plot(rows, lu_dep_pct, '-s', color=COLORS["secondary"], lw=1.4, ms=5,
                label='Lu & Zhang (2019) — deposition (%)')
    if lu_err is not None:
        ax_dep.fill_between(rows, lu_dep_pct-np.asarray(lu_err), lu_dep_pct+np.asarray(lu_err),
                            color=COLORS["secondary"], alpha=0.18, lw=0)
    if this_dep_pct is not None:
        ax_dep.plot(rows, this_dep_pct, '-o', color=COLORS["primary"], lw=1.4, ms=4,
                    label='This study — deposition (%)')

    ax_dep.set_xlabel('Row number')
    ax_dep.set_ylabel('Deposition rate [%]')
    ax_dep.set_title('(a) Deposition gradient across rows')
    ax_dep.legend(frameon=False, loc='upper right')
    ax_dep.grid(False)

    # (b) Field inhibition range: Tang et al. shown as interval, compared to this-study shelter
    lo, hi = tang_inhib_range
    ax_inhib.axhspan(lo*100, hi*100, color=COLORS["tertiary"], alpha=0.20, label='Tang et al. (2021) — inhibition range')
    ax_inhib.axhline(lo*100, color=COLORS["tertiary"], lw=1.0, alpha=0.8)
    ax_inhib.axhline(hi*100, color=COLORS["tertiary"], lw=1.0, alpha=0.8)

    if this_shelter is not None:
        # convert shelter efficiency metric to a comparable “inhibition” proxy ONLY if justified
        # otherwise, report as text annotation, not as a line on this axis.
        ax_inhib.text(0.5, 0.10, f'This study shelter: {this_shelter:+.0%} (not plotted on % axis)',
                      transform=ax_inhib.transAxes, ha='center', va='bottom', fontsize=8)

    ax_inhib.set_xlim(0, 1)
    ax_inhib.set_xticks([])
    ax_inhib.set_ylabel('Sand inhibition [%]')
    ax_inhib.set_title('(b) Field-scale inhibition (interval)')
    ax_inhib.legend(frameon=False, loc='upper right')
    ax_inhib.grid(False)

    fig.tight_layout()
    return fig
```
Key rule: **Do not combine dissimilar metrics on one axis.** Either normalize both to a common quantity with a defensible mapping, or separate panels.

## 4) Caption-to-figure consistency checks (early red flags)

- F3 caption (“three downstream positions”) vs visible content (appears to show a single outlet series) needs reconciliation.
- F6 caption claims numerical annotations are present; current figure does not show them.
- F7 label suggests `u_*/u_*t - 1` whereas caption says “erosion rate”; verify which is correct and align.
- F12 axis label admits mixing metrics; must be rethought.

## 5) Priority fix list (fastest path to journal-grade)

1) **Fix F12**: separate metrics, remove mixed-axis label, restore palette consistency.
2) **Upgrade F2(b)**: replace bar chart with a convergence plot + Richardson/GCI narrative.
3) **Add physical context to x-plots** (F5, and F2/F8 if kept as lines): row location markers/spans.
4) **Unify colormap scales** and reduce redundant colorbars (F4, F6, F7): shared colorbars, shared `vmin/vmax`, lighter grids/off by default.
5) Remove tilde artifacts in plot text everywhere; use plain spaces and proper units formatting.

## 6) Overall verdict

There is a solid start: vector outputs, readable typography, and coherent multi-panel structure for several key results (F4, F6, F7, F11). However, multiple figures still read as “first-pass Matplotlib” rather than journal-grade graphics: **bar charts, redundant legends/colorbars, heavy grids, and mixed-unit comparisons**.

Score: 8/10
