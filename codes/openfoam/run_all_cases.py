#!/usr/bin/env python3
"""
Generate and run all 36 parametric cases + mesh independence + validation.
Uses parallel execution on 8 cores per case (running sequentially).
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from setup_case import setup_case, projected_height, domain_length

# Parametric study parameters
H_VALUES = [0.1, 0.3, 0.5, 0.8]
THETA_VALUES = [15, 25, 35]
S_FACTORS = [2, 4, 6]

BASE_DIR = Path(__file__).parent / "parametric_study"
RESULTS_DIR = Path(__file__).parent.parent / "results"


def run_case(case_dir, n_procs=4):
    """Run a single OpenFOAM case: decompose, run parallel, reconstruct."""
    case_dir = Path(case_dir)
    start = time.time()

    # Decompose
    r = subprocess.run(['decomposePar'], cwd=case_dir,
                      capture_output=True, text=True)
    if r.returncode != 0:
        print(f"    decomposePar failed, running serial")
        r = subprocess.run(['simpleFoam'], cwd=case_dir,
                         capture_output=True, text=True, timeout=28800)
        with open(case_dir / 'log.simpleFoam', 'w') as f:
            f.write(r.stdout)
    else:
        r = subprocess.run(
            ['mpirun', '-np', str(n_procs), 'simpleFoam', '-parallel'],
            cwd=case_dir, capture_output=True, text=True, timeout=28800
        )
        with open(case_dir / 'log.simpleFoam', 'w') as f:
            f.write(r.stdout)

        # Reconstruct latest time
        subprocess.run(['reconstructPar', '-latestTime'],
                      cwd=case_dir, capture_output=True, text=True)

        # Write cell centres for post-processing
        subprocess.run(['postProcess', '-func', 'writeCellCentres', '-latestTime'],
                      cwd=case_dir, capture_output=True, text=True)

    elapsed = time.time() - start

    # Check convergence
    converged = False
    if (case_dir / 'log.simpleFoam').exists():
        log = (case_dir / 'log.simpleFoam').read_text()
        if 'SIMPLE solution converged' in log:
            converged = True

    return elapsed, converged


def setup_mesh_independence():
    """Set up 3 mesh levels for mesh independence study."""
    H, theta, S_factor = 0.5, 25, 4
    Hp = projected_height(theta)
    S = S_factor * Hp

    cases = []
    for level in ['coarse', 'medium', 'fine']:
        case_name = f"mesh_{level}"
        case_dir = BASE_DIR / "mesh_independence" / case_name
        print(f"\n  Setting up mesh independence: {level}")
        ok = setup_case(case_dir, H, theta, S, mesh_level=level)
        if ok:
            cases.append({'name': case_name, 'dir': str(case_dir), 'level': level})
    return cases


def setup_parametric_study():
    """Set up all 36 parametric cases."""
    cases = []
    case_id = 0

    for H in H_VALUES:
        for theta in THETA_VALUES:
            Hp = projected_height(theta)
            for s_factor in S_FACTORS:
                S = s_factor * Hp
                case_id += 1
                case_name = f"case_{case_id:02d}_H{H:.1f}_T{theta}_S{s_factor}Hp"
                case_dir = BASE_DIR / case_name

                print(f"\n  [{case_id}/36] {case_name}: H={H}m, theta={theta}deg, S={S:.2f}m")
                ok = setup_case(case_dir, H, theta, S, mesh_level='coarse')
                if ok:
                    cases.append({
                        'id': case_id,
                        'name': case_name,
                        'dir': str(case_dir),
                        'H': H, 'theta': theta, 'S': S,
                        'S_factor': s_factor,
                    })
    return cases


def main():
    BASE_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Parse command line
    if len(sys.argv) > 1:
        action = sys.argv[1]
    else:
        action = 'setup'

    if action == 'setup':
        # Set up all cases
        print("=" * 60)
        print("SETTING UP MESH INDEPENDENCE STUDY")
        print("=" * 60)
        mesh_cases = setup_mesh_independence()

        print("\n" + "=" * 60)
        print("SETTING UP 36 PARAMETRIC CASES")
        print("=" * 60)
        param_cases = setup_parametric_study()

        # Save case lists
        all_cases = {
            'mesh_independence': mesh_cases,
            'parametric': param_cases,
        }
        with open(BASE_DIR / 'all_cases.json', 'w') as f:
            json.dump(all_cases, f, indent=2)

        print(f"\n{'=' * 60}")
        print(f"SETUP COMPLETE: {len(mesh_cases)} mesh + {len(param_cases)} parametric cases")
        print(f"Case list saved to: {BASE_DIR / 'all_cases.json'}")
        print(f"\nTo run: python3 {__file__} run")

    elif action == 'run':
        # Load case list
        with open(BASE_DIR / 'all_cases.json') as f:
            all_cases = json.load(f)

        # Run mesh independence first
        print("=" * 60)
        print("RUNNING MESH INDEPENDENCE STUDY")
        print("=" * 60)
        for case in all_cases.get('mesh_independence', []):
            print(f"\n  Running {case['name']}...")
            elapsed, converged = run_case(case['dir'])
            status = "CONVERGED" if converged else "NOT CONVERGED"
            print(f"    {status} in {elapsed:.0f}s")

        # Run parametric cases
        print("\n" + "=" * 60)
        print("RUNNING PARAMETRIC STUDY (36 cases)")
        print("=" * 60)
        results = []
        for i, case in enumerate(all_cases.get('parametric', [])):
            print(f"\n  [{i+1}/36] Running {case['name']}...")
            elapsed, converged = run_case(case['dir'])
            status = "CONVERGED" if converged else "NOT CONVERGED"
            print(f"    {status} in {elapsed:.0f}s")
            results.append({**case, 'elapsed': elapsed, 'converged': converged})

        # Save run results
        with open(RESULTS_DIR / 'run_status.json', 'w') as f:
            json.dump(results, f, indent=2)

        n_conv = sum(1 for r in results if r['converged'])
        print(f"\n{'=' * 60}")
        print(f"COMPLETED: {n_conv}/{len(results)} cases converged")

    elif action == 'setup_one':
        # Set up and run a single test case
        H, theta, s_factor = 0.5, 25, 4
        Hp = projected_height(theta)
        S = s_factor * Hp
        case_dir = BASE_DIR / "test_single"
        print(f"Setting up test case: H={H}m, theta={theta}deg, S={S:.2f}m")
        ok = setup_case(case_dir, H, theta, S, mesh_level='coarse')
        if ok:
            print("Running...")
            elapsed, converged = run_case(case_dir)
            print(f"{'CONVERGED' if converged else 'NOT CONVERGED'} in {elapsed:.0f}s")


if __name__ == "__main__":
    main()
