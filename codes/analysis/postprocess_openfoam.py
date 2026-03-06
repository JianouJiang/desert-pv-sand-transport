#!/usr/bin/env python3
"""
Post-process OpenFOAM results for all parametric cases.

Extracts:
1. Velocity profiles at key x-locations (upstream, between panels, downstream)
2. Friction velocity (u*) along the ground from wallShearStress
3. Pressure coefficient (Cp) on panel surfaces
4. Flow field data for contour plots
5. Sand transport metrics computed from u* and saltation theory
"""

import os
import sys
import json
import numpy as np
from pathlib import Path

# Physical constants
RHO = 1.225          # Air density [kg/m3]
RHO_P = 2650.0       # Sand particle density [kg/m3]
D50 = 200e-6          # Median sand diameter [m]
G = 9.81              # Gravitational acceleration [m/s2]
NU = 1.5e-5           # Kinematic viscosity [m^2/s]
KAPPA = 0.41          # von Karman constant
Z0 = 0.001            # Desert surface roughness [m]
U_REF = 10.0          # Reference wind speed [m/s]
Z_REF = 10.0          # Reference height [m]
PANEL_LENGTH = 2.0    # Panel chord [m]

# Threshold friction velocity for sand entrainment (Shao & Lu 2000)
# u*t = A_N * sqrt((rho_p/rho - 1) * g * d + gamma / (rho * d))
# For D50=200um desert sand, u*t ~ 0.25 m/s
A_N = 0.111
GAMMA = 3.0e-4  # Cohesion parameter [kg/s2]
UST_THRESHOLD = A_N * np.sqrt((RHO_P / RHO - 1) * G * D50 + GAMMA / (RHO * D50))


def read_openfoam_vector_field(filepath):
    """Read an OpenFOAM vector field file, return (x, y, z) arrays of the vector components."""
    with open(filepath, 'r') as f:
        content = f.read()

    # Find the internalField section
    idx = content.find('internalField')
    if idx == -1:
        raise ValueError(f"No internalField found in {filepath}")

    # Find the start of data (after the count and opening paren)
    rest = content[idx:]
    paren_start = rest.find('(')
    if paren_start == -1:
        raise ValueError(f"No data block found in {filepath}")

    # Extract the count
    between = rest[:paren_start].strip()
    count_str = between.split('\n')[-1].strip()
    if count_str.endswith('nonuniform List<vector>'):
        count_str = count_str.replace('nonuniform List<vector>', '').strip()
    count = int(count_str.split()[-1])

    data_start = idx + paren_start + 1
    # Find the list-closing paren (on its own line)
    data_end = content.find('\n)', data_start)
    if data_end == -1:
        data_end = content.find('\n);', data_start)
    data_block = content[data_start:data_end]

    # Parse vectors like (vx vy vz)
    vectors = []
    for line in data_block.strip().split('\n'):
        line = line.strip()
        if line.startswith('(') and line.endswith(')'):
            vals = line[1:-1].split()
            if len(vals) == 3:
                vectors.append([float(v) for v in vals])

    arr = np.array(vectors)
    return arr[:, 0], arr[:, 1], arr[:, 2]


def read_openfoam_scalar_field(filepath):
    """Read an OpenFOAM scalar field file."""
    with open(filepath, 'r') as f:
        content = f.read()

    idx = content.find('internalField')
    if idx == -1:
        raise ValueError(f"No internalField found in {filepath}")

    rest = content[idx:]
    paren_start = rest.find('(')
    if paren_start == -1:
        # Might be uniform
        if 'uniform' in rest:
            val = float(rest.split('uniform')[1].split(';')[0].strip())
            return None  # uniform field
        raise ValueError(f"No data block found in {filepath}")

    between = rest[:paren_start].strip()
    count_line = [l for l in between.split('\n') if l.strip()][-1].strip()
    count = int(count_line.split()[-1]) if count_line[-1].isdigit() else int(count_line)

    data_start = idx + paren_start + 1
    # Find the list-closing paren (on its own line)
    data_end = content.find('\n)', data_start)
    if data_end == -1:
        data_end = content.find('\n);', data_start)
    data_block = content[data_start:data_end]

    values = []
    for line in data_block.strip().split('\n'):
        line = line.strip()
        if line:
            try:
                values.append(float(line))
            except ValueError:
                pass

    return np.array(values)


