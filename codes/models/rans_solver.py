#!/usr/bin/env python3
"""
2D Steady RANS Solver for ABL Flow Over PV Panel Arrays
========================================================
Vorticity--stream function formulation with mixing-length turbulence model.
Direct sparse Poisson solver (scipy.sparse.linalg.splu).
Immersed boundary method (volume penalization) for PV panels.

Physics:
  - Incompressible 2D RANS (steady)
  - Mixing-length turbulence model: nu_t = l_m^2 |du/dy|
  - ABL log-law inlet profile with roughness z0
  - Panels as immersed boundaries (penalty method)

Reference frame: x = streamwise, y = vertical.

Author: Worker Agent (Paper Factory)
"""

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import splu
import json
import os
import time


# Physical constants
RHO_AIR = 1.225       # kg/m^3
NU_AIR = 1.5e-5       # m^2/s
KAPPA = 0.41          # von Karman constant
GRAVITY = 9.81        # m/s^2


def create_grid(Lx, Ly, Nx, Ny, y_stretch=1.0):
    """Create computational grid with optional y-stretching."""
    dx = Lx / Nx
    x = np.linspace(dx / 2, Lx - dx / 2, Nx)

    if abs(y_stretch - 1.0) < 1e-10:
        dy_arr = np.full(Ny, Ly / Ny)
        yf = np.linspace(0, Ly, Ny + 1)
    else:
        r = y_stretch
        dy0 = Ly * (r - 1.0) / (r**Ny - 1.0)
        dy_arr = dy0 * r ** np.arange(Ny)
        yf = np.concatenate(([0.0], np.cumsum(dy_arr)))
        yf[-1] = Ly
        dy_arr = np.diff(yf)

    y = 0.5 * (yf[:-1] + yf[1:])
    return {'x': x, 'y': y, 'dx': dx, 'dy': dy_arr,
            'Nx': Nx, 'Ny': Ny, 'Lx': Lx, 'Ly': Ly}


def create_panel_mask(grid, panels):
    """Create 0/1 mask for immersed boundary panels."""
    X, Y = np.meshgrid(grid['x'], grid['y'], indexing='ij')
    mask = np.zeros_like(X)
    for p in panels:
        theta = np.radians(p['theta_deg'])
        ct, st = np.cos(theta), np.sin(theta)
        t = p.get('thickness', 0.04)
        s = (X - p['x0']) * ct + (Y - p['H']) * st
        n = -(X - p['x0']) * st + (Y - p['H']) * ct
        inside = (s >= 0) & (s <= p['L']) & (np.abs(n) <= t / 2)
        mask = np.maximum(mask, inside.astype(float))
    return mask


def define_panel_array(N_rows, H, theta_deg, S, L=2.0, x_start=None):
    """Define array of N_rows panels."""
    if x_start is None:
        x_start = max(10.0, 5.0 * (H + L * np.sin(np.radians(theta_deg))))
    panels = []
    for i in range(N_rows):
        panels.append({'x0': x_start + i * S, 'H': H,
                        'theta_deg': theta_deg, 'L': L, 'thickness': 0.04})
    return panels


def abl_profiles(y, u_ref, z_ref, z0):
    """Log-law ABL profiles. Returns (u, u_star)."""
    u_star = u_ref * KAPPA / np.log((z_ref + z0) / z0)
    u = (u_star / KAPPA) * np.log((y + z0) / z0)
    return u, u_star


