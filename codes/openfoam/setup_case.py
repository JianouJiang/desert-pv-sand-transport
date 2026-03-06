#!/usr/bin/env python3
"""
Set up OpenFOAM 2D case with tilted PV panels using blockMesh + topoSet + createBaffles.

This is the correct approach for thin panel baffles in OpenFOAM:
1. blockMesh: structured 2D mesh (one cell in y, empty front/back)
2. topoSet: identify cell faces nearest to each panel line
3. createBaffles: convert those internal faces to wall boundaries

The panels are approximated by the mesh faces that best align with the
tilted panel geometry. With sufficient mesh resolution (panel region ~0.02m),
the staircase approximation is adequate for RANS.
"""

import os
import sys
import json
import shutil
import subprocess
import math
import numpy as np
from pathlib import Path

# Physical constants
PANEL_LENGTH = 2.0       # Panel chord [m]
N_ROWS = 8               # Number of panel rows
Z0 = 0.001               # Desert roughness [m]
U_REF = 10.0             # Reference wind speed [m/s]
Z_REF = 10.0             # Reference height [m]
NU = 1.5e-5              # Kinematic viscosity [m^2/s]
DOMAIN_HEIGHT = 30.0     # Domain height [m]

BASE_DIR = Path(__file__).parent


def panel_endpoints(H, theta_deg, row_idx, fetch=20.0, S=None):
    """Get (x_le, z_le, x_te, z_te) for panel row row_idx."""
    theta = math.radians(theta_deg)
    dx = PANEL_LENGTH * math.cos(theta)
    dz = PANEL_LENGTH * math.sin(theta)
    x_le = fetch + row_idx * S
    return x_le, H, x_le + dx, H + dz


def projected_height(theta_deg):
    return PANEL_LENGTH * math.sin(math.radians(theta_deg))


def domain_length(theta_deg, S, n_rows=N_ROWS, fetch=20.0):
    """Total domain length."""
    dx = PANEL_LENGTH * math.cos(math.radians(theta_deg))
    Hp = projected_height(theta_deg)
    array_end = fetch + (n_rows - 1) * S + dx
    wake = max(40.0, 15 * Hp)
    return array_end + wake


