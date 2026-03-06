#!/usr/bin/env python3
"""
Generate OpenFOAM case directories for the 36-case parametric study.

Each case: 8-row PV panel array in 2D ABL flow.
Panels modeled as thin baffles using snappyHexMesh with STL geometry.

Parameters:
  H:     ground clearance {0.1, 0.3, 0.5, 0.8} m
  theta: tilt angle {15, 25, 35} degrees
  S:     row spacing {2*Hp, 4*Hp, 6*Hp} where Hp = panel height projected
"""

import os
import shutil
import json
import numpy as np
from pathlib import Path

# Physical parameters
PANEL_LENGTH = 2.0        # Panel chord length [m]
N_ROWS = 8                # Number of panel rows
Z0 = 0.001                # Desert roughness length [m]
U_REF = 10.0              # Reference wind speed at z_ref [m/s]
Z_REF = 10.0              # Reference height [m]
NU = 1.5e-5               # Kinematic viscosity [m^2/s]
DOMAIN_HEIGHT = 30.0       # Domain height [m]

# Parametric matrix
H_VALUES = [0.1, 0.3, 0.5, 0.8]     # Ground clearance [m]
THETA_VALUES = [15, 25, 35]           # Tilt angle [degrees]
S_FACTORS = [2, 4, 6]                 # Row spacing as multiple of Hp

BASE_DIR = Path(__file__).parent / "parametric_study"


def panel_geometry(H, theta_deg, L=PANEL_LENGTH):
    """Compute panel corner coordinates for a single panel.

    Panel bottom-left at (0, H), tilted by theta from horizontal.
    Returns (x_bottom, z_bottom, x_top, z_top).
    """
    theta = np.radians(theta_deg)
    dx = L * np.cos(theta)
    dz = L * np.sin(theta)
    return (0.0, H, dx, H + dz)


def projected_height(theta_deg, L=PANEL_LENGTH):
    """Vertical projected height of the panel."""
    return L * np.sin(np.radians(theta_deg))


def create_stl_panels(case_dir, H, theta_deg, S, n_rows=N_ROWS):
    """Create STL file for thin panel baffles (2D extruded in y)."""
    theta = np.radians(theta_deg)
    L = PANEL_LENGTH

    # Panel dimensions
    dx = L * np.cos(theta)
    dz = L * np.sin(theta)
    Hp = projected_height(theta_deg)

    # Domain width in y (for 2D: thin slice)
    y_min = -0.01
    y_max = 1.01

    # First panel starts after inlet fetch
    x_start = 20.0  # 20m fetch before first panel

    stl_dir = case_dir / "constant" / "geometry"
    stl_dir.mkdir(parents=True, exist_ok=True)

    triangles = []
    panel_positions = []

    for i in range(n_rows):
        x0 = x_start + i * S
        z0_panel = H
        x1 = x0 + dx
        z1_panel = H + dz

        panel_positions.append({
            'row': i + 1,
            'x_le': x0,
            'z_le': z0_panel,
            'x_te': x1,
            'z_te': z1_panel
        })

        # Panel is a thin quad in 2D (extruded in y)
        # Front face (wind-facing side)
        # Two triangles per face
        # Vertices: (x0,y_min,z0), (x1,y_min,z1), (x1,y_max,z1), (x0,y_max,z0)
        p1 = (x0, y_min, z0_panel)
        p2 = (x1, y_min, z1_panel)
        p3 = (x1, y_max, z1_panel)
        p4 = (x0, y_max, z0_panel)

        # Normal pointing upward-into-wind (front face)
        triangles.append((p1, p3, p2))  # CCW for outward normal
        triangles.append((p1, p4, p3))

        # Back face (downwind side) - reversed normals
        triangles.append((p1, p2, p3))
        triangles.append((p1, p3, p4))

    # Write ASCII STL
    stl_path = stl_dir / "panels.stl"
    with open(stl_path, 'w') as f:
        f.write("solid panels\n")
        for tri in triangles:
            # Compute normal
            v1 = np.array(tri[1]) - np.array(tri[0])
            v2 = np.array(tri[2]) - np.array(tri[0])
            n = np.cross(v1, v2)
            norm = np.linalg.norm(n)
            if norm > 0:
                n = n / norm
            f.write(f"  facet normal {n[0]:.6e} {n[1]:.6e} {n[2]:.6e}\n")
            f.write("    outer loop\n")
            for vertex in tri:
                f.write(f"      vertex {vertex[0]:.6f} {vertex[1]:.6f} {vertex[2]:.6f}\n")
            f.write("    endloop\n")
            f.write("  endfacet\n")
        f.write("endsolid panels\n")

    return panel_positions


