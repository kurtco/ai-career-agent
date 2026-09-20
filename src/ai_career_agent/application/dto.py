from typing import List

from pydantic import BaseModel, Field

from ai_career_agent.domain.entities import Score


class EvaluationResult(BaseModel):
    """Schema Pydantic del LLM para structured output; como un DTO de class-validator."""

    score: Score
    reason: str = Field(..., max_length=500)
    missing_skills: List[str] = Field(default_factory=list)
    matched_skills: List[str] = Field(default_factory=list)


class MessageResult(BaseModel):
    """Schema Pydantic del mensaje generado por el LLM."""

    content: str = Field(..., max_length=700)