def write_blockMeshDict(case_dir, H, theta_deg, S, mesh_level='medium'):
    """Write blockMeshDict with multi-block graded mesh."""
    Hp = projected_height(theta_deg)
    dx = PANEL_LENGTH * math.cos(math.radians(theta_deg))
    L = domain_length(theta_deg, S)

    # Mesh resolution settings
    res = {
        'coarse':  {'dx_panel': 0.05,  'dx_far': 0.5,  'dz_ground': 0.02, 'dz_panel': 0.03, 'dz_far': 1.0},
        'medium':  {'dx_panel': 0.025, 'dx_far': 0.3,  'dz_ground': 0.01, 'dz_panel': 0.015, 'dz_far': 0.5},
        'fine':    {'dx_panel': 0.012, 'dx_far': 0.2,  'dz_ground': 0.005, 'dz_panel': 0.008, 'dz_far': 0.3},
    }[mesh_level]

    # X-direction: three regions
    # 1. Inlet fetch (0 to fetch-2): coarser
    # 2. Panel region (fetch-2 to array_end+10): fine
    # 3. Wake (array_end+10 to L): coarser
    fetch = 20.0
    array_end = fetch + (N_ROWS - 1) * S + dx
    x_regions = [
        (0, fetch - 2, res['dx_far']),
        (fetch - 2, array_end + 10, res['dx_panel']),
        (array_end + 10, L, res['dx_far']),
    ]

    # Z-direction: four regions
    # 1. Ground to 0.5*H: fine near ground
    # 2. 0.5*H to H+Hp+1: very fine (panel region)
    # 3. H+Hp+1 to 5: moderate
    # 4. 5 to 30: coarse
    z_bot = max(H * 0.5, 0.05)
    z_panel_top = H + Hp + 1.0
    z_mid = min(5.0, DOMAIN_HEIGHT / 2)

    z_regions = [
        (0, z_bot, res['dz_ground']),
        (z_bot, z_panel_top, res['dz_panel']),
        (z_panel_top, z_mid, res['dz_far'] * 0.5),
        (z_mid, DOMAIN_HEIGHT, res['dz_far']),
    ]

    # Calculate cell counts and grading for each region
    def cells_and_grading(start, end, target_size):
        length = end - start
        n = max(2, int(round(length / target_size)))
        return n

    nx_regions = [(cells_and_grading(a, b, d), b - a) for a, b, d in x_regions]
    nz_regions = [(cells_and_grading(a, b, d), b - a) for a, b, d in z_regions]

    total_nx = sum(n for n, _ in nx_regions)
    total_nz = sum(n for n, _ in nz_regions)

    # For simplicity, use a single block with simpleGrading
    # Multi-block would be better but more complex
    # Use a single block with enough cells
    nx = total_nx
    nz = total_nz

    content = f"""FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      blockMeshDict;
}}

convertToMeters 1;

vertices
(
    (0     0   0)            // 0
    ({L:.4f} 0   0)          // 1
    ({L:.4f} 1   0)          // 2
    (0     1   0)            // 3
    (0     0   {DOMAIN_HEIGHT})  // 4
    ({L:.4f} 0   {DOMAIN_HEIGHT})  // 5
    ({L:.4f} 1   {DOMAIN_HEIGHT})  // 6
    (0     1   {DOMAIN_HEIGHT})  // 7
);

blocks
(
    hex (0 1 2 3 4 5 6 7) ({nx} 1 {nz})
    simpleGrading
    (
        1
        1
        (
            ({z_bot / DOMAIN_HEIGHT:.6f} {nz_regions[0][0]} 1)
            ({(z_panel_top - z_bot) / DOMAIN_HEIGHT:.6f} {nz_regions[1][0]} 1)
            ({(z_mid - z_panel_top) / DOMAIN_HEIGHT:.6f} {nz_regions[2][0]} 3)
            ({(DOMAIN_HEIGHT - z_mid) / DOMAIN_HEIGHT:.6f} {nz_regions[3][0]} 10)
        )
    )
);

boundary
(
    inlet
    {{
        type patch;
        faces ((0 3 7 4));
    }}
    outlet
    {{
        type patch;
        faces ((1 5 6 2));
    }}
    ground
    {{
        type wall;
        faces ((0 1 2 3));
    }}
    top
    {{
        type patch;
        faces ((4 7 6 5));
    }}
    frontAndBack
    {{
        type empty;
        faces ((0 4 5 1) (3 2 6 7));
    }}
);
"""
    sys_dir = case_dir / "system"
    sys_dir.mkdir(parents=True, exist_ok=True)
    (sys_dir / "blockMeshDict").write_text(content)
    return nx, nz


def write_panel_stl(case_dir, H, theta_deg, S, fetch=20.0):
    """Write an STL file of all panel surfaces for topoSet."""
    theta = math.radians(theta_deg)
    dx = PANEL_LENGTH * math.cos(theta)
    dz = PANEL_LENGTH * math.sin(theta)

    geom_dir = case_dir / "constant" / "geometry"
    geom_dir.mkdir(parents=True, exist_ok=True)

    stl_path = geom_dir / "panels.stl"
    with open(stl_path, 'w') as f:
        f.write("solid panels\n")
        for i in range(N_ROWS):
            x_le = fetch + i * S
            z_le = H
            x_te = x_le + dx
            z_te = z_le + dz

            # Panel as a quad, extruded in y from -0.1 to 1.1
            # Two triangles per face
            y0, y1 = -0.1, 1.1

            # Vertices
            v1 = (x_le, y0, z_le)
            v2 = (x_te, y0, z_te)
            v3 = (x_te, y1, z_te)
            v4 = (x_le, y1, z_le)

            # Normal (outward from panel top surface)
            nx = -math.sin(theta)
            nz = math.cos(theta)

            for tri in [(v1, v2, v3), (v1, v3, v4)]:
                f.write(f"  facet normal {nx:.6f} 0 {nz:.6f}\n")
                f.write("    outer loop\n")
                for v in tri:
                    f.write(f"      vertex {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")
                f.write("    endloop\n")
                f.write("  endfacet\n")
        f.write("endsolid panels\n")

    return stl_path


