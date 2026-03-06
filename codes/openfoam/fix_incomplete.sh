#!/bin/bash
# Re-run cases that completed restart but lack data beyond time 2000
# (unconverged cases where writeInterval=2000 prevented time 3000 from being saved)
# Run AFTER main restart script completes and resources are free.
source /opt/openfoam10/etc/bashrc

BASE="/home/jianoujiang/Desktop/paper-factory/projects/desert_solar_sand_transport/codes/openfoam/parametric_study"
LOG="/home/jianoujiang/Desktop/paper-factory/projects/desert_solar_sand_transport/logs/fix_incomplete.log"

echo "$(date): Starting fix_incomplete" | tee "$LOG"

# Find cases with latest_time=2000, not converged, and restart already completed
FIXME=()
for d in "$BASE"/case_*; do
    [ -d "$d" ] || continue
    # Check if restart log exists and is complete (has "End" or "DONE" or just finished)
    restart_log="$d/log.simpleFoam_restart"
    [ -f "$restart_log" ] || continue
    # Check latest time dir
    latest=$(ls "$d" | grep -E '^[0-9]+$' | sort -n | tail -1)
    if [ "$latest" = "2000" ]; then
        # Check if case converged
        if ! grep -q "converged" "$restart_log" 2>/dev/null; then
            # Check if processor0/2000 exists for restart
            if [ -d "$d/processor0/2000" ]; then
                FIXME+=("$d")
            fi
        fi
    fi
done

echo "Found ${#FIXME[@]} cases to fix" | tee -a "$LOG"

for d in "${FIXME[@]}"; do
    name=$(basename "$d")
    echo "$(date +%H:%M:%S) Fixing $name" | tee -a "$LOG"
    cd "$d"
    # startFrom and writeInterval already set correctly
    mpirun -np 4 simpleFoam -parallel > log.simpleFoam_fix 2>&1
    reconstructPar -latestTime >> log.simpleFoam_fix 2>&1
    postProcess -func wallShearStress -latestTime >> log.simpleFoam_fix 2>&1
    postProcess -func writeCellCentres -latestTime >> log.simpleFoam_fix 2>&1
    echo "$(date +%H:%M:%S) Fixed $name" | tee -a "$LOG"
done

echo "$(date): Fix complete" | tee -a "$LOG"