def domain_length(H, theta_deg, S, n_rows=N_ROWS):
    """Calculate required domain length."""
    Hp = projected_height(theta_deg)
    dx_panel = PANEL_LENGTH * np.cos(np.radians(theta_deg))
    # 20m inlet fetch + panels + 10*panel_height wake
    array_length = (n_rows - 1) * S + dx_panel
    wake_length = max(30.0, 10 * (H + Hp))
    return 20.0 + array_length + wake_length


def write_blockMeshDict(case_dir, L_domain, H, theta_deg):
    """Write blockMeshDict for rectangular background mesh."""
    Hp = projected_height(theta_deg)
    panel_top = H + Hp

    # Mesh sizing: ~0.05m near ground, stretching upward
    # Horizontal: ~0.1m resolution in panel region
    nx = int(L_domain / 0.1)   # ~0.1m in x
    nz_below = 30              # cells below panel region
    nz_panel = 20              # cells in panel region
    nz_above = 50              # cells above panel region

    # Use simpleGrading with vertical grading
    nz = 80

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
    (0     0   0)
    ({L_domain:.1f} 0   0)
    ({L_domain:.1f} 1   0)
    (0     1   0)
    (0     0   {DOMAIN_HEIGHT})
    ({L_domain:.1f} 0   {DOMAIN_HEIGHT})
    ({L_domain:.1f} 1   {DOMAIN_HEIGHT})
    (0     1   {DOMAIN_HEIGHT})
);

blocks
(
    hex (0 1 2 3 4 5 6 7) ({nx} 1 {nz})
    simpleGrading
    (
        1
        1
        (
            (0.05 30 1)
            (0.10 20 1)
            (0.85 30 20)
        )
    )
);

boundary
(
    inlet
    {{
        type patch;
        faces
        (
            (0 3 7 4)
        );
    }}
    outlet
    {{
        type patch;
        faces
        (
            (1 5 6 2)
        );
    }}
    ground
    {{
        type wall;
        faces
        (
            (0 1 2 3)
        );
    }}
    top
    {{
        type patch;
        faces
        (
            (4 7 6 5)
        );
    }}
    frontAndBack
    {{
        type empty;
        faces
        (
            (0 4 5 1)
            (3 2 6 7)
        );
    }}
);
"""
    (case_dir / "system").mkdir(parents=True, exist_ok=True)
    with open(case_dir / "system" / "blockMeshDict", 'w') as f:
        f.write(content)


def write_snappyHexMeshDict(case_dir, H, theta_deg):
    """Write snappyHexMeshDict to refine around panels and insert baffles."""
    Hp = projected_height(theta_deg)
    panel_top = H + Hp

    # Refinement box around panel region
    x_start = 18.0  # slightly before first panel
    x_end_est = 20.0 + 7 * 6 * Hp + PANEL_LENGTH * np.cos(np.radians(theta_deg)) + 5.0

    content = f"""FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      snappyHexMeshDict;
}}

castellatedMesh true;
snap            true;
addLayers       false;

