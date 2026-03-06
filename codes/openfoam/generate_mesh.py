#!/usr/bin/env python3
"""
Generate 3D (one-cell-thick) OpenFOAM mesh with tilted PV panels using gmsh OCC.

Panels modeled as thin solid bodies (5mm thick) subtracted from the domain.
This creates proper wall boundaries around each panel.
"""

import os
import json
import subprocess
import numpy as np
import gmsh


def create_panel_mesh(H, theta_deg, S, n_rows=8, panel_length=2.0,
                      mesh_level='medium', output_dir='.'):
    """Create a 3D mesh with tilted PV panels for OpenFOAM 2D simulation."""
    theta = np.radians(theta_deg)
    L_p = panel_length
    dx = L_p * np.cos(theta)
    dz = L_p * np.sin(theta)
    Hp = L_p * np.sin(theta)
    panel_thick = 0.005  # 5mm panel thickness

    fetch = 20.0
    wake = max(40.0, 15 * (H + Hp))
    array_end = fetch + (n_rows - 1) * S + dx
    L_domain = array_end + wake
    H_domain = 30.0
    Y_thick = 1.0

    res_map = {
        'coarse':  {'panel': 0.04,  'near': 0.10, 'far': 3.0},
        'medium':  {'panel': 0.02,  'near': 0.05, 'far': 2.0},
        'fine':    {'panel': 0.01,  'near': 0.025, 'far': 1.5},
    }
    res = res_map[mesh_level]

    gmsh.initialize()
    gmsh.option.setNumber('General.Terminal', 0)
    gmsh.model.add('pv_array')

    # Use OCC kernel for boolean operations
    # Create 3D domain box
    domain = gmsh.model.occ.addBox(0, 0, 0, L_domain, Y_thick, H_domain)

    # Create panel solids (thin boxes, tilted)
    panel_tags = []
    for i in range(n_rows):
        x_le = fetch + i * S
        z_le = H

        # Panel center
        xc = x_le + dx / 2
        zc = z_le + dz / 2

        # Create thin rectangle at origin, rotate, translate
        # Panel dimensions: length L_p, height panel_thick, width Y_thick+0.1
        panel = gmsh.model.occ.addBox(
            -L_p / 2, -0.05, -panel_thick / 2,
            L_p, Y_thick + 0.1, panel_thick
        )

        # Rotate around y-axis by theta
        gmsh.model.occ.rotate([(3, panel)], 0, 0, 0, 0, 1, 0, theta)

        # Translate to correct position
        gmsh.model.occ.translate([(3, panel)], xc, 0, zc)

        panel_tags.append(panel)

    gmsh.model.occ.synchronize()

    # Cut panels from domain
    result = gmsh.model.occ.cut(
        [(3, domain)],
        [(3, t) for t in panel_tags],
        removeObject=True,
        removeTool=True
    )
    gmsh.model.occ.synchronize()

    # Get the resulting volume(s)
    volumes = gmsh.model.getEntities(3)
    if not volumes:
        print("  ERROR: No volumes after boolean cut!")
        gmsh.finalize()
        return None, {}

    # --- Identify boundary surfaces ---
    all_surfs = gmsh.model.getEntities(2)
    tol = 0.05

    ground_s, inlet_s, outlet_s, top_s, fb_s, panel_s = [], [], [], [], [], []

    for dim, tag in all_surfs:
        bb = gmsh.model.getBoundingBox(dim, tag)
        xn, yn, zn, xx, yx, zx = bb
        dy = yx - yn
        dxs = xx - xn
        dzs = zx - zn

        # Front/back faces (y-normal, span full domain)
        if dy < tol:
            fb_s.append(tag)
            continue

        # Ground (z=0, spans domain width in x, full y)
        if abs(zn) < tol and abs(zx) < tol and dxs > 1.0:
            ground_s.append(tag)
            continue

        # Top (z=H_domain)
        if abs(zn - H_domain) < tol and abs(zx - H_domain) < tol and dxs > 1.0:
            top_s.append(tag)
            continue

        # Inlet (x=0)
        if abs(xn) < tol and abs(xx) < tol and dzs > 1.0:
            inlet_s.append(tag)
            continue

        # Outlet (x=L_domain)
        if abs(xn - L_domain) < tol and abs(xx - L_domain) < tol and dzs > 1.0:
            outlet_s.append(tag)
            continue

        # Everything else is a panel surface
        # Verify it's near a panel location
        for ip in range(n_rows):
            x_le = fetch + ip * S
            x_te = x_le + dx
            z_le = H
            z_te = H + dz
            if (xn > x_le - 1 and xx < x_te + 1 and
                zn > z_le - 0.5 and zx < z_te + 0.5):
                panel_s.append(tag)
                break

    # Physical groups
    vol_tags = [t for _, t in volumes]
    gmsh.model.addPhysicalGroup(3, vol_tags, name='internalMesh')

    if ground_s:
        gmsh.model.addPhysicalGroup(2, ground_s, name='ground')
    if inlet_s:
        gmsh.model.addPhysicalGroup(2, inlet_s, name='inlet')
    if outlet_s:
        gmsh.model.addPhysicalGroup(2, outlet_s, name='outlet')
    if top_s:
        gmsh.model.addPhysicalGroup(2, top_s, name='top')
    if fb_s:
        gmsh.model.addPhysicalGroup(2, fb_s, name='frontAndBack')
    if panel_s:
        gmsh.model.addPhysicalGroup(2, panel_s, name='panels')

    # Unassigned surfaces go to defaultFaces
    assigned = set(ground_s + inlet_s + outlet_s + top_s + fb_s + panel_s)
    unassigned = [t for _, t in all_surfs if t not in assigned]
    if unassigned:
        gmsh.model.addPhysicalGroup(2, unassigned, name='defaultFaces')

    # --- Mesh refinement ---
    # Distance from panel surfaces
    if panel_s:
        f_dist = gmsh.model.mesh.field.add("Distance")
        gmsh.model.mesh.field.setNumbers(f_dist, "SurfacesList", panel_s)
        gmsh.model.mesh.field.setNumber(f_dist, "Sampling", 100)

        f_th = gmsh.model.mesh.field.add("Threshold")
        gmsh.model.mesh.field.setNumber(f_th, "InField", f_dist)
        gmsh.model.mesh.field.setNumber(f_th, "SizeMin", res['panel'])
        gmsh.model.mesh.field.setNumber(f_th, "SizeMax", res['far'])
        gmsh.model.mesh.field.setNumber(f_th, "DistMin", 0.1)
        gmsh.model.mesh.field.setNumber(f_th, "DistMax", 5.0)

        fields = [f_th]
    else:
        fields = []

    # Box refinement in panel region
    f_box = gmsh.model.mesh.field.add("Box")
    gmsh.model.mesh.field.setNumber(f_box, "VIn", res['near'])
    gmsh.model.mesh.field.setNumber(f_box, "VOut", res['far'])
    gmsh.model.mesh.field.setNumber(f_box, "XMin", fetch - 3)
    gmsh.model.mesh.field.setNumber(f_box, "XMax", array_end + 10)
    gmsh.model.mesh.field.setNumber(f_box, "YMin", -0.1)
    gmsh.model.mesh.field.setNumber(f_box, "YMax", Y_thick + 0.1)
    gmsh.model.mesh.field.setNumber(f_box, "ZMin", 0)
    gmsh.model.mesh.field.setNumber(f_box, "ZMax", min(H + Hp + 3, 8))
    gmsh.model.mesh.field.setNumber(f_box, "Thickness", 2.0)
    fields.append(f_box)

    f_min = gmsh.model.mesh.field.add("Min")
    gmsh.model.mesh.field.setNumbers(f_min, "FieldsList", fields)
    gmsh.model.mesh.field.setAsBackgroundMesh(f_min)

    gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
    gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)

    # Extrude settings for 2D
    gmsh.option.setNumber("Mesh.Algorithm", 6)
    gmsh.option.setNumber("Mesh.Algorithm3D", 1)
    gmsh.option.setNumber("Mesh.Smoothing", 5)

    # Generate mesh
    gmsh.model.mesh.generate(3)

    # Stats
    n_nodes = len(gmsh.model.mesh.getNodes()[0])
    elems3d = gmsh.model.mesh.getElements(3)
    n_cells = sum(len(e) for e in elems3d[1]) if elems3d[1] else 0

    # Save
    msh_path = os.path.join(output_dir, 'mesh.msh')
    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    gmsh.option.setNumber("Mesh.Binary", 0)
    gmsh.write(msh_path)

    gmsh.finalize()

    info = {
        'n_nodes': n_nodes, 'n_cells': n_cells,
        'L_domain': L_domain, 'H_domain': H_domain,
        'panels': len(panel_s), 'ground': len(ground_s),
        'fb': len(fb_s), 'unassigned': len(unassigned),
    }
    print(f"  {n_cells} cells | panels={len(panel_s)}, ground={len(ground_s)}, "
          f"fb={len(fb_s)}, unassigned={len(unassigned)}")
    return msh_path, info