def write_topoSetDict(case_dir, H, theta_deg, S, fetch=20.0):
    """Write topoSetDict using searchableSurfaceToFaceZone with STL."""

    # First create the STL file
    write_panel_stl(case_dir, H, theta_deg, S, fetch)

    content = """FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      topoSetDict;
}

actions
(
    {
        name    panelFaces;
        type    faceZoneSet;
        action  new;
        source  searchableSurfaceToFaceZone;
        surface triSurfaceMesh;
        file    "panels.stl";
    }
);
"""
    (case_dir / "system" / "topoSetDict").write_text(content)


def write_createBafflesDict(case_dir):
    """Write createBafflesDict to convert panel faces to wall baffles."""
    content = """FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      createBafflesDict;
}

internalFacesOnly true;

baffles
{
    panelBaffles
    {
        type        faceZone;
        zoneName    panelFaces;

        owner
        {
            name        panels;
            type        wall;

            patchFields
            {
                U
                {
                    type    noSlip;
                }
                p
                {
                    type    zeroGradient;
                }
                k
                {
                    type    kqRWallFunction;
                    value   uniform 0.66;
                }
                epsilon
                {
                    type    epsilonWallFunction;
                    value   uniform 0.0215;
                }
                nut
                {
                    type    nutUWallFunction;
                    value   uniform 0.18;
                }
            }
        }

        neighbour
        {
            name        panels_shadow;
            type        wall;

            patchFields
            {
                U
                {
                    type    noSlip;
                }
                p
                {
                    type    zeroGradient;
                }
                k
                {
                    type    kqRWallFunction;
                    value   uniform 0.66;
                }
                epsilon
                {
                    type    epsilonWallFunction;
                    value   uniform 0.0215;
                }
                nut
                {
                    type    nutUWallFunction;
                    value   uniform 0.18;
                }
            }
        }
    }
}
"""
    (case_dir / "system" / "createBafflesDict").write_text(content)


