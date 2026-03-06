#!/usr/bin/env python3
"""
Lagrangian Particle Tracking for Aeolian Sand Transport
========================================================
Tracks sand grains through a 2D velocity field (from RANS solver).

Injection: Particles are released from the ground surface across the domain
wherever the local friction velocity exceeds the threshold (active saltation).
This models the self-sustaining saltation layer.

Forces:
  - Drag (Schiller-Naumann)
  - Gravity (buoyancy-corrected)
  - Stochastic turbulent dispersion

Deposition:
  - Ground: y <= 0 (with probabilistic rebound for saltation)
  - Panel: inside panel mask
  - Escaped: exits domain

Author: Worker Agent (Paper Factory)
"""

import numpy as np
from scipy.interpolate import RegularGridInterpolator


RHO_AIR = 1.225
RHO_SAND = 2650.0
MU_AIR = 1.8e-5
NU_AIR = MU_AIR / RHO_AIR
GRAVITY = 9.81
KAPPA = 0.41


def threshold_friction_velocity(d_p, rho_p=RHO_SAND, rho_a=RHO_AIR):
    """Threshold friction velocity for sand entrainment (Shao & Lu 2000)."""
    AN = 0.0123
    gamma = 3e-4  # N/m, interparticle cohesion
    u_star_t = np.sqrt(AN * (rho_p * GRAVITY * d_p / rho_a + gamma / (rho_a * d_p)))
    return u_star_t


def settling_velocity(d_p, rho_p=RHO_SAND, rho_a=RHO_AIR, mu_a=MU_AIR):
    """Terminal settling velocity for a sphere (iterative Schiller-Naumann)."""
    tau_p = rho_p * d_p**2 / (18 * mu_a)
    v_s = tau_p * GRAVITY * (1 - rho_a / rho_p)  # Stokes estimate
    for _ in range(10):
        Re_p = rho_a * v_s * d_p / mu_a
        f = 1.0 + 0.15 * max(Re_p, 1e-6)**0.687
        v_s = tau_p * GRAVITY * (1 - rho_a / rho_p) / f
    return v_s


def create_interpolators(result):
    """Create velocity/mask interpolators from RANS result."""
    g = result['grid']
    x, y = g['x'], g['y']
    kw = dict(bounds_error=False, fill_value=None, method='linear')
    return {
        'u': RegularGridInterpolator((x, y), result['u'], **kw),
        'v': RegularGridInterpolator((x, y), result['v'], **kw),
        'nu_t': RegularGridInterpolator((x, y), result['nu_t'], **kw),
        'mask': RegularGridInterpolator((x, y), result['mask'],
                                         bounds_error=False, fill_value=0.0),
    }


def inject_particles(N_particles, grid, result, d_p, rng):
    """Inject particles representing the incoming sand flux.

    Uses a dual injection approach:
    1. Inlet flux: particles at the inlet with Rouse concentration profile
       (represents developed upwind sand flux entering the domain)
    2. Ground saltation: particles ejected from the ground in the
       approach region before the first panel

    This ensures a realistic vertical distribution of sand flux.
    """
    x_arr = grid['x']
    y_arr = grid['y']
    u_in = result['u_in']
    u_star = result['u_star']

    # Rouse exponent for concentration profile
    v_s = settling_velocity(d_p)
    P_rouse = v_s / (KAPPA * max(u_star, 0.01))

    # --- Group 1: Inlet injection (70% of particles) ---
    n_inlet = int(0.7 * N_particles)

    # Sample heights from Rouse profile: c(y) ~ y^(-P)
    # For sampling: use inverse CDF of truncated power law
    y_min = max(grid['dy'][0] * 0.5, 0.005)
    y_max = min(grid['Ly'] * 0.5, 3.0)

    if P_rouse < 0.5:
        # Nearly uniform (fine dust)
        y0_inlet = rng.uniform(y_min, y_max, n_inlet)
    elif P_rouse < 10:
        # Power-law distribution
        u_samples = rng.uniform(0, 1, n_inlet)
        alpha = 1.0 - P_rouse
        if abs(alpha) < 0.01:
            y0_inlet = y_min * np.exp(u_samples * np.log(y_max / y_min))
        else:
            y0_inlet = (y_min**alpha + u_samples * (y_max**alpha - y_min**alpha))**(1/alpha)
        y0_inlet = np.clip(y0_inlet, y_min, y_max)
    else:
        # Very heavy particles: concentrated near ground
        y0_inlet = rng.exponential(scale=0.8 * u_star**2 / GRAVITY, size=n_inlet)
        y0_inlet = np.clip(y0_inlet, y_min, 0.5)

    x0_inlet = np.full(n_inlet, x_arr[1])
    up_inlet = np.interp(y0_inlet, y_arr, u_in) * 0.8  # slightly slower than wind
    vp_inlet = np.zeros(n_inlet)  # steady-state flux

    # --- Group 2: Ground saltation source (30% of particles) ---
    n_ground = N_particles - n_inlet

    # Source from ground across the domain
    x0_ground = rng.uniform(x_arr[0], x_arr[-1] * 0.8, n_ground)
    y0_ground = np.full(n_ground, y_min)

    # Saltation ejection
    ejection_speed = rng.uniform(1.5, 3.0, n_ground) * u_star
    ejection_angle = rng.uniform(40, 70, n_ground) * np.pi / 180
    vp_ground = ejection_speed * np.sin(ejection_angle)
    up_ground = ejection_speed * np.cos(ejection_angle) + u_star * 2.0

    # Combine
    x0 = np.concatenate([x0_inlet, x0_ground])
    y0 = np.concatenate([y0_inlet, y0_ground])
    up0 = np.concatenate([up_inlet, up_ground])
    vp0 = np.concatenate([vp_inlet, vp_ground])

    return x0, y0, up0, vp0


