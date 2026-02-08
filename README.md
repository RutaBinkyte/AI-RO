
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

## Set-up .env
```bash
# put openai_compatible or mock
LLM_BACKEND=openai_compatible 

OPENAI_API_KEY=YOUR_KEY

OPENAI_BASE_URL=YOUR_URL

OPENAI_MODEL=YOUR_MODEL

TEMPERATURE=
TOP_P=
MAX_TOKENS=

## Quickstart 
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt


# For DEMO set LLM_BACKEND=mock in .env
python -m src.pipeline --input data/references.yaml --out outputs --run-name demo
# For actual run, set LLM_BACKEND=openai_compatible and provide info in .env
python -m src.pipeline --run-name your_name
