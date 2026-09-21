# TASKS 001 — Pipeline Autónomo de LinkedIn

> Entregables paso a paso derivados del plan.
>
> **REGLA:** Cada task terminado DEBE marcarse como `[x]` en este archivo inmediatamente al completarse.
> Un task solo se marca `[x]` cuando está verificado (código escrito + cumple su criterio de aceptación si aplica).
> Está prohibido marcar `[x]` tasks no terminados.

## Fase 1: Setup

- [x] T001 — Inicializar proyecto con `uv` (`pyproject.toml`, estructura de carpetas bajo `src/ai_career_agent/`)
- [x] T002 — Instalar dependencias: `playwright`, `playwright-stealth`, `pydantic`, `pydantic-settings`, `google-genai`, `openai`, `apscheduler`; dev: `pytest`, `pytest-asyncio`
- [x] T003 — Crear `.env.example` (keys `GEMINI_API_KEY` y `DEEPSEEK_API_KEY`) y `src/ai_career_agent/infrastructure/config.py` (pydantic-settings)

## Fase 2: Dominio

- [x] T004 — `src/ai_career_agent/domain/entities.py`: `JobOffer`, `MessageDraft`, enums `Score`, `CompensationPeriod`, `ContractType` — con comentarios didácticos (Art. II)
- [x] T005 — `src/ai_career_agent/domain/ports.py`: interfaces `JobScraper`, `LLMClient`, `OfferRepository`, `MessagePresenter` (ABCs; analogía con interfaces de Nest)

## Fase 3: Casos de Uso

- [x] T006 — `FetchOffersUseCase`: límite diario 20-30 vía `OfferRepository.count_today()`, manejo de `BlockedError` (CA-5, CA-6)
- [x] T007 — `EvaluateJobUseCase`: orquestar LLM → DTO Pydantic → mapeo a `JobOffer.score` (REQ-1, REQ-2, REQ-3)
- [x] T008 — `GenerateMessageUseCase`: drafts ≤700 chars con highlights de `data/cv.md` (R4.1–R4.4)
- [x] T009 — `src/ai_career_agent/application/dto.py`: schemas Pydantic del semáforo (structured output)

## Fase 4: Infraestructura

- [x] T010 — `PlaywrightLinkedInScraper`: stealth, `storage_state`, delays aleatorios, scroll, detección de captcha (Art. IV) — validado con corrida real
- [x] T011 — `GeminiClient`: structured output nativo (`response_schema`) con free tier, detrás de `LLMClient` (D3.1) — validado con corrida real
- [ ] T011b — `DeepSeekClient`: fallback vía API compatible OpenAI (`base_url` platform.deepseek.com) — *código listo, pendiente validación con saldo*
- [x] T011c — `LLMClientFacade`: intenta Gemini, ante rate limit/error 5xx cae a DeepSeek (Art. V.5) — verificado vía tests
- [x] T012 — `SqliteRepository`: persistencia de ofertas procesadas en `data/history.db` (D3.4)
- [x] T013 — `src/ai_career_agent/adapters/presenter.py`: salida por consola de drafts y scoring

## Fase 5: Entrada y Scheduling

- [x] T014 — `src/ai_career_agent/main.py`: composición manual de dependencias (D3.8) + flujo completo (§4 del plan)
- [x] T015 — Scheduler APScheduler 9:00 AM `America/Bogota` (D3.7, Art. VI)

## Fase 6: Validación

- [x] T016 — Tests de criterios de aceptación CA-1 a CA-4 (evaluación del semáforo con mocks del LLM); 6 tests pasan
- [x] T017 — Prueba manual E2E: corrida real con ≤5 ofertas verificando delays y persistencia — validada con 3 ofertas reales