def write_boundary_conditions(case_dir, u_ref=U_REF, z0=Z0, include_panels=False):
    """Write 0/ boundary condition files."""
    zero_dir = case_dir / "0"
    zero_dir.mkdir(parents=True, exist_ok=True)
    inc_dir = zero_dir / "include"
    inc_dir.mkdir(exist_ok=True)

    (inc_dir / "ABLConditions").write_text(
        f"Uref {u_ref};\nZref {Z_REF};\nzDir (0 0 1);\nflowDir (1 0 0);\n"
        f"z0 uniform {z0};\nzGround uniform 0.0;\n"
    )

    panel_bc = ""
    if include_panels:
        panel_bc = """
    panels { type noSlip; }
    panels_shadow { type noSlip; }"""

    (zero_dir / "U").write_text(f"""FoamFile
{{ version 2.0; format ascii; class volVectorField; object U; }}
dimensions [0 1 -1 0 0 0 0];
internalField uniform ({u_ref} 0 0);
boundaryField
{{
    inlet {{ type atmBoundaryLayerInletVelocity; #include "include/ABLConditions" }}
    outlet {{ type inletOutlet; inletValue uniform (0 0 0); value uniform ({u_ref} 0 0); }}
    ground {{ type noSlip; }}
    top {{ type atmBoundaryLayerInletVelocity; #include "include/ABLConditions" }}
    frontAndBack {{ type empty; }}{panel_bc}
}}
""")

    panel_bc_p = ""
    if include_panels:
        panel_bc_p = """
    panels { type zeroGradient; }
    panels_shadow { type zeroGradient; }"""

    (zero_dir / "p").write_text(f"""FoamFile
{{ version 2.0; format ascii; class volScalarField; object p; }}
dimensions [0 2 -2 0 0 0 0];
internalField uniform 0;
boundaryField
{{
    inlet {{ type zeroGradient; }}
    outlet {{ type fixedValue; value uniform 0; }}
    ground {{ type zeroGradient; }}
    top {{ type zeroGradient; }}
    frontAndBack {{ type empty; }}{panel_bc_p}
}}
""")

    panel_bc_k = ""
    if include_panels:
        panel_bc_k = """
    panels { type kqRWallFunction; value uniform 0.66; }
    panels_shadow { type kqRWallFunction; value uniform 0.66; }"""

    (zero_dir / "k").write_text(f"""FoamFile
{{ version 2.0; format ascii; class volScalarField; object k; }}
dimensions [0 2 -2 0 0 0 0];
internalField uniform 0.66;
boundaryField
{{
    inlet {{ type atmBoundaryLayerInletK; #include "include/ABLConditions" }}
    outlet {{ type inletOutlet; inletValue uniform 0.66; value uniform 0.66; }}
    ground {{ type kqRWallFunction; value uniform 0.66; }}
    top {{ type atmBoundaryLayerInletK; #include "include/ABLConditions" }}
    frontAndBack {{ type empty; }}{panel_bc_k}
}}
""")

    panel_bc_eps = ""
    if include_panels:
        panel_bc_eps = """
    panels { type epsilonWallFunction; value uniform 0.0215; }
    panels_shadow { type epsilonWallFunction; value uniform 0.0215; }"""

    (zero_dir / "epsilon").write_text(f"""FoamFile
{{ version 2.0; format ascii; class volScalarField; object epsilon; }}
dimensions [0 2 -3 0 0 0 0];
internalField uniform 0.0215;
boundaryField
{{
    inlet {{ type atmBoundaryLayerInletEpsilon; #include "include/ABLConditions" }}
    outlet {{ type inletOutlet; inletValue uniform 0.0215; value uniform 0.0215; }}
    ground {{ type epsilonWallFunction; value uniform 0.0215; }}
    top {{ type atmBoundaryLayerInletEpsilon; #include "include/ABLConditions" }}
    frontAndBack {{ type empty; }}{panel_bc_eps}
}}
""")

    panel_bc_nut = ""
    if include_panels:
        panel_bc_nut = """
    panels { type nutUWallFunction; value uniform 0.18; }
    panels_shadow { type nutUWallFunction; value uniform 0.18; }"""

    (zero_dir / "nut").write_text(f"""FoamFile
{{ version 2.0; format ascii; class volScalarField; object nut; }}
dimensions [0 2 -1 0 0 0 0];
internalField uniform 0.18;
boundaryField
{{
    inlet {{ type calculated; value uniform 0.18; }}
    outlet {{ type calculated; value uniform 0.18; }}
    ground {{ type nutUWallFunction; value uniform 0.18; }}
    top {{ type calculated; value uniform 0.18; }}
    frontAndBack {{ type empty; }}{panel_bc_nut}
}}
""")


