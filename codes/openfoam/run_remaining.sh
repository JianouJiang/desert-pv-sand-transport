#!/bin/bash
# Run remaining OpenFOAM cases, skipping already-completed ones.
# Sources OpenFOAM and runs each case sequentially on 4 cores.

source /opt/openfoam10/etc/bashrc || true

BASE="/home/jianoujiang/Desktop/paper-factory/projects/desert_solar_sand_transport/codes/openfoam/parametric_study"
NPROCS=4

run_case() {
    local case_dir="$1"
    local name=$(basename "$case_dir")

    # Skip if already completed (log.simpleFoam exists with final time)
    if [ -f "$case_dir/log.simpleFoam" ]; then
        echo "SKIP: $name (already done)"
        # But ensure cell centres are written
        if [ ! -f "$case_dir"/*/Cx 2>/dev/null ]; then
            postProcess -func writeCellCentres -latestTime -case "$case_dir" > /dev/null 2>&1 || true
        fi
        return 0
    fi

    echo "RUN: $name"
    local start=$SECONDS

    # Clean any partial processor dirs
    rm -rf "$case_dir"/processor*/[1-9]* 2>/dev/null

    # Decompose
    if decomposePar -case "$case_dir" > /dev/null 2>&1; then
        # Run parallel
        mpirun -np $NPROCS simpleFoam -parallel -case "$case_dir" > "$case_dir/log.simpleFoam" 2>&1 || true

        # Reconstruct
        reconstructPar -latestTime -case "$case_dir" > /dev/null 2>&1 || true

        # Write cell centres
        postProcess -func writeCellCentres -latestTime -case "$case_dir" > /dev/null 2>&1 || true
    else
        # Run serial
        echo "  decomposePar failed, running serial"
        simpleFoam -case "$case_dir" > "$case_dir/log.simpleFoam" 2>&1 || true

        # Write cell centres
        postProcess -func writeCellCentres -latestTime -case "$case_dir" > /dev/null 2>&1 || true
    fi

    local elapsed=$((SECONDS - start))
    echo "  Done in ${elapsed}s"
}

echo "============================================"
echo "RUNNING REMAINING OPENFOAM CASES"
echo "============================================"
echo ""

# Mesh independence
echo "--- MESH INDEPENDENCE ---"
for level in coarse medium fine; do
    case_dir="$BASE/mesh_independence/mesh_$level"
    if [ -d "$case_dir" ]; then
        run_case "$case_dir"
    fi
done

# Parametric cases
echo ""
echo "--- PARAMETRIC STUDY ---"
for case_dir in "$BASE"/case_*; do
    if [ -d "$case_dir" ]; then
        run_case "$case_dir"
    fi
done

echo ""
echo "============================================"
echo "ALL CASES COMPLETE"
echo "============================================"
