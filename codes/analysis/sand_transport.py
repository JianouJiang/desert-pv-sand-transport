#!/usr/bin/env python3
"""
Sand Transport Model for PV Array Deposition
=============================================
Uses RANS friction velocity + saltation physics to compute deposition.

Key physics:
  - Sand flux: Owen (1964) formula, q = C * rho_a/g * u*^3 * (1 - u*_t^2/u*^2)
  - Saltation concentration profile: exponential decay c(y) = c_0 * exp(-y/lambda_s)
    where lambda_s = 2*u*^2/g (Anderson & Haff 1991)
  - Panel deposition: gravitational settling + impaction from saltation layer
  - Ground deposition/erosion: from gradient of horizontal sand flux

Author: Worker Agent (Paper Factory)
"""

import numpy as np


RHO_AIR = 1.225
RHO_SAND = 2650.0
MU_AIR = 1.8e-5
GRAVITY = 9.81
KAPPA = 0.41


def threshold_friction_velocity(d_p, rho_p=RHO_SAND, rho_a=RHO_AIR):
    """Shao & Lu (2000) threshold."""
    return np.sqrt(0.0123 * (rho_p * GRAVITY * d_p / rho_a + 3e-4 / (rho_a * d_p)))


def settling_velocity(d_p, rho_p=RHO_SAND, rho_a=RHO_AIR, mu_a=MU_AIR):
    """Terminal settling velocity (iterative Schiller-Naumann)."""
    tau_p = rho_p * d_p**2 / (18 * mu_a)
    v_s = tau_p * GRAVITY * (1 - rho_a / rho_p)
    for _ in range(10):
        Re_p = rho_a * v_s * d_p / mu_a
        f = 1.0 + 0.15 * max(Re_p, 1e-6)**0.687
        v_s = tau_p * GRAVITY * (1 - rho_a / rho_p) / f
    return v_s


def sand_flux_owen(u_star, u_star_t, rho_a=RHO_AIR):
    """Owen (1964) sand flux [kg/(m*s)]."""
    C = 0.25
    u_star = np.atleast_1d(np.float64(u_star))
    q = np.zeros_like(u_star)
    active = u_star > u_star_t
    us = u_star[active]
    q[active] = C * (rho_a / GRAVITY) * us**3 * (1 - (u_star_t / us)**2)
    return q


def saltation_height_scale(u_star):
    """Saltation layer decay height lambda_s [m] (Anderson & Haff 1991)."""
    return 2.0 * u_star**2 / GRAVITY


def saltation_concentration(y, u_star, q_sand, d_p):
    """Saltation concentration profile [kg/m^3].

    c(y) = c_0 * exp(-y / lambda_s)
    c_0 = q / (u_mean_salt * lambda_s)
    """
    lam = saltation_height_scale(u_star)
    lam = max(lam, 1e-6)

    # Mean velocity in saltation layer
    u_mean_salt = (u_star / KAPPA) * np.log((lam + 0.001) / 0.001)
    u_mean_salt = max(u_mean_salt, 0.1)

    c_0 = q_sand / (u_mean_salt * lam) if q_sand > 0 else 0.0

    y = np.atleast_1d(np.float64(y))
    c = c_0 * np.exp(-y / lam)
    return c


def panel_impaction_efficiency(d_p, u_wind, L_panel,
                               rho_p=RHO_SAND, mu_a=MU_AIR):
    """Impaction efficiency from Stokes number."""
    tau_p = rho_p * d_p**2 / (18 * mu_a)
    Stk = tau_p * u_wind / L_panel
    return Stk / (Stk + 0.5)


