# SupportPilot React Frontend

A React + Vite frontend for the current SupportPilot FastAPI backend. It implements the backend features that are present in the supplied project: ticket intake, automatic category/severity/priority classification, ticket listing and filtering, lifecycle status updates, activity history, CSV bulk upload, and stats/analytics.

## Requirements
- Node.js 18+ (Node 20+ recommended)
- The SupportPilot FastAPI backend and PostgreSQL running

## Run the backend first
From the existing project root:

```bash
docker compose up -d
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API should be available at `http://localhost:8000`; docs are at `http://localhost:8000/docs`.

## Run the frontend
In this folder (`frontend`):

```bash
npm install
cp .env.example .env
npm run dev
```

Open the Vite URL shown in the terminal (usually `http://localhost:5173`). If the API uses a different URL, update `VITE_API_URL` in `.env` and restart Vite.

## API endpoints used
- `GET /health` (backend connection can also be checked in the API docs)
- `POST /tickets`
- `GET /tickets`
- `GET /tickets/{ticket_id}`
- `GET /tickets/{ticket_id}/history`
- `PATCH /tickets/{ticket_id}/status`
- `POST /tickets/bulk`
- `GET /stats`

## Current scope / honest limitations
The supplied backend is currently Milestone 1: intake, ML classification, ticket lifecycle and summary statistics. The UI therefore displays classification output returned by the backend; it does not fabricate generated resolutions or knowledge article references. Knowledge-base/RAG, LLM resolution generation, LangGraph multi-agent orchestration, Jira and email integrations are not exposed by the supplied backend API yet. The sidebar labels for not-yet-implemented modules show a notice rather than pretending those features work.

CSV upload requires `description` and `email`; `subject`, `department`, and `name` are optional. The current backend permits these status transitions: Open → Classified → In Progress → Resolved → Closed.


## Milestone 2 — Role D frontend

The frontend now includes a Knowledge base workspace and an AI resolution panel in each ticket detail drawer.

- Knowledge base: article browsing, category filtering, `/kb/search`, and an article reader.
- RAG metrics: knowledge article count, generated responses, average confidence, human-review rate, and average response latency from `/rag/stats`.
- Ticket resolution: generate/regenerate via `POST /tickets/{ticket_id}/resolve`, copy the suggested reply, inspect retrieved articles and relevance, numbered steps, sources, confidence, human-review guidance, and the four-stage execution trace.
- Loading, empty, and error states are included.
- To preview the Milestone 2 UI without the API, set `USE_MOCKS = true` near the top of `src/App.jsx`. It defaults to `false` and uses the real backend.

### Run locally

From `frontend/` run `npm install` and `npm run dev`. Start the FastAPI backend separately using the instructions in the repository README. Set `VITE_API_URL` if the backend is not at `http://localhost:8000`.

No demo credentials or login IDs are embedded in the frontend.
