
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Tuple

import pandas as pd


def write_json(obj: Dict[str, Any], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def write_text(text: str, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def build_audit_table(papers: List[Dict[str, Any]], taxonomy: Dict[str, Any]) -> pd.DataFrame:
    # Build mapping paper_id -> cluster_id
    mapping = {}
    for c in taxonomy.get("clusters", []):
        for pid in c.get("paper_ids", []):
            mapping[pid] = c.get("cluster_id", "")

    rows = []
    for p in papers:
        rows.append(
            {
                "paper_id": p["id"],
                "citation": p["citation"],
                "pid": p["pid"],
                "cluster_id": mapping.get(p["id"], ""),
                "verified_pid_exists": "",      # to be filled by human
                "claim_support_checked": "",    # to be filled by human
                "notes": "",                    # to be filled by human
            }
        )
    return pd.DataFrame(rows)


def write_audit_csv(df: pd.DataFrame, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)


def build_provenance_card(
    *,
    run_name: str,
    topic: str,
    backend: str,
    model: str,
    base_url: str | None,
    parameters: Dict[str, Any],
    input_bundle_sha256: str,
    log_paths: List[str],
    outputs: List[str],
) -> str:
    lines = []
    lines.append("# AI-RO Provenance Card (Condition A)\n")
    lines.append(f"- Run name: `{run_name}`")
    lines.append(f"- Topic: {topic}")
    lines.append(f"- Backend: `{backend}`")
    lines.append(f"- Model: `{model}`")
    if base_url:
        lines.append(f"- Base URL: `{base_url}`")
    lines.append(f"- Parameters: `{parameters}`")
    lines.append(f"- Input bundle SHA-256: `{input_bundle_sha256}`")
    lines.append("\n## Interaction logs")
    for p in log_paths:
        lines.append(f"- `{p}`")
    lines.append("\n## Generated outputs")
    for o in outputs:
        lines.append(f"- `{o}`")
    lines.append("\n## Disclosure snippet (suggested)")
    lines.append(
        "> We used a generative language model as an assistive tool for structural synthesis and language drafting of the related work section. "
        "We provided human-authored summaries of each cited work and constrained the model to cite only from this set. "
        "All interpretive claims and references were validated by the authors. "
        "We release prompts, interaction logs, and generated intermediate artifacts as an AI Research Object (AI-RO)."
    )
    return "\n".join(lines) + "\n"

