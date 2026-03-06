#!/usr/bin/env python3
"""
Generate validation figure: velocity profiles downstream of PV panel.

Extracts vertical velocity profiles from converged parametric case (case_23:
H=0.5m, theta=25deg, S=4Hp) at multiple downstream positions behind the
first panel row. Compares against:
  1. Upstream (undisturbed) ABL profile
  2. Analytical log-law profile
  3. Expected wake deficit pattern for k-epsilon behind bluff bodies

This validates that the solver captures the essential wake physics:
separation, reattachment, and velocity recovery.

Reference: The k-epsilon model is known to overpredict reattachment length
by ~20-30% for bluff bodies (Tominaga et al., 2008), and typical wake
deficit at x/H=5 is 10-15% for 2D obstacles.
"""

import sys
import numpy as np
from pathlib import Path

# Add project paths
PROJECT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_DIR / 'codes' / 'utils'))
from plotting_utils import plt, COLORS

# Constants
KAPPA = 0.41
U_REF = 10.0
Z_REF = 10.0
Z0 = 0.001
PANEL_LENGTH = 2.0


def parse_openfoam_field(filepath):
    """Parse an OpenFOAM scalar field file and return values as numpy array."""
    with open(filepath) as f:
        content = f.read()
    # Find the data block
    idx = content.find('internalField')
    if idx < 0:
        return np.array([])
    # Find opening paren after the count
    start = content.find('(', idx)
    # Find the closing paren on its own line
    end = content.find('\n)', start)
    if end < 0:
        end = content.find(')', start + 1)
    data_str = content[start + 1:end].strip()
    return np.array([float(x) for x in data_str.split()])


def parse_openfoam_vector_field(filepath):
    """Parse an OpenFOAM vector field file and return Ux, Uy, Uz arrays."""
    with open(filepath) as f:
        content = f.read()
    idx = content.find('internalField')
    if idx < 0:
        return np.array([]), np.array([]), np.array([])
    start = content.find('(', idx)
    end = content.find('\n)', start)
    if end < 0:
        end = content.find(')', start + 1)
    data_str = content[start + 1:end].strip()
    # Parse vector tuples (Ux Uy Uz)
    lines = data_str.split('\n')
    ux, uy, uz = [], [], []
    for line in lines:
        line = line.strip().strip('()')
        if not line:
            continue
        parts = line.split()
        if len(parts) >= 3:
            ux.append(float(parts[0]))
            uy.append(float(parts[1]))
            uz.append(float(parts[2]))
    return np.array(ux), np.array(uy), np.array(uz)


def extract_profiles(case_dir, time_dir, x_positions, x_tol=0.5):
    """Extract vertical velocity profiles at specified x-positions."""
    td = Path(case_dir) / str(time_dir)

    # Read cell centres
    cx = parse_openfoam_field(td / 'Cx')
    cz = parse_openfoam_field(td / 'Cz')

    # Read velocity
    ux, _, uz = parse_openfoam_vector_field(td / 'U')

    # Read TKE
    k = parse_openfoam_field(td / 'k')

    profiles = {}
    for x_target in x_positions:
        mask = np.abs(cx - x_target) < x_tol
        if mask.sum() < 5:
            # Try wider tolerance
            mask = np.abs(cx - x_target) < x_tol * 2
        if mask.sum() < 5:
            print(f"  Warning: only {mask.sum()} cells near x={x_target:.2f}")
            continue

        z_prof = cz[mask]
        u_prof = ux[mask]
        k_prof = k[mask]

        # Sort by z
        order = np.argsort(z_prof)
        profiles[x_target] = {
            'z': z_prof[order],
            'U': u_prof[order],
            'k': k_prof[order],
        }

    return profiles


