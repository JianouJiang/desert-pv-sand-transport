#!/usr/bin/env python3
"""
Generate all publication-quality figures from OpenFOAM simulation results.
=========================================================================
Figures F1-F12 as specified in plan.md, using real CFD data.
"""

import sys
import os
import json
import numpy as np
from pathlib import Path
from scipy.interpolate import griddata

# Setup paths
SCRIPT_DIR = Path(__file__).resolve().parent
CODES_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(CODES_DIR))

from utils.plotting_utils import plt, COLORS, save_figure
import utils.plotting_utils as pu
from analysis.postprocess_openfoam import (
    extract_flow_field_2d, extract_velocity_profiles,
    compute_friction_velocity_from_wss, UST_THRESHOLD, Z0, U_REF, Z_REF, KAPPA,
    PANEL_LENGTH, read_openfoam_scalar_field, read_openfoam_vector_field
)

PROJECT_DIR = CODES_DIR.parent
FIG_DIR = str(PROJECT_DIR / 'manuscript' / 'figures')
os.makedirs(FIG_DIR, exist_ok=True)
pu.FIGURE_DIR = FIG_DIR

OF_DIR = CODES_DIR / 'openfoam' / 'parametric_study'
RESULTS_DIR = CODES_DIR / 'results'

# Physical constants
G = 9.81
RHO = 1.225


def load_results():
    """Load the post-processed OpenFOAM results."""
    results_file = RESULTS_DIR / 'openfoam_results.json'
    if results_file.exists():
        with open(results_file) as f:
            return json.load(f)
    return None


def panel_geometry(H, theta_deg, S, n_rows=8, fetch=20.0, L=2.0):
    """Return panel endpoint coordinates for plotting."""
    theta = np.radians(theta_deg)
    dx = L * np.cos(theta)
    dz = L * np.sin(theta)
    panels = []
    for i in range(n_rows):
        x_le = fetch + i * S
        panels.append({
            'x_le': x_le, 'z_le': H,
            'x_te': x_le + dx, 'z_te': H + dz,
        })
    return panels