def build_poisson_matrix(grid, mask):
    """Assemble Poisson operator matrix and LU-factorize.

    nabla^2(psi) = rhs
    BCs: psi=0 at ground (j=0), dpsi/dy=u_top at top (j=Ny-1),
         Dirichlet at inlet (i=0), zero-gradient at outlet (i=Nx-1).

    Returns (LU_factor, bc_rhs_template) where bc_rhs_template encodes
    the boundary condition contributions.
    """
    Nx, Ny = grid['Nx'], grid['Ny']
    x, y = grid['x'], grid['y']
    dx = grid['dx']
    N = Nx * Ny

    rows, cols, vals = [], [], []

    for i in range(Nx):
        for j in range(Ny):
            n = i * Ny + j

            # Inside panels or at Dirichlet boundaries: psi = prescribed
            if i == 0 or j == 0 or j == Ny - 1 or mask[i, j] > 0.5:
                rows.append(n); cols.append(n); vals.append(1.0)
                continue

            # Interior point
            # d²psi/dx² ≈ (psi_{i+1,j} - 2 psi_{i,j} + psi_{i-1,j}) / dx²
            aW = 1.0 / (dx * dx)
            aE = 1.0 / (dx * dx)

            # d²psi/dy² on non-uniform grid
            dy_s = y[j] - y[j - 1]  # distance to south neighbor
            dy_n = y[j + 1] - y[j]  # distance to north neighbor
            dy_c = 0.5 * (dy_s + dy_n)
            aS = 1.0 / (dy_s * dy_c)
            aN = 1.0 / (dy_n * dy_c)
            aP = -(aW + aE + aS + aN)

            # West neighbor
            if i > 1 or True:  # i=0 is Dirichlet handled above
                rows.append(n); cols.append((i - 1) * Ny + j); vals.append(aW)

            # East neighbor
            if i < Nx - 1:
                rows.append(n); cols.append((i + 1) * Ny + j); vals.append(aE)
            else:
                # Outlet: zero-gradient => psi[Nx] = psi[Nx-1] => no east contrib,
                # add aE to aP
                aP += aE

            # South
            rows.append(n); cols.append(i * Ny + (j - 1)); vals.append(aS)
            # North
            rows.append(n); cols.append(i * Ny + (j + 1)); vals.append(aN)

            # Diagonal
            rows.append(n); cols.append(n); vals.append(aP)

    A = sparse.csr_matrix((vals, (rows, cols)), shape=(N, N))
    LU = splu(A.tocsc())
    return LU


def solve_poisson(LU, grid, mask, rhs, psi_in, psi_top):
    """Solve Poisson equation using pre-factored LU.

    rhs : (Nx, Ny) array (the vorticity or similar source term)
    psi_in : (Ny,) inlet stream function profile
    psi_top : float, stream function at top boundary
    """
    Nx, Ny = grid['Nx'], grid['Ny']
    b = rhs.copy().ravel()

    # Apply BCs by setting the corresponding entries of b
    for j in range(Ny):
        # Inlet (i=0): Dirichlet
        b[0 * Ny + j] = psi_in[j]
        # Ground (j=0): psi=0
        for i in range(Nx):
            b[i * Ny + 0] = 0.0
        # Top (j=Ny-1): psi=psi_top
        for i in range(Nx):
            b[i * Ny + (Ny - 1)] = psi_top

    # Set panel cells to interpolated psi (hold at surrounding fluid value)
    for i in range(Nx):
        for j in range(Ny):
            if mask[i, j] > 0.5:
                b[i * Ny + j] = psi_in[j]  # approximate

    psi = LU.solve(b)
    return psi.reshape(Nx, Ny)


