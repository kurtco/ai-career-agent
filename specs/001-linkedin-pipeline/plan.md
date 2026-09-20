# PLAN 001 — Pipeline Autónomo de LinkedIn

> CÓMO se implementa la spec 001, respetando la constitución.

## 1. Árbol de Directorios (Clean Architecture)

```
ai-career-agent/
├── constitution.md
├── specs/001-linkedin-pipeline/
├── pyproject.toml              # uv (gestión de dependencias)
├── .env.example                # API keys del LLM (nunca en código)
├── data/
│   ├── session_state.json      # cookies/estado de sesión de LinkedIn
│   └── history.db              # SQLite: ofertas procesadas (auditoría límite diario)
└── src/ai_career_agent/
    ├── domain/
    │   ├── entities.py         # JobOffer, MessageDraft, enums (Score: RED/ORANGE/GREEN)
    │   ├── ports.py            # Interfaces: JobScraper, LLMClient, OfferRepository, MessagePresenter
    │   └── exceptions.py       # BlockedError
    ├── application/
    │   ├── use_cases/
    │   │   ├── fetch_offers.py     # FetchOffersUseCase (aplica límite diario 20-30)
    │   │   ├── evaluate_job.py     # EvaluateJobUseCase (semáforo)
    │   │   └── generate_message.py # GenerateMessageUseCase (drafts WOW)
    │   └── dto.py              # Schemas Pydantic de entrada/salida del LLM
    ├── infrastructure/
    │   ├── scraper/
    │   │   └── playwright_linkedin.py  # Adaptador stealth + anti-ban (Art. IV)
    │   ├── llm/
    │   │   ├── gemini_client.py        # Principal: free tier, structured output nativo (response_schema)
    │   │   ├── deepseek_client.py      # Fallback: API compatible OpenAI (platform.deepseek.com)
    │   │   └── facade.py               # Intenta Gemini, fallback a DeepSeek
    │   ├── persistence/
    │   │   └── sqlite_repository.py    # Implementa OfferRepository
    │   └── config.py           # Settings vía pydantic-settings (.env)
    ├── adapters/
    │   └── presenter.py        # Formato de salida (consola/markdown)
    └── main.py                 # Punto de entrada + scheduler 9:00 AM America/Bogota
```

## 2. Dependencias (uv)

| Paquete | Uso |
|---|---|
| `playwright` + `playwright-stealth` | Navegador indetectable (Art. IV.1) |
| `pydantic` | Entidades/DTOs y structured output del LLM |
| `pydantic-settings` | Configuración desde `.env` |
| `google-genai` | Cliente Gemini (free tier, Google AI Studio) |
| `openai` | Cliente DeepSeek fallback (base_url `https://api.deepseek.com/v1`) |
| `apscheduler` | Scheduler con timezone `America/Bogota` |

## 3. Decisiones Técnicas

- **D3.1 — LLM:** Gemini Flash (free tier) como principal con structured output nativo (`response_schema` → JSON que parsea directo al DTO Pydantic). DeepSeek V4 Flash como fallback vía API compatible OpenAI. `LLMClientFacade` intenta Gemini; ante rate limit o error 5xx cae a DeepSeek (Art. V.4-5). Directo a proveedores, sin OpenRouter.
- **D3.2 — Sesión:** `session_state.json` se carga con `browser.new_context(storage_state=...)`. Cero login automático (Art. IV.2). El archivo vive en `data/` y está en `.gitignore`.
- **D3.3 — Comportamiento humano:** `asyncio.sleep(random.uniform(1.5, 4.0))` entre acciones + scroll progresivo antes de leer el DOM (Art. IV.3).
- **D3.4 — Límite diario:** `OfferRepository.count_today()` sobre `history.db` (fecha en `America/Bogota`); si ≥ 30, abortar la corrida (Art. IV.4, CA-6).
- **D3.5 — Captcha/bloqueo:** detectar checkpoint de LinkedIn en el DOM → lanzar `BlockedError`, loguear y abortar. Sin reintentos (Art. IV.5, CA-5).
- **D3.6 — CV para highlights (R4.2):** `data/cv.md` cargado por `GenerateMessageUseCase`; los 2-3 highlights se seleccionan por match semántico contra la oferta.
- **D3.7 — Scheduler:** APScheduler `CronTrigger(hour=9, minute=0, timezone="America/Bogota")` (Art. VI.2).
- **D3.8 — Inyección de dependencias:** composición manual en `main.py` (equivalente al módulo raíz de Nest; sin framework DI).

## 4. Flujo de Ejecución

```
main.py (9:00 AM)
  → FetchOffersUseCase
      → verifica límite diario (D3.4)
      → PlaywrightLinkedInScraper.fetch() (stealth, delays, scroll)
      → aborta si BlockedError (D3.5)
  → para cada oferta:
      → EvaluateJobUseCase → LLMClientFacade (Gemini → DeepSeek fallback) → DTO Pydantic → JobOffer.score
      → persistir en history.db
      → si VERDE/NARANJA:
          → GenerateMessageUseCase → MessageDraft (≤700 chars)
          → Presenter imprime draft
```