# ================================================================
# F1: Computational domain schematic
# ================================================================
def fig_F1():
    """Computational domain schematic with annotated parameters."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7.0, 5.5),
                                     gridspec_kw={'height_ratios': [1, 1]})

    H, theta, S, L = 0.5, 25, 3.38, 2.0
    panels = panel_geometry(H, theta, S, n_rows=3, fetch=5.0)

    ax = ax1
    # Ground
    ax.fill_between([0, 25], [-0.3, -0.3], [0, 0], color='#D2B48C', alpha=0.5)
    ax.plot([0, 25], [0, 0], 'k-', linewidth=1.5)

    # Panels
    for i, p in enumerate(panels):
        ax.plot([p['x_le'], p['x_te']], [p['z_le'], p['z_te']],
                'b-', linewidth=3, solid_capstyle='round')
        ax.plot([p['x_le'], p['x_le']], [0, p['z_le']], 'k-', linewidth=0.8)

    # Annotations
    p0 = panels[0]
    ax.annotate('', xy=(p0['x_le'] - 0.3, 0), xytext=(p0['x_le'] - 0.3, H),
                arrowprops=dict(arrowstyle='<->', color='red', lw=1.2))
    ax.text(p0['x_le'] - 1.2, H / 2, '$H$', color='red', fontsize=11,
            ha='center', va='center')

    arc_r = 1.2
    arc_th = np.linspace(0, np.radians(theta), 30)
    ax.plot(p0['x_le'] + arc_r * np.cos(arc_th),
            H + arc_r * np.sin(arc_th), 'g-', lw=1)
    ax.text(p0['x_le'] + 1.5, H + 0.25, r'$\theta$', color='green', fontsize=11)

    p1 = panels[1]
    ax.annotate('', xy=(p0['x_le'], -0.15), xytext=(p1['x_le'], -0.15),
                arrowprops=dict(arrowstyle='<->', color='purple', lw=1.2))
    ax.text((p0['x_le'] + p1['x_le']) / 2, -0.25, '$S$', color='purple',
            fontsize=11, ha='center', va='top')

    ax.annotate('', xy=(2.5, 2.5), xytext=(0.5, 2.5),
                arrowprops=dict(arrowstyle='->', color='navy', lw=2))
    ax.text(1.5, 2.75, r'Wind ($u_{\mathrm{ref}}$)', fontsize=9,
            ha='center', color='navy')

    ax.fill_between([0, 25], [0, 0], [0.05, 0.05], color='orange', alpha=0.2)
    ax.text(20, 0.1, 'Saltation layer', fontsize=7, color='orange', style='italic')

    ax.set_xlim(0, 22)
    ax.set_ylim(-0.35, 3.5)
    ax.set_xlabel('$x$ [m]')
    ax.set_ylabel('$z$ [m]')
    ax.set_title('(a) Cross-section with parameters', fontsize=10)
    ax.set_aspect('equal')
    ax.grid(False)

    # Bottom: domain overview with BC labels
    ax = ax2
    Lx, Ly = 80, 30
    ax.add_patch(plt.Rectangle((0, 0), Lx, Ly, fill=False, edgecolor='k', lw=1.5))

    ax.fill_between([18, 55], [0], [3], color='lightblue', alpha=0.3)
    ax.text(36, 1.5, '8-row PV array', ha='center', fontsize=8, style='italic')

    ax.text(-3, Ly / 2, 'Inlet\n(ABL profile)', fontsize=7, ha='right',
            va='center', color='blue')
    ax.text(Lx + 3, Ly / 2, 'Outlet\n(zero-gradient)', fontsize=7,
            ha='left', va='center', color='red')
    ax.text(Lx / 2, Ly + 1, 'Top (ABL profile)', fontsize=7,
            ha='center', color='gray')
    ax.text(Lx / 2, -1, r'Ground (no-slip, $z_0 = 0.001$ m)', fontsize=7,
            ha='center', va='top', color='brown')

    # Dimension labels
    ax.annotate('', xy=(0, -3), xytext=(Lx, -3),
                arrowprops=dict(arrowstyle='<->', color='k', lw=0.8))
    ax.text(Lx / 2, -4.5, f'${Lx}$ m', fontsize=8, ha='center')

    ax.annotate('', xy=(Lx + 5, 0), xytext=(Lx + 5, Ly),
                arrowprops=dict(arrowstyle='<->', color='k', lw=0.8))
    ax.text(Lx + 8, Ly / 2, f'${Ly}$ m', fontsize=8, ha='left', va='center')

    ax.set_xlim(-10, Lx + 15)
    ax.set_ylim(-6, Ly + 3)
    ax.set_xlabel('$x$ [m]')
    ax.set_ylabel('$z$ [m]')
    ax.set_title('(b) Computational domain', fontsize=10)
    ax.set_aspect('equal')
    ax.grid(False)

    fig.tight_layout()
    save_figure(fig, 'F1_domain_schematic')
    print("  F1 done")


# ================================================================
# F2: Mesh independence study
# ================================================================
def fig_F2(results):
    """Mesh independence: velocity profiles for coarse/medium/fine grids."""
    mesh_results = results.get('mesh_independence', [])
    if not mesh_results:
        print("  F2 skipped: no mesh independence data")
        return

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 3.5))

    colors = {'coarse': COLORS['primary'], 'medium': COLORS['secondary'],
              'fine': COLORS['tertiary']}
    labels = {'coarse': 'Coarse', 'medium': 'Medium', 'fine': 'Fine'}

    for mr in mesh_results:
        level = mr.get('mesh_level', 'unknown')
        ustar = mr.get('ustar', {})
        if not ustar:
            continue

        x = np.array(ustar['x'])
        u = np.array(ustar['ustar'])

        ax1.plot(x, u, color=colors.get(level, 'k'), label=labels.get(level, level))

    ax1.axhline(y=UST_THRESHOLD, color='red', ls='--', lw=0.8, label=r'$u_{*t}$')
    # Add row-location markers (use reference case: H=0.5, theta=25, S=4Hp)
    Hp_ref = PANEL_LENGTH * np.sin(np.radians(25))
    S_ref = 4 * Hp_ref
    fetch_ref = 20.0
    for i in range(8):
        x_le = fetch_ref + i * S_ref
        x_te = x_le + PANEL_LENGTH * np.cos(np.radians(25))
        ax1.axvspan(x_le, x_te, alpha=0.06, color='k', lw=0)
    ax1.set_xlabel('$x$ [m]')
    ax1.set_ylabel(r'$u_*$ [m/s]')
    ax1.set_title('(a) Friction velocity along ground')
    ax1.legend(fontsize=7, loc='lower right')
    ax1.grid(False)

    # Panel (b): convergence plot — key scalars vs grid spacing
    # Sort mesh results by cell count (coarse→fine)
    sorted_mr = sorted(mesh_results,
                       key=lambda m: m.get('metadata', {}).get('n_cells',
                                     m.get('convergence', {}).get('n_cells', 0)))
    n_cells = []
    dep_vals = []
    shelter_vals = []
    level_names = []
    for mr in sorted_mr:
        sand = mr.get('sand_transport', {})
        meta = mr.get('metadata', {})
        level = mr.get('mesh_level', 'unknown')
        nc = meta.get('n_cells', mr.get('convergence', {}).get('n_cells', 0))
        if sand and nc > 0:
            n_cells.append(nc)
            dep_vals.append(sand.get('panel_deposition', 0))
            shelter_vals.append(sand.get('shelter_efficiency', 0))
            level_names.append(level)

    if n_cells:
        h_char = 1.0 / np.sqrt(np.array(n_cells, dtype=float))
        dep_arr = np.array(dep_vals)

        # Plot coarse and medium with solid line; fine with open marker (unreliable)
        if len(h_char) >= 3:
            ax2.plot(h_char[:2], dep_arr[:2], 'o-', color=COLORS['primary'], lw=1.4, ms=6)
            ax2.plot(h_char[2], dep_arr[2], 'o', color=COLORS['primary'], ms=6,
                     mfc='white', mew=1.5)
            ax2.annotate('fine (unreliable)', (h_char[2], dep_arr[2]),
                         textcoords='offset points', xytext=(5, 5), fontsize=6.5,
                         color='0.5', fontstyle='italic')
        else:
            ax2.plot(h_char, dep_arr, 'o-', color=COLORS['primary'], lw=1.4, ms=6)

        for i, name in enumerate(level_names):
            if i < 2:  # Only label coarse and medium
                ax2.annotate(name, (h_char[i], dep_arr[i]),
                             textcoords='offset points', xytext=(5, 5), fontsize=7)

        # GCI error bar on medium mesh + Richardson extrapolation (2-level, p=2)
        if len(dep_arr) >= 2:
            r_21 = h_char[0] / h_char[1]  # coarse/medium spacing ratio
            p_obs = 2.0  # assumed order for 2-level GCI
            F_s = 3.0
            e_rel = abs(dep_arr[1] - dep_arr[0]) / dep_arr[1]
            gci_pct = F_s * e_rel / (r_21**p_obs - 1)
            dep_ext = dep_arr[1] + (dep_arr[1] - dep_arr[0]) / (r_21**p_obs - 1)

            # GCI error bar on medium point
            yerr = dep_arr[1] * gci_pct
            ax2.errorbar(h_char[1], dep_arr[1], yerr=yerr, fmt='none',
                         ecolor=COLORS['secondary'], capsize=4, capthick=1.2, lw=1.2)

            # Richardson extrapolated value (horizontal dashed line)
            ax2.axhline(dep_ext, color=COLORS['secondary'], ls='--', lw=1.0, alpha=0.7)
            ax2.text(0.98, 0.92,
                     f'$p = {p_obs:.0f}$ (assumed)\n'
                     f'GCI$_{{21}}$ = {gci_pct*100:.1f}%\n'
                     f'$Q_{{ext}}$ = {dep_ext:.2e}',
                     transform=ax2.transAxes, ha='right', va='top', fontsize=6.5,
                     color=COLORS['secondary'],
                     bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='0.8', alpha=0.9))

        ax2.set_xlabel(r'$1/\sqrt{N_{\mathrm{cells}}}$')
        ax2.set_ylabel('Panel deposition [kg/(m s)]')
        ax2.set_title('(b) Grid convergence of deposition')
        ax2.ticklabel_format(axis='y', style='scientific', scilimits=(-2, 2))
        ax2.invert_xaxis()
        ax2.grid(False)

    fig.tight_layout()
    save_figure(fig, 'F2_mesh_independence')
    print("  F2 done")


# ================================================================
# F3: Validation - ABL log-law profile
# ================================================================
def fig_F3():
    """Validation: compare ABL precursor profile with log-law."""
    abl_dir = CODES_DIR / 'openfoam' / 'abl_precursor'

    # Find latest time directory
    time_dirs = sorted([d for d in abl_dir.iterdir()
                       if d.is_dir() and d.name not in ('0', 'constant', 'system',
                                                         'postProcessing', 'dynamicCode')
                       and not d.name.startswith('processor')],
                      key=lambda x: float(x.name) if x.name.replace('.', '').isdigit() else -1)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 3.5))

    # Analytical log-law
    z_anal = np.logspace(np.log10(Z0 * 10), np.log10(30), 200)
    ustar_ref = KAPPA * U_REF / np.log(Z_REF / Z0)
    u_loglaw = (ustar_ref / KAPPA) * np.log(z_anal / Z0)

    ax1.semilogx(u_loglaw, z_anal, 'k-', label='Log-law (analytical)', lw=2)
    ax1.set_xlabel('$U$ [m/s]')
    ax1.set_ylabel('$z$ [m]')
    ax1.set_title('(a) Velocity profile')

    # TKE profile
    k_anal = ustar_ref**2 / np.sqrt(0.09) * np.ones_like(z_anal)
    ax2.semilogx(k_anal, z_anal, 'k-', label='Equilibrium $k$', lw=2)
    ax2.set_xlabel('$k$ [m$^2$/s$^2$]')
    ax2.set_ylabel('$z$ [m]')
    ax2.set_title('(b) Turbulent kinetic energy')

    # Overlay OpenFOAM ABL precursor data
    if time_dirs:
        latest = time_dirs[-1]
        try:
            # Read cell centres and fields
            cz_file = latest / 'Cz'
            u_file = latest / 'U'
            k_file = latest / 'k'

            if cz_file.exists() and u_file.exists():
                cz = read_openfoam_scalar_field(str(cz_file))
                ux, _, _ = read_openfoam_vector_field(str(u_file))

                if cz is not None:
                    # Extract vertical profile at a single x-column
                    cx = read_openfoam_scalar_field(str(latest / 'Cx'))
                    if cx is not None:
                        # Find the x-value nearest to 80% of domain (outlet-ish)
                        x_target = 0.8 * cx.max()
                        x_nearest = cx[np.argmin(np.abs(cx - x_target))]
                        mask = np.abs(cx - x_nearest) < 0.01
                        z_sim = cz[mask]
                        u_sim = ux[mask]
                        order = np.argsort(z_sim)
                        ax1.semilogx(u_sim[order], z_sim[order], 'o',
                                    color=COLORS['primary'], markersize=4,
                                    label='OpenFOAM (outlet)')

                if k_file.exists() and cz is not None:
                    k_vals = read_openfoam_scalar_field(str(k_file))
                    if k_vals is not None and cx is not None:
                        z_sim = cz[mask]
                        k_sim = k_vals[mask]
                        order = np.argsort(z_sim)
                        ax2.semilogx(k_sim[order], z_sim[order], 'o',
                                    color=COLORS['primary'], markersize=4,
                                    label='OpenFOAM (outlet)')

        except Exception as e:
            print(f"    Could not read ABL data: {e}")

    ax1.legend(fontsize=8)
    ax2.legend(fontsize=8)

    fig.tight_layout()
    save_figure(fig, 'F3_validation_loglaw')
    print("  F3 done")


# ================================================================
# F4: Flow field comparison for three tilt angles
# ================================================================
def fig_F4(results):
    """Velocity magnitude contours for theta=15,25,35 at fixed H=0.5, S=4Hp."""
    param_results = results.get('parametric', [])

    # Find cases with H=0.5 and S_factor=4
    target_cases = {}
    for r in param_results:
        meta = r.get('metadata', {})
        if abs(meta.get('H', 0) - 0.5) < 0.01 and abs(meta.get('S_factor', 0) - 4) < 0.1:
            theta = meta.get('theta', 0)
            target_cases[theta] = r

    if len(target_cases) < 3:
        print(f"  F4 skipped: only {len(target_cases)} matching cases found")
        # Generate placeholder with analytical estimate
        _fig_F4_placeholder()
        return

    fig, axes = plt.subplots(3, 1, figsize=(7.0, 7.0), sharex=True)

    # First pass: collect all fields to determine shared vmin/vmax
    fields_data = {}
    for theta in [15, 25, 35]:
        case = target_cases.get(theta)
        if case is None:
            continue
        case_dir = None
        all_cases_file = OF_DIR / 'all_cases.json'
        if all_cases_file.exists():
            with open(all_cases_file) as f:
                all_cases = json.load(f)
            for c in all_cases.get('parametric', []):
                if (abs(c.get('H', 0) - 0.5) < 0.01
                    and abs(c.get('theta', 0) - theta) < 1
                    and abs(c.get('S_factor', 0) - 4) < 0.1):
                    case_dir = Path(c['dir'])
                    break
        if case_dir is None or not case_dir.exists():
            continue
        field = extract_flow_field_2d(case_dir, x_range=(15, 60), z_range=(0, 5))
        if field is not None:
            fields_data[theta] = field

    if not fields_data:
        _fig_F4_placeholder()
        return

    all_umag = np.concatenate([f['Umag'] for f in fields_data.values()])
    vmin, vmax = 0, np.nanpercentile(all_umag, 99)
    levels = np.linspace(vmin, vmax, 20)

    # Second pass: plot with shared scale
    cf_last = None
    for idx, theta in enumerate([15, 25, 35]):
        ax = axes[idx]
        if theta not in fields_data:
            continue
        field = fields_data[theta]

        xi = np.linspace(15, 60, 300)
        zi = np.linspace(0, 5, 100)
        Xi, Zi = np.meshgrid(xi, zi)
        Ui = griddata((field['x'], field['z']), field['Umag'],
                      (Xi, Zi), method='linear')

        cf_last = ax.contourf(Xi, Zi, Ui, levels=levels, cmap='cividis',
                              extend='max')

        # Overlay panels
        Hp = PANEL_LENGTH * np.sin(np.radians(theta))
        S_val = 4 * Hp
        panels = panel_geometry(0.5, theta, S_val, n_rows=8, fetch=20.0)
        for p in panels:
            ax.plot([p['x_le'], p['x_te']], [p['z_le'], p['z_te']],
                    'k-', lw=2)

        ax.set_ylabel('$z$ [m]')
        ax.set_title(f'({chr(97 + idx)}) $\\theta = {theta}^\\circ$', fontsize=10)
        ax.set_ylim(0, 5)
        ax.set_aspect('equal')

    axes[-1].set_xlabel('$x$ [m]')

    # Single shared colorbar
    if cf_last is not None:
        fig.subplots_adjust(right=0.88)
        cbar_ax = fig.add_axes([0.90, 0.15, 0.02, 0.7])
        fig.colorbar(cf_last, cax=cbar_ax, label='$|U|$ [m/s]')

    save_figure(fig, 'F4_flow_field_tilt_comparison')
    print("  F4 done")


def _fig_F4_placeholder():
    """Placeholder F4 until OpenFOAM results are ready."""
    fig, axes = plt.subplots(3, 1, figsize=(7.0, 7.0), sharex=True)
    for idx, theta in enumerate([15, 25, 35]):
        ax = axes[idx]
        ax.text(0.5, 0.5, f'OpenFOAM results pending\n$\\theta = {theta}^\\circ$',
                transform=ax.transAxes, ha='center', va='center', fontsize=14,
                color='gray')
        ax.set_ylabel('$z$ [m]')
        ax.set_title(f'({chr(97 + idx)}) $\\theta = {theta}^\\circ$', fontsize=10)
    axes[-1].set_xlabel('$x$ [m]')
    fig.tight_layout()
    save_figure(fig, 'F4_flow_field_tilt_comparison')
    print("  F4 done (placeholder)")


# ================================================================
# F5: Friction velocity profile showing transport regimes
# ================================================================
def fig_F5(results):
    """Friction velocity amplification along ground for different H values."""
    param_results = results.get('parametric', [])

    fig, ax = plt.subplots(figsize=(7.0, 3.5))

    H_values = [0.1, 0.3, 0.5, 0.8]
    color_list = [COLORS['primary'], COLORS['secondary'],
                  COLORS['tertiary'], COLORS['quaternary']]

    for H_val, color in zip(H_values, color_list):
        # Find case with this H, theta=25, S_factor=4
        for r in param_results:
            meta = r.get('metadata', {})
            if (abs(meta.get('H', 0) - H_val) < 0.01
                and abs(meta.get('theta', 0) - 25) < 1
                and abs(meta.get('S_factor', 0) - 4) < 0.1):
                ustar = r.get('ustar', {})
                sand = r.get('sand_transport', {})
                if ustar and sand:
                    x = np.array(ustar['x'])
                    u = np.array(ustar['ustar'])
                    ustar_up = sand.get('ustar_upstream_sim', np.mean(u[x < 18]))
                    ax.plot(x, u / ustar_up, color=color, label=f'$H = {H_val}$ m')
                break

    ax.axhline(y=1.0, color='k', ls='--', lw=0.8, label='Undisturbed')
    # Add row-location markers
    Hp_ref = PANEL_LENGTH * np.sin(np.radians(25))
    S_ref = 4 * Hp_ref
    fetch_ref = 20.0
    for i in range(8):
        x_le = fetch_ref + i * S_ref
        x_te = x_le + PANEL_LENGTH * np.cos(np.radians(25))
        ax.axvspan(x_le, x_te, alpha=0.06, color='k', lw=0)
    ax.set_xlabel('$x$ [m]')
    ax.set_ylabel(r'$u_* / u_{*,\mathrm{ref}}$')
    ax.set_title(r'Friction velocity amplification ($\theta = 25^\circ$, $S = 4H_p$)')
    ax.legend(loc='upper right', fontsize=8)
    ax.set_ylim(0, 2.0)
    ax.grid(False)

    fig.tight_layout()
    save_figure(fig, 'F5_friction_velocity_regimes')
    print("  F5 done")


# ================================================================
# F6: Parametric heatmap of panel deposition
# ================================================================
def fig_F6(results):
    """Heatmaps of panel deposition rate vs H and S for three tilt angles."""
    param_results = results.get('parametric', [])
    if not param_results:
        print("  F6 skipped: no parametric data")
        return

    # First pass: collect all data to determine shared color scale
    all_dep_log = []
    grids_data = {}
    for theta_target in [15, 25, 35]:
        H_vals = []
        S_factors = []
        dep_vals = []
        conv_flags = []
        for r in param_results:
            meta = r.get('metadata', {})
            sand = r.get('sand_transport', {})
            conv = r.get('convergence', {})
            if abs(meta.get('theta', 0) - theta_target) < 1 and sand:
                H_vals.append(meta['H'])
                S_factors.append(meta.get('S_factor', meta['S'] / (PANEL_LENGTH * np.sin(np.radians(theta_target)))))
                dep = sand.get('panel_deposition', 1e-20)
                dep_vals.append(max(dep, 1e-20))
                conv_flags.append(conv.get('converged', True))
        if H_vals:
            dep_arr = np.log10(np.array(dep_vals))
            all_dep_log.extend(dep_arr.tolist())
            H_arr = np.array(H_vals)
            S_arr = np.array(S_factors)
            H_unique = sorted(set(H_arr))
            S_unique = sorted(set(S_arr))
            grid = np.full((len(H_unique), len(S_unique)), np.nan)
            conv_grid = np.ones((len(H_unique), len(S_unique)), dtype=bool)
            for h, s, d, c in zip(H_arr, S_arr, dep_arr, conv_flags):
                hi = H_unique.index(h)
                si = S_unique.index(s)
                grid[hi, si] = d
                conv_grid[hi, si] = c
            grids_data[theta_target] = (grid, H_unique, S_unique, conv_grid)

    if not all_dep_log:
        print("  F6 skipped: no data")
        return

    vmin_dep = min(all_dep_log)
    vmax_dep = max(all_dep_log)

    fig, axes = plt.subplots(1, 3, figsize=(7.0, 3.5), sharey=True)
    im_last = None
    for idx, theta_target in enumerate([15, 25, 35]):
        ax = axes[idx]
        if theta_target not in grids_data:
            ax.text(0.5, 0.5, 'No data', transform=ax.transAxes, ha='center')
            continue
        grid, H_unique, S_unique, conv_grid = grids_data[theta_target]
        im_last = ax.imshow(grid, aspect='auto', origin='lower',
                            cmap='YlOrRd_r', interpolation='nearest',
                            vmin=vmin_dep, vmax=vmax_dep,
                            extent=[min(S_unique) - 0.5, max(S_unique) + 0.5,
                                    min(H_unique) - 0.05, max(H_unique) + 0.05])
        # Annotate cell values and hatch unconverged cells
        from matplotlib.patches import Rectangle
        dS = 1.0 if len(S_unique) < 2 else (S_unique[1] - S_unique[0])
        dH = 0.1 if len(H_unique) < 2 else (H_unique[1] - H_unique[0])
        for hi, h in enumerate(H_unique):
            for si, s in enumerate(S_unique):
                val = grid[hi, si]
                if not np.isnan(val):
                    ax.text(s, h, f'{val:.1f}', ha='center', va='center',
                            fontsize=6, color='k' if val > (vmin_dep + vmax_dep) / 2 else 'w')
                    if not conv_grid[hi, si]:
                        rect = Rectangle((s - dS / 2, h - dH / 2), dS, dH,
                                         fill=False, edgecolor='k', linewidth=0.5,
                                         hatch='///', alpha=0.6)
                        ax.add_patch(rect)
                        # Bold border for case_34 (limit cycle)
                        if abs(h - 0.8) < 0.01 and theta_target == 35 and abs(s - 2) < 0.1:
                            rect2 = Rectangle((s - dS / 2, h - dH / 2), dS, dH,
                                              fill=False, edgecolor='red', linewidth=1.8)
                            ax.add_patch(rect2)
        ax.set_xticks(S_unique)
        ax.set_xticklabels([f'{int(s)}$H_p$' for s in S_unique])
        ax.set_xlabel('Row spacing $S$')
        ax.set_title(f'$\\theta = {theta_target}^\\circ$', fontsize=10)
        if idx == 0:
            ax.set_ylabel('Ground clearance $H$ [m]')
        ax.grid(False)

    # Single shared colorbar
    if im_last is not None:
        fig.subplots_adjust(right=0.88, bottom=0.22)
        cbar_ax = fig.add_axes([0.90, 0.22, 0.02, 0.63])
        cb = fig.colorbar(im_last, cax=cbar_ax)
        cb.set_label(r'$\log_{10}(Q_{\mathrm{panel}})$')

    # Legend for hatching (proxy artist)
    from matplotlib.patches import Patch
    hatch_proxy = Patch(facecolor='white', edgecolor='k', hatch='///',
                        linewidth=0.5, alpha=0.6, label='Not formally converged')
    fig.legend(handles=[hatch_proxy], loc='lower center', ncol=1,
               fontsize=7, frameon=False, bbox_to_anchor=(0.44, 0.01))

    save_figure(fig, 'F6_parametric_heatmap_panel_deposition')
    print("  F6 done")


# ================================================================
# F7: Foundation erosion map
# ================================================================
def fig_F7(results):
    """Foundation erosion intensity map."""
    param_results = results.get('parametric', [])

    # First pass: collect all erosion data for shared color scale
    all_erosion = []
    grids_data_f7 = {}
    for theta_target in [15, 25, 35]:
        H_vals = []
        S_factors = []
        erosion_vals = []
        for r in param_results:
            meta = r.get('metadata', {})
            sand = r.get('sand_transport', {})
            if abs(meta.get('theta', 0) - theta_target) < 1 and sand:
                H_vals.append(meta['H'])
                S_factors.append(meta.get('S_factor', 4))
                erosion_vals.append(sand.get('erosion_intensity', 0))
        if H_vals:
            all_erosion.extend(erosion_vals)
            H_arr = np.array(H_vals)
            S_arr = np.array(S_factors)
            er_arr = np.array(erosion_vals)
            H_unique = sorted(set(H_arr))
            S_unique = sorted(set(S_arr))
            grid = np.full((len(H_unique), len(S_unique)), np.nan)
            for h, s, e in zip(H_arr, S_arr, er_arr):
                hi = H_unique.index(h)
                si = S_unique.index(s)
                grid[hi, si] = e
            grids_data_f7[theta_target] = (grid, H_unique, S_unique)

    vmin_er = 0
    vmax_er = max(all_erosion) if all_erosion else 1

    fig, axes = plt.subplots(1, 3, figsize=(7.0, 3.5), sharey=True)
    im_last = None
    for idx, theta_target in enumerate([15, 25, 35]):
        ax = axes[idx]
        if theta_target not in grids_data_f7:
            ax.text(0.5, 0.5, 'No data', transform=ax.transAxes, ha='center')
            continue
        grid, H_unique, S_unique = grids_data_f7[theta_target]
        im_last = ax.imshow(grid, aspect='auto', origin='lower',
                            cmap='Reds', interpolation='nearest',
                            vmin=vmin_er, vmax=vmax_er,
                            extent=[min(S_unique) - 0.5, max(S_unique) + 0.5,
                                    min(H_unique) - 0.05, max(H_unique) + 0.05])
        ax.set_xticks(S_unique)
        ax.set_xticklabels([f'{int(s)}$H_p$' for s in S_unique])
        ax.set_xlabel('Row spacing $S$')
        ax.set_title(f'$\\theta = {theta_target}^\\circ$', fontsize=10)
        if idx == 0:
            ax.set_ylabel('Ground clearance $H$ [m]')
        ax.grid(False)

    # Single shared colorbar
    if im_last is not None:
        fig.subplots_adjust(right=0.88)
        cbar_ax = fig.add_axes([0.90, 0.15, 0.02, 0.7])
        cb = fig.colorbar(im_last, cax=cbar_ax)
        cb.set_label(r'$u_*/u_{*t} - 1$')

    save_figure(fig, 'F7_foundation_erosion_map')
    print("  F7 done")


# ================================================================
# F8: Sand accumulation by row position
# ================================================================
def fig_F8(results):
    """Deposition rate as a function of row position."""
    # This requires per-row deposition data from the simulation
    # For now, show the shelter efficiency trend
    param_results = results.get('parametric', [])

    fig, ax = plt.subplots(figsize=(7.0, 3.5))

    H_values = [0.1, 0.3, 0.5, 0.8]
    color_list = [COLORS['primary'], COLORS['secondary'],
                  COLORS['tertiary'], COLORS['quaternary']]

    for H_val, color in zip(H_values, color_list):
        for r in param_results:
            meta = r.get('metadata', {})
            if (abs(meta.get('H', 0) - H_val) < 0.01
                and abs(meta.get('theta', 0) - 25) < 1
                and abs(meta.get('S_factor', 0) - 4) < 0.1):
                ustar = r.get('ustar', {})
                sand = r.get('sand_transport', {})
                if ustar and sand:
                    x = np.array(ustar['x'])
                    u = np.array(ustar['ustar'])
                    ustar_up = sand.get('ustar_upstream_sim', np.mean(u[x < 18]))

                    # Compute normalized flux Q/Q_ref = (u*/u*_ref)^3
                    Q_norm = (u / ustar_up)**3

                    # Find panel x-positions
                    Hp = PANEL_LENGTH * np.sin(np.radians(25))
                    S_val = 4 * Hp
                    fetch = 20.0
                    panel_x = [fetch + i * S_val for i in range(8)]

                    # Get normalized Q at each panel location
                    Q_panels = []
                    for px in panel_x:
                        mask = np.abs(x - px) < S_val * 0.3
                        if np.any(mask):
                            Q_panels.append(np.mean(Q_norm[mask]))

                    if Q_panels:
                        ax.plot(range(1, len(Q_panels) + 1), Q_panels,
                                'o-', color=color, label=f'$H = {H_val}$ m')
                break

    ax.axhline(y=1.0, color='k', ls='--', lw=0.8, label='Undisturbed')
    ax.set_xlabel('Row number')
    ax.set_ylabel(r'$Q / Q_{\mathrm{ref}}$')
    ax.set_title(r'Normalized sand flux by row ($\theta = 25^\circ$, $S = 4H_p$)')
    ax.legend(fontsize=8)
    ax.set_xticks(range(1, 9))

    fig.tight_layout()
    save_figure(fig, 'F8_accumulation_by_row')
    print("  F8 done")


# ================================================================
# F9: Shelter efficiency and regime classification
# ================================================================
def fig_F9(results):
    """Shelter efficiency vs H with regime boundaries."""
    param_results = results.get('parametric', [])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 3.5))

    theta_values = [15, 25, 35]
    colors_t = [COLORS['primary'], COLORS['secondary'], COLORS['tertiary']]

    for theta_val, color in zip(theta_values, colors_t):
        H_vals = []
        shelter_vals = []
        for r in param_results:
            meta = r.get('metadata', {})
            sand = r.get('sand_transport', {})
            if (abs(meta.get('theta', 0) - theta_val) < 1
                and abs(meta.get('S_factor', 0) - 4) < 0.1 and sand):
                H_vals.append(meta['H'])
                shelter_vals.append(sand['shelter_efficiency'])

        if H_vals:
            order = np.argsort(H_vals)
            ax1.plot(np.array(H_vals)[order], np.array(shelter_vals)[order],
                     'o-', color=color, label=f'$\\theta = {theta_val}^\\circ$')

    ax1.set_xlabel('Ground clearance $H$ [m]')
    ax1.set_ylabel('Shelter efficiency')
    ax1.set_title('(a) Shelter efficiency')
    ax1.legend()
    ax1.axhline(y=0, color='k', ls=':', lw=0.5)

    # Panel (b): Total panel deposition vs H with C uncertainty band
    C_baseline = 0.25
    C_lo, C_hi = 0.1, 0.5
    for theta_val, color in zip(theta_values, colors_t):
        H_vals = []
        dep_vals = []
        for r in param_results:
            meta = r.get('metadata', {})
            sand = r.get('sand_transport', {})
            if (abs(meta.get('theta', 0) - theta_val) < 1
                and abs(meta.get('S_factor', 0) - 4) < 0.1 and sand):
                dep = sand.get('panel_deposition', 0)
                if dep > 0:
                    H_vals.append(meta['H'])
                    dep_vals.append(dep)

        if H_vals:
            order = np.argsort(H_vals)
            H_arr = np.array(H_vals)[order]
            dep_arr = np.array(dep_vals)[order]
            ax2.semilogy(H_arr, dep_arr, 'o-', color=color,
                         label=f'$\\theta = {theta_val}^\\circ$')
            # C uncertainty band (deposition is linear in C)
            ax2.fill_between(H_arr, dep_arr * (C_lo / C_baseline),
                             dep_arr * (C_hi / C_baseline),
                             color=color, alpha=0.12)

    # Regime boundary lines
    ustar_ref = KAPPA * U_REF / np.log(Z_REF / Z0)
    lambda_s = 2 * ustar_ref**2 / G
    for mult, label in [(2, r'$H = 2\lambda_s$'), (10, r'$H = 10\lambda_s$')]:
        H_bound = mult * lambda_s
        ax2.axvline(x=H_bound, color='k', ls='--', lw=0.7, alpha=0.5)
        ax2.text(H_bound + 0.01, ax2.get_ylim()[0] if ax2.get_ylim()[0] > 0
                 else 1e-9, label, fontsize=7, rotation=90, va='bottom')

    ax2.set_xlabel('Ground clearance $H$ [m]')
    ax2.set_ylabel('Panel deposition [kg/(m$\\cdot$s)]')
    ax2.set_title('(b) Panel deposition vs $H$')
    ax2.legend(fontsize=7)

    fig.tight_layout()
    save_figure(fig, 'F9_shelter_and_regime')
    print("  F9 done")


# ================================================================
# F10: Design nomogram
# ================================================================
def fig_F10(results):
    """Design nomogram in (H, theta) space."""
    param_results = results.get('parametric', [])

    fig, ax = plt.subplots(figsize=(5.5, 4.5))

    # Plot regime boundaries
    H_range = np.linspace(0.05, 1.0, 100)
    ustar_ref = KAPPA * U_REF / np.log(Z_REF / Z0)
    lambda_s = 2 * ustar_ref**2 / G

    # Capture-transitional boundary: H/lambda_s = 2
    ax.axvline(x=2 * lambda_s, color='red', ls='--', lw=1.5, label=r'$H = 2\lambda_s$')
    # Transitional-passthrough boundary: H/lambda_s = 10
    ax.axvline(x=10 * lambda_s, color='green', ls='--', lw=1.5, label=r'$H = 10\lambda_s$')

    # Fill regime regions
    ax.axvspan(0, 2 * lambda_s, alpha=0.15, color='red', label='Capture zone')
    ax.axvspan(2 * lambda_s, 10 * lambda_s, alpha=0.15, color='orange', label='Transitional')
    ax.axvspan(10 * lambda_s, 1.0, alpha=0.15, color='green', label='Pass-through zone')

    # Overlay simulation data points
    regime_markers = {'capture': 'v', 'transitional': 's', 'pass-through': '^'}
    regime_colors = {'capture': 'red', 'transitional': 'orange', 'pass-through': 'green'}

    for r in param_results:
        meta = r.get('metadata', {})
        sand = r.get('sand_transport', {})
        if sand and abs(meta.get('S_factor', 0) - 4) < 0.1:
            regime = sand.get('regime', 'unknown')
            ax.scatter(meta['H'], meta['theta'],
                      marker=regime_markers.get(regime, 'o'),
                      c=regime_colors.get(regime, 'gray'),
                      s=80, edgecolors='k', linewidth=0.5, zorder=5)

    ax.set_xlabel('Ground clearance $H$ [m]')
    ax.set_ylabel(r'Tilt angle $\theta$ [$^\circ$]')
    ax.set_title('Design nomogram: sand transport regime')
    ax.set_xlim(0, 0.9)
    ax.set_ylim(10, 40)
    ax.legend(loc='upper left', fontsize=8)

    fig.tight_layout()
    save_figure(fig, 'F10_design_nomogram')
    print("  F10 done")


# ================================================================
# F11: Sensitivity analysis (tornado chart)
# ================================================================
def fig_F11(results):
    """Sensitivity analysis: how regime boundaries shift with wind speed and grain size.

    Uses the analytical sand transport model with CFD-derived amplification factors.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 3.5))

    # Physical parameters
    from analysis.postprocess_openfoam import RHO, RHO_P, D50, A_N, GAMMA

    H_range = np.linspace(0.01, 1.0, 200)

    # (a) Wind speed sensitivity with u*t uncertainty band
    u_refs = [8, 10, 14]
    colors_u = [COLORS['primary'], 'k', COLORS['tertiary']]
    for u_ref, color in zip(u_refs, colors_u):
        ustar = KAPPA * u_ref / np.log(Z_REF / Z0)
        lambda_s = 2 * ustar**2 / G
        dep_frac = np.exp(-H_range / lambda_s)
        ax1.semilogy(H_range, dep_frac, color=color, lw=1.4,
                     label=f'$u_{{\\mathrm{{ref}}}} = {u_ref}$ m/s')

        # u*t +/- 15% uncertainty: affects lambda_s = 2*u*^2/g
        # but u* is set by wind, not threshold. The threshold only
        # determines WHERE transport starts, not the concentration profile.
        # So the envelope comes from u* uncertainty (not plotted on this panel)

    # Show C=[0.1, 0.5] uncertainty band for reference case (u_ref=10)
    ustar_10 = KAPPA * 10 / np.log(Z_REF / Z0)
    lambda_s_10 = 2 * ustar_10**2 / G
    dep_mid = np.exp(-H_range / lambda_s_10)
    # C only scales absolute flux Q = C*(rho/g)*u*^3, so log10(Q_lo) = log10(Q) + log10(0.1/0.25)
    # On the deposition_fraction plot, C doesn't change the fraction, only absolute deposition
    # Instead show u*t +/-15% effect: changes whether transport is active (shifts left boundary)
    # For clarity, add text annotation about C uncertainty
    ax1.text(0.03, 0.05, r'$C \in [0.1, 0.5]$ scales absolute $Q$' '\n'
             r'by $\times 0.4$--$2.0$; regime boundaries unchanged',
             transform=ax1.transAxes, fontsize=6.5, va='bottom', color='0.4',
             bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='0.8', alpha=0.9))

    ax1.axhline(y=np.exp(-2), color='gray', ls=':', lw=0.8)
    ax1.axhline(y=np.exp(-10), color='gray', ls=':', lw=0.8)
    ax1.text(0.85, np.exp(-2) * 1.5, r'$H/\lambda_s = 2$', fontsize=7,
             ha='right', color='gray')
    ax1.text(0.85, np.exp(-10) * 2, r'$H/\lambda_s = 10$', fontsize=7,
             ha='right', color='gray')
    ax1.set_xlabel('Ground clearance $H$ [m]')
    ax1.set_ylabel(r'$\exp(-H/\lambda_s)$')
    ax1.set_title(r'(a) Wind speed ($D_{50} = 200\;\mu$m)')
    ax1.legend(fontsize=8, loc='upper right')
    ax1.set_ylim(1e-15, 1)

    # (b) Tornado chart: parameter sensitivity from parametric study
    param_results = results.get('parametric', [])
    base_dep = None
    for r in param_results:
        meta = r.get('metadata', {})
        sand = r.get('sand_transport', {})
        if (abs(meta.get('H', 0) - 0.5) < 0.01
            and abs(meta.get('theta', 0) - 25) < 1
            and abs(meta.get('S_factor', 0) - 4) < 0.1 and sand):
            base_dep = sand.get('panel_deposition', 1e-10)
            break

    if base_dep and base_dep > 0 and param_results:
        params = ['$H$', r'$\theta$', '$S$']
        ranges = []
        for vary_key, fix1_key, fix1_val, fix2_key, fix2_val in [
            ('H', 'theta', 25, 'S_factor', 4),
            ('theta', 'H', 0.5, 'S_factor', 4),
            ('S_factor', 'H', 0.5, 'theta', 25),
        ]:
            deps = []
            for r in param_results:
                m = r.get('metadata', {})
                s = r.get('sand_transport', {})
                if (abs(m.get(fix1_key, 0) - fix1_val) < 0.1
                    and abs(m.get(fix2_key, 0) - fix2_val) < 0.1 and s):
                    dep = max(s.get('panel_deposition', 1e-20), 1e-20)
                    deps.append(dep)
            if deps:
                ranges.append((np.log10(min(deps)) - np.log10(base_dep),
                               np.log10(max(deps)) - np.log10(base_dep)))
            else:
                ranges.append((0, 0))

        # Add C and u*t as additional uncertainty sources
        # C: [0.1, 0.5] around baseline 0.25 → log10 range = [-0.40, +0.30]
        c_lo = np.log10(0.1 / 0.25)  # -0.40
        c_hi = np.log10(0.5 / 0.25)  # +0.30
        params.append('$C$')
        ranges.append((c_lo, c_hi))
        # u*t: +-15% → u*t enters as (1 - u*t^2/u*^2), nonlinear
        # For our conditions u*=0.445, u*t=0.26: ratio = 0.34
        # u*t_lo = 0.221, u*t_hi = 0.299 → ratio_lo=0.25, ratio_hi=0.45
        # Q ~ (1 - ratio): Q_lo/Q_base = (1-0.45)/(1-0.34) = 0.83 → -0.08
        # Q_hi/Q_base = (1-0.25)/(1-0.34) = 1.14 → +0.06
        params.append('$u_{*t}$')
        ranges.append((-0.08, 0.06))

        y_pos = range(len(params))
        ax2.barh(y_pos, [r[1] for r in ranges], color=COLORS['secondary'],
                 label='Increase', height=0.5)
        ax2.barh(y_pos, [r[0] for r in ranges], color=COLORS['primary'],
                 label='Decrease', height=0.5)
        ax2.set_yticks(list(y_pos))
        ax2.set_yticklabels(params)
        ax2.set_xlabel(r'$\Delta \log_{10}(Q_{\mathrm{panel}})$')
        ax2.set_title('(b) Parameter sensitivity')
        ax2.legend(fontsize=8)
        ax2.axvline(x=0, color='k', lw=0.5)
    else:
        ax2.text(0.5, 0.5, 'Parametric data\nnot yet available',
                 transform=ax2.transAxes, ha='center', va='center',
                 fontsize=12, color='gray')

    fig.tight_layout()
    save_figure(fig, 'F11_sensitivity_analysis')
    print("  F11 done")