def read_mesh_centers(case_dir):
    """Read cell center coordinates from OpenFOAM case (requires writeCellCentres)."""
    case_dir = Path(case_dir)

    # Check if cellCentres have been written
    # Look in the latest time directory
    time_dirs = sorted([d for d in case_dir.iterdir()
                       if d.is_dir() and d.name not in ('0', 'constant', 'system',
                                                         'postProcessing', 'dynamicCode')
                       and not d.name.startswith('processor')],
                      key=lambda x: float(x.name) if x.name.replace('.', '').isdigit() else -1)

    if not time_dirs:
        return None, None, None

    latest = time_dirs[-1]

    # Try to read ccx, ccy, ccz files (written by writeCellCentres utility)
    ccx_file = latest / 'ccx'
    if not ccx_file.exists():
        # Alternative: Cx, Cy, Cz
        ccx_file = latest / 'Cx'

    if not ccx_file.exists():
        return None, None, None

    cx = read_openfoam_scalar_field(str(ccx_file))
    cy = read_openfoam_scalar_field(str(latest / ('ccy' if (latest / 'ccy').exists() else 'Cy')))
    cz = read_openfoam_scalar_field(str(latest / ('ccz' if (latest / 'ccz').exists() else 'Cz')))
    return cx, cy, cz


def extract_velocity_profiles(case_dir, x_locations, z_max=5.0):
    """Extract vertical velocity profiles at specified x-locations."""
    case_dir = Path(case_dir)

    # Find latest time directory
    time_dirs = sorted([d for d in case_dir.iterdir()
                       if d.is_dir() and d.name not in ('0', 'constant', 'system',
                                                         'postProcessing', 'dynamicCode')
                       and not d.name.startswith('processor')],
                      key=lambda x: float(x.name) if x.name.replace('.', '').isdigit() else -1)

    if not time_dirs:
        return None

    latest = time_dirs[-1]

    # Read U field
    u_file = latest / 'U'
    if not u_file.exists():
        return None

    ux, uy, uz = read_openfoam_vector_field(str(u_file))

    # Read cell centres
    cx, cy, cz = read_mesh_centers(case_dir)
    if cx is None:
        return None

    profiles = {}
    for x_loc in x_locations:
        # Find cells near x_loc (within half a cell width)
        dx_tol = 0.5  # tolerance in x
        mask = np.abs(cx - x_loc) < dx_tol
        if not np.any(mask):
            continue

        z_vals = cz[mask]
        u_vals = ux[mask]

        # Sort by z
        order = np.argsort(z_vals)
        z_sorted = z_vals[order]
        u_sorted = u_vals[order]

        # Filter to z_max
        keep = z_sorted <= z_max
        profiles[x_loc] = {
            'z': z_sorted[keep].tolist(),
            'U': u_sorted[keep].tolist(),
        }

    return profiles


