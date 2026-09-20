from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class Score(str, Enum):
    """Semáforo de evaluación: igual a un status enum en TypeScript."""

    RED = "red"
    ORANGE = "orange"
    GREEN = "green"


class CompensationPeriod(str, Enum):
    MONTHLY = "monthly"
    HOURLY = "hourly"


class ContractType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    UNKNOWN = "unknown"


class JobOffer(BaseModel):
    """Entidad pura de dominio; equivalente a una entity/aggregate de Nest."""

    id: str
    title: str
    company: str
    location: str = ""
    description: str = ""
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    currency: str = "USD"
    compensation_period: CompensationPeriod = CompensationPeriod.MONTHLY
    contract_type: ContractType = ContractType.UNKNOWN
    is_remote: bool = False
    stack_tags: List[str] = Field(default_factory=list)
    url: str = ""
    score: Score = Score.RED
    reason: str = ""
    missing_skills: List[str] = Field(default_factory=list)
    matched_skills: List[str] = Field(default_factory=list)
    processed_at: Optional[datetime] = None


class MessageDraft(BaseModel):
    """Value object con el mensaje generado; similar a un DTO de salida de Nest."""

    offer_id: str
    content: str = Field(..., max_length=700)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
