
from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests


@dataclass
class LLMConfig:
    backend: str  # mock | openai_compatible
    api_key: Optional[str]
    base_url: Optional[str]
    model: str
    temperature: float
    top_p: float
    max_tokens: int


class LLMClient:
    def __init__(self, cfg: LLMConfig) -> None:
        self.cfg = cfg

    def generate(self, prompt: str) -> str:
        if self.cfg.backend == "mock":
            return self._mock_generate(prompt)
        if self.cfg.backend == "openai_compatible":
            return self._openai_compatible_generate(prompt)
        raise ValueError(f"Unknown LLM_BACKEND: {self.cfg.backend}")

    def _mock_generate(self, prompt: str) -> str:
        # Deterministic-ish mock to make workshop demos runnable without keys.
        # We detect which stage by looking for schema hints.
        if '"clusters"' in prompt and "VALID JSON ONLY" in prompt:
            # Return a tiny plausible taxonomy JSON
            return json.dumps(
                {
                    "taxonomy_title": "Mock taxonomy",
                    "clusters": [
                        {
                            "cluster_id": "C1",
                            "name": "Approach family A",
                            "rationale": "Grouped by similar high-level approach as described in summaries.",
                            "paper_ids": ["P1"],
                            "comparative_phrases": [
                                "In contrast to P1 (…; …), our work emphasizes …",
                                "Whereas P1 targets …, we address …",
                            ],
                        },
                        {
                            "cluster_id": "C2",
                            "name": "Approach family B",
                            "rationale": "Grouped by alternative assumptions/setting highlighted in notes.",
                            "paper_ids": ["P2"],
                            "comparative_phrases": [
                                "Compared to P2 (…; …), our method differs by …",
                            ],
                        },
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )

        # Otherwise, return a draft-like text
        words = [
            "This", "is", "a", "MOCK", "related", "work", "draft.", "Replace",
            "LLM_BACKEND=mock", "with", "openai_compatible", "to", "get", "real",
            "outputs.", "Citations", "must", "be", "validated", "by", "humans."
        ]
        random.seed(0)
        return "RELATED WORK (DRAFT)\n\n" + " ".join(words) + "\n\nCLAIM CHECKLIST\n- [NEEDS HUMAN CHECK] Mock claim referencing P1/P2.\n"

    def _openai_compatible_generate(self, prompt: str) -> str:
        if not self.cfg.base_url:
            raise ValueError("OPENAI_BASE_URL is required for openai_compatible backend")
        if not self.cfg.api_key:
            raise ValueError("OPENAI_API_KEY is required for openai_compatible backend")

        url = self.cfg.base_url.rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.cfg.api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": self.cfg.model,
            "messages": [
                {"role": "system", "content": "You are a careful assistant. Follow the user's constraints exactly."},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.cfg.temperature,
            "top_p": self.cfg.top_p,
            "max_tokens": self.cfg.max_tokens,
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