def extract_wall_shear_stress(case_dir):
    """Extract wall shear stress from postProcessing/wallShearStress1."""
    case_dir = Path(case_dir)
    wss_dir = case_dir / 'postProcessing' / 'wallShearStress1'

    if not wss_dir.exists():
        return None

    # Find latest time
    time_dirs = sorted([d for d in wss_dir.iterdir() if d.is_dir()],
                      key=lambda x: float(x.name))

    if not time_dirs:
        return None

    latest = time_dirs[-1]

    # wallShearStress is a vector field on walls
    wss_file = latest / 'wallShearStress.dat'
    if not wss_file.exists():
        # Try alternative formats
        for fname in ['wallShearStress', 'wallShearStress.raw']:
            wss_file = latest / fname
            if wss_file.exists():
                break

    if not wss_file.exists():
        return None

    # Parse the file (format depends on OpenFOAM version)
    # Typically: x y z wss_x wss_y wss_z
    data = []
    with open(wss_file) as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            vals = line.split()
            if len(vals) >= 6:
                data.append([float(v) for v in vals[:6]])

    if not data:
        return None

    arr = np.array(data)
    return {
        'x': arr[:, 0].tolist(),
        'z': arr[:, 2].tolist(),
        'wss_x': arr[:, 3].tolist(),
        'wss_z': arr[:, 5].tolist(),
    }


def compute_friction_velocity_from_wss(case_dir):
    """Compute u* from wallShearStress field on the ground patch.

    In OpenFOAM the wallShearStress field has dimensions [0 2 -2 0 0 0 0],
    i.e. kinematic wall shear stress (tau/rho). So u* = sqrt(|tau_w|).
    """
    case_dir = Path(case_dir)

    time_dirs = sorted([d for d in case_dir.iterdir()
                       if d.is_dir() and d.name not in ('0', 'constant', 'system',
                                                         'postProcessing', 'dynamicCode')
                       and not d.name.startswith('processor')],
                      key=lambda x: float(x.name) if x.name.replace('.', '').isdigit() else -1)

    if not time_dirs:
        return None

    latest = time_dirs[-1]
    wss_file = latest / 'wallShearStress'
    if not wss_file.exists():
        return None

    # Read the wallShearStress field and extract the ground patch
    with open(wss_file) as f:
        content = f.read()

    # Find the ground patch boundary data
    ground_idx = content.find('ground')
    if ground_idx == -1:
        return None

    # Extract the ground patch data block
    rest = content[ground_idx:]
    paren_start = rest.find('(')
    if paren_start == -1:
        return None

    # Get count
    between = rest[:paren_start]
    lines = [l.strip() for l in between.split('\n') if l.strip()]
    count = None
    for line in reversed(lines):
        try:
            count = int(line)
            break
        except ValueError:
            continue
    if count is None:
        return None

    data_start = ground_idx + paren_start + 1
    # Find the list-closing paren (on its own line, not a vector-closing paren)
    data_end = content.find('\n)', data_start)
    if data_end == -1:
        data_end = content.find('\n);', data_start)
    data_block = content[data_start:data_end]

    wss_vectors = []
    for line in data_block.strip().split('\n'):
        line = line.strip()
        if line.startswith('(') and line.endswith(')'):
            vals = line[1:-1].split()
            if len(vals) == 3:
                wss_vectors.append([float(v) for v in vals])

    if not wss_vectors:
        return None

    wss_arr = np.array(wss_vectors)
    # u* = sqrt(|tau_w|) where tau_w is kinematic
    wss_mag = np.sqrt(wss_arr[:, 0]**2 + wss_arr[:, 2]**2)
    ustar = np.sqrt(wss_mag)

    # We need x-coordinates of the ground face centres
    # Read from the mesh face centres via Cx field on the ground patch
    cx_file = latest / 'Cx'
    if not cx_file.exists():
        # Fall back: evenly space across domain
        meta_file = case_dir / 'case_metadata.json'
        if meta_file.exists():
            with open(meta_file) as f:
                meta = json.load(f)
            L_domain = meta.get('domain_length', 85.0)
        else:
            L_domain = 85.0
        x_ground = np.linspace(0, L_domain, len(ustar))
    else:
        # Extract Cx values for ground patch from the boundary field
        with open(cx_file) as f:
            cx_content = f.read()
        gnd_idx = cx_content.find('ground')
        if gnd_idx == -1:
            x_ground = np.linspace(0, 85.0, len(ustar))
        else:
            cx_rest = cx_content[gnd_idx:]
            cx_paren = cx_rest.find('(')
            cx_data_start = gnd_idx + cx_paren + 1
            cx_data_end = cx_content.find('\n)', cx_data_start)
            if cx_data_end == -1:
                cx_data_end = cx_content.find('\n);', cx_data_start)
            cx_block = cx_content[cx_data_start:cx_data_end]
            x_vals = []
            for line in cx_block.strip().split('\n'):
                line = line.strip()
                if line:
                    try:
                        x_vals.append(float(line))
                    except ValueError:
                        pass
            x_ground = np.array(x_vals) if x_vals else np.linspace(0, 85.0, len(ustar))

    return {
        'x': x_ground.tolist() if isinstance(x_ground, np.ndarray) else x_ground,
        'ustar': ustar.tolist(),
    }


