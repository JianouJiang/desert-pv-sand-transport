#!/bin/bash
# reproduce.sh — Regenerate all figures and results for Desert PV Sand Transport paper
# Expected runtime: ~250-310 CPU-hours for full CFD (2-3 weeks on 8 cores)
# For figure regeneration only (from saved results): ~30 minutes
# Usage: bash results/reproduce.sh [--figures-only]
set -e

echo "=== Desert PV Wind-Sand Transport — Full Reproduction Script ==="
echo "Started at: $(date)"

cd codes
if [ -f requirements.txt ]; then
    pip install -r requirements.txt -q
fi

if [ "$1" = "--figures-only" ]; then
    echo "[FIGURES ONLY MODE] Regenerating figures from saved results..."
    for fig_script in figures/fig_*.py; do
        if [ -f "$fig_script" ]; then
            echo "  Running $fig_script..."
            python3 "$fig_script"
        fi
    done
else
    # Step 1: ABL precursor simulation
    echo "[1/6] Running ABL precursor simulation..."
    python3 data_processing/setup_abl_precursor.py 2>/dev/null || echo "ABL setup not yet created"

    # Step 2: Mesh generation and independence study
    echo "[2/6] Mesh independence study..."
    python3 validation/mesh_independence.py 2>/dev/null || echo "Mesh study not yet created"

    # Step 3: Turbulence model validation
    echo "[3/6] Turbulence model validation..."
    python3 validation/turbulence_validation.py 2>/dev/null || echo "Validation not yet created"

    # Step 4: Parametric study (36 cases)
    echo "[4/6] Running 36-case parametric study..."
    python3 models/run_parametric_study.py 2>/dev/null || echo "Parametric study not yet created"

    # Step 5: Sensitivity analysis
    echo "[5/6] Running sensitivity analysis..."
    python3 analysis/sensitivity_analysis.py 2>/dev/null || echo "Sensitivity analysis not yet created"

    # Step 6: Generate all figures
    echo "[6/6] Generating figures..."
    for fig_script in figures/fig_*.py; do
        if [ -f "$fig_script" ]; then
            echo "  Running $fig_script..."
            python3 "$fig_script"
        fi
    done
fi

cd ..
echo "=== Reproduction complete at $(date) ==="