geometry
{{
    panels.stl
    {{
        type triSurfaceMesh;
        name panels;
    }}

    refinementBox
    {{
        type searchableBox;
        min ({x_start:.1f} -1 0);
        max ({x_end_est:.1f} 2 {min(panel_top + 2.0, 5.0):.1f});
    }}
}}

castellatedMeshControls
{{
    maxLocalCells 500000;
    maxGlobalCells 2000000;
    minRefinementCells 10;
    maxLoadUnbalance 0.10;
    nCellsBetweenLevels 3;

    features
    (
    );

    refinementSurfaces
    {{
        panels
        {{
            level (3 3);
            faceZone panelsFaceZone;
            cellZone panelsCellZone;
            cellZoneInside inside;
        }}
    }}

    resolveFeatureAngle 30;

    refinementRegions
    {{
        refinementBox
        {{
            mode inside;
            levels ((1e15 2));
        }}
    }}

    locationInMesh (10 0.5 15);
    allowFreeStandingZoneFaces true;
}}

snapControls
{{
    nSmoothPatch 3;
    tolerance 2.0;
    nSolveIter 100;
    nRelaxIter 5;
    nFeatureSnapIter 10;
}}

addLayersControls
{{
    relativeSizes true;
    layers
    {{
    }}
    expansionRatio 1.0;
    finalLayerThickness 0.3;
    minThickness 0.1;
    nGrow 0;
    featureAngle 60;
    nRelaxIter 3;
    nSmoothSurfaceNormals 1;
    nSmoothNormals 3;
    nSmoothThickness 10;
    maxFaceThicknessRatio 0.5;
    maxThicknessToMedialRatio 0.3;
    minMedialAxisAngle 90;
    nBufferCellsNoExtrude 0;
    nLayerIter 50;
}}

meshQualityControls
{{
    maxNonOrtho 65;
    maxBoundarySkewness 20;
    maxInternalSkewness 4;
    maxConcave 80;
    minVol 1e-13;
    minTetQuality -1e30;
    minArea -1;
    minTwist 0.02;
    minDeterminant 0.001;
    minFaceWeight 0.02;
    minVolRatio 0.01;
    minTriangleTwist -1;
    nSmoothScale 4;
    errorReduction 0.75;
}}

debug 0;
mergeTolerance 1e-6;
"""
    with open(case_dir / "system" / "snappyHexMeshDict", 'w') as f:
        f.write(content)


def write_boundary_conditions(case_dir):
    """Write 0/ boundary condition files for simpleFoam with k-epsilon."""
    zero_dir = case_dir / "0"
    zero_dir.mkdir(parents=True, exist_ok=True)
    include_dir = zero_dir / "include"
    include_dir.mkdir(exist_ok=True)

    # ABL conditions
    with open(include_dir / "ABLConditions", 'w') as f:
        f.write(f"""Uref            {U_REF};
Zref            {Z_REF};
zDir            (0 0 1);
flowDir         (1 0 0);
z0              uniform {Z0};
zGround         uniform 0.0;
""")

    # U
    with open(zero_dir / "U", 'w') as f:
        f.write(f"""FoamFile
{{
    version     2.0;
    format      ascii;
    class       volVectorField;
    object      U;
}}

dimensions      [0 1 -1 0 0 0 0];

internalField   uniform ({U_REF} 0 0);

boundaryField
{{
    inlet
    {{
        type            atmBoundaryLayerInletVelocity;
        #include        "include/ABLConditions"
    }}

    outlet
    {{
        type            inletOutlet;
        inletValue      uniform (0 0 0);
        value           uniform ({U_REF} 0 0);
    }}

    ground
    {{
        type            noSlip;
    }}

    top
    {{
        type            atmBoundaryLayerInletVelocity;
        #include        "include/ABLConditions"
    }}

    frontAndBack
    {{
        type            empty;
    }}

    panels
    {{
        type            noSlip;
    }}
}}
""")

    # p
    with open(zero_dir / "p", 'w') as f:
        f.write(f"""FoamFile
{{
    version     2.0;
    format      ascii;
    class       volScalarField;
    object      p;
}}

