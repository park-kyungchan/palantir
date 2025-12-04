---
description: Build and deploy the application
---
1. Verify that all tests have passed (Manual confirmation or check previous step).
2. Build the production artifacts.
// turbo
3. Run `cd math && docker compose build`
4. Deploy the services.
// turbo
5. Run `cd math && docker compose up -d`
6. Perform a final health check.
// turbo
7. Run `curl -f http://localhost:8000/health || echo "Backend Health Check Failed"`
