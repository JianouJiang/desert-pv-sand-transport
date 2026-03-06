#!/bin/bash
# Restart unconverged parametric cases from iteration 2000 to 3000
# Two parallel runners, 4 procs each
source /opt/openfoam10/etc/bashrc

BASE="/home/jianoujiang/Desktop/paper-factory/projects/desert_solar_sand_transport/codes/openfoam/parametric_study"
LOG="/home/jianoujiang/Desktop/paper-factory/projects/desert_solar_sand_transport/logs/restart.log"

echo "$(date): Starting restart script" | tee "$LOG"

# Collect unconverged cases
CASES=()
for d in "$BASE"/case_*; do
    [ -d "$d" ] || continue
    log="$d/log.simpleFoam"
    [ -f "$log" ] || continue
    # Already restarted?
    [ -f "$d/log.simpleFoam_restart" ] && continue
    # Check convergence: if residualControl was NOT met, the log ends with "End" but no "converged" message
    # Simple check: endTime was 2000, if case needs more iterations
    current_end=$(grep "^endTime" "$d/system/controlDict" 2>/dev/null | awk '{print $2}' | tr -d ';')
    if [ "$current_end" = "2000" ]; then
        CASES+=("$d")
    fi
done

echo "Found ${#CASES[@]} cases to restart" | tee -a "$LOG"

run_one() {
    local d="$1"
    local name=$(basename "$d")
    echo "$(date +%H:%M:%S) START $name" | tee -a "$LOG"

    # Update endTime
    sed -i 's/endTime\s\+2000;/endTime         3000;/' "$d/system/controlDict"

    # Run in parallel from existing decomposed state
    cd "$d"
    mpirun -np 4 simpleFoam -parallel > log.simpleFoam_restart 2>&1

    # Reconstruct latest time
    reconstructPar -latestTime >> log.simpleFoam_restart 2>&1

    # Wall shear stress post-processing
    postProcess -func wallShearStress -latestTime >> log.simpleFoam_restart 2>&1
    postProcess -func writeCellCentres -latestTime >> log.simpleFoam_restart 2>&1

    echo "$(date +%H:%M:%S) DONE  $name" | tee -a "$LOG"
}

# Run 2 at a time
i=0
for d in "${CASES[@]}"; do
    run_one "$d" &
    ((i++))
    if (( i % 2 == 0 )); then
        wait
    fi
done
wait

echo "$(date): All restarts complete" | tee -a "$LOG"
