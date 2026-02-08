
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class LLMInteraction:
    stage: str
    timestamp_utc: str
    backend: str
    model: str
    base_url: Optional[str]
    parameters: Dict[str, Any]
    prompt_sha256: str
    response_sha256: str
    prompt_text: str
    response_text: str
    input_bundle_sha256: str


class ProvenanceLogger:
    def __init__(self, log_dir: str) -> None:
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

    def log_interaction(
        self,
        *,
        run_prefix: str,
        stage: str,
        backend: str,
        model: str,
        base_url: Optional[str],
        parameters: Dict[str, Any],
        prompt_text: str,
        response_text: str,
        input_bundle_text: str,
    ) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        prompt_hash = _sha256(prompt_text)
        response_hash = _sha256(response_text)
        bundle_hash = _sha256(input_bundle_text)

        record = LLMInteraction(
            stage=stage,
            timestamp_utc=ts,
            backend=backend,
            model=model,
            base_url=base_url,
            parameters=parameters,
            prompt_sha256=prompt_hash,
            response_sha256=response_hash,
            prompt_text=prompt_text,
            response_text=response_text,
            input_bundle_sha256=bundle_hash,
        )

        filename = f"{run_prefix}_{stage}_{ts}.json"
        path = os.path.join(self.log_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(record), f, ensure_ascii=False, indent=2)

        return path