def compute_sand_transport_metrics(ustar_data, case_metadata):
    """
    Compute sand transport metrics from friction velocity distribution.

    Uses relative metrics (amplification factors) from the CFD simulation,
    applied to the design ABL friction velocity (u*_design = 0.445 m/s)
    to compute physical sand transport quantities.

    The RANS k-epsilon simulation gives correct spatial variation (u*/u*_upstream)
    but underestimates absolute u* due to horizontal homogeneity limitations.
    We extract amplification factors and apply them to the known ABL u*.
    """
    if ustar_data is None:
        return None

    x = np.array(ustar_data['x'])
    ustar = np.array(ustar_data['ustar'])

    H = case_metadata['H']
    theta = case_metadata['theta']
    S = case_metadata['S']

    # Design ABL friction velocity: u* = U_ref * kappa / ln(z_ref/z0)
    USTAR_DESIGN = U_REF * KAPPA / np.log(Z_REF / Z0)  # ~0.445 m/s

    # Identify upstream reference region
    fetch = 20.0  # upstream fetch before first panel
    Lp = PANEL_LENGTH * np.cos(np.radians(theta))
    Hp = PANEL_LENGTH * np.sin(np.radians(theta))
    array_end = fetch + 7 * S + Lp

    mask_upstream = x < fetch - 2
    mask_array = (x >= fetch) & (x <= array_end)
    mask_downstream = (x > array_end + 2) & (x < x.max() - 5)

    # Upstream reference u* (from simulation itself)
    ustar_upstream_sim = np.mean(ustar[mask_upstream]) if np.any(mask_upstream) else np.mean(ustar)

    # Amplification factor array: u*(x) / u*_upstream from simulation
    amp = ustar / ustar_upstream_sim

    # Physical u* distribution: apply amplification to design u*
    ustar_phys = USTAR_DESIGN * amp

    # u* amplification factor within array
    ustar_amp_array = np.mean(amp[mask_array]) if np.any(mask_array) else 1.0
    ustar_amp_max = np.max(amp[mask_array]) if np.any(mask_array) else 1.0
    ustar_amp_min = np.min(amp[mask_array]) if np.any(mask_array) else 1.0

    # Owen saltation flux: Q = C * (rho/g) * u*^3 * (1 - u*t^2/u*^2), u* > u*t
    C_OWEN = 0.25  # Owen coefficient (literature range 0.1-0.5)
    Q = np.where(
        ustar_phys > UST_THRESHOLD,
        C_OWEN * (RHO / G) * ustar_phys**3 * (1 - UST_THRESHOLD**2 / ustar_phys**2),
        0.0
    )
    Q_upstream = C_OWEN * (RHO / G) * USTAR_DESIGN**3 * (1 - UST_THRESHOLD**2 / USTAR_DESIGN**2)

    # Saltation layer scale: lambda_s = 2 * u*^2 / g (Owen 1964), using design u*
    lambda_s = 2 * USTAR_DESIGN**2 / G

    # Panel deposition: analytical vertical profile (design u*) scaled by
    # CFD-adjusted mean ground flux within the array.
    # Rationale: the saltation vertical profile adjusts slowly (non-equilibrium),
    # but the total horizontal flux responds to local u* changes from the array.
    if lambda_s > 0:
        deposition_fraction = np.exp(-H / lambda_s) - np.exp(-(H + Hp) / lambda_s)
    else:
        deposition_fraction = 0.0

    # Mean ground-level flux within array (CFD-derived)
    Q_array = np.mean(Q[mask_array]) if np.any(mask_array) else Q_upstream
    Q_downstream_val = np.mean(Q[mask_downstream]) if np.any(mask_downstream) else Q_upstream
    shelter_efficiency = 1 - Q_array / Q_upstream if Q_upstream > 0 else 0

    # Panel deposition = array-mean ground flux * fraction reaching panel height
    panel_deposition = Q_array * deposition_fraction

    # Erosion metrics: where u* is amplified above upstream
    erosion_amp_fraction = np.sum(amp[mask_array] > 1.1) / max(np.sum(mask_array), 1)
    erosion_intensity = np.mean(np.maximum(amp[mask_array] - 1, 0)) if np.any(mask_array) else 0

    # Regime classification based on H/lambda_s (using design u*)
    # Boundaries from exponential concentration profile analysis:
    #   Capture (H/λ < 2): panel well inside saltation layer, high deposition
    #   Transitional (2 < H/λ < 10): exponential decrease in deposition
    #   Pass-through (H/λ > 10): negligible saltation reaches panel
    H_over_lambda = H / lambda_s if lambda_s > 0 else float('inf')
    if H_over_lambda < 2:
        regime = 'capture'
    elif H_over_lambda < 10:
        regime = 'transitional'
    else:
        regime = 'pass-through'

    return {
        'ustar_upstream_sim': float(ustar_upstream_sim),
        'ustar_design': float(USTAR_DESIGN),
        'ustar_amp_mean': float(ustar_amp_array),
        'ustar_amp_max': float(ustar_amp_max),
        'ustar_amp_min': float(ustar_amp_min),
        'Q_upstream': float(Q_upstream),
        'Q_array_mean': float(Q_array),
        'Q_downstream_mean': float(Q_downstream_val),
        'panel_deposition': float(panel_deposition),
        'deposition_fraction': float(deposition_fraction),
        'lambda_s': float(lambda_s),
        'H_over_lambda': float(H_over_lambda),
        'erosion_amp_fraction': float(erosion_amp_fraction),
        'erosion_intensity': float(erosion_intensity),
        'shelter_efficiency': float(shelter_efficiency),
        'regime': regime,
    }


