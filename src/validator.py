
from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class Paper(BaseModel):
    id: str = Field(..., description="Unique id like P1, P2")
    citation: str
    pid: str
    title: Optional[str] = None
    summary: str
    strengths: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    relation_to_work: str = ""
    comments: str = ""

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("paper.id cannot be empty")
        return v

    @field_validator("pid")
    @classmethod
    def validate_pid(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("paper.pid cannot be empty")
        # Lightly enforce "persistent-ish" identifiers
        allowed_prefixes = ("doi:", "arxiv:", "acl:", "url:")
        if not v.startswith(allowed_prefixes):
            raise ValueError(f"paper.pid must start with one of {allowed_prefixes}, got: {v}")
        return v

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 20:
            raise ValueError("paper.summary looks too short; add a grounded summary from reading")
        return v


class InputBundle(BaseModel):
    topic: str
    contribution_statement: str
    papers: List[Paper]

    @field_validator("topic")
    @classmethod
    def validate_topic(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("topic cannot be empty")
        return v

    @field_validator("papers")
    @classmethod
    def validate_unique_ids(cls, papers: List[Paper]) -> List[Paper]:
        ids = [p.id for p in papers]
        if len(ids) != len(set(ids)):
            raise ValueError("paper.id values must be unique")
        if len(papers) < 2:
            raise ValueError("Provide at least 2 papers to form a taxonomy")
        return papers

