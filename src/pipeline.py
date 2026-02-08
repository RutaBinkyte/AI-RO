
from __future__ import annotations

import argparse
import json
import os
from typing import Any, Dict

import yaml
from dotenv import load_dotenv

from src.validator import InputBundle
from src.llm_client import LLMClient, LLMConfig
from src.logger import ProvenanceLogger
from src.visualization import render_taxonomy_graph
from src.artifact_builder import (
    write_json,
    write_text,
    build_audit_table,
    write_audit_csv,
    build_provenance_card,
)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def load_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def papers_block(bundle: InputBundle) -> str:
    # Compact block for prompts while remaining inspectable.
    lines = []
    for p in bundle.papers:
        lines.append(f"- id: {p.id}")
        lines.append(f"  citation: {p.citation}")
        lines.append(f"  pid: {p.pid}")
        if p.title:
            lines.append(f"  title: {p.title}")
        lines.append("  summary: |")
        for s in p.summary.strip().splitlines():
            lines.append(f"    {s}")
        lines.append("  strengths:")
        for s in p.strengths:
            lines.append(f"    - {s}")
        lines.append("  limitations:")
        for s in p.limitations:
            lines.append(f"    - {s}")
        lines.append("  relation_to_work: |")
        for s in (p.relation_to_work or "").strip().splitlines() or [""]:
            lines.append(f"    {s}")
        lines.append("  comments: |")
        for s in (p.comments or "").strip().splitlines() or [""]:
            lines.append(f"    {s}")
        lines.append("")
    return "\n".join(lines).strip()


def main() -> None:
    load_dotenv()

    ap = argparse.ArgumentParser(description="AI-RO Condition A pipeline: taxonomy + related work draft + artifacts")
    ap.add_argument("--input", default="data/references.yaml", help="Path to YAML input bundle")
    ap.add_argument("--out", default="outputs", help="Output directory")
    ap.add_argument("--run-name", default="run", help="Name prefix for logs/outputs")
    ap.add_argument("--target-words", type=int, default=700, help="Target words for draft")
    args = ap.parse_args()

    in_path = os.path.join(ROOT, args.input) if not os.path.isabs(args.input) else args.input
    out_dir = os.path.join(ROOT, args.out) if not os.path.isabs(args.out) else args.out

    raw = load_yaml(in_path)
    bundle = InputBundle.model_validate(raw)

    # Keep an input bundle text for hashing/logging
    input_bundle_text = yaml.safe_dump(raw, sort_keys=False, allow_unicode=True)

    # Config
    backend = os.getenv("LLM_BACKEND", "mock").strip()
    print("DEBUG backend =", backend)
    cfg = LLMConfig(
        backend=backend,
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        temperature=float(os.getenv("TEMPERATURE", "0.2")),
        top_p=float(os.getenv("TOP_P", "1.0")),
        max_tokens=int(os.getenv("MAX_TOKENS", "1400")),
    )
    client = LLMClient(cfg)
    logger = ProvenanceLogger(log_dir=os.path.join(ROOT, "logs"))

    # --- Stage 1: Taxonomy ---
    tax_prompt_tmpl = read_text(os.path.join(ROOT, "prompts", "taxonomy_prompt.txt"))
    tax_prompt = (
        tax_prompt_tmpl.replace("{{TOPIC}}", bundle.topic)
        .replace("{{CONTRIBUTION_STATEMENT}}", bundle.contribution_statement.strip())
        .replace("{{PAPERS_BLOCK}}", papers_block(bundle))
    )

    tax_response = client.generate(tax_prompt)

    # Parse taxonomy JSON strictly (fail fast if not JSON)
    try:
        taxonomy = json.loads(tax_response)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            "Taxonomy stage did not return valid JSON. "
            "For reliability, reduce temperature and ensure prompt constraints are followed.\n"
            f"JSON error: {e}\nResponse was:\n{tax_response[:2000]}"
        )

    tax_log_path = logger.log_interaction(
        run_prefix=args.run_name,
        stage="taxonomy",
        backend=cfg.backend,
        model=cfg.model,
        base_url=cfg.base_url,
        parameters={"temperature": cfg.temperature, "top_p": cfg.top_p, "max_tokens": cfg.max_tokens},
        prompt_text=tax_prompt,
        response_text=tax_response,
        input_bundle_text=input_bundle_text,
    )

    # --- Stage 2: Synthesis Draft ---
    syn_prompt_tmpl = read_text(os.path.join(ROOT, "prompts", "synthesis_prompt.txt"))
    syn_prompt = syn_prompt_tmpl.replace("{{TARGET_WORDS}}", str(args.target_words))

    # Provide taxonomy + notes as embedded JSON/YAML text
    syn_prompt += "\n\nINPUT:\n"
    syn_prompt += f"Topic: {bundle.topic}\n"
    syn_prompt += "Contribution statement:\n" + bundle.contribution_statement.strip() + "\n\n"
    syn_prompt += "Taxonomy (JSON):\n" + json.dumps(taxonomy, ensure_ascii=False, indent=2) + "\n\n"
    syn_prompt += "Papers (notes):\n" + papers_block(bundle) + "\n"

    syn_response = client.generate(syn_prompt)

    syn_log_path = logger.log_interaction(
        run_prefix=args.run_name,
        stage="synthesis",
        backend=cfg.backend,
        model=cfg.model,
        base_url=cfg.base_url,
        parameters={"temperature": cfg.temperature, "top_p": cfg.top_p, "max_tokens": cfg.max_tokens},
        prompt_text=syn_prompt,
        response_text=syn_response,
        input_bundle_text=input_bundle_text,
    )

    # --- Outputs ---
    os.makedirs(out_dir, exist_ok=True)

    taxonomy_path = os.path.join(out_dir, f"{args.run_name}_taxonomy.json")
    draft_path = os.path.join(out_dir, f"{args.run_name}_draft_text.md")
    graph_path = os.path.join(out_dir, f"{args.run_name}_taxonomy_graph.png")
    audit_path = os.path.join(out_dir, f"{args.run_name}_audit_table.csv")
    prov_path = os.path.join(out_dir, f"{args.run_name}_provenance_card.md")

    write_json(taxonomy, taxonomy_path)
    write_text(syn_response, draft_path)
    render_taxonomy_graph(taxonomy, graph_path)

    df = build_audit_table([p.model_dump() for p in bundle.papers], taxonomy)
    write_audit_csv(df, audit_path)

    # Pull input hash from one of the logs (both share it)
    with open(tax_log_path, "r", encoding="utf-8") as f:
        tax_log = json.load(f)
    input_hash = tax_log["input_bundle_sha256"]

    prov_text = build_provenance_card(
        run_name=args.run_name,
        topic=bundle.topic,
        backend=cfg.backend,
        model=cfg.model,
        base_url=cfg.base_url,
        parameters={"temperature": cfg.temperature, "top_p": cfg.top_p, "max_tokens": cfg.max_tokens},
        input_bundle_sha256=input_hash,
        log_paths=[tax_log_path, syn_log_path],
        outputs=[taxonomy_path, graph_path, draft_path, audit_path],
    )
    write_text(prov_text, prov_path)

    print("✅ Done.")
    print("Outputs:")
    print(f"- {taxonomy_path}")
    print(f"- {graph_path}")
    print(f"- {draft_path}")
    print(f"- {audit_path}")
    print(f"- {prov_path}")
    print("Logs:")
    print(f"- {tax_log_path}")
    print(f"- {syn_log_path}")


if __name__ == "__main__":
    main()

