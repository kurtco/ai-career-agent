from datetime import datetime
from typing import Type, TypeVar

from google import genai
from google.genai.types import GenerateContentConfig

from ai_career_agent.application.dto import EvaluationResult, MessageResult
from ai_career_agent.domain.entities import JobOffer, MessageDraft, Score
from ai_career_agent.domain.ports import LLMClient

T = TypeVar("T")


class GeminiClient(LLMClient):
    """Cliente principal de LLM usando Gemini; como un servicio externo inyectado en Nest."""

    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-lite"):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    async def evaluate(self, offer: JobOffer) -> JobOffer:
        config = GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=EvaluationResult,
        )
        response = self.client.models.generate_content(
            model=self.model,
            contents=_build_evaluation_prompt(offer),
            config=config,
        )
        result = EvaluationResult.model_validate_json(response.text)
        offer.score = result.score
        offer.reason = result.reason
        offer.missing_skills = result.missing_skills
        offer.matched_skills = result.matched_skills
        return offer

    async def generate_message(self, offer: JobOffer, cv_text: str) -> MessageDraft:
        config = GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=MessageResult,
        )
        response = self.client.models.generate_content(
            model=self.model,
            contents=_build_message_prompt(offer, cv_text),
            config=config,
        )
        result = MessageResult.model_validate_json(response.text)
        return MessageDraft(offer_id=offer.id, content=result.content)


def _build_evaluation_prompt(offer: JobOffer) -> str:
    return f"""Evalúa esta oferta de trabajo como un filtro de semáforo.

OFERTA:
Título: {offer.title}
Empresa: {offer.company}
Ubicación: {offer.location}
Remoto: {offer.is_remote}
Tipo de contrato: {offer.contract_type.value}
Periodo de compensación: {offer.compensation_period.value}
Salario mínimo: {offer.salary_min}
Salario máximo: {offer.salary_max}
Stack: {', '.join(offer.stack_tags)}
Descripción:
{offer.description}

REGLAS DEL USUARIO:
- Salario objetivo: $5,000-$7,000+ USD/mes.
- Aceptable solo si full-time long-term: $4,000-$4,999/mes.
- Descartar si < $4,000/mes mensual, o < $35/h SOLO si es por hora.
- Stack ideal: Node.js, TypeScript, React, Next.js, AI.
- Aceptar Python solo si también incluye Node.js/TypeScript.
- Descartar roles 100% Python senior, DevOps-first, Java o .NET monolítico.
- Busca remoto internacional contractor para Colombia/LATAM.

Responde con JSON válido según el schema."""


def _build_message_prompt(offer: JobOffer, cv_text: str) -> str:
    return f"""Escribe un mensaje de postulación en inglés para LinkedIn (máximo 700 caracteres).

OFERTA:
Título: {offer.title}
Empresa: {offer.company}
Stack: {', '.join(offer.stack_tags)}
Descripción:
{offer.description}

CV DEL CANDIDATO:
{cv_text or 'No disponible'}

REGLAS:
- Máximo 700 caracteres.
- 2-3 highlights del CV con match exacto.
- Estructura: saludo → gancho sobre el rol y seniority → logro técnico → CTA suave.
- Tono Staff/Lead Engineer, profesional y directo.

Responde con JSON válido: {{"content": "..."}}."""