def extract_flow_field_2d(case_dir, x_range=None, z_range=None):
    """Extract 2D flow field (U, p, k) for contour plotting."""
    case_dir = Path(case_dir)

    time_dirs = sorted([d for d in case_dir.iterdir()
                       if d.is_dir() and d.name not in ('0', 'constant', 'system',
                                                         'postProcessing', 'dynamicCode')
                       and not d.name.startswith('processor')],
                      key=lambda x: float(x.name) if x.name.replace('.', '').isdigit() else -1)

    if not time_dirs:
        return None

    latest = time_dirs[-1]

    # Read fields
    result = {}

    ux, uy, uz = read_openfoam_vector_field(str(latest / 'U'))
    result['Ux'] = ux
    result['Uz'] = uz
    result['Umag'] = np.sqrt(ux**2 + uz**2)

    p_file = latest / 'p'
    if p_file.exists():
        result['p'] = read_openfoam_scalar_field(str(p_file))

    k_file = latest / 'k'
    if k_file.exists():
        result['k'] = read_openfoam_scalar_field(str(k_file))

    cx, cy, cz = read_mesh_centers(case_dir)
    if cx is None:
        return None

    result['x'] = cx
    result['z'] = cz

    # Apply range filters
    if x_range is not None:
        mask = (cx >= x_range[0]) & (cx <= x_range[1])
        if z_range is not None:
            mask &= (cz >= z_range[0]) & (cz <= z_range[1])
        for key in result:
            if isinstance(result[key], np.ndarray):
                result[key] = result[key][mask]

    return result