dimensions      [0 2 -2 0 0 0 0];

internalField   uniform 0;

boundaryField
{{
    inlet
    {{
        type            zeroGradient;
    }}

    outlet
    {{
        type            fixedValue;
        value           uniform 0;
    }}

    ground
    {{
        type            zeroGradient;
    }}

    top
    {{
        type            zeroGradient;
    }}

    frontAndBack
    {{
        type            empty;
    }}

    panels
    {{
        type            zeroGradient;
    }}
}}
""")

    # k
    with open(zero_dir / "k", 'w') as f:
        f.write(f"""FoamFile
{{
    version     2.0;
    format      ascii;
    class       volScalarField;
    object      k;
}}

dimensions      [0 2 -2 0 0 0 0];

internalField   uniform 0.66;

boundaryField
{{
    inlet
    {{
        type            atmBoundaryLayerInletK;
        #include        "include/ABLConditions"
    }}

    outlet
    {{
        type            inletOutlet;
        inletValue      uniform 0.66;
        value           uniform 0.66;
    }}

    ground
    {{
        type            kqRWallFunction;
        value           uniform 0.66;
    }}

    top
    {{
        type            atmBoundaryLayerInletK;
        #include        "include/ABLConditions"
    }}

    frontAndBack
    {{
        type            empty;
    }}

    panels
    {{
        type            kqRWallFunction;
        value           uniform 0.66;
    }}
}}
""")

    # epsilon
    with open(zero_dir / "epsilon", 'w') as f:
        f.write(f"""FoamFile
{{
    version     2.0;
    format      ascii;
    class       volScalarField;
    object      epsilon;
}}

dimensions      [0 2 -3 0 0 0 0];

internalField   uniform 0.0215;

boundaryField
{{
    inlet
    {{
        type            atmBoundaryLayerInletEpsilon;
        #include        "include/ABLConditions"
    }}

    outlet
    {{
        type            inletOutlet;
        inletValue      uniform 0.0215;
        value           uniform 0.0215;
    }}

    ground
    {{
        type            epsilonWallFunction;
        value           uniform 0.0215;
    }}

    top
    {{
        type            atmBoundaryLayerInletEpsilon;
        #include        "include/ABLConditions"
    }}

    frontAndBack
    {{
        type            empty;
    }}

    panels
    {{
        type            epsilonWallFunction;
        value           uniform 0.0215;
    }}
}}
""")

    # nut
    with open(zero_dir / "nut", 'w') as f:
        f.write(f"""FoamFile
{{
    version     2.0;
    format      ascii;
    class       volScalarField;
    object      nut;
}}

dimensions      [0 2 -1 0 0 0 0];

internalField   uniform 0.18;

boundaryField
{{
    inlet
    {{
        type            calculated;
        value           uniform 0.18;
    }}

    outlet
    {{
        type            calculated;
        value           uniform 0.18;
    }}

    ground
    {{
        type            nutUWallFunction;
        value           uniform 0.18;
    }}

    top
    {{
        type            calculated;
        value           uniform 0.18;
    }}

    frontAndBack
    {{
        type            empty;
    }}

    panels
    {{
        type            nutUWallFunction;
        value           uniform 0.18;
    }}
}}
""")


def write_system_files(case_dir, L_domain, H, theta_deg, S, end_time=3000):
    """Write system/ directory files."""
    sys_dir = case_dir / "system"
    sys_dir.mkdir(parents=True, exist_ok=True)

    Hp = projected_height(theta_deg)

    # controlDict
    with open(sys_dir / "controlDict", 'w') as f:
        f.write(f"""FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      controlDict;
}}

application     simpleFoam;

libs            ("libatmosphericModels.so");

