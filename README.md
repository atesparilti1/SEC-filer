# SEC Filing Analyzer

AI-powered analysis of SEC 10-K and 10-Q filings. Enter a US public company's
ticker, pick a filing, and get a structured breakdown of its business risks,
growth opportunities, financial trends, and management priorities — grounded
in the actual filing text and real SEC XBRL financial data.

Runs entirely free by default: five well-known tickers ship with **pre-generated
demo analyses** for instant exploration, and any other filing is analyzed
**live by a local LLM via [Ollama](https://ollama.com)** — no API key, no
billing. A hosted OpenAI backend is also supported as a drop-in swap for
higher-quality output.

<p align="left">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.12-blue">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-backend-teal">
  <img alt="React" src="https://img.shields.io/badge/React-19-blue">
  <img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-frontend-blue">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-lightgrey">
</p>

## Screenshots

> _Add screenshots of the dashboard, risk analysis view, and comparison view here._

| Dashboard | Filing Comparison |
| --- | --- |
| `docs/screenshot-dashboard.png` | `docs/screenshot-compare.png` |

## Why this matters

Reading a 10-K or 10-Q cover-to-cover takes hours, and the most decision-relevant
information — a newly disclosed risk, a shift in management's stated priorities,
a subtle change in growth strategy — is often buried in dense legal boilerplate.

SEC Filing Analyzer is built for the workflow an analyst or investor actually
has: pull up a ticker, skim the risks and opportunities that changed, sanity-check
them against real reported financials, and move on. It never lets the AI invent
a number — every financial figure on the page is computed in Python directly
from SEC's own XBRL data — and every qualitative claim is traceable back to a
quote from the filing itself.

## Features

- **Ticker search** — resolves a ticker (AAPL, NVDA, AMD, MSFT, META, …) to its
  SEC CIK and lists recent 10-K/10-Q filings.
- **Demo mode** — AAPL, NVDA, AMD, MSFT, and META ship with real,
  pre-generated analyses seeded into the cache at startup, so the app is fully
  explorable the moment it's cloned — no AI provider required.
- **Free local AI for everything else** — any other filing is analyzed live by
  a local model served through Ollama (`AI_PROVIDER=ollama`, the default).
  Swapping to OpenAI (`AI_PROVIDER=openai`) is a one-line config change for
  higher-quality output at the cost of API usage.
- **Grounded AI analysis** — extracts the Business, Risk Factors, and MD&A
  sections of a filing and sends only that text to the AI model, which returns
  a strict JSON schema: executive summary, key risks (with severity), growth
  opportunities, financial insights, management priorities, red flags, and
  positive signals.
- **Real financial metrics** — revenue, net income, operating income, total
  assets/liabilities, cash, and operating cash flow are pulled from SEC XBRL
  company facts. YoY growth and margins are calculated in Python — the AI
  model never touches this arithmetic.
- **Filing comparison** — compare two filings (e.g. the same company's last two
  10-Ks) and see new risks, removed risks, escalated risks, and shifts in
  strategy or financial trajectory.
- **Caching** — every analyzed filing is cached by
  `(ticker, accession_number, filing_type)`, so re-opening a filing is instant
  and never re-spends AI tokens.
- **Resilient error handling** — a bad ticker, an unreachable SEC endpoint, a
  filing that fails to parse, or an AI/schema failure all return a clean error
  message instead of crashing the app.

## Architecture

```
┌──────────────┐      REST/JSON      ┌───────────────┐      HTTPS       ┌─────────────────┐
│   React +    │ ──────────────────► │   FastAPI      │ ───────────────► │  SEC EDGAR API   │
│  TypeScript  │ ◄────────────────── │   backend      │ ◄─────────────── │  (filings, XBRL) │
└──────────────┘                     └───────┬───────┘                  └─────────────────┘
                                              │
                                              ├──► Ollama (local LLM, default — free)
                                              │       — or —
                                              ├──► OpenAI API (hosted LLM — paid)
                                              │
                                              └──► SQLite (cached + pre-seeded demo analyses)
```

**Backend** (`/backend`) is a layered FastAPI app:

- `app/services/edgar_client.py` — all SEC EDGAR HTTP access (ticker lookup,
  filings list, filing documents, XBRL company facts), rate-limited and sent
  with a proper `User-Agent` per SEC's fair-access policy.
- `app/services/filing_parser.py` — strips a filing down to plain text and
  extracts just the Business / Risk Factors / MD&A sections, filtering out
  table-of-contents noise, and truncates to a character budget before it ever
  reaches the AI model.
- `app/services/financial_metrics.py` — turns raw XBRL facts into a clean
  annual time series and computes YoY growth / margins in plain Python.
- `app/services/ai_analysis.py` — dispatches to whichever AI provider is
  configured (local Ollama or hosted OpenAI) with a strict JSON schema so
  output always matches the app's data model, for both single-filing
  analysis and filing-to-filing comparison.
- `app/services/analyze_pipeline.py` — orchestrates resolve → fetch → parse →
  analyze → cache so the API routers stay thin.
- `app/services/demo_seed.py` — loads the bundled `app/demo_data/*.json`
  fixtures into the cache at startup, marked `is_demo=True`.
- `app/routers/*` — the HTTP layer; `app/models.py` / `app/schemas.py` define
  the SQLAlchemy and Pydantic models.

**Frontend** (`/frontend`) is a Vite + React + TypeScript app styled with
Tailwind CSS v4 and charted with Recharts, structured as reusable components
(`components/`), pages (`pages/`), and a typed API client (`api/`).

## Technology Stack

| Layer | Technology |
| --- | --- |
| Backend | Python, FastAPI, Pydantic v2, SQLAlchemy 2.0, httpx, pandas |
| AI | Ollama (local, default) or OpenAI API — both via structured/strict JSON schema output |
| Data source | SEC EDGAR (submissions, filing documents, XBRL company facts) |
| Database | SQLite (swap-in ready for PostgreSQL — see below) |
| Frontend | React 19, TypeScript, Vite, Tailwind CSS v4, Recharts, React Router |
| Testing | pytest, respx (HTTP mocking) |

## Local Installation

### Prerequisites

- Python 3.12+
- Node.js 20+
- To analyze filings beyond the five demo tickers, one of:
  - [Ollama](https://ollama.com) (free, local, default) — install it, then
    `ollama pull llama3.1:8b`
  - An [OpenAI API key](https://platform.openai.com/account/api-keys) (paid,
    set `AI_PROVIDER=openai`)

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # macOS/Linux

pip install -r requirements.txt
cp .env.example .env             # defaults to local Ollama — no key needed
uvicorn app.main:app --reload --port 8000
```

The five demo tickers work immediately with no further setup. To analyze any
other filing, either have Ollama running locally (`ollama serve`, default) or
set `AI_PROVIDER=openai` and add your key in `.env`.

The API is now live at `http://127.0.0.1:8000`, with interactive OpenAPI docs
at `http://127.0.0.1:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app is now live at `http://127.0.0.1:5173` (the Vite dev server proxies
`/api` to the backend — see `vite.config.ts`).

### Running tests

```bash
cd backend
pytest
```

## Environment Variables

Defined in `backend/.env` (see `backend/.env.example`):

| Variable | Description |
| --- | --- |
| `AI_PROVIDER` | `ollama` (default, free/local) or `openai` (paid/hosted). Only affects filings *not* in the demo set. |
| `OLLAMA_BASE_URL` | Where Ollama is listening (default: `http://localhost:11434`). |
| `OLLAMA_MODEL` | Local model to use (default: `llama3.1:8b` — run `ollama pull llama3.1:8b` first). |
| `OPENAI_API_KEY` | Your OpenAI API key. Only required when `AI_PROVIDER=openai`. |
| `OPENAI_MODEL` | Model used for analysis when `AI_PROVIDER=openai` (default: `gpt-4o-mini`). |
| `SEC_USER_AGENT` | Required by SEC's fair-access policy — format: `"App Name contact@example.com"`. |
| `DATABASE_URL` | SQLAlchemy connection string. Defaults to local SQLite; point this at a PostgreSQL URL (`postgresql+psycopg2://...`) to switch databases with no code changes. |
| `CORS_ORIGINS` | Comma-separated list of allowed frontend origins. |

## API Endpoints

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/api/company/{ticker}` | Resolve a ticker to its CIK and company name. |
| `GET` | `/api/company/{ticker}/filings` | List recent 10-K/10-Q filings for a company. |
| `GET` | `/api/financials/{ticker}` | Computed historical financial metrics (revenue, margins, growth, …). |
| `POST` | `/api/analyze` | Analyze a filing (or return the cached analysis if it already exists). |
| `GET` | `/api/analysis/{id}` | Fetch a previously generated analysis by its database id. |
| `POST` | `/api/compare` | Compare two filings and return risk/strategy/financial deltas. |
| `GET` | `/api/health` | Liveness check. |

Full request/response schemas are available via the auto-generated OpenAPI
docs at `/docs` once the backend is running.

## Demo Companies

The search bar ships with quick-access buttons for `AAPL`, `NVDA`, `AMD`,
`MSFT`, and `META`. Their most recent 10-K analyses are pre-generated and
bundled in `backend/app/demo_data/*.json`; `app/services/demo_seed.py` loads
them into the cache at startup, so these five work instantly with zero AI
setup. Regenerate them (e.g. after a prompt change) with:

```bash
cd backend
python scripts/generate_demo_data.py            # all five
python scripts/generate_demo_data.py AAPL NVDA   # just these
```

## Future Improvements

- Persist raw filing text/sections so re-parsing isn't needed if the AI schema evolves.
- Add authentication and per-user saved analyses/watchlists.
- Support foreign private issuers (20-F) and non-XBRL filers.
- Stream the AI response for a faster perceived analysis time.
- Add a PostgreSQL + Alembic migration setup for production deployments.
- Sector/peer comparison (compare filings across companies, not just over time).

## License

MIT