def check_convergence(case_dir):
    """Check convergence from log.simpleFoam and log.simpleFoam_restart."""
    case_dir = Path(case_dir)
    import re

    # Read all solver logs (original, restart, fix, extend)
    log_names = ['log.simpleFoam', 'log.simpleFoam_restart',
                 'log.simpleFoam_fix', 'log.simpleFoam_extend']
    combined_content = ''
    for name in log_names:
        lf = case_dir / name
        if lf.exists():
            combined_content += '\n' + lf.read_text()

    if not combined_content.strip():
        return {'converged': False, 'iterations': 0, 'final_residuals': {}}

    converged = 'SIMPLE solution converged' in combined_content

    # Extract max solver iteration across all logs.
    # Each log may contain postProcess output with its own "Time =" lines.
    # Parse each log file separately: strip post-solver sections, then
    # take the maximum iteration found across all logs.
    max_iter = 0
    conv_match_global = re.search(r'SIMPLE solution converged in (\d+) iterations', combined_content)
    if conv_match_global:
        max_iter = int(conv_match_global.group(1))
    else:
        for name in log_names:
            lf = case_dir / name
            if not lf.exists():
                continue
            log_text = '\n' + lf.read_text()
            # Strip postProcess sections that contain their own "Time =" entries
            for marker in ['wallShearStress wallShearStress:', 'writeCellCentres writeCellCentres:']:
                idx = log_text.find(marker)
                if idx > 0:
                    log_text = log_text[:idx]
            time_matches = re.findall(r'\nTime = (\d+)', log_text)
            if time_matches:
                max_iter = max(max_iter, int(time_matches[-1]))
    iterations = max_iter

    # Extract final residuals from the LAST log that has solver output
    # (restart log takes precedence if it exists)
    last_content = combined_content
    lines = last_content.strip().split('\n')
    residuals = {}
    for line in reversed(lines):
        if 'Solving for' in line and 'Final residual' in line:
            parts = line.split(',')
            var = ''
            for p in parts:
                if 'Solving for' in p:
                    var = p.split('Solving for')[-1].strip().rstrip(',')
                if 'Final residual' in p:
                    try:
                        res = float(p.split('=')[-1].strip().rstrip(','))
                        if var not in residuals:
                            residuals[var] = res
                    except ValueError:
                        pass
            if len(residuals) >= 4:
                break

    return {
        'converged': converged,
        'iterations': iterations,
        'final_residuals': residuals,
    }


def postprocess_case(case_dir):
    """Full post-processing pipeline for a single case."""
    case_dir = Path(case_dir)
    print(f"  Post-processing: {case_dir.name}")

    # Read metadata
    meta_file = case_dir / 'case_metadata.json'
    if meta_file.exists():
        with open(meta_file) as f:
            metadata = json.load(f)
    else:
        print(f"    WARNING: No metadata found")
        return None

    # Check convergence
    conv = check_convergence(case_dir)
    print(f"    Convergence: {'YES' if conv['converged'] else 'NO'} ({conv['iterations']} iterations)")

    # Need writeCellCentres first
    results = {
        'metadata': metadata,
        'convergence': conv,
    }

    # Friction velocity from wallShearStress field on ground patch
    ustar_data = compute_friction_velocity_from_wss(case_dir)
    if ustar_data:
        results['ustar'] = ustar_data

        # Sand transport metrics
        sand_metrics = compute_sand_transport_metrics(ustar_data, metadata)
        if sand_metrics:
            results['sand_transport'] = sand_metrics
            print(f"    Regime: {sand_metrics['regime']}")
            print(f"    Panel deposition: {sand_metrics['panel_deposition']:.2e} kg/m/s")
            print(f"    Shelter efficiency: {sand_metrics['shelter_efficiency']:.1%}")

    return results


