# Knowledge Base 22: JVM Backend Foundations (Java/Kotlin) for Product Development (Dev)
> **Module ID**: `22_java_kotlin_backend_foundations`
> **Prerequisites**: 00b_functions_and_scope, 19_deployment_and_ci_cd (recommended)
> **Estimated Time**: 60 Minutes
> **Tier**: 2–3 (Intermediate→Advanced)

---

## 1. Universal Concept: Strong Contracts + Concurrency Control

Product-development backends (platform teams) tend to optimize for:
- **stable contracts** (types, APIs, compatibility)
- **predictable concurrency** (threading/executors, cancellation/timeouts, backpressure)
- **operational determinism** (build artifacts, reproducible builds, CI gates)

The JVM family (Java/Kotlin) is a common fit because it combines:
- a mature runtime (JVM) with well-defined performance/GC behavior,
- a massive ecosystem (libraries, tooling, observability),
- strong type systems (compile-time validation for large codebases).

---

## 2. Technical Explanation: Minimal Service Boundary + Controlled Concurrency

### A) Java 21: request handling + executor + time budget

Below is a minimal example that demonstrates a service boundary and concurrency control primitives that scale better than “spawn a thread per request”.

```java
import com.sun.net.httpserver.HttpServer;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.concurrent.*;

public final class MiniService {
  private static final Duration REQUEST_TIMEOUT = Duration.ofMillis(200);

  public static void main(String[] args) throws IOException {
    ExecutorService pool = Executors.newFixedThreadPool(8);

    HttpServer server = HttpServer.create(new InetSocketAddress(8080), 0);
    server.createContext("/healthz", exchange -> {
      byte[] body = "ok".getBytes(StandardCharsets.UTF_8);
      exchange.sendResponseHeaders(200, body.length);
      try (OutputStream os = exchange.getResponseBody()) {
        os.write(body);
      }
    });

    server.createContext("/work", exchange -> {
      Future<String> result = pool.submit(() -> {
        // Simulate CPU / IO work.
        Thread.sleep(50);
        return "done";
      });

      try {
        String bodyStr = result.get(REQUEST_TIMEOUT.toMillis(), TimeUnit.MILLISECONDS);
        byte[] body = bodyStr.getBytes(StandardCharsets.UTF_8);
        exchange.sendResponseHeaders(200, body.length);
        try (OutputStream os = exchange.getResponseBody()) {
          os.write(body);
        }
      } catch (TimeoutException e) {
        result.cancel(true);
        exchange.sendResponseHeaders(504, -1);
      } catch (ExecutionException | InterruptedException e) {
        exchange.sendResponseHeaders(500, -1);
        Thread.currentThread().interrupt();
      } finally {
        exchange.close();
      }
    });

    server.setExecutor(pool);
    server.start();
  }
}
```

핵심 포인트:
- “요청 처리”와 “작업 실행”을 분리하고, 작업은 **Executor**를 통해 제한된 풀에서만 실행.
- `Future.get(timeout)`으로 **시간 예산**을 강제하고, 타임아웃 시 `cancel(true)`로 중단 시도.
- 이 패턴이 확장되면 “큐 길이/거부 정책/리트라이/서킷브레이커” 같은 운영 개념으로 연결됨.

### B) Kotlin: null-safety + algebraic-ish modeling (sealed)

Kotlin은 JVM 위에서 동작하면서도, “nullability”와 “모델링(ADT 스타일)”을 통해 계약을 더 강하게 표현할 수 있음.

```kotlin
sealed interface WorkResult {
  data class Ok(val message: String) : WorkResult
  data class Error(val reason: String) : WorkResult
}

fun parseLimit(raw: String?): Int =
  raw?.toIntOrNull()?.coerceIn(1, 100) ?: 10
```

핵심 포인트:
- `String?`와 같은 타입으로 “null 가능성”을 계약에 포함.
- `sealed interface`로 성공/실패 케이스를 닫힌 집합으로 모델링(런타임 `null`/예외 남발을 줄이는 방향).

---

## 3. Cross-Stack Comparison

| Dimension | Java/Kotlin (JVM) | Go | Python | Node (TS/JS) |
|---|---|---|---|---|
| Type enforcement | compile-time (nominal + generics) | compile-time | runtime (typing optional) | TS compile-time + JS runtime |
| Concurrency primitive | threads, executors, futures (Java 21+: virtual threads option) | goroutines/channels | asyncio tasks | event loop + promises |
| Cancellation/timeout | futures cancel + timeouts, frameworks add contexts | `context.Context` | task cancel + `asyncio.timeout()` | AbortController + timers |
| Build artifact | JAR (often container image) | static binary | wheel/sdist | bundled JS + lockfile |
| Common pitfalls | thread leaks, blocking IO on shared pool, GC pressure | goroutine leaks, shared memory races | runaway tasks, missing timeouts | microtask starvation, blocking CPU on event loop |

---

## 4. Palantir Context (Non-Speculative)

Product Development(Dev/PD)는 Foundry/Gotham/AIP 같은 **플랫폼 자체**를 범용적으로 만들기 때문에:
- 언어/런타임 선택은 “개발 속도”보다 **장기 유지보수/운영 일관성/성능 예측 가능성**의 영향을 크게 받음.
- 빌드/테스트/배포 파이프라인에서 **JVM(Gradle) + TypeScript**가 함께 등장하는 경우가 많아, 프론트엔드라도 JVM 빌드 도구를 읽을 줄 아는 역량이 중요해짐.

근거로 참고 가능한 Palantir 공개 레포 예시:
- Gradle tooling/standards: https://github.com/palantir/gradle-baseline
- Java storage/infra: https://github.com/palantir/atlasdb
- Multi-language API tooling: https://github.com/palantir/conjure

---

## 5. Design Philosophy (Primary Sources)

- Java Language Specification (언어/타입/메모리 모델의 규범): https://docs.oracle.com/javase/specs/
- JEP Index (특히 virtual threads/structured concurrency 관련 JEP): https://openjdk.org/jeps/
- Kotlin Language Documentation (null-safety, sealed, data class 등): https://kotlinlang.org/docs/home.html

---

## 6. Practice Exercise (Interview-Safe)

**Goal:** “제한된 동시성 + 타임아웃 + 정상 종료”를 갖춘 미니 작업 서비스 설계.

**Constraints:**
- 작업 실행은 풀/큐로 제한(무제한 스레드/무제한 태스크 금지)
- 각 요청/작업에 시간 예산을 부여
- graceful shutdown 시 새 요청 차단 + 진행 중 작업 정리

**Acceptance Criteria:**
- 동시에 1,000번 호출해도 프로세스가 폭증하지 않음(스레드/메모리)
- 타임아웃이 동작하고, 실패가 “조용히 무시”되지 않음(명시적 응답/로그)

**Two sizes:**
- 10분: 위 Java 예제에서 `/work`에 timeout + cancel + 504 응답을 더 명확히 만들기
- 30분: in-memory queue + worker pool + shutdown 훅까지 추가하기

---

## 7. Adaptive Next Steps

- JVM을 “운영 관점”으로 더 파고들면: GC/heap, allocation hot spots, thread dump, p99 latency.
- Kotlin을 “계약 관점”으로 더 파고들면: null-safety 설계, sealed 결과 타입, DTO/Domain 분리.
- 빌드/배포까지 연결하면: Gradle task graph, reproducible builds, containerization, rollout/rollback.

