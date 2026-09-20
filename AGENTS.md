# AGENTS.md — AI Career Agent

> Repo-specific guidance for OpenCode sessions. Read this first, then `constitution.md`, then the active spec.

## Sources of truth (read in this order)

1. **`constitution.md`** — immutable principles: Clean Architecture, anti-ban rules, coding style, LLM providers, 9 AM `America/Bogota` schedule.
2. **`specs/001-linkedin-pipeline/spec.md`** — functional requirements: semáforo scoring, salary/stack filters, message generator rules.
3. **`specs/001-linkedin-pipeline/plan.md`** — implementation plan: directory tree, dependencies, architecture decisions.
4. **`specs/001-linkedin-pipeline/tasks.md`** — deliverables. **Only mark `[x]` when the task is fully implemented and verified.**

## Developer commands

- `uv run pytest` — ejecuta la suite de tests.
- `uv run ai-career-agent --now` — corre el pipeline una vez (requiere `.env` + `data/session_state.json`).
- `uv run python scripts/create_session.py` — abre LinkedIn para logueo manual y guarda `data/session_state.json`.

## Current state

- Proyecto Python inicializado con `uv`, Python 3.12.
- Código bajo `src/ai_career_agent/` siguiendo Clean Architecture.
- Tests unitarios en `tests/`; CA-1 a CA-4 cubiertos con mocks.
- E2E real bloqueado hasta tener `GEMINI_API_KEY`/`DEEPSEEK_API_KEY` y `data/session_state.json`.

## Architecture rules you cannot override

- **Clean Architecture, no exceptions.** Domain → Application → Adapters → Infrastructure. Infrastructure never imports from outer layers.
- **Strict separation:** scraping (Playwright), LLM calls, and business logic live in separate modules. Mixing them violates `constitution.md` Art. III.
- **Puertos e inyección manual:** casos de uso reciben dependencias por constructor (estilo Nest providers). No usar frameworks DI en v1.

## LLM providers (locked)

- **Primary:** Google Gemini Flash, free tier via Google AI Studio (`GEMINI_API_KEY`). Structured output nativo con `response_schema`.
- **Fallback:** DeepSeek V4 Flash (`DEEPSEEK_API_KEY`) via `https://api.deepseek.com/v1` usando el SDK de OpenAI con `base_url`.
- **Do not use OpenRouter.** Both clients implement the `LLMClient` port; a facade intenta Gemini primero y cae a DeepSeek ante rate limit o 5xx.

## Code style (locked)

- Comments in **Spanish only**, max 200 characters, only at architectural joints or dependency injection.
- Every comment explains "qué hace esto" and includes a quick TypeScript/NestJS analogy for the user (TS/NestJS background).

## Anti-ban guardrails for LinkedIn scraping

- Load session state from `data/session_state.json` — zero automated login flows.
- Random organic delays + scroll before DOM extraction.
- Hard daily cap: 20–30 offers/day, persisted in `data/history.db` to survive restarts.
- On captcha/block: abort and log; **no retries**.

## Adding a new iteration

Create a new spec directory with the same three files:

```
specs/002-<nombre>/
  spec.md    # QUÉ
  plan.md    # CÓMO
  tasks.md   # entregables paso a paso
```

Never change `constitution.md` unless the user explicitly asks for a principle change.

## Common mistakes to avoid

- Marking tasks `[x]` before code is written and verified.
- Using OpenRouter or Anthropic/OpenAI as primary providers.
- Writing English comments or adding comments everywhere.
- Running the scraper without `data/session_state.json`; that file must be produced by a manual LinkedIn login in Playwright.
- Adding logic to `main.py` beyond composition and scheduler wiring.
