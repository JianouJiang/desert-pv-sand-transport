# Reproducibility Checklist — Desert PV Wind-Sand Transport

## Code
- [ ] All dependencies listed in `codes/requirements.txt`
- [ ] OpenFOAM version and solver settings documented
- [ ] Setup instructions in `codes/README.md`
- [ ] Code runs on a clean environment without modification
- [ ] Random seeds fixed for Lagrangian particle injection

## Data
- [ ] Meteorological input data (wind speed PDFs, grain sizes) documented
- [ ] Validation data sources cited with access instructions
- [ ] All OpenFOAM case files included

## Results
- [ ] `results/reproduce.sh` exists and regenerates all figures/tables
- [ ] `--figures-only` mode available for quick figure regeneration
- [ ] Script exits with code 0 on success
- [ ] Generated outputs match paper's figures and tables

## Process Log
- [ ] `process-log/README.md` describes research workflow
- [ ] AI session logs included in `process-log/ai-sessions/`
- [ ] Human decisions documented in `process-log/human-decisions/`
- [ ] All AI tools and versions disclosed

## Licensing
- [ ] Paper: CC-BY 4.0
- [ ] Code: MIT License
- [ ] Data: CC-BY 4.0
