#!/bin/bash
# Restart unconverged parametric cases from iteration 2000 to 3000
# Uses 2 parallel runners (4 procs each = 8 total, leaving 2 for system)
set -e

source /opt/openfoam10/etc/bashrc

BASE_DIR="/home/jianoujiang/Desktop/paper-factory/projects/desert_solar_sand_transport/codes/openfoam/parametric_study"
RESULTS_JSON="/home/jianoujiang/Desktop/paper-factory/projects/desert_solar_sand_transport/codes/results/openfoam_results.json"

# Find unconverged cases by checking log.simpleFoam for convergence message
UNCONVERGED=()
for case_dir in "$BASE_DIR"/case_*; do
    [ -d "$case_dir" ] || continue
    log="$case_dir/log.simpleFoam"
    [ -f "$log" ] || continue
    # Check if case hit endTime (didn't converge naturally)
    if grep -q "End$" "$log" && ! grep -q "converged" "$log"; then
        UNCONVERGED+=("$case_dir")
    fi
done

echo "Found ${#UNCONVERGED[@]} unconverged cases"

run_case() {
    local case_dir="$1"
    local case_name=$(basename "$case_dir")

    echo "[$(date +%H:%M)] Starting restart: $case_name"

    # Update endTime to 3000 in controlDict
    sed -i 's/endTime\s\+2000;/endTime         3000;/' "$case_dir/system/controlDict"

    # Also update in processor dirs
    for proc_dir in "$case_dir"/processor*; do
        if [ -d "$proc_dir/system" ]; then
            # processor dirs share root system/ in OF10, so this is actually the same file
            break
        fi
    done

    # Redistribute latest time to processors
    cd "$case_dir"

    # Check if 2000 exists in processor dirs
    if [ ! -d "processor0/2000" ]; then
        # Need to decompose the 2000 time step
        decomposePar -time 2000 -force > log.decompose_restart 2>&1
    fi

    # Run simpleFoam from 2000 to 3000
    mpirun -np 4 simpleFoam -parallel > log.simpleFoam_restart 2>&1

    # Reconstruct latest time
    reconstructPar -latestTime > log.reconstruct_restart 2>&1

    # Post-process wallShearStress
    postProcess -func wallShearStress -latestTime > log.postProcess_restart 2>&1
    postProcess -func writeCellCentres -latestTime > log.cellCentres_restart 2>&1

    echo "[$(date +%H:%M)] Finished: $case_name"
}

# Run cases in batches of 2 (2 parallel, 4 procs each = 8 cores)
i=0
for case_dir in "${UNCONVERGED[@]}"; do
    run_case "$case_dir" &
    ((i++))
    if (( i % 2 == 0 )); then
        wait
    fi
done
wait

echo "All ${#UNCONVERGED[@]} cases restarted. Total time: $(date)"