def setup_openfoam_case(case_dir, H, theta_deg, S, n_rows=8,
                        mesh_level='medium', u_ref=10.0, z0=0.001):
    """Create a complete OpenFOAM case directory."""
    os.makedirs(case_dir, exist_ok=True)
    for d in ['system', '0/include', 'constant']:
        os.makedirs(os.path.join(case_dir, d), exist_ok=True)

    # Generate mesh
    print(f"  Generating mesh...")
    msh_path, mesh_info = create_panel_mesh(
        H, theta_deg, S, n_rows=n_rows,
        mesh_level=mesh_level, output_dir=case_dir
    )
    if msh_path is None:
        return False

    # Write all case files
    _write_system_files(case_dir)
    _write_constant_files(case_dir)
    _write_BCs(case_dir, u_ref, z0)

    # Convert mesh
    print("  Converting to OpenFOAM...")
    result = subprocess.run(['gmshToFoam', 'mesh.msh'],
                          cwd=case_dir, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  gmshToFoam FAILED:\n{result.stderr[-300:]}")
        return False

    # Fix boundary types
    _fix_boundary(case_dir)

    # Write run script
    _write_run_script(case_dir, H, theta_deg, S)

    return True


def _write_system_files(case_dir):
    """Write controlDict, fvSchemes, fvSolution, decomposeParDict."""
    sd = os.path.join(case_dir, 'system')

    with open(os.path.join(sd, 'controlDict'), 'w') as f:
        f.write("""FoamFile
{
    version 2.0; format ascii; class dictionary; object controlDict;
}

application     simpleFoam;
libs            ("libatmosphericModels.so");
startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         3000;
deltaT          1;
writeControl    timeStep;
writeInterval   1000;
purgeWrite      2;
writeFormat     ascii;
writePrecision  8;
writeCompression off;
timeFormat      general;
timePrecision   6;
runTimeModifiable true;

functions
{
    wallShearStress1
    {
        type            wallShearStress;
        libs            ("libfieldFunctionObjects.so");
        writeControl    writeTime;
        patches         (ground panels);
    }
}
""")

    with open(os.path.join(sd, 'fvSchemes'), 'w') as f:
        f.write("""FoamFile
{
    version 2.0; format ascii; class dictionary; object fvSchemes;
}
ddtSchemes { default steadyState; }
gradSchemes { default Gauss linear; grad(U) cellLimited Gauss linear 1; }
divSchemes
{
    default none;
    div(phi,U) bounded Gauss linearUpwindV grad(U);
    div(phi,k) bounded Gauss upwind;
    div(phi,epsilon) bounded Gauss upwind;
    div((nuEff*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes { default Gauss linear corrected; }
interpolationSchemes { default linear; }
snGradSchemes { default corrected; }
wallDist { method meshWave; }
""")

    with open(os.path.join(sd, 'fvSolution'), 'w') as f:
        f.write("""FoamFile
{
    version 2.0; format ascii; class dictionary; object fvSolution;
}
solvers
{
    p { solver GAMG; smoother GaussSeidel; tolerance 1e-7; relTol 0.01; }
    "(U|k|epsilon)" { solver PBiCGStab; preconditioner DILU; tolerance 1e-8; relTol 0.01; }
}
SIMPLE
{
    nNonOrthogonalCorrectors 1;
    consistent yes;
    residualControl { p 1e-5; U 1e-5; "(k|epsilon)" 1e-5; }
}
relaxationFactors
{
    fields { p 0.3; }
    equations { U 0.7; k 0.7; epsilon 0.7; }
}
""")

    with open(os.path.join(sd, 'decomposeParDict'), 'w') as f:
        f.write("""FoamFile
{
    version 2.0; format ascii; class dictionary; object decomposeParDict;
}
numberOfSubdomains 8;
method scotch;
""")


def _write_constant_files(case_dir):
    cd = os.path.join(case_dir, 'constant')
    with open(os.path.join(cd, 'physicalProperties'), 'w') as f:
        f.write("""FoamFile
{
    version 2.0; format ascii; class dictionary; object physicalProperties;
}
viscosityModel constant;
nu [0 2 -1 0 0 0 0] 1.5e-05;
""")
    with open(os.path.join(cd, 'momentumTransport'), 'w') as f:
        f.write("""FoamFile
{
    version 2.0; format ascii; class dictionary; object momentumTransport;
}
simulationType RAS;
RAS { model kEpsilon; turbulence on; printCoeffs on; }
""")


def _write_BCs(case_dir, u_ref=10.0, z0=0.001):
    """Write boundary conditions for ABL flow with k-epsilon."""
    z_dir = os.path.join(case_dir, '0')
    inc = os.path.join(z_dir, 'include')
    os.makedirs(inc, exist_ok=True)

    with open(os.path.join(inc, 'ABLConditions'), 'w') as f:
        f.write(f"Uref {u_ref};\nZref 10.0;\nzDir (0 0 1);\nflowDir (1 0 0);\n"
                f"z0 uniform {z0};\nzGround uniform 0.0;\n")

    fields = {
        'U': {
            'dim': '[0 1 -1 0 0 0 0]',
            'internal': f'uniform ({u_ref} 0 0)',
            'inlet': 'type atmBoundaryLayerInletVelocity; #include "include/ABLConditions"',
            'outlet': f'type inletOutlet; inletValue uniform (0 0 0); value uniform ({u_ref} 0 0)',
            'ground': 'type noSlip',
            'top': 'type atmBoundaryLayerInletVelocity; #include "include/ABLConditions"',
            'panels': 'type noSlip',
        },
        'p': {
            'dim': '[0 2 -2 0 0 0 0]',
            'internal': 'uniform 0',
            'inlet': 'type zeroGradient',
            'outlet': 'type fixedValue; value uniform 0',
            'ground': 'type zeroGradient',
            'top': 'type zeroGradient',
            'panels': 'type zeroGradient',
        },
        'k': {
            'dim': '[0 2 -2 0 0 0 0]',
            'internal': 'uniform 0.66',
            'inlet': 'type atmBoundaryLayerInletK; #include "include/ABLConditions"',
            'outlet': 'type inletOutlet; inletValue uniform 0.66; value uniform 0.66',
            'ground': 'type kqRWallFunction; value uniform 0.66',
            'top': 'type atmBoundaryLayerInletK; #include "include/ABLConditions"',
            'panels': 'type kqRWallFunction; value uniform 0.66',
        },
        'epsilon': {
            'dim': '[0 2 -3 0 0 0 0]',
            'internal': 'uniform 0.0215',
            'inlet': 'type atmBoundaryLayerInletEpsilon; #include "include/ABLConditions"',
            'outlet': 'type inletOutlet; inletValue uniform 0.0215; value uniform 0.0215',
            'ground': 'type epsilonWallFunction; value uniform 0.0215',
            'top': 'type atmBoundaryLayerInletEpsilon; #include "include/ABLConditions"',
            'panels': 'type epsilonWallFunction; value uniform 0.0215',
        },
        'nut': {
            'dim': '[0 2 -1 0 0 0 0]',
            'internal': 'uniform 0.18',
            'inlet': 'type calculated; value uniform 0.18',
            'outlet': 'type calculated; value uniform 0.18',
            'ground': 'type nutUWallFunction; value uniform 0.18',
            'top': 'type calculated; value uniform 0.18',
            'panels': 'type nutUWallFunction; value uniform 0.18',
        },
    }

    for field_name, fd in fields.items():
        cl = 'volVectorField' if field_name == 'U' else 'volScalarField'
        with open(os.path.join(z_dir, field_name), 'w') as f:
            f.write(f"FoamFile\n{{ version 2.0; format ascii; class {cl}; object {field_name}; }}\n\n")
            f.write(f"dimensions {fd['dim']};\ninternalField {fd['internal']};\n\nboundaryField\n{{\n")
            for patch in ['inlet', 'outlet', 'ground', 'top', 'panels']:
                f.write(f"    {patch} {{ {fd[patch]}; }}\n")
            f.write("    frontAndBack { type empty; }\n")
            f.write("    defaultFaces { type empty; }\n")
            f.write("}\n")


def _fix_boundary(case_dir):
    """Fix boundary types in polyMesh/boundary after gmshToFoam."""
    bp = os.path.join(case_dir, 'constant', 'polyMesh', 'boundary')
    if not os.path.exists(bp):
        return

    with open(bp, 'r') as f:
        lines = f.readlines()

    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if stripped in ('frontAndBack', 'defaultFaces'):
            new_lines.append(line)
            i += 1
            while i < len(lines):
                l = lines[i]
                if 'type' in l and 'patch' in l:
                    new_lines.append(l.replace('patch', 'empty'))
                else:
                    new_lines.append(l)
                i += 1
                if '}' in l:
                    break
        elif stripped in ('ground', 'panels'):
            new_lines.append(line)
            i += 1
            while i < len(lines):
                l = lines[i]
                if 'type' in l and 'patch' in l:
                    new_lines.append(l.replace('patch', 'wall'))
                else:
                    new_lines.append(l)
                i += 1
                if '}' in l:
                    break
        else:
            new_lines.append(line)
            i += 1

    with open(bp, 'w') as f:
        f.writelines(new_lines)


def _write_run_script(case_dir, H, theta_deg, S):
    script = f"""#!/bin/bash
cd "{case_dir}"
echo "=== H={H}m theta={theta_deg}deg S={S:.2f}m ==="
echo "Start: $(date)"
checkMesh > log.checkMesh 2>&1
decomposePar > log.decomposePar 2>&1
if [ $? -eq 0 ]; then
    mpirun -np 8 simpleFoam -parallel > log.simpleFoam 2>&1
    reconstructPar -latestTime > log.reconstructPar 2>&1
else
    simpleFoam > log.simpleFoam 2>&1
fi
echo "Done: $(date)"
"""
    sp = os.path.join(case_dir, 'Allrun')
    with open(sp, 'w') as f:
        f.write(script)
    os.chmod(sp, 0o755)


if __name__ == "__main__":
    test_dir = "/tmp/test_pv_occ"

    H = 0.5
    theta = 25
    Hp = 2.0 * np.sin(np.radians(theta))
    S = 4 * Hp

    print(f"Case: H={H}m, theta={theta}deg, S={S:.2f}m")
    ok = setup_openfoam_case(test_dir, H, theta, S, n_rows=8, mesh_level='coarse')

    if ok:
        print("\ncheckMesh:")
        r = subprocess.run(['checkMesh'], cwd=test_dir,
                         capture_output=True, text=True)
        for line in r.stdout.split('\n'):
            if any(k in line for k in ['Mesh OK', 'cells:', 'faces:', 'points:',
                                        'Failed', 'FAILED', 'Number of']):
                print(f"  {line.strip()}")

        print("\nBoundary patches:")
        r2 = subprocess.run(['grep', '-A2', 'type', 'constant/polyMesh/boundary'],
                          cwd=test_dir, capture_output=True, text=True)
        print(r2.stdout[:500])