def track_particles(result, N_particles=5000, d_p=200e-6,
                    dt=0.002, max_steps=30000,
                    rebound_prob=0.6, rebound_coeff=0.4,
                    rng_seed=42, verbose=True):
    """Track sand particles through the RANS velocity field.

    Features saltation rebound: when a particle hits the ground, it has
    a probability of rebounding (sustaining saltation) rather than depositing.
    """
    rng = np.random.default_rng(rng_seed)
    grid = result['grid']
    x_arr, y_arr = grid['x'], grid['y']
    Lx, Ly = grid['Lx'], grid['Ly']
    panels = result['panels']

    interps = create_interpolators(result)

    tau_p = RHO_SAND * d_p**2 / (18 * MU_AIR)
    v_s = settling_velocity(d_p)
    u_star_t = threshold_friction_velocity(d_p)

    if verbose:
        print(f"Tracking {N_particles} particles, d={d_p*1e6:.0f} um")
        print(f"  tau_p={tau_p:.4f}s, v_settle={v_s:.3f} m/s, u*_t={u_star_t:.3f} m/s")

    # Inject particles
    xp, yp, up, vp = inject_particles(
        N_particles, grid, result, d_p, rng)

    active = np.ones(N_particles, dtype=bool)
    fate = np.full(N_particles, -1, dtype=int)  # 0=ground, 1=panel, 2=escaped
    dep_x = np.full(N_particles, np.nan)
    dep_y = np.full(N_particles, np.nan)
    dep_panel_idx = np.full(N_particles, -1, dtype=int)
    n_rebounds = np.zeros(N_particles, dtype=int)
    max_rebounds = 20  # limit saltation chain

    # Trajectory storage
    n_store = min(200, N_particles)
    store_idx = rng.choice(N_particles, n_store, replace=False)
    store_every = max(1, max_steps // 500)
    traj_x, traj_y = [], []

    for step in range(max_steps):
        if not np.any(active):
            break

        idx = np.where(active)[0]
        n_act = len(idx)

        # Clip positions to domain for interpolation
        xp_clip = np.clip(xp[idx], x_arr[0], x_arr[-1])
        yp_clip = np.clip(yp[idx], y_arr[0], y_arr[-1])
        pts = np.column_stack([xp_clip, yp_clip])

        # Fluid velocity at particle positions
        uf = interps['u'](pts)
        vf = interps['v'](pts)
        nut = interps['nu_t'](pts)

        # Handle NaN from extrapolation
        uf = np.nan_to_num(uf, nan=0.0)
        vf = np.nan_to_num(vf, nan=0.0)
        nut = np.nan_to_num(nut, nan=0.0)

        # Relative velocity
        du = uf - up[idx]
        dv = vf - vp[idx]
        dv_mag = np.sqrt(du**2 + dv**2) + 1e-30

        # Particle Reynolds number
        Re_p = RHO_AIR * dv_mag * d_p / MU_AIR
        f_drag = 1.0 + 0.15 * np.clip(Re_p, 0, 1000)**0.687

        # Drag acceleration
        ax = f_drag / tau_p * du
        ay = f_drag / tau_p * dv

        # Gravity
        ay -= GRAVITY * (1.0 - RHO_AIR / RHO_SAND)

        # Turbulent dispersion
        sigma_v = np.sqrt(np.maximum(nut * 100, 0))  # approx turbulent velocity
        sigma_v = np.minimum(sigma_v, 2.0)  # cap
        ax += sigma_v * rng.standard_normal(n_act) * np.sqrt(2.0 / max(dt, 1e-6)) * 0.01
        ay += sigma_v * rng.standard_normal(n_act) * np.sqrt(2.0 / max(dt, 1e-6)) * 0.01

        # Euler integration
        up[idx] += ax * dt
        vp[idx] += ay * dt
        xp[idx] += up[idx] * dt
        yp[idx] += vp[idx] * dt

        # --- Panel deposition ---
        act_idx = np.where(active)[0]
        if len(act_idx) > 0:
            xpc = np.clip(xp[act_idx], x_arr[0], x_arr[-1])
            ypc = np.clip(yp[act_idx], y_arr[0], y_arr[-1])
            mask_val = interps['mask'](np.column_stack([xpc, ypc]))
            mask_val = np.nan_to_num(mask_val, nan=0.0)
            hit = mask_val > 0.5
            hit_global = act_idx[hit]
            if len(hit_global) > 0:
                fate[hit_global] = 1
                dep_x[hit_global] = xp[hit_global]
                dep_y[hit_global] = yp[hit_global]
                for pi, p in enumerate(panels):
                    theta = np.radians(p['theta_deg'])
                    ct, st = np.cos(theta), np.sin(theta)
                    for gi in hit_global:
                        sx = (xp[gi] - p['x0']) * ct + (yp[gi] - p['H']) * st
                        if 0 <= sx <= p['L']:
                            dep_panel_idx[gi] = pi
                active[hit_global] = False

        # --- Ground interaction: rebound or deposit ---
        ground_hit = active & (yp <= 0)
        g_idx = np.where(ground_hit)[0]
        if len(g_idx) > 0:
            # Rebound or deposit
            can_rebound = n_rebounds[g_idx] < max_rebounds
            do_rebound = can_rebound & (rng.random(len(g_idx)) < rebound_prob)
            rebound_idx = g_idx[do_rebound]
            deposit_idx = g_idx[~do_rebound]

            # Rebound particles
            if len(rebound_idx) > 0:
                yp[rebound_idx] = y_arr[0] * 0.5
                impact_speed = np.sqrt(up[rebound_idx]**2 + vp[rebound_idx]**2)
                rebound_speed = impact_speed * rebound_coeff
                rebound_angle = rng.uniform(40, 70, len(rebound_idx)) * np.pi / 180
                vp[rebound_idx] = rebound_speed * np.sin(rebound_angle)
                up[rebound_idx] = rebound_speed * np.cos(rebound_angle)
                n_rebounds[rebound_idx] += 1

            # Deposit particles
            if len(deposit_idx) > 0:
                fate[deposit_idx] = 0
                dep_x[deposit_idx] = xp[deposit_idx]
                dep_y[deposit_idx] = 0.0
                active[deposit_idx] = False

        # --- Escaped ---
        esc_right = active & (xp > Lx)
        fate[np.where(esc_right)[0]] = 2
        active[np.where(esc_right)[0]] = False

        esc_left = active & (xp < 0)
        fate[np.where(esc_left)[0]] = 2
        active[np.where(esc_left)[0]] = False

        esc_top = active & (yp > Ly)
        fate[np.where(esc_top)[0]] = 3
        active[np.where(esc_top)[0]] = False

        # Store trajectories
        if step % store_every == 0:
            traj_x.append(xp[store_idx].copy())
            traj_y.append(yp[store_idx].copy())

        if verbose and step % 5000 == 0 and step > 0:
            print(f"  Step {step:5d}: active={np.sum(active)}, "
                  f"ground={np.sum(fate==0)}, panel={np.sum(fate==1)}, "
                  f"escaped={np.sum(fate==2)}")

    # Results
    n_ground = int(np.sum(fate == 0))
    n_panel = int(np.sum(fate == 1))
    n_escaped = int(np.sum(fate == 2))
    n_top = int(np.sum(fate == 3))

    panel_dep_count = np.zeros(len(panels), dtype=int)
    for pi in range(len(panels)):
        panel_dep_count[pi] = np.sum(dep_panel_idx == pi)

    ground_dep_x = dep_x[fate == 0]

    if verbose:
        print(f"\n  ground={n_ground}, panel={n_panel}, "
              f"escaped={n_escaped}, top={n_top}, remain={np.sum(fate==-1)}")
        print(f"  Panel capture: {n_panel/N_particles:.4f}")
        if len(panels) > 0:
            print(f"  Per-panel: {panel_dep_count}")

    return {
        'fate': fate, 'dep_x': dep_x, 'dep_y': dep_y,
        'dep_panel_idx': dep_panel_idx,
        'panel_dep_count': panel_dep_count,
        'ground_dep_x': ground_dep_x,
        'n_ground': n_ground, 'n_panel': n_panel,
        'n_escaped': n_escaped, 'n_top': n_top,
        'N_particles': N_particles, 'd_p': d_p,
        'traj_x': np.array(traj_x) if traj_x else np.array([]),
        'traj_y': np.array(traj_y) if traj_y else np.array([]),
        'store_idx': store_idx,
    }


def compute_metrics(tracking, panels, grid):
    """Compute five key deposition metrics."""
    fate = tracking['fate']
    dep_x = tracking['dep_x']
    N = tracking['N_particles']
    n_pan = len(panels)

    # Panel deposition flux
    panel_flux = tracking['panel_dep_count'] / max(N, 1)

    # Ground deposition histogram
    x_bins = np.linspace(0, grid['Lx'], 200)
    gnd_x = dep_x[fate == 0]
    gnd_hist, _ = np.histogram(gnd_x, bins=x_bins)
    gnd_hist = gnd_hist / max(N, 1)

    # Inter-row accumulation
    inter_row = np.zeros(max(n_pan - 1, 1))
    for i in range(n_pan - 1):
        theta_i = np.radians(panels[i]['theta_deg'])
        x_end_i = panels[i]['x0'] + panels[i]['L'] * np.cos(theta_i)
        x_start_next = panels[i + 1]['x0']
        inter_row[i] = np.sum((gnd_x >= x_end_i) & (gnd_x < x_start_next)) / max(N, 1)

    return {
        'panel_dep_flux': panel_flux,
        'total_capture': float(np.sum(panel_flux)),
        'gnd_hist': gnd_hist,
        'gnd_bins': x_bins,
        'inter_row_dep': inter_row,
        'capture_frac': tracking['n_panel'] / max(N, 1),
        'escape_frac': tracking['n_escaped'] / max(N, 1),
        'ground_frac': tracking['n_ground'] / max(N, 1),
    }


if __name__ == '__main__':
    from rans_solver import create_grid, solve_rans, define_panel_array

    for H_test in [0.1, 0.5]:
        print("=" * 60)
        print(f"Test: 3 panels, H={H_test}m, theta=25deg, d=200um")
        print("=" * 60)

        panels = define_panel_array(N_rows=3, H=H_test, theta_deg=25.0,
                                    S=5.0, L=2.0, x_start=10.0)
        grid = create_grid(Lx=35.0, Ly=8.0, Nx=200, Ny=60, y_stretch=1.04)

        flow = solve_rans(grid, panels, u_ref=10.0, z_ref=10.0, z0=0.001,
                          max_iter=300, tol=1e-4, verbose=False)

        tr = track_particles(flow, N_particles=5000, d_p=200e-6,
                             dt=0.002, max_steps=20000, verbose=False)

        m = compute_metrics(tr, panels, grid)
        print(f"  Capture: {m['capture_frac']:.4f}")
        print(f"  Escape:  {m['escape_frac']:.4f}")
        print(f"  Ground:  {m['ground_frac']:.4f}")
        print(f"  Per-panel: {m['panel_dep_flux']}")
        print()
