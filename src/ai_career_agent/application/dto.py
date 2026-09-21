from typing import List

from pydantic import BaseModel, Field

from ai_career_agent.domain.entities import Score


class EvaluationResult(BaseModel):
    """Schema Pydantic del LLM para structured output; como un DTO de class-validator."""

    score: Score
    reason: str
    missing_skills: List[str] = Field(default_factory=list)
    matched_skills: List[str] = Field(default_factory=list)


class MessageResult(BaseModel):
    """Schema Pydantic del mensaje generado por el LLM.

    No limitamos aquí a 700 caracteres porque el LLM a veces lo excede;
    el cliente recorta después de validar el JSON.
    """

    content: str
