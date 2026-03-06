#!/usr/bin/env python3
"""
Compare u* amplification factors between u_ref=10 and u_ref=14 m/s.
Tests Re-independence assumption for RANS amplification factors.
"""
import sys
import numpy as np
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_DIR / 'codes' / 'figures'))
from generate_validation_figure import parse_openfoam_field, parse_openfoam_vector_field

KAPPA = 0.41
Z0 = 0.001
ZREF = 10.0


def compute_ustar_from_wss(case_dir, time_dir):
    """Compute u* = sqrt(|wallShearStress|) along ground."""
    td = Path(case_dir) / str(time_dir)
    cx = parse_openfoam_field(td / 'Cx')
    cz = parse_openfoam_field(td / 'Cz')

    # Read wall shear stress
    wss_path = td / 'wallShearStress'
    if not wss_path.exists():
        print(f"No wallShearStress in {td}")
        return None, None, None

    wsx, _, wsz = parse_openfoam_vector_field(wss_path)
    wss_mag = np.sqrt(wsx**2 + wsz**2)

    # Ground cells: z close to 0
    ground_mask = cz < 0.5  # near ground
    x_g = cx[ground_mask]
    ustar_g = np.sqrt(wss_mag[ground_mask])

    # Sort by x
    order = np.argsort(x_g)
    return x_g[order], ustar_g[order], cz[ground_mask][order]


def get_latest_time(case_dir):
    """Find the latest time directory."""
    case_dir = Path(case_dir)
    time_dirs = sorted([d.name for d in case_dir.iterdir()
                       if d.is_dir() and d.name not in
                       ('0', 'constant', 'system', 'postProcessing', 'dynamicCode')
                       and not d.name.startswith('processor')
                       and d.name.replace('.', '').isdigit()],
                      key=lambda x: float(x))
    return time_dirs[-1] if time_dirs else None


def main():
    study_dir = PROJECT_DIR / 'codes' / 'openfoam' / 'parametric_study'
    case_10 = study_dir / 'case_23_H0.5_T25_S4Hp'
    case_14 = study_dir / 'sensitivity_uref14_H0.5_T25_S4Hp'

    ustar_10_design = KAPPA * 10.0 / np.log(ZREF / Z0)
    ustar_14_design = KAPPA * 14.0 / np.log(ZREF / Z0)

    print(f"Analytical u*_10 = {ustar_10_design:.4f} m/s")
    print(f"Analytical u*_14 = {ustar_14_design:.4f} m/s")
    print(f"Ratio = {ustar_14_design/ustar_10_design:.4f}")

    # Extract u* profiles
    t10 = get_latest_time(case_10)
    t14 = get_latest_time(case_14)
    print(f"\ncase_23 latest time: {t10}")
    print(f"sensitivity latest time: {t14}")

    if t10 is None or t14 is None:
        print("ERROR: Missing time directories")
        return

    x10, ustar10, z10 = compute_ustar_from_wss(case_10, t10)
    x14, ustar14, z14 = compute_ustar_from_wss(case_14, t14)

    if ustar10 is None or ustar14 is None:
        print("ERROR: Could not read wallShearStress")
        return

    # Compute amplification factors: u*/u*_upstream
    # Upstream reference: x < 15 m (before array)
    up10 = ustar10[x10 < 15].mean()
    up14 = ustar14[x14 < 15].mean()
    print(f"\nUpstream u*_10 (CFD) = {up10:.4f}")
    print(f"Upstream u*_14 (CFD) = {up14:.4f}")

    # Array region: x between 20 and 55 m
    arr10_mask = (x10 > 20) & (x10 < 55)
    arr14_mask = (x14 > 20) & (x14 < 55)

    amp10 = ustar10[arr10_mask] / up10
    amp14 = ustar14[arr14_mask] / up14

    # Interpolate to common x for direct comparison
    x_common = np.linspace(20, 55, 500)
    amp10_interp = np.interp(x_common, x10[arr10_mask], amp10)
    amp14_interp = np.interp(x_common, x14[arr14_mask], amp14)

    # Statistics
    diff = amp14_interp - amp10_interp
    rel_diff = diff / amp10_interp

    print(f"\n=== AMPLIFICATION FACTOR COMPARISON (array region x=20-55m) ===")
    print(f"Mean amp factor (u_ref=10): {amp10_interp.mean():.4f}")
    print(f"Mean amp factor (u_ref=14): {amp14_interp.mean():.4f}")
    print(f"Max amp factor (u_ref=10):  {amp10_interp.max():.4f}")
    print(f"Max amp factor (u_ref=14):  {amp14_interp.max():.4f}")
    print(f"Mean difference: {diff.mean():.4f}")
    print(f"Mean |relative difference|: {np.abs(rel_diff).mean()*100:.2f}%")
    print(f"Max |relative difference|:  {np.abs(rel_diff).max()*100:.2f}%")
    print(f"RMSE of amplification factors: {np.sqrt(np.mean(diff**2)):.4f}")

    # Shelter efficiency comparison
    # Q ~ u*^3, so shelter_eff = 1 - mean(u*^3)/u*_up^3
    q_ratio_10 = np.mean(ustar10[arr10_mask]**3) / up10**3
    q_ratio_14 = np.mean(ustar14[arr14_mask]**3) / up14**3
    shelter_10 = 1.0 - q_ratio_10
    shelter_14 = 1.0 - q_ratio_14

    print(f"\n=== FLUX RATIO AND SHELTER EFFICIENCY ===")
    print(f"Q_array/Q_upstream (u_ref=10): {q_ratio_10:.4f}")
    print(f"Q_array/Q_upstream (u_ref=14): {q_ratio_14:.4f}")
    print(f"Shelter efficiency (u_ref=10): {shelter_10:.4f}")
    print(f"Shelter efficiency (u_ref=14): {shelter_14:.4f}")
    print(f"Difference in shelter eff:     {abs(shelter_14 - shelter_10):.4f}")

    conclusion = "PASS" if np.abs(rel_diff).mean() < 0.05 else "MARGINAL" if np.abs(rel_diff).mean() < 0.10 else "FAIL"
    print(f"\n=== CONCLUSION: Re-independence {conclusion} ===")
    print(f"Mean |relative difference| in amplification factors: {np.abs(rel_diff).mean()*100:.1f}%")
    if conclusion == "PASS":
        print("Amplification factors are effectively Re-independent (<5% difference).")
        print("The assumption used in Section 7.2 (applying u_ref=10 factors to other wind speeds) is validated.")
    elif conclusion == "MARGINAL":
        print("Amplification factors show modest Re-dependence (5-10%).")
        print("The assumption is approximately valid but introduces ~5-10% additional uncertainty.")
    else:
        print("Amplification factors show significant Re-dependence (>10%).")
        print("The assumption may not be valid; consider wind-speed-specific simulations.")


if __name__ == '__main__':
    main()
