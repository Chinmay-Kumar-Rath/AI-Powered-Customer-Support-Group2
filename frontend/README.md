# SupportPilot – Role D Final Frontend

This React + Vite frontend combines the supplied Milestone 1/2/3 backend capabilities into a single role-aware application.

## Run

```bash
cd frontend
npm install
copy .env.example .env   # Windows
npm run dev
```

The backend should be running at `http://localhost:8000` (or set `VITE_API_URL`).

## Frontend coverage

- One `apiFetch` wrapper for every request; bearer Authorization is added in one place and 401 clears the session and returns the user to login.
- React Router + AuthContext + protected role routes.
- Employee login, registration, logout and dashboard.
- My tickets with status/category/priority filters and search.
- Create ticket and backend classification result.
- Ticket detail: category, sub-category, severity, priority, both confidence values, processing time, status badge, four-step RAG trace, retrieved articles/relevance, generated answer, numbered steps, sources, confidence badge, human-review banner, Regenerate and Copy Reply.
- Status history from `/tickets/{id}/history`.
- “Did this fix it?” with Yes/No, 1–5 rating and comment. The form is shown when the backend allows feedback (`Awaiting User` or `Resolved`).
- Escalation status, engineer, team, due time and Jira field. Jira is shown as unavailable because the supplied backend `EscalationOut` has no Jira reference field.
- Knowledge Base search/filter/viewer and RAG metrics.
- Staff/admin stats and ticket operations, including CSV import.
- Bell notification integration calls `GET /notifications`. The supplied backend currently returns 404 for that route, so the UI falls back to recent ticket activity without changing the backend.
- Loading, empty, error, toast and responsive/mobile states.
- `src/mocks.js` and `USE_MOCKS=false` document the Milestone 2 mock-first switch; Milestone 3 uses live backend data.

## Testing/report assets

See the repository-level `testing/` directory for the 100-ticket held-out test set, API evaluation script, fresh-50 runner and failure handoff. See `docs/person4_report.md` and `docs/demo_script_2_3_minutes.md` for the report/demo structure.