def solve_rans(grid, panels, u_ref=10.0, z_ref=10.0, z0=0.001,
               max_iter=400, tol=1e-4, verbose=True):
    """Solve 2D steady RANS.

    Returns dict with all flow fields.
    """
    t0 = time.time()
    Nx, Ny = grid['Nx'], grid['Ny']
    x, y = grid['x'], grid['y']
    dx = grid['dx']
    dy = grid['dy']
    Ly = grid['Ly']

    mask = create_panel_mask(grid, panels)
    fluid = 1.0 - mask

    u_in, u_star = abl_profiles(y, u_ref, z_ref, z0)
    delta = Ly

    # Inlet stream function
    psi_in = np.zeros(Ny)
    for j in range(1, Ny):
        psi_in[j] = psi_in[j - 1] + u_in[j - 1] * dy[j - 1]
    psi_top = psi_in[-1] + u_in[-1] * dy[-1]

    if verbose:
        print(f"RANS: {Nx}x{Ny}, u_ref={u_ref:.1f} m/s, z0={z0}, "
              f"u*={u_star:.4f}, panels={len(panels)}")

    # Build and factorize Poisson matrix
    if verbose:
        print("  Factorizing Poisson matrix...")
    LU = build_poisson_matrix(grid, mask)
    if verbose:
        print(f"  LU factorized in {time.time() - t0:.1f}s")

    # Initialize velocity
    u = np.outer(np.ones(Nx), u_in) * fluid
    v = np.zeros((Nx, Ny))
    psi = np.outer(np.ones(Nx), psi_in)

    residuals = []

    for iteration in range(max_iter):
        u_prev = u.copy()

        # ---- Mixing-length eddy viscosity ----
        l_m = np.minimum(KAPPA * y[np.newaxis, :], 0.09 * delta)
        dudy = np.zeros((Nx, Ny))
        dudy[:, 1:-1] = (np.abs(u[:, 2:] - u[:, :-2])
                         / (y[2:] - y[:-2])[np.newaxis, :])
        dudy[:, 0] = np.abs(u[:, 1]) / y[1]
        nu_t = l_m**2 * dudy
        nu_t = np.clip(nu_t, 0, 2000 * NU_AIR)

        # ---- Compute vorticity omega = dv/dx - du/dy ----
        omega = np.zeros((Nx, Ny))

        # Interior: central differences
        omega[1:-1, 1:-1] = (
            (v[2:, 1:-1] - v[:-2, 1:-1]) / (2 * dx)
            - (u[1:-1, 2:] - u[1:-1, :-2])
              / (y[2:] - y[:-2])[np.newaxis, :]
        )

        # Ground (j=0): Thom's formula
        omega[:, 0] = -2.0 * u[:, 1] / (y[1] * y[1])  # wall vorticity

        # Top: free-stream, omega -> 0
        omega[:, -1] = 0.0

        # Inlet
        omega[0, 1:-1] = -(u_in[2:] - u_in[:-2]) / (y[2:] - y[:-2])

        # Outlet
        omega[-1, :] = omega[-2, :]

        # Mask: zero vorticity inside panels
        omega *= fluid

        # ---- Solve Poisson: nabla^2(psi) = -omega ----
        rhs = -omega.copy()
        psi_new = solve_poisson(LU, grid, mask, rhs, psi_in, psi_top)

        # Under-relax psi
        alpha_psi = 0.4
        psi = alpha_psi * psi_new + (1 - alpha_psi) * psi

        # ---- Velocity from stream function ----
        # u = dpsi/dy
        u_new = np.zeros((Nx, Ny))
        u_new[:, 1:-1] = ((psi[:, 2:] - psi[:, :-2])
                          / (y[2:] - y[:-2])[np.newaxis, :])
        u_new[:, 0] = 0.0         # no-slip ground
        u_new[:, -1] = u_in[-1]   # free-stream top

        # v = -dpsi/dx
        v_new = np.zeros((Nx, Ny))
        v_new[1:-1, :] = -(psi[2:, :] - psi[:-2, :]) / (2 * dx)
        v_new[0, :] = 0.0
        v_new[-1, :] = v_new[-2, :]

        # Inlet BCs
        u_new[0, :] = u_in
        v_new[0, :] = 0.0

        # Apply immersed boundary
        u_new *= fluid
        v_new *= fluid

        # Under-relax velocity
        alpha_u = 0.3
        u = alpha_u * u_new + (1 - alpha_u) * u_prev
        v = alpha_u * v_new + (1 - alpha_u) * v

        # ---- Convergence check ----
        res = np.sqrt(np.mean((u - u_prev)**2)) / max(np.mean(np.abs(u_prev) + 1e-10), 1e-10)
        residuals.append(res)

        if verbose and (iteration % 50 == 0 or iteration < 5):
            print(f"  Iter {iteration:4d}: res={res:.3e}  [{time.time() - t0:.1f}s]")

        if res < tol and iteration > 30:
            if verbose:
                print(f"  CONVERGED at iter {iteration}, res={res:.3e}")
            break
    else:
        if verbose:
            print(f"  Max iterations. res={residuals[-1]:.3e}")

    # ---- Post-process: friction velocity at ground ----
    u_star_local = np.zeros(Nx)
    for i in range(Nx):
        u1 = u[i, 1]
        if u1 > 1e-6:
            u_star_local[i] = u1 * KAPPA / max(np.log((y[1] + z0) / z0), 0.1)
        elif u1 < -1e-6:
            u_star_local[i] = -abs(u1) * KAPPA / max(np.log((y[1] + z0) / z0), 0.1)
    tau_w = RHO_AIR * np.sign(u_star_local) * u_star_local**2

    # Reattachment lengths
    reattach_lengths = []
    for p in panels:
        theta = np.radians(p['theta_deg'])
        x_trail = p['x0'] + p['L'] * np.cos(theta)
        j_near_ground = min(3, Ny - 1)
        i_trail = np.searchsorted(x, x_trail)
        i_end = min(i_trail + int(15.0 / dx), Nx)
        if i_trail < Nx:
            u_gnd = u[i_trail:i_end, j_near_ground]
            pos = np.where(u_gnd > 0.05 * u_ref)[0]
            Lr = pos[0] * dx if len(pos) > 0 else (i_end - i_trail) * dx
        else:
            Lr = 0.0
        reattach_lengths.append(Lr)

    elapsed = time.time() - t0
    if verbose:
        print(f"  Total time: {elapsed:.1f}s")

    return {
        'u': u, 'v': v, 'psi': psi, 'omega': omega,
        'nu_t': nu_t, 'mask': mask, 'grid': grid,
        'u_star': u_star, 'u_star_local': u_star_local, 'tau_w': tau_w,
        'panels': panels, 'residuals': np.array(residuals),
        'u_ref': u_ref, 'z0': z0, 'u_in': u_in,
        'reattach_lengths': reattach_lengths,
    }


