# Nginx Runtime Config

`frontend.conf` is copied into the production frontend container by
`frontend/Dockerfile`.

Build the frontend image from the repository root:

```powershell
docker build -f frontend/Dockerfile -t opssight/frontend:local .
```

This keeps React/Vite source files in `frontend/` and runtime web-server config
in `deploy/`.
