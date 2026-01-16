# Knowledge Base 21: Python Backend & Async Patterns (Role: FDE/Deployment Strategist)
> **Module ID**: `21_python_backend_async`
> **Prerequisites**: 00d_async_basics
> **Estimated Time**: 45 Minutes
> **Tier**: 2–3 (Intermediate→Advanced)

---

## 1. Universal Concept: Structured Concurrency + Resource Ownership

Async systems break when:
- cancellation is ignored
- timeouts are missing
- resources (connections, file handles) outlive the request that created them

The universal goal is **structured concurrency**:
“spawned work must be owned by a scope and cleaned up predictably”.

---

## 2. Technical Explanation: Async I/O + Timeouts

```python
import asyncio


async def fetch_one(n: int) -> int:
    await asyncio.sleep(0.01)
    return n


async def main() -> None:
    async with asyncio.timeout(1.0):
        results = await asyncio.gather(*(fetch_one(i) for i in range(10)))
        print(sum(results))


if __name__ == "__main__":
    asyncio.run(main())
```

Key ideas:
- `asyncio.run()` is the entrypoint boundary.
- `asyncio.timeout()` (Py 3.11+) enforces time budgets.
- `asyncio.gather()` aggregates tasks; failure semantics must be chosen intentionally.

---

## 3. Cross-Stack Comparison

| Concept | Python | Go | Node (TS/JS) |
|---|---|---|---|
| Async primitive | task/coroutine | goroutine | promise |
| Timeout | `asyncio.timeout()` | `context.WithTimeout()` | `AbortController` + timers |
| Cancellation | task cancel | context cancel | abort signal |

---

## 4. Palantir Context (Interview-Relevant, Non-Speculative)

Common interview probes:
- how you prevent “runaway” async tasks
- how you design timeouts and retries
- how you debug production async issues (logs, traces, metrics)

---

## 5. Design Philosophy (Primary Sources)

- Python `asyncio` documentation: https://docs.python.org/3/library/asyncio.html  
- `asyncio.timeout` reference: https://docs.python.org/3/library/asyncio-task.html#asyncio.timeout  
- Python packaging overview (deployment relevance): https://packaging.python.org/

---

## 6. Practice Exercise

1) Write an async “fan-out/fan-in” function with a concurrency limit.
2) Add per-task timeouts and a global timeout.
3) Decide and document: fail-fast vs best-effort semantics.

---

## 7. Adaptive Next Steps

- If you need **web services** → learn ASGI servers and request lifecycles.
- If you need **typing** → learn `typing.Protocol`, generics, and mypy/pyright workflows.
- If you need **deployment** → learn container images and dependency pinning.