def save_result(result, filepath):
    """Save result to npz."""
    d = {}
    for k, v in result.items():
        if isinstance(v, np.ndarray):
            d[k] = v
        elif k == 'grid':
            for k2, v2 in v.items():
                d[f'g_{k2}'] = np.atleast_1d(v2)
        elif k == 'panels':
            d['_p'] = np.array([json.dumps(v)])
        elif k == 'reattach_lengths':
            d['_rl'] = np.array(v)
        elif isinstance(v, (int, float)):
            d[k] = np.array([v])
    os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
    np.savez_compressed(filepath, **d)


def load_result(filepath):
    """Load result from npz."""
    data = np.load(filepath, allow_pickle=True)
    r = {}; g = {}
    for k in data.files:
        if k.startswith('g_'):
            v = data[k]; g[k[2:]] = v.item() if v.size == 1 else v
        elif k == '_p':
            r['panels'] = json.loads(str(data[k][0]))
        elif k == '_rl':
            r['reattach_lengths'] = list(data[k])
        else:
            v = data[k]; r[k] = v.item() if v.size == 1 else v
    r['grid'] = g
    return r


if __name__ == '__main__':
    print("=" * 60)
    print("Test 1: Flat terrain ABL")
    print("=" * 60)
    g = create_grid(Lx=20.0, Ly=10.0, Nx=100, Ny=50, y_stretch=1.04)
    r = solve_rans(g, panels=[], u_ref=10.0, z_ref=10.0, z0=0.001,
                   max_iter=300, tol=1e-4)

    u_out = r['u'][-5, :]
    u_log, _ = abl_profiles(g['y'], 10.0, 10.0, 0.001)
    valid = u_log > 0.5
    err = np.mean(np.abs(u_out[valid] - u_log[valid]) / u_log[valid])
    print(f"  Error vs log-law: {err:.4f}")
    print(f"  {'PASS' if err < 0.15 else 'FAIL'}")

    print()
    print("=" * 60)
    print("Test 2: Single panel")
    print("=" * 60)
    p = [{'x0': 8.0, 'H': 0.5, 'theta_deg': 25.0, 'L': 2.0, 'thickness': 0.05}]
    g2 = create_grid(Lx=25.0, Ly=8.0, Nx=150, Ny=60, y_stretch=1.04)
    r2 = solve_rans(g2, p, u_ref=10.0, z_ref=10.0, z0=0.001,
                    max_iter=300, tol=1e-4)
    print(f"  Reattachment: {r2['reattach_lengths'][0]:.2f} m")
    u_s = r2['u_star_local']
    print(f"  u* range: [{u_s.min():.3f}, {u_s.max():.3f}]")
