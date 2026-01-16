# Knowledge Base 19: Deployment & CI/CD Foundations (Role: Deployment Strategist)
> **Module ID**: `19_deployment_and_ci_cd`
> **Prerequisites**: 00a_programming_fundamentals, 07_version_control
> **Estimated Time**: 45 Minutes
> **Tier**: 3 (Advanced)

---

## 1. Universal Concept: Reproducibility Under Constraints

Deployment is the practice of turning *source code* into a **repeatable, auditable, environment-specific** running system.

The core idea:
- **Build** produces immutable artifacts (binaries/images/packages).
- **Release** selects artifacts + config for an environment.
- **Deploy** applies the release safely (progressive rollout, rollback).

---

## 2. Technical Explanation: The Minimal Pipeline

### A. Artifact identity
- Pin dependencies (lockfiles, modules).
- Produce a unique artifact identifier (image digest, build metadata).

### B. CI (verification)
- Lint + unit tests + typecheck
- Integration tests behind feature flags or ephemeral envs

### C. CD (delivery)
- Progressive delivery: canary / blue-green
- Rollback strategy: re-deploy previous artifact digest

---

## 3. Cross-Stack Comparison

| Concern | Python | Go | TS/JS (Node) |
|---|---|---|---|
| Build artifact | wheel/sdist | static binary | bundled JS + lockfile |
| Dependency pinning | `requirements.lock`/`uv.lock`/poetry | `go.sum` | `package-lock.json`/`pnpm-lock.yaml` |
| Typical runtime | container or venv | container or VM | container or serverless |
| Health checks | HTTP endpoints | HTTP endpoints | HTTP endpoints |

---

## 4. Palantir Context (Interview-Relevant, Non-Speculative)

Deployment Strategist / FDE interview loops commonly probe:
- deterministic builds, rollback plans, incident mitigation
- CI pipeline design and what you gate on (tests vs. deployment stages)
- how to reason about changes in a monorepo with mixed languages

---

## 5. Design Philosophy (Primary Sources)

- GitHub Actions documentation (workflow model, runners, job/step semantics):  
  https://docs.github.com/en/actions
- Dockerfile reference (image build primitives, `RUN`/`CMD`/`ENTRYPOINT`):  
  https://docs.docker.com/engine/reference/builder/
- Kubernetes concepts (desired state, controllers, rollout objects):  
  https://kubernetes.io/docs/concepts/

---

## 6. Practice Exercise (Repo-Agnostic)

Given a mixed repo (Python + Go + TS):
1) Identify the build entrypoints: `package.json scripts`, `pyproject.toml [project.scripts]`, `go.mod`, `Dockerfile`, `.github/workflows/*`.
2) Define a CI workflow:
   - TS: `npm ci && npm test`
   - Python: `python -m pytest`
   - Go: `go test ./...`
3) Define a CD workflow:
   - Build Docker image and push by digest
   - Deploy a canary with 10% traffic
   - Roll back on error budget regression

---

## 7. Adaptive Next Steps

- If you care about **rollouts/rollback** → learn canary vs blue-green, health checks, SLOs.
- If you care about **monorepo scaling** → learn change detection, build caching, hermetic builds.
- If you care about **incident response** → learn observability signals and safe deploy patterns.

