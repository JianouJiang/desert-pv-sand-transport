#!/bin/bash
# Run parametric cases from the END of the list backward.
# Designed to run alongside run_remaining.sh to utilize freed CPU cores.
# run_remaining.sh runs case_01 → case_36; this runs case_36 → case_01.
# Both scripts skip cases that already have a log.simpleFoam file.

source /opt/openfoam10/etc/bashrc || true

BASE="/home/jianoujiang/Desktop/paper-factory/projects/desert_solar_sand_transport/codes/openfoam/parametric_study"
NPROCS=4

run_case() {
    local case_dir="$1"
    local name=$(basename "$case_dir")

    # Skip if already completed or being run by the other script
    if [ -f "$case_dir/log.simpleFoam" ]; then
        echo "SKIP: $name (already done or running)"
        # Ensure cell centres are written
        if ! ls "$case_dir"/*/Cx >/dev/null 2>&1; then
            postProcess -func writeCellCentres -latestTime -case "$case_dir" > /dev/null 2>&1 || true
        fi
        return 0
    fi

    echo "RUN (reverse): $name"
    local start=$SECONDS

    # Clean any partial processor dirs
    rm -rf "$case_dir"/processor*/[1-9]* 2>/dev/null

    # Decompose
    if decomposePar -case "$case_dir" > /dev/null 2>&1; then
        mpirun -np $NPROCS simpleFoam -parallel -case "$case_dir" > "$case_dir/log.simpleFoam" 2>&1 || true
        reconstructPar -latestTime -case "$case_dir" > /dev/null 2>&1 || true
        postProcess -func writeCellCentres -latestTime -case "$case_dir" > /dev/null 2>&1 || true
    else
        echo "  decomposePar failed, running serial"
        simpleFoam -case "$case_dir" > "$case_dir/log.simpleFoam" 2>&1 || true
        postProcess -func writeCellCentres -latestTime -case "$case_dir" > /dev/null 2>&1 || true
    fi

    local elapsed=$((SECONDS - start))
    echo "  Done in ${elapsed}s"
}

echo "============================================"
echo "REVERSE RUNNER: Cases 36 → 1"
echo "============================================"
echo ""

# Run cases in reverse order
for i in $(seq 36 -1 1); do
    case_dir=$(printf "$BASE/case_%02d_*" $i)
    # Expand glob
    for d in $case_dir; do
        if [ -d "$d" ]; then
            run_case "$d"
            break
        fi
    done
done

echo ""
echo "============================================"
echo "REVERSE RUNNER COMPLETE"
echo "============================================"
