# OpsSight Frontend

React/Vite single-page application for OpsSight.ai. It contains the tenant dashboard, model monitoring pages, incident drawer, remediation approval console, schema registry, Slack integration, report viewer, and real-time notification UI.

## Structure

```text
src/api/          API clients and request helpers
src/components/   Shared UI components
src/hooks/        Reusable React hooks, including live updates
src/layouts/      Application shell and navigation
src/pages/        Route-level feature pages
src/routes/       Protected route wiring
src/store/        Zustand stores for auth and UI state
```

## Commands

```powershell
npm install
npm run dev
npm run build
npm run lint
npm run preview
```

## Production Notes

- Build output in `dist/` and Vite cache in `.vite/` are generated artifacts and should not be committed.
- Keep API URLs and OAuth callback origins environment-driven for each deployment.
- The notification bell and incident pages depend on authenticated API calls plus WebSocket/SSE-style live updates from the backend.
- Build the production container from the repository root so it can copy `deploy/nginx/frontend.conf`:

```powershell
docker build -f frontend/Dockerfile -t opssight/frontend:local .
```