def write_system_files(case_dir, end_time=2000):
    """Write controlDict, fvSchemes, fvSolution."""
    sd = case_dir / "system"
    sd.mkdir(parents=True, exist_ok=True)

    (sd / "controlDict").write_text(f"""FoamFile
{{ version 2.0; format ascii; class dictionary; object controlDict; }}

application     simpleFoam;
libs            ("libatmosphericModels.so");
startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         {end_time};
deltaT          1;
writeControl    timeStep;
writeInterval   {end_time};
purgeWrite      2;
writeFormat     ascii;
writePrecision  8;
writeCompression off;
timeFormat      general;
timePrecision   6;
runTimeModifiable true;

functions
{{
    wallShearStress1
    {{
        type            wallShearStress;
        libs            ("libfieldFunctionObjects.so");
        writeControl    writeTime;
    }}

    residuals
    {{
        type            residuals;
        libs            ("libutilityFunctionObjects.so");
        writeControl    timeStep;
        writeInterval   50;
        fields          (p U k epsilon);
    }}
}}
""")

    (sd / "fvSchemes").write_text("""FoamFile
{ version 2.0; format ascii; class dictionary; object fvSchemes; }
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

    (sd / "fvSolution").write_text("""FoamFile
{ version 2.0; format ascii; class dictionary; object fvSolution; }
solvers
{
    p
    {
        solver          GAMG;
        smoother        DICGaussSeidel;
        tolerance       1e-6;
        relTol          0.1;
        nPreSweeps      0;
        nPostSweeps     2;
        cacheAgglomeration on;
        agglomerator    faceAreaPair;
        nCellsInCoarsestLevel 10;
        mergeLevels     1;
    }
    "(U|k|epsilon)"
    {
        solver          PBiCGStab;
        preconditioner  DILU;
        tolerance       1e-7;
        relTol          0.1;
    }
}
SIMPLE
{
    nNonOrthogonalCorrectors 0;
    consistent yes;
    residualControl { p 2e-4; U 2e-4; "(k|epsilon)" 2e-4; }
}
relaxationFactors
{
    fields { p 0.5; }
    equations { U 0.7; k 0.7; epsilon 0.7; }
}
""")

    (sd / "decomposeParDict").write_text("""FoamFile
{ version 2.0; format ascii; class dictionary; object decomposeParDict; }
numberOfSubdomains 4;
method scotch;
""")


def write_constant_files(case_dir):
    """Write physical properties and turbulence model."""
    cd = case_dir / "constant"
    cd.mkdir(parents=True, exist_ok=True)

    (cd / "physicalProperties").write_text(f"""FoamFile
{{ version 2.0; format ascii; class dictionary; object physicalProperties; }}
viscosityModel constant;
nu [0 2 -1 0 0 0 0] {NU};
""")

    (cd / "momentumTransport").write_text("""FoamFile
{ version 2.0; format ascii; class dictionary; object momentumTransport; }
simulationType RAS;
RAS { model kEpsilon; turbulence on; printCoeffs on; }
""")


def setup_case(case_dir, H, theta_deg, S, mesh_level='medium', n_rows=N_ROWS):
    """Set up a complete OpenFOAM case."""
    case_dir = Path(case_dir)
    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True)

    print(f"  Writing case files...")
    write_blockMeshDict(case_dir, H, theta_deg, S, mesh_level)
    write_topoSetDict(case_dir, H, theta_deg, S)
    write_createBafflesDict(case_dir)
    write_system_files(case_dir)
    write_constant_files(case_dir)

    # Write initial BCs (without panels - needed for blockMesh/topoSet)
    write_boundary_conditions(case_dir, include_panels=False)

    # Save metadata
    Hp = projected_height(theta_deg)
    metadata = {
        'H': H, 'theta': theta_deg, 'S': S,
        'S_factor': round(S / Hp, 1),
        'Hp': round(Hp, 4),
        'mesh_level': mesh_level,
        'n_rows': n_rows,
    }
    (case_dir / "case_metadata.json").write_text(json.dumps(metadata, indent=2))

    # Run blockMesh
    print(f"  Running blockMesh...")
    r = subprocess.run(['blockMesh'], cwd=case_dir, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  blockMesh FAILED:\n{r.stderr[-300:]}")
        return False
    for line in r.stdout.split('\n'):
        if 'nCells' in line:
            print(f"    {line.strip()}")

    # Run topoSet
    print(f"  Running topoSet...")
    r = subprocess.run(['topoSet'], cwd=case_dir, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  topoSet FAILED:\n{r.stderr[-500:]}")
        return False
    for line in r.stdout.split('\n'):
        if 'size' in line:
            print(f"    {line.strip()}")

    # Run createBaffles
    print(f"  Running createBaffles...")
    r = subprocess.run(['createBaffles', '-overwrite'],
                      cwd=case_dir, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"  createBaffles FAILED:\n{r.stderr[-500:]}")
        return False

    # Rewrite BCs with panels + panels_shadow patches
    write_boundary_conditions(case_dir, include_panels=True)

    # Check mesh
    r = subprocess.run(['checkMesh'], cwd=case_dir, capture_output=True, text=True)
    for line in r.stdout.split('\n'):
        if 'Mesh OK' in line or 'cells:' in line or 'Failed' in line:
            print(f"    {line.strip()}")

    return True


if __name__ == "__main__":
    test_dir = Path("/tmp/test_baffle_case")

    H = 0.5
    theta = 25
    Hp = projected_height(theta)
    S = 4 * Hp

    print(f"Test: H={H}m, theta={theta}deg, S={S:.2f}m ({4}*Hp)")
    ok = setup_case(test_dir, H, theta, S, mesh_level='coarse')

    if ok:
        print("\nBoundary patches:")
        r = subprocess.run(['bash', '-c', 'grep -B1 "nFaces" constant/polyMesh/boundary'],
                         cwd=test_dir, capture_output=True, text=True)
        print(r.stdout[:500])