# ================================================================
# F12: Comparison with field observations (NO fabricated data)
# ================================================================
def fig_F12(results):
    """
    Compare simulation-predicted deposition trends with published experimental data.
    Panel (a): row-wise deposition gradient (Lu & Zhang 2019 vs this study).
    Panel (b): field-scale sand inhibition range (Tang et al. 2021 vs this study).
    """
    fig, (ax_dep, ax_inhib) = plt.subplots(1, 2, figsize=(7.0, 3.5),
                                            gridspec_kw={'width_ratios': [1.4, 1.0]})

    # Published data: Lu & Zhang (2019), Renewable Energy 135, 21-31
    lu_zhang_rows = [1, 2, 3, 4, 5]
    lu_zhang_dep_pct = [18.89, 12.35, 9.62, 6.83, 5.71]

    ax_dep.plot(lu_zhang_rows, lu_zhang_dep_pct, '-s', color=COLORS['secondary'],
                markersize=6, lw=1.4, label='Lu & Zhang (2019)')

    # Overlay our row-wise deposition trend if available
    param_results = results.get('parametric', [])
    shelter_val = None
    for r in param_results:
        meta = r.get('metadata', {})
        if (abs(meta.get('H', 0) - 0.5) < 0.01
            and abs(meta.get('theta', 0) - 25) < 1
            and abs(meta.get('S_factor', 0) - 4) < 0.1):
            sand = r.get('sand_transport', {})
            if sand:
                shelter_val = sand.get('shelter_efficiency', 0)
            break

    ax_dep.set_xlabel('Row number')
    ax_dep.set_ylabel('Deposition rate [%]')
    ax_dep.set_title('(a) Row-wise deposition gradient')
    ax_dep.legend(frameon=False, fontsize=8)
    ax_dep.grid(False)

    # Panel (b): field-scale sand inhibition
    # Tang et al. (2021) J. Arid Land — field measurement: 35–89% inhibition
    tang_lo, tang_hi = 35.46, 88.51
    ax_inhib.axhspan(tang_lo, tang_hi, color=COLORS['tertiary'], alpha=0.20)
    ax_inhib.axhline(tang_lo, color=COLORS['tertiary'], lw=1.0, alpha=0.8)
    ax_inhib.axhline(tang_hi, color=COLORS['tertiary'], lw=1.0, alpha=0.8)
    ax_inhib.text(0.5, (tang_lo + tang_hi) / 2, 'Tang et al. (2021)\nfield inhibition',
                  ha='center', va='center', fontsize=8, color=COLORS['tertiary'],
                  transform=ax_inhib.get_yaxis_transform())

    # Show this study's shelter metric as text annotation (different metric, not on same axis)
    if shelter_val is not None:
        ax_inhib.text(0.5, 0.08,
                      f'This study: shelter efficiency = {shelter_val:.0%}\n'
                      r'(different metric; not directly comparable)',
                      transform=ax_inhib.transAxes, ha='center', va='bottom',
                      fontsize=7, style='italic', color='0.4')

    ax_inhib.set_xlim(0, 1)
    ax_inhib.set_xticks([])
    ax_inhib.set_ylabel('Sand inhibition [%]')
    ax_inhib.set_title('(b) Field-scale inhibition')
    ax_inhib.set_ylim(0, 100)
    ax_inhib.grid(False)

    fig.tight_layout()
    save_figure(fig, 'F12_field_comparison')
    print("  F12 done")


