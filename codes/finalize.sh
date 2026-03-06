#!/bin/bash
# Finalize paper: post-process all OpenFOAM results, generate figures, update manuscript.
# Run this AFTER all simulations have completed.

set -euo pipefail

BASE="/home/jianoujiang/Desktop/paper-factory/projects/desert_solar_sand_transport"
cd "$BASE"

echo "============================================"
echo "STEP 1: Post-process all OpenFOAM results"
echo "============================================"
python3 codes/analysis/postprocess_openfoam.py

echo ""
echo "============================================"
echo "STEP 2: Update GCI table in manuscript"
echo "============================================"
python3 codes/analysis/update_gci_table.py

echo ""
echo "============================================"
echo "STEP 3: Generate all 12 figures"
echo "============================================"
python3 codes/figures/generate_openfoam_figures.py

echo ""
echo "============================================"
echo "STEP 4: Compile LaTeX manuscript"
echo "============================================"
cd manuscript
pdflatex -interaction=nonstopmode main.tex > /dev/null 2>&1
bibtex main > /dev/null 2>&1
pdflatex -interaction=nonstopmode main.tex > /dev/null 2>&1
pdflatex -interaction=nonstopmode main.tex > /dev/null 2>&1
echo "LaTeX compilation complete"
echo "Pages: $(pdfinfo main.pdf 2>/dev/null | grep Pages | awk '{print $2}' || echo 'unknown')"

echo ""
echo "============================================"
echo "FINALIZATION COMPLETE"
echo "============================================"
echo "Output: manuscript/main.pdf"
