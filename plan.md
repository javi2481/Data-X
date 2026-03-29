# plan.md

## 1) Objectives
- Build a production-ready **Code Audit Report Viewer** for the Data-X repo.
- Backend (FastAPI) serves the audit report as **versioned JSON** with deep links to GitHub (file + line ranges).
- Frontend (React) renders an **interactive, beautiful** report with filtering, search, severity badges, and code suggestion blocks.
- Ensure the report includes:
  1. Architecture & Structure Analysis
  2. Bug Detection & Vulnerabilities (file + line numbers)
  3. Improvement & Refactoring Opportunities (ready-to-implement code examples)
  4. AI/ML Processing Optimization
  5. Prioritized Action Plan (Critical/Medium/Low)

## 2) Implementation Steps

### Phase 1 — Core Flow POC (Isolation)
**Core = report JSON contract + UI rendering of issues with file/line anchors (no auth).**

User stories:
1. As a user, I can open the app and immediately see a summary of findings by severity.
2. As a user, I can click an issue and jump to the exact GitHub file and line range.
3. As a user, I can read a suggested fix with a copy-ready code snippet.
4. As a user, I can filter issues by severity/category and search by keyword.
5. As a user, I can view AI/ML optimization items separately from security/bugs.

Steps:
1. Define `AuditReport` JSON schema (Pydantic) with: metadata (repo, commit), sections, issues, actions.
2. Hardcode the **already-produced analysis** into a single `report_v1.json` (no mock “fake” data; only real findings already identified).
3. Create FastAPI endpoint `GET /api/report` returning the JSON.
4. Create minimal React page that:
   - fetches `/api/report`
   - renders: severity counts + issues list
   - supports deep-link buttons to GitHub: `https://github.com/javi2481/data-x/blob/main/{path}#L{start}-L{end}`
5. POC test: run backend+frontend locally; verify rendering + links + copy-to-clipboard for code blocks.
6. Fix until stable: validate JSON parsing, empty states, loading/error handling.

### Phase 2 — V1 App Development (MVP)

User stories:
1. As a user, I can navigate between the 5 report sections via a left sidebar.
2. As a user, I can expand/collapse each issue and see evidence + impact + recommendation.
3. As a user, I can view “Critical” items first and export the action plan as Markdown.
4. As a user, I can compare categories (Security vs Reliability vs Performance vs AI/ML) through charts.
5. As a user, I can view refactor proposals with diffs (before/after) and rationale.

Backend (FastAPI):
1. Create `app/main.py` for this new audit-viewer API (separate from Data-X; new service).
2. Add models:
   - `Issue {id, title, severity, category, description, impact, file, line_start, line_end, references[], suggested_fix{summary, code, notes}, tags[]}`
   - `Section {key, title, content_markdown, issues[]}`
   - `ActionPlan {critical[], medium[], low[]}`
3. Endpoints:
   - `GET /api/report` (full)
   - `GET /api/report/summary` (counts, top issues)
   - `GET /api/report/issues?severity=&category=&q=`
   - `GET /api/report/export.md` (server-side Markdown export)
4. Add CORS + gzip + cache headers (ETag) for report payload.

Frontend (React):
1. Use React + TypeScript + Tailwind + shadcn/ui for consistent, polished UI.
2. Layout:
   - Left nav: sections
   - Main: section content + issue cards
   - Right drawer: filters (severity, category, tags)
3. Components:
   - `SeverityBadge`, `IssueCard`, `CodeBlock` (copy), `GitHubLink`, `ActionPlanBoard`
   - `SearchBar` with debounced filtering
4. Visualizations:
   - Severity distribution (bar)
   - Category distribution (donut)
5. UX states:
   - skeleton loading
   - empty results
   - API error with retry

Conclude Phase 2:
- Run 1 end-to-end test pass: load app → browse sections → filter/search → open issue → open GitHub link → export Markdown.

### Phase 3 — Production Hardening + Content Deepening

User stories:
1. As a user, I can pin/share a direct URL to a specific issue.
2. As a user, I can switch between report versions (e.g., `v1`, `v2`) safely.
3. As a user, I can download the full report JSON for offline review.
4. As a user, I can view “AI/ML optimization” recommendations grouped by cost/latency impact.
5. As a user, I can see a “Fix ROI” score per recommendation to prioritize.

Steps:
1. Add routing for deep links: `/issues/:id`, `/sections/:key`.
2. Add report versioning: `GET /api/report?version=v1`.
3. Add basic observability:
   - backend request logs + timings
   - frontend error boundary + Sentry-ready hooks (optional).
4. Expand report content to include:
   - architecture diagram (static SVG)
   - refactor diffs for top criticals
   - AI/ML optimization checklist (caching, persistence, batching, timeouts)
5. Add lightweight CI checks: formatting/lint + typecheck.

### Phase 4 — Optional Enhancements (Ask before adding auth)

User stories:
1. As a user, I can restrict report access to my team.
2. As a user, I can leave comments on issues.
3. As a user, I can track which issues are fixed/accepted/ignored.
4. As a user, I can generate a new report from a different commit.
5. As a user, I can compare reports between commits.

Steps:
1. If needed, add JWT auth + roles (viewer/editor).
2. Add persistence (MongoDB) for comments/statuses (report itself remains static JSON).
3. Add “report diff” view (two versions).

## 3) Next Actions (Immediate)
1. Create `report_v1.json` from the current analysis (include the provided critical/high/medium/low items with file+line ranges).
2. Scaffold the audit-viewer backend (FastAPI) with `/api/report`.
3. Scaffold the frontend React app with the report page + issue cards + GitHub line links.
4. Validate POC end-to-end locally.

## 4) Success Criteria
- App loads and renders the complete audit report with all 5 required sections.
- Every bug/vulnerability includes **file + line numbers** and a working GitHub link.
- Refactor recommendations include **copy-ready code examples**.
- AI/ML optimization section clearly addresses embeddings/FAISS/LLM caching/persistence/timeouts.
- Action plan is prioritized (Critical/Medium/Low) and exportable as Markdown.
- No auth required for v1; UX is polished with search/filter, loading/error states, and deep links.