# ================================================================
# Main
# ================================================================
def main():
    print("=" * 60)
    print("GENERATING FIGURES FROM OPENFOAM RESULTS")
    print("=" * 60)

    results = load_results()

    # F1: Domain schematic (no data needed)
    print("\nF1: Domain schematic")
    fig_F1()

    # F3: ABL validation (uses precursor data)
    print("\nF3: ABL validation")
    fig_F3()

    if results is None:
        print("\nWARNING: No OpenFOAM results file found.")
        print("Run postprocess_openfoam.py first.")
        print("Generating placeholder figures...")
        results = {'mesh_independence': [], 'parametric': []}

    # F2: Mesh independence
    print("\nF2: Mesh independence")
    fig_F2(results)

    # F4: Flow field
    print("\nF4: Flow field comparison")
    fig_F4(results)

    # F5: Friction velocity
    print("\nF5: Friction velocity regimes")
    fig_F5(results)

    # F6: Parametric heatmap
    print("\nF6: Parametric heatmap")
    fig_F6(results)

    # F7: Foundation erosion
    print("\nF7: Foundation erosion")
    fig_F7(results)

    # F8: Row-by-row accumulation
    print("\nF8: Sand accumulation by row")
    fig_F8(results)

    # F9: Shelter efficiency and regime
    print("\nF9: Shelter and regime")
    fig_F9(results)

    # F10: Design nomogram
    print("\nF10: Design nomogram")
    fig_F10(results)

    # F11: Sensitivity analysis
    print("\nF11: Sensitivity analysis")
    fig_F11(results)

    # F12: Field comparison (verified data only)
    print("\nF12: Field comparison")
    fig_F12(results)

    print("\n" + "=" * 60)
    print("ALL FIGURES GENERATED")
    print("=" * 60)


if __name__ == '__main__':
    main()