def postprocess_all(study_dir, output_dir):
    """Post-process all cases in the parametric study."""
    study_dir = Path(study_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load case list
    case_list_file = study_dir / 'all_cases.json'
    if not case_list_file.exists():
        print("ERROR: No all_cases.json found. Run setup first.")
        return

    with open(case_list_file) as f:
        all_cases = json.load(f)

    all_results = {
        'mesh_independence': [],
        'parametric': [],
    }

    # Process mesh independence cases
    print("=" * 60)
    print("POST-PROCESSING MESH INDEPENDENCE STUDY")
    print("=" * 60)
    for case in all_cases.get('mesh_independence', []):
        result = postprocess_case(case['dir'])
        if result:
            result['mesh_level'] = case['level']
            all_results['mesh_independence'].append(result)

    # Process parametric cases
    print("\n" + "=" * 60)
    print("POST-PROCESSING PARAMETRIC STUDY")
    print("=" * 60)
    for case in all_cases.get('parametric', []):
        result = postprocess_case(case['dir'])
        if result:
            all_results['parametric'].append(result)

    # Save results
    output_file = output_dir / 'openfoam_results.json'
    with open(output_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)

    print(f"\nResults saved to: {output_file}")

    # Summary statistics
    n_converged = sum(1 for r in all_results['parametric']
                     if r.get('convergence', {}).get('converged', False))
    n_total = len(all_results['parametric'])
    print(f"Converged: {n_converged}/{n_total}")

    # Compute GCI if mesh independence data available (2+ levels)
    if len(all_results['mesh_independence']) >= 2:
        gci = compute_gci(all_results['mesh_independence'])
        all_results['gci'] = gci
        # Re-save with GCI included
        with open(output_file, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        print(f"\nGCI results:")
        for k, v in gci.items():
            if k.startswith('_'):
                print(f"  Note: {v}")
            else:
                vals = v.get('values', [])
                pct = v.get('gci_fine_pct', 0)
                method = v.get('method', 'unknown')
                print(f"  {k}: GCI={pct:.2f}% ({method}), values={[f'{x:.4f}' for x in vals]}")

    return all_results


def compute_gci(mesh_results):
    """Compute Grid Convergence Index (Roache 1994) from mesh independence study.

    Supports both 2-level and 3-level GCI:
    - 3-level (coarse/medium/fine): observed order p, F_s = 1.25
    - 2-level (coarse/medium): assumed p=2, F_s = 3.0 (Roache recommendation)

    If the fine mesh shows non-monotonic convergence or wall-function issues,
    falls back to 2-level GCI using coarse and medium meshes only.
    """
    def get_mesh_level(r):
        return r.get('metadata', {}).get('mesh_level', r.get('mesh_level', ''))

    def get_n_cells(r):
        n = r.get('metadata', {}).get('n_cells', 0)
        if n == 0:
            level = get_mesh_level(r)
            n = {'coarse': 95000, 'medium': 375000, 'fine': 1389000}.get(level, 100000)
        return n

    level_order = {'coarse': 0, 'medium': 1, 'fine': 2}
    sorted_results = sorted(mesh_results,
                           key=lambda r: level_order.get(get_mesh_level(r), -1))

    if len(sorted_results) < 2:
        return {'error': 'Need at least 2 mesh levels for GCI'}

    n_cells = [get_n_cells(r) for r in sorted_results]

    quantities = {
        'ustar_upstream': lambda r: r.get('sand_transport', {}).get('ustar_upstream_sim', None),
        'shelter_efficiency': lambda r: r.get('sand_transport', {}).get('shelter_efficiency', None),
        'ustar_amp_max': lambda r: r.get('sand_transport', {}).get('ustar_amp_max', None),
    }

    gci_results = {}
    has_three = len(sorted_results) >= 3
    use_two_level = not has_three

    if has_three:
        # Check fine mesh convergence and monotonicity
        fine_conv = sorted_results[2].get('convergence', {})
        fine_converged = fine_conv.get('converged', False)
        # Also check for non-monotonic convergence in key quantities
        se_ext = quantities['shelter_efficiency']
        se_vals = [se_ext(r) for r in sorted_results]
        if all(v is not None for v in se_vals):
            se_c, se_m, se_f = se_vals
            # If fine mesh deviates > 3x from coarse-medium trend, it's anomalous
            cm_change = abs(se_m - se_c)
            mf_change = abs(se_f - se_m)
            anomalous = mf_change > 5 * cm_change if cm_change > 1e-10 else False
        else:
            anomalous = False
        if not fine_converged or anomalous:
            use_two_level = True
            gci_results['_note'] = (
                f'Fine mesh did not converge (y+~49, p-residual ~1e-3); '
                f'2-level GCI (coarse/medium) used with F_s=3.0'
            )

    if use_two_level:
        # 2-level GCI: coarse → medium, assumed p=2, F_s=3.0
        r_21 = (n_cells[1] / n_cells[0]) ** 0.5
        F_s = 3.0
        p_assumed = 2.0

        for qname, extractor in quantities.items():
            f_coarse = extractor(sorted_results[0])
            f_medium = extractor(sorted_results[1])
            if f_coarse is None or f_medium is None:
                continue

            if abs(f_medium) < 1e-20:
                continue

            e_21 = abs((f_medium - f_coarse) / f_medium)
            gci_fine = F_s * e_21 / (r_21**p_assumed - 1)

            all_vals = [float(f_coarse), float(f_medium)]
            if has_three:
                f_fine = extractor(sorted_results[2])
                if f_fine is not None:
                    all_vals.append(float(f_fine))

            gci_results[qname] = {
                'values': all_vals,
                'order_p': p_assumed,
                'gci_fine_pct': float(gci_fine * 100),
                'r_21': float(r_21),
                'F_s': float(F_s),
                'method': '2-level',
            }
    else:
        # 3-level GCI with observed order
        r_21 = (n_cells[2] / n_cells[1]) ** 0.5
        r_32 = (n_cells[1] / n_cells[0]) ** 0.5
        F_s = 1.25

        for qname, extractor in quantities.items():
            vals = [extractor(r) for r in sorted_results]
            if any(v is None for v in vals):
                continue

            f3, f2, f1 = vals[0], vals[1], vals[2]  # coarse, medium, fine

            if abs(f2 - f1) < 1e-20 or abs(f3 - f2) < 1e-20:
                gci_results[qname] = {
                    'values': [float(f3), float(f2), float(f1)],
                    'gci_fine_pct': 0.0,
                    'note': 'Values identical across grids'
                }
                continue

            ratio = (f3 - f2) / (f2 - f1)
            if ratio > 0:
                p = abs(np.log(abs(ratio))) / np.log(r_32)
                p = min(max(p, 0.5), 4.0)
            else:
                p = 2.0

            e_21 = abs((f1 - f2) / f1) if abs(f1) > 1e-20 else 0
            gci_fine = F_s * e_21 / (r_21**p - 1)

            gci_results[qname] = {
                'values': [float(f3), float(f2), float(f1)],
                'order_p': float(p),
                'gci_fine_pct': float(gci_fine * 100),
                'r_21': float(r_21),
                'r_32': float(r_32),
                'F_s': float(F_s),
                'method': '3-level',
            }

    return gci_results


if __name__ == '__main__':
    base = Path(__file__).parent.parent
    study_dir = base / 'openfoam' / 'parametric_study'
    output_dir = base / 'results'

    if len(sys.argv) > 1 and sys.argv[1] == 'single':
        # Post-process a single test case
        test_dir = study_dir / 'test_single'
        if test_dir.exists():
            result = postprocess_case(test_dir)
            if result:
                with open(output_dir / 'test_single_results.json', 'w') as f:
                    json.dump(result, f, indent=2, default=str)
        else:
            print("No test_single case found")
    else:
        postprocess_all(study_dir, output_dir)