def generate_validation_figure():
    """Generate the panel-wake validation figure."""
    # Use S=6Hp case for wider inter-panel gap (gap = 3.86 Hp)
    case_dir = (PROJECT_DIR / 'codes' / 'openfoam' / 'parametric_study'
                / 'case_24_H0.5_T25_S6Hp')

    # Case parameters
    H = 0.5
    theta = 25.0
    Hp = PANEL_LENGTH * np.sin(np.radians(theta))
    S = 6 * Hp
    fetch = 20.0

    # Panel 1 trailing edge
    x_te1 = fetch + PANEL_LENGTH * np.cos(np.radians(theta))

    # Extraction positions: upstream, and x/Hp = 1, 2, 3 downstream of TE
    # (all within the inter-panel gap, which extends to 3.86 Hp)
    x_upstream = 10.0  # well upstream of array
    x_positions = [
        x_upstream,
        x_te1 + 1 * Hp,
        x_te1 + 2 * Hp,
        x_te1 + 3 * Hp,
    ]
    labels = [
        'Upstream',
        f'$x/H_p = 1$',
        f'$x/H_p = 2$',
        f'$x/H_p = 3$',
    ]

    # Find latest time directory
    time_dirs = sorted([d.name for d in case_dir.iterdir()
                       if d.is_dir() and d.name not in
                       ('0', 'constant', 'system', 'postProcessing', 'dynamicCode')
                       and not d.name.startswith('processor')
                       and d.name.replace('.', '').isdigit()],
                      key=lambda x: float(x))
    if not time_dirs:
        print("ERROR: No time directories found")
        return
    latest = time_dirs[-1]
    print(f"  Using time directory: {latest}")

    # Extract profiles
    print("  Extracting velocity profiles...")
    profiles = extract_profiles(case_dir, latest, x_positions, x_tol=0.3)

    if len(profiles) < 2:
        print(f"  ERROR: Only {len(profiles)} profiles extracted (need >= 2)")
        return

    # Analytical log-law
    ustar_ref = KAPPA * U_REF / np.log(Z_REF / Z0)
    z_anal = np.linspace(0.01, 5.0, 200)
    u_loglaw = (ustar_ref / KAPPA) * np.log(z_anal / Z0)

    # --- Create figure ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 4.0))

    # Panel (a): Velocity profiles
    # Log-law reference
    ax1.plot(u_loglaw, z_anal, 'k--', lw=1.5, label='Log-law', alpha=0.6)

    colors_prof = [COLORS['primary'], COLORS['secondary'],
                   COLORS['tertiary'], COLORS.get('quaternary', '#e07b39')]
    markers = ['o', 's', '^', 'D']

    for i, (x_pos, lbl) in enumerate(zip(x_positions, labels)):
        if x_pos not in profiles:
            continue
        prof = profiles[x_pos]
        z = prof['z']
        U = prof['U']
        # Subsample for clarity (every 3rd point)
        step = max(1, len(z) // 25)
        ax1.plot(U[::step], z[::step], markers[i], color=colors_prof[i],
                 ms=4, mew=0.5, label=lbl, alpha=0.85)

    ax1.set_xlabel('$U_x$ [m/s]')
    ax1.set_ylabel('$z$ [m]')
    ax1.set_title('(a) Velocity profiles behind first panel row')
    ax1.set_ylim(0, 3.0)
    ax1.set_xlim(0, None)
    ax1.legend(fontsize=7, loc='lower right', frameon=False)
    ax1.grid(False)

    # Add panel schematic on the profile plot
    # Show panel as a thick line at x_te1
    panel_z_bottom = H
    panel_z_top = H + Hp
    # Just mark the panel height range
    ax1.axhspan(panel_z_bottom, panel_z_top, alpha=0.08, color='k', lw=0)
    ax1.text(0.5, (panel_z_bottom + panel_z_top) / 2, 'panel\nheight',
             fontsize=6, ha='center', va='center', color='0.5')

    # Panel (b): Normalized velocity U/U_upstream at each downstream station
    if x_upstream in profiles:
        u_up = profiles[x_upstream]
        z_up = u_up['z']
        U_up = u_up['U']

        for i, (x_pos, lbl) in enumerate(zip(x_positions[1:], labels[1:])):
            if x_pos not in profiles:
                continue
            prof = profiles[x_pos]
            z_p = prof['z']
            U_p = prof['U']

            # Interpolate upstream to same z-grid
            U_up_interp = np.interp(z_p, z_up, U_up)
            U_ratio = U_p / np.clip(U_up_interp, 0.5, None)

            # Subsample
            step = max(1, len(z_p) // 25)
            ax2.plot(U_ratio[::step], z_p[::step], markers[i + 1],
                     color=colors_prof[i + 1], ms=4, mew=0.5,
                     label=lbl, alpha=0.85)

        # Reference line at U/U_up = 1
        ax2.axvline(1.0, color='k', ls='--', lw=1.0, alpha=0.5)

        # Mark panel height zone
        ax2.axhspan(H, H + Hp, alpha=0.08, color='k', lw=0)
        ax2.text(0.15, (H + Hp / 2), 'panel', fontsize=6, va='center',
                 color='0.5')

        ax2.set_xlabel('$U / U_\\mathrm{upstream}$')
        ax2.set_ylabel('$z$ [m]')
        ax2.set_title('(b) Normalized velocity profiles')
        ax2.set_xlim(-0.2, 1.5)
        ax2.set_ylim(0, 3.0)
        ax2.legend(fontsize=7, loc='lower right', frameon=False)
        ax2.grid(False)

        # Print quantitative recovery metrics
        print(f"\n  Wake recovery metrics:")
        for x_pos, lbl in zip(x_positions[1:], labels[1:]):
            if x_pos not in profiles:
                continue
            prof = profiles[x_pos]
            z_p = prof['z']
            U_p = prof['U']
            U_up_interp = np.interp(z_p, z_up, U_up)
            # Mean velocity ratio above ground, below 2*H
            mask = (z_p > 0.1) & (z_p < 2 * H)
            ratio = U_p[mask] / np.clip(U_up_interp[mask], 0.5, None)
            xHp = (x_pos - x_te1) / Hp
            print(f"    {lbl}: mean U/U_up (z<2H) = {np.mean(ratio):.3f}, "
                  f"min U/U_up = {np.min(ratio):.3f}")

    fig.tight_layout()

    # Save
    fig_dir = PROJECT_DIR / 'manuscript' / 'figures'
    for ext in ['pdf', 'png']:
        out = fig_dir / f'F3_validation_wake_profiles.{ext}'
        fig.savefig(out, dpi=300, bbox_inches='tight')
        print(f"  Saved: {out}")

    plt.close(fig)
    print("  Validation figure done")


if __name__ == '__main__':
    generate_validation_figure()
