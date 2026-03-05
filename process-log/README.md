# Process Log — Desert PV Wind-Sand Transport

## Research Workflow Overview

This paper was produced using the Paper Factory autonomous agent system, following AIDER journal's open-process requirements.

### AI Tools Used
- **Claude Opus 4.6** (Anthropic) — Primary Worker agent: OpenFOAM CFD setup, simulation execution, Lagrangian particle tracking, data analysis, LaTeX writing, figure generation
- **Claude Opus 4.6** — Judge agent: critical scientific review, anti-shortcut enforcement (verifies simulations actually ran)
- **Claude Opus 4.6** — Statistician agent: statistical rigor, mesh independence, validation metrics
- **Claude Opus 4.6** — Editor agent: writing quality, LaTeX compliance
- **GPT-5.2** (OpenAI Codex) — Illustrator agent: figure quality review
- **Qwen 2.5 7B** (local Ollama) — Zero-token coordination

### Agent Workflow
Iterative loop: Worker → Judge → Worker → Statistician → Worker → Editor → Worker → Illustrator → repeat

### Computational Methods
- RANS CFD (SST k-omega) in OpenFOAM for atmospheric boundary layer flow
- Eulerian-Lagrangian particle tracking for saltating sand grains
- 36-case parametric study: 4 ground clearances × 3 tilt angles × 3 row spacings

### Human Decisions
All significant human interventions are logged in `human-decisions/decisions.md`.

### AI Session Logs
Full agent session logs stored in `ai-sessions/` and `../logs/`.