def compute_transport(result, d_p=200e-6):
    """Compute sand transport metrics from RANS flow result.

    Returns dict with all five key metrics plus spatial distributions.
    """
    grid = result['grid']
    x = grid['x']
    y = grid['y']
    Nx, Ny = grid['Nx'], grid['Ny']
    dx = grid['dx']
    panels = result['panels']
    u = result['u']
    u_star_loc = result['u_star_local']
    u_star_ref = result['u_star']

    v_s = settling_velocity(d_p)
    u_star_t = threshold_friction_velocity(d_p)
    lam_ref = saltation_height_scale(u_star_ref)

    # === Ground-level sand flux ===
    q_sand = sand_flux_owen(u_star_loc, u_star_t)
    q_ref = sand_flux_owen(np.array([u_star_ref]), u_star_t)[0]

    # Deposition rate = -dq/dx
    dq_dx = np.gradient(q_sand, dx)
    dep_rate = -dq_dx
    erosion = np.maximum(-dep_rate, 0)
    deposition = np.maximum(dep_rate, 0)

    # === Panel deposition ===
    n_panels = len(panels)
    panel_dep = np.zeros(n_panels)
    panel_dep_grav = np.zeros(n_panels)
    panel_dep_impact = np.zeros(n_panels)

    for pi, p in enumerate(panels):
        H = p['H']
        theta = np.radians(p['theta_deg'])
        L = p['L']

        # Panel cross-section heights
        y_bot = H
        y_top = H + L * np.sin(theta)
        y_panel = np.linspace(y_bot, y_top, 100)

        # Local conditions at panel location
        i_p = np.searchsorted(x, p['x0'] + L * np.cos(theta) / 2)
        i_p = min(i_p, Nx - 1)
        u_star_panel = max(u_star_loc[i_p], 0.01)
        q_panel = sand_flux_owen(np.array([u_star_panel]), u_star_t)[0]

        # Saltation concentration at panel heights
        c_at_panel = saltation_concentration(y_panel, u_star_ref, max(q_ref, 1e-20), d_p)

        # Wind speed at panel heights
        u_at_panel = np.interp(y_panel, y, u[i_p, :])

        # Gravitational settling onto panel top surface
        # Rate per unit panel width = integral of c * v_s * cos(theta) along panel
        panel_width_proj = L * np.cos(theta)  # horizontal projection
        dy_panel = np.diff(y_panel)
        c_mid = 0.5 * (c_at_panel[:-1] + c_at_panel[1:])
        grav = np.sum(c_mid * v_s * np.cos(theta) * dy_panel)
        panel_dep_grav[pi] = grav

        # Impaction (inertial deposition on windward face)
        eta = panel_impaction_efficiency(d_p, np.mean(u_at_panel), L)
        flux = np.sum(c_mid * u_at_panel[:-1] * dy_panel)
        impact = eta * flux * np.sin(theta)
        panel_dep_impact[pi] = impact

        panel_dep[pi] = grav + impact

    # === Foundation erosion (near panel base) ===
    found_erosion = np.zeros(n_panels)
    for pi, p in enumerate(panels):
        i_foot = np.searchsorted(x, p['x0'])
        zone = int(max(1.0 / dx, 1))
        i0 = max(0, i_foot - zone)
        i1 = min(Nx, i_foot + zone)
        found_erosion[pi] = np.mean(erosion[i0:i1]) if i1 > i0 else 0

    # === Inter-row accumulation ===
    inter_row = np.zeros(max(n_panels - 1, 1))
    for i in range(n_panels - 1):
        theta_i = np.radians(panels[i]['theta_deg'])
        x_end = panels[i]['x0'] + panels[i]['L'] * np.cos(theta_i)
        x_start = panels[i + 1]['x0']
        i0 = np.searchsorted(x, x_end)
        i1 = np.searchsorted(x, x_start)
        if i1 > i0:
            inter_row[i] = np.mean(deposition[i0:i1])

    # === Shelter ratio ===
    if n_panels > 0:
        theta_last = np.radians(panels[-1]['theta_deg'])
        x_trail = panels[-1]['x0'] + panels[-1]['L'] * np.cos(theta_last)
        i_trail = np.searchsorted(x, x_trail)
        i_down = min(Nx, i_trail + int(5.0 / dx))
        u_star_down = np.mean(u_star_loc[i_trail:i_down]) if i_down > i_trail else u_star_ref
        i_up = max(0, np.searchsorted(x, panels[0]['x0']) - int(3.0 / dx))
        u_star_up = np.mean(u_star_loc[:max(i_up, 1)])
        shelter = u_star_down / max(u_star_up, 0.01)
    else:
        shelter = 1.0

    # Reattachment lengths from RANS
    reattach = result.get('reattach_lengths', [])

    return {
        'x': x, 'q_sand': q_sand, 'dep_rate': dep_rate,
        'erosion': erosion, 'deposition': deposition,
        'u_star_local': u_star_loc,

        'panel_dep': panel_dep,
        'panel_dep_grav': panel_dep_grav,
        'panel_dep_impact': panel_dep_impact,
        'panel_dep_norm': panel_dep / max(q_ref, 1e-30),

        'foundation_erosion': found_erosion,
        'inter_row_dep': inter_row,
        'shelter_ratio': shelter,
        'reattach_lengths': reattach,

        # Summary scalars
        'total_panel_dep': float(np.sum(panel_dep)),
        'total_panel_dep_norm': float(np.sum(panel_dep) / max(q_ref, 1e-30)),
        'mean_found_erosion': float(np.mean(found_erosion)),
        'mean_inter_row': float(np.mean(inter_row)),
        'mean_panel_dep_per_row': float(np.mean(panel_dep)) if n_panels > 0 else 0,

        # Physical parameters
        'u_star_t': u_star_t, 'v_s': v_s,
        'lambda_s': lam_ref, 'q_ref': q_ref,
    }


def run_parametric_case(H, theta_deg, S, u_ref=10.0, d_p=200e-6,
                        N_rows=8, L=2.0, z0=0.001):
    """Run a single parametric case: RANS flow + sand transport.

    Returns (flow_result, transport_result).
    """
    from models.rans_solver import create_grid, solve_rans, define_panel_array

    panels = define_panel_array(N_rows=N_rows, H=H, theta_deg=theta_deg,
                                S=S, L=L)
    # Domain size: upstream buffer + array + downstream buffer
    x_last = panels[-1]['x0'] + L * np.cos(np.radians(theta_deg))
    Lx = x_last + 15.0  # 15m downstream buffer
    Ly = max(8.0, 3 * (H + L * np.sin(np.radians(theta_deg))))

    Nx = max(200, int(Lx / 0.15))  # ~15cm resolution
    Ny = 60

    grid = create_grid(Lx=Lx, Ly=Ly, Nx=Nx, Ny=Ny, y_stretch=1.04)
    flow = solve_rans(grid, panels, u_ref=u_ref, z_ref=10.0, z0=z0,
                      max_iter=400, tol=1e-4, verbose=False)
    transport = compute_transport(flow, d_p=d_p)

    return flow, transport


if __name__ == '__main__':
    import sys
    sys.path.insert(0, '.')

    print("=" * 60)
    print("Regime transition test: varying ground clearance H")
    print("=" * 60)

    for H in [0.1, 0.3, 0.5, 0.8]:
        flow, st = run_parametric_case(H=H, theta_deg=25, S=6.0,
                                        u_ref=10.0, d_p=200e-6, N_rows=4)
        print(f"H={H:.1f}m: panel_dep={st['total_panel_dep']:.4e} kg/(m*s), "
              f"norm={st['total_panel_dep_norm']:.4f}, "
              f"shelter={st['shelter_ratio']:.3f}, "
              f"lambda_s={st['lambda_s']*100:.1f}cm")
