# Knowledge Base 20: Go Services & Concurrency (Role: FDE/Deployment Strategist)
> **Module ID**: `20_go_services_and_concurrency`
> **Prerequisites**: 00a_programming_fundamentals, 00b_functions_and_scope
> **Estimated Time**: 45 Minutes
> **Tier**: 2–3 (Intermediate→Advanced)

---

## 1. Universal Concept: Composition + Concurrency Safety

Go encourages:
- **composition over inheritance** (small interfaces, explicit wiring)
- **concurrency as a first-class tool**, but with explicit communication (channels) and lifecycle control (contexts)

---

## 2. Technical Explanation: Minimal HTTP Service

```go
package main

import (
  "context"
  "log"
  "net/http"
  "time"
)

func main() {
  mux := http.NewServeMux()
  mux.HandleFunc("/healthz", func(w http.ResponseWriter, _ *http.Request) {
    w.WriteHeader(http.StatusOK)
    _, _ = w.Write([]byte("ok"))
  })

  srv := &http.Server{
    Addr:              ":8080",
    Handler:           mux,
    ReadHeaderTimeout: 5 * time.Second,
  }

  go func() {
    log.Fatal(srv.ListenAndServe())
  }()

  // In real systems: wait for signal, then graceful shutdown with context.
  ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
  defer cancel()
  _ = srv.Shutdown(ctx)
}
```

Key ideas:
- `http.Server` is the service boundary.
- `go func(){...}()` starts concurrency (goroutine).
- `context.Context` is the cancellation/timeout propagation mechanism.

---

## 3. Cross-Stack Comparison

| Concept | Go | Python | Node (TS/JS) |
|---|---|---|---|
| Concurrency primitive | goroutine/channel | `asyncio` tasks | event loop + promises |
| Cancellation | `context.Context` | `asyncio.timeout()` / cancel tasks | abort controller / custom |
| Server | `net/http` | FastAPI/Flask | Express/Fastify |

---

## 4. Palantir Context (Interview-Relevant, Non-Speculative)

For “service thinking” interviews, expect questions like:
- how to structure packages for maintainability
- what a graceful shutdown is and why it matters
- how to propagate timeouts and handle backpressure

---

## 5. Design Philosophy (Primary Sources)

- Go specification (language fundamentals): https://go.dev/ref/spec  
- Effective Go (style, idioms): https://go.dev/doc/effective_go  
- Go blog (documentation hub): https://go.dev/doc/

---

## 6. Practice Exercise

1) Add `/readyz` endpoint that depends on a downstream dependency (simulated).
2) Add request timeouts and log when a request exceeds a budget.
3) Add a worker goroutine pool for background jobs and shut it down cleanly.

---

## 7. Adaptive Next Steps

- If you need **gRPC** → learn proto-first APIs and interceptors.
- If you need **performance** → learn `pprof`, allocations, and contention.
- If you need **reliability** → learn timeouts, retries, and circuit breaking patterns.