startFrom       startTime;
startTime       0;
stopAt          endTime;
endTime         {end_time};

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
{{
    wallShearStress
    {{
        type            wallShearStress;
        libs            ("libfieldFunctionObjects.so");
        writeControl    writeTime;
        patches         (ground panels);
    }}

    yPlus
    {{
        type            yPlus;
        libs            ("libfieldFunctionObjects.so");
        writeControl    writeTime;
    }}
}}
""")

    # fvSchemes
    with open(sys_dir / "fvSchemes", 'w') as f:
        f.write("""FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      fvSchemes;
}

ddtSchemes
{
    default         steadyState;
}

gradSchemes
{
    default         Gauss linear;
    grad(U)         cellLimited Gauss linear 1;
}

divSchemes
{
    default         none;
    div(phi,U)      bounded Gauss linearUpwindV grad(U);
    div(phi,k)      bounded Gauss upwind;
    div(phi,epsilon) bounded Gauss upwind;
    div((nuEff*dev2(T(grad(U))))) Gauss linear;
}

laplacianSchemes
{
    default         Gauss linear corrected;
}

interpolationSchemes
{
    default         linear;
}

snGradSchemes
{
    default         corrected;
}

wallDist
{
    method          meshWave;
}
""")

    # fvSolution
    with open(sys_dir / "fvSolution", 'w') as f:
        f.write("""FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      fvSolution;
}

solvers
{
    p
    {
        solver          GAMG;
        smoother        GaussSeidel;
        tolerance       1e-7;
        relTol          0.01;
    }

    "(U|k|epsilon)"
    {
        solver          PBiCGStab;
        preconditioner  DILU;
        tolerance       1e-8;
        relTol          0.01;
    }
}

SIMPLE
{
    nNonOrthogonalCorrectors 1;
    consistent      yes;

    residualControl
    {
        p               1e-5;
        U               1e-5;
        "(k|epsilon)"   1e-5;
    }
}

relaxationFactors
{
    fields
    {
        p               0.3;
    }
    equations
    {
        U               0.7;
        k               0.7;
        epsilon         0.7;
    }
}
""")


def write_constant_files(case_dir):
    """Write constant/ directory files."""
    const_dir = case_dir / "constant"
    const_dir.mkdir(parents=True, exist_ok=True)

    # physicalProperties (OF10)
    with open(const_dir / "physicalProperties", 'w') as f:
        f.write(f"""FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      physicalProperties;
}}

viscosityModel  constant;
nu              [0 2 -1 0 0 0 0] {NU};
""")

    # momentumTransport (OF10 - replaces turbulenceProperties)
    with open(const_dir / "momentumTransport", 'w') as f:
        f.write("""FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      momentumTransport;
}

simulationType  RAS;

RAS
{
    model           kEpsilon;
    turbulence      on;
    printCoeffs     on;
}
""")


def write_decompose_dict(case_dir, n_procs=8):
    """Write decomposeParDict for parallel execution."""
    sys_dir = case_dir / "system"
    with open(sys_dir / "decomposeParDict", 'w') as f:
        f.write(f"""FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      decomposeParDict;
}}

numberOfSubdomains {n_procs};

method          scotch;
""")


def create_case(case_name, H, theta_deg, S):
    """Create a complete OpenFOAM case directory."""
    case_dir = BASE_DIR / case_name

    if case_dir.exists():
        shutil.rmtree(case_dir)
    case_dir.mkdir(parents=True)

    L_domain = domain_length(H, theta_deg, S)

    # Create panel STL geometry
    panel_positions = create_stl_panels(case_dir, H, theta_deg, S)

    # Write mesh files
    write_blockMeshDict(case_dir, L_domain, H, theta_deg)
    write_snappyHexMeshDict(case_dir, H, theta_deg)

    # Write boundary conditions
    write_boundary_conditions(case_dir)

    # Write system files
    write_system_files(case_dir, L_domain, H, theta_deg, S)

    # Write constant files
    write_constant_files(case_dir)

    # Write decomposition dictionary
    write_decompose_dict(case_dir)

    # Save case metadata
    metadata = {
        'case_name': case_name,
        'H': H,
        'theta': theta_deg,
        'S': S,
        'S_factor': S / projected_height(theta_deg),
        'domain_length': L_domain,
        'n_rows': N_ROWS,
        'panel_length': PANEL_LENGTH,
        'panel_positions': panel_positions,
        'u_ref': U_REF,
        'z0': Z0,
    }
    with open(case_dir / "case_metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)

    return case_dir, metadata


def generate_run_script(case_dir, case_name, n_procs=8):
    """Generate a shell script to run the case."""
    script = f"""#!/bin/bash
