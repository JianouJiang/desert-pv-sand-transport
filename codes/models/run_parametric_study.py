#!/usr/bin/env python3
"""
Parametric Study: PV Array Sand Transport
==========================================
Runs the full parametric matrix:
  H     = {0.1, 0.3, 0.5, 0.8} m   (ground clearance)
  theta = {15, 25, 35} deg           (tilt angle)
  S     = {2H_panel, 4H_panel, 6H_panel} (row spacing, scaled by panel projection height)

Where H_panel = H + L*sin(theta) is the total panel height above ground.

36 cases total. Uses 8 cores via multiprocessing.

Author: Worker Agent (Paper Factory)
"""

import sys
import os
import json
import time
import numpy as np
from multiprocessing import Pool

# Ensure imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from rans_solver import create_grid, solve_rans, define_panel_array


def run_single_case(params):
    """Run a single parametric case."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    from analysis.sand_transport import compute_transport

    H, theta_deg, S, case_id = params
    L = 2.0  # panel chord length [m]
    N_rows = 8
    u_ref = 10.0
    z0 = 0.001
    d_p = 200e-6

    try:
        panels = define_panel_array(N_rows=N_rows, H=H, theta_deg=theta_deg,
                                    S=S, L=L)
        theta_rad = np.radians(theta_deg)
        x_last = panels[-1]['x0'] + L * np.cos(theta_rad)
        Lx = x_last + 15.0
        Ly = max(8.0, 3 * (H + L * np.sin(theta_rad)))
        Nx = max(200, int(Lx / 0.15))
        Ny = 60

        grid = create_grid(Lx=Lx, Ly=Ly, Nx=Nx, Ny=Ny, y_stretch=1.04)
        flow = solve_rans(grid, panels, u_ref=u_ref, z_ref=10.0, z0=z0,
                          max_iter=400, tol=1e-4, verbose=False)
        transport = compute_transport(flow, d_p=d_p)

        result = {
            'H': H, 'theta_deg': theta_deg, 'S': S, 'case_id': case_id,
            'total_panel_dep': transport['total_panel_dep'],
            'total_panel_dep_norm': transport['total_panel_dep_norm'],
            'mean_panel_dep': transport['mean_panel_dep_per_row'],
            'panel_dep_per_row': transport['panel_dep'].tolist(),
            'mean_found_erosion': transport['mean_found_erosion'],
            'foundation_erosion': transport['foundation_erosion'].tolist(),
            'mean_inter_row': transport['mean_inter_row'],
            'inter_row_dep': transport['inter_row_dep'].tolist(),
            'shelter_ratio': transport['shelter_ratio'],
            'reattach_lengths': transport['reattach_lengths'],
            'u_star_t': transport['u_star_t'],
            'lambda_s': transport['lambda_s'],
            'q_ref': transport['q_ref'],
            'status': 'success',
        }
    except Exception as e:
        result = {
            'H': H, 'theta_deg': theta_deg, 'S': S, 'case_id': case_id,
            'status': 'failed', 'error': str(e),
        }

    return result


def build_case_matrix():
    """Build the 36-case parametric matrix."""
    H_values = [0.1, 0.3, 0.5, 0.8]
    theta_values = [15, 25, 35]
    L = 2.0  # panel chord

    cases = []
    case_id = 0
    for H in H_values:
        for theta_deg in theta_values:
            theta_rad = np.radians(theta_deg)
            H_panel = H + L * np.sin(theta_rad)  # total panel height

            for S_factor in [2, 4, 6]:
                S = S_factor * H_panel
                cases.append((H, theta_deg, S, case_id))
                case_id += 1

    return cases


def run_sensitivity_study(base_results):
    """Run wind speed and grain size sensitivity cases."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    from analysis.sand_transport import compute_transport

    # Select 3 representative configurations
    configs = [
        (0.1, 25, None, 'capture'),
        (0.3, 25, None, 'transitional'),
        (0.8, 25, None, 'passthrough'),
    ]

    L = 2.0
    N_rows = 8
    sensitivity_results = []

    for H, theta_deg, _, regime in configs:
        theta_rad = np.radians(theta_deg)
        H_panel = H + L * np.sin(theta_rad)
        S = 4 * H_panel

        # Wind speed sensitivity
        for u_ref in [8.0, 10.0, 14.0]:
            panels = define_panel_array(N_rows=N_rows, H=H, theta_deg=theta_deg,
                                        S=S, L=L)
            x_last = panels[-1]['x0'] + L * np.cos(theta_rad)
            Lx = x_last + 15.0
            Ly = max(8.0, 3 * H_panel)
            Nx = max(200, int(Lx / 0.15))

            grid = create_grid(Lx=Lx, Ly=Ly, Nx=Nx, Ny=60, y_stretch=1.04)
            flow = solve_rans(grid, panels, u_ref=u_ref, z_ref=10.0, z0=0.001,
                              max_iter=400, tol=1e-4, verbose=False)

            for d_p in [100e-6, 200e-6, 300e-6]:
                t = compute_transport(flow, d_p=d_p)
                sensitivity_results.append({
                    'regime': regime, 'H': H, 'theta_deg': theta_deg, 'S': S,
                    'u_ref': u_ref, 'd_p': d_p * 1e6,
                    'total_panel_dep': t['total_panel_dep'],
                    'shelter_ratio': t['shelter_ratio'],
                    'mean_found_erosion': t['mean_found_erosion'],
                })

    return sensitivity_results


def main():
    t0 = time.time()
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           '..', '..', 'codes', 'results')
    os.makedirs(out_dir, exist_ok=True)

    # === Parametric study ===
    cases = build_case_matrix()
    print(f"Running {len(cases)} parametric cases on 8 workers...")

    with Pool(8) as pool:
        results = pool.map(run_single_case, cases)

    # Save results
    out_path = os.path.join(out_dir, 'parametric_results.json')
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Saved to {out_path}")

    # Summary
    n_success = sum(1 for r in results if r['status'] == 'success')
    n_fail = sum(1 for r in results if r['status'] == 'failed')
    print(f"\n{n_success} success, {n_fail} failed")

    if n_success > 0:
        # Print summary table
        print(f"\n{'H':>5} {'theta':>6} {'S':>6} {'panel_dep':>12} "
              f"{'shelter':>8} {'erosion':>10}")
        print("-" * 60)
        for r in sorted(results, key=lambda x: (x['H'], x['theta_deg'], x['S'])):
            if r['status'] == 'success':
                print(f"{r['H']:5.1f} {r['theta_deg']:6.0f} {r['S']:6.2f} "
                      f"{r['total_panel_dep']:12.4e} "
                      f"{r['shelter_ratio']:8.3f} "
                      f"{r['mean_found_erosion']:10.4e}")

    # === Sensitivity study ===
    print(f"\nRunning sensitivity study...")
    sens = run_sensitivity_study(results)
    sens_path = os.path.join(out_dir, 'sensitivity_results.json')
    with open(sens_path, 'w') as f:
        json.dump(sens, f, indent=2)
    print(f"Saved to {sens_path}")

    elapsed = time.time() - t0
    print(f"\nTotal time: {elapsed:.0f}s ({elapsed/60:.1f} min)")


if __name__ == '__main__':
    main()
