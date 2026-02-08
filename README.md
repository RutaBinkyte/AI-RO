
# AI-RO Related Work Pipeline 

This repo provides a topic-agnostic, provenance-first pipeline for *legitimate* AI-assisted drafting of a Related Work section.

## What it does
Given human-authored structured notes for each cited paper (YAML):
- Builds a taxonomy (clusters) via an LLM with strict "no invention" constraints
- Drafts a Related Work section using only the provided notes + citations
- Produces AI-RO artifacts:
  - interaction logs (prompt + response + hashes + parameters)
  - taxonomy.json
  - related work draft markdown
  - audit_table.csv (for human verification)
  - provenance_card.md (appendix-ready)
  - taxonomy_graph.png (paper-ready figure)

## Quickstart 
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# set LLM_BACKEND=mock in .env
python -m src.pipeline --input data/references.yaml --out outputs --run-name demo
