# AI Career Agent

An autonomous Python pipeline that fetches LinkedIn job offers, scores them against your filters, and drafts high-impact connection messages.

## What it does

1. **Scrapes LinkedIn** with human-like behavior (stealth, random delays, scroll).
2. **Scores every offer** with an LLM using a traffic-light system:
   - 🔴 Red — does not match critical filters.
   - 🟠 Orange — matches but misses a secondary skill.
   - 🟢 Green — strong match.
3. **Generates drafts** (≤700 chars) for Green and Orange offers.
4. **Respects a hard daily cap** (default 30 offers/day) stored in a local SQLite database.

## Architecture

Clean Architecture: `domain` → `application` → `adapters` → `infrastructure`.

- **LLM providers:** Google Gemini (primary, free tier) with DeepSeek V4 Flash as fallback.
- **Scraper:** Playwright with session persistence.
- **Scheduler:** runs daily at 9:00 AM `America/Bogota`.

## Account safety

- **Use a secondary LinkedIn account for the agent.** Do not run the scraper with your personal profile; LinkedIn may restrict or suspend accounts that show automated behavior.
- **Do not store your LinkedIn password in `.env`.** The login is manual (`scripts/create_session.py` opens a real browser). Keeping the password in `.env` is unnecessary and a security risk.
- Keep the daily offer limit low, and stop immediately if LinkedIn shows a captcha or security checkpoint.

## Setup

1. Install dependencies and Playwright browsers:
   ```bash
   uv sync
   uv run playwright install chromium
   ```

2. Copy the environment template and add your API keys:
   ```bash
   cp .env.example .env
   ```
   - Get a free `GEMINI_API_KEY` at [Google AI Studio](https://aistudio.google.com/app/apikey).
   - Get a `DEEPSEEK_API_KEY` at [DeepSeek Platform](https://platform.deepseek.com/api_keys).
   - Optional: set `COMPANY_BLACKLIST=BairesDev,Lumenalta` to skip companies you don't want.
   - Optional: set `LINKEDIN_EXPORT_PATH=data/linkedin_export` if you want to import your LinkedIn Job Alerts.

3. Create a LinkedIn session manually with your secondary account:
   ```bash
   uv run python scripts/create_session.py
   ```
   Log in inside the opened browser, then press Enter in the terminal. This saves `data/session_state.json`.

## LinkedIn Job Alerts import

If you have Job Alerts configured in LinkedIn:

1. Request your data export at [LinkedIn Data Export](https://www.linkedin.com/mypreferences/d/download-my-data).
2. When the email arrives, download and unzip the archive into `data/linkedin_export/`.
3. The agent will automatically read `Job Alerts.csv` and run each saved search in addition to `LINKEDIN_SEARCH_URL`.

## Running every day

### Option A — Scheduler (recommended)

Run the agent in the background. It will execute once daily at 9:00 AM Colombia time:

```bash
uv run ai-career-agent
```

### Option B — One-off run

Run the pipeline immediately:

```bash
uv run ai-career-agent --now
```

After each run, an HTML report is generated in `data/reports/` and opened automatically in your browser. It shows every offer, the score, the reason, the LinkedIn URL and a copy-to-clipboard button for the draft message.

Use `--no-open` if you do not want the browser to open automatically.

To regenerate today's report from the local database without running a new search:

```bash
uv run ai-career-agent --report-only
```

## Testing

```bash
uv run pytest
```

## Project docs

- `constitution.md` — immutable project principles.
- `specs/001-linkedin-pipeline/` — feature spec, implementation plan and tasks.
- `AGENTS.md` — guidance for future AI coding sessions.