# Run script for case: {case_name}
# Generated automatically

cd "{case_dir}"

echo "=== Case: {case_name} ==="
echo "Starting at: $(date)"

# 1. Background mesh
echo "Running blockMesh..."
blockMesh > log.blockMesh 2>&1
if [ $? -ne 0 ]; then echo "blockMesh FAILED"; exit 1; fi

# 2. Refine mesh with snappyHexMesh
echo "Running snappyHexMesh..."
snappyHexMesh -overwrite > log.snappyHexMesh 2>&1
if [ $? -ne 0 ]; then
    echo "snappyHexMesh FAILED - running without panel refinement"
    # Fall through to run with blockMesh mesh only
fi

# 3. Check mesh quality
echo "Running checkMesh..."
checkMesh > log.checkMesh 2>&1

# 4. Decompose for parallel
echo "Decomposing..."
decomposePar > log.decomposePar 2>&1
if [ $? -ne 0 ]; then echo "decomposePar FAILED"; exit 1; fi

# 5. Run solver
echo "Running simpleFoam on {n_procs} cores..."
mpirun -np {n_procs} simpleFoam -parallel > log.simpleFoam 2>&1
if [ $? -ne 0 ]; then echo "simpleFoam FAILED"; exit 1; fi

# 6. Reconstruct
echo "Reconstructing..."
reconstructPar -latestTime > log.reconstructPar 2>&1

echo "Completed at: $(date)"
echo "=== Done: {case_name} ==="
"""
    script_path = case_dir / "Allrun"
    with open(script_path, 'w') as f:
        f.write(script)
    os.chmod(script_path, 0o755)


def main():
    """Generate all 36 parametric cases."""
    BASE_DIR.mkdir(parents=True, exist_ok=True)

    cases = []
    case_id = 0

    for H in H_VALUES:
        for theta in THETA_VALUES:
            Hp = projected_height(theta)
            for s_factor in S_FACTORS:
                S = s_factor * Hp
                case_id += 1
                case_name = f"case_{case_id:02d}_H{H:.1f}_T{theta}_S{s_factor}Hp"

                print(f"Creating {case_name}: H={H}m, theta={theta}deg, S={S:.2f}m ({s_factor}*Hp)")

                case_dir, metadata = create_case(case_name, H, theta, S)
                generate_run_script(case_dir, case_name)

                cases.append(metadata)

    # Save case matrix
    with open(BASE_DIR / "case_matrix.json", 'w') as f:
        json.dump(cases, f, indent=2)

    print(f"\nGenerated {len(cases)} cases in {BASE_DIR}")

    # Generate master run script
    with open(BASE_DIR / "Allrun_all", 'w') as f:
        f.write("#!/bin/bash\n")
        f.write("# Run all parametric cases sequentially\n")
        f.write(f"# Total cases: {len(cases)}\n\n")
        for i, case in enumerate(cases):
            cn = case['case_name']
            f.write(f'echo "=== Case {i+1}/{len(cases)}: {cn} ==="\n')
            f.write(f'cd "{BASE_DIR / cn}"\n')
            f.write(f'bash Allrun\n\n')
    os.chmod(BASE_DIR / "Allrun_all", 0o755)

    print(f"Master run script: {BASE_DIR / 'Allrun_all'}")


if __name__ == "__main__":
    main()
