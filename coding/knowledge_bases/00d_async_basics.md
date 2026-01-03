# Knowledge Base 00d: Async Basics
> **Module ID**: `00d_async_basics`
> **Prerequisites**: 00b_functions_and_scope
> **Estimated Time**: 35 Minutes
> **Tier**: 1 (Beginner)

---

## 1. Universal Concept: Non-Blocking Execution

**Synchronous**: Tasks execute one at a time, in order.
**Asynchronous**: Tasks can start, wait, and complete independently.

**Analogy**: 
- Sync = Waiting in line at a coffee shop
- Async = Ordering via app, doing other things, picking up when ready

---

## 2. Why Async?

```javascript
// ❌ Blocking (synchronous)
const data = fetchDataSync();  // UI freezes for 3 seconds
console.log(data);

// ✅ Non-blocking (asynchronous)
fetchDataAsync()
    .then(data => console.log(data));  // UI stays responsive
```

**JavaScript is single-threaded** — it can only do one thing at a time. Async allows long operations (network, file I/O) to run "in the background" without blocking.

---

## 3. Callbacks (The Old Way)

```javascript
// Callback pattern
function loadData(callback) {
    setTimeout(() => {
        callback("Data loaded!");
    }, 1000);
}

loadData((result) => {
    console.log(result);  // "Data loaded!" after 1 second
});
```

### Callback Hell
```javascript
// Deeply nested callbacks - hard to read/maintain
loadUser(userId, (user) => {
    loadPosts(user.id, (posts) => {
        loadComments(posts[0].id, (comments) => {
            console.log(comments);  // 😱
        });
    });
});
```

---

## 4. Promises (The Better Way)

A **Promise** represents a value that may be available now, later, or never.

### Creating Promises
```javascript
const promise = new Promise((resolve, reject) => {
    setTimeout(() => {
        const success = true;
        if (success) {
            resolve("Data loaded!");
        } else {
            reject(new Error("Failed to load"));
        }
    }, 1000);
});
```

### Using Promises
```javascript
promise
    .then(result => console.log(result))
    .catch(error => console.error(error))
    .finally(() => console.log("Done"));
```

### Promise Chaining
```javascript
loadUser(userId)
    .then(user => loadPosts(user.id))
    .then(posts => loadComments(posts[0].id))
    .then(comments => console.log(comments))
    .catch(error => console.error(error));
```

---

## 5. Async/Await (The Best Way)

Syntactic sugar over Promises — looks synchronous, runs asynchronously.

```javascript
async function fetchUserData(userId) {
    try {
        const user = await loadUser(userId);
        const posts = await loadPosts(user.id);
        const comments = await loadComments(posts[0].id);
        return comments;
    } catch (error) {
        console.error(error);
    }
}
```

### TypeScript Async Functions
```typescript
async function fetchData(): Promise<string> {
    const response = await fetch("/api/data");
    const data = await response.json();
    return data.message;
}
```

---

## 6. Promise Static Methods

```javascript
const p1 = Promise.resolve(1);
const p2 = Promise.resolve(2);
const p3 = Promise.resolve(3);

// All must succeed
Promise.all([p1, p2, p3])
    .then(results => console.log(results));  // [1, 2, 3]

// First to settle (succeed or fail)
Promise.race([p1, p2, p3])
    .then(result => console.log(result));  // 1 (fastest)

// All settled (ES2020)
Promise.allSettled([p1, Promise.reject("error")])
    .then(results => console.log(results));
// [{status: "fulfilled", value: 1}, {status: "rejected", reason: "error"}]
```

---

## 7. Error Handling

```javascript
// With .catch()
fetchData()
    .then(data => process(data))
    .catch(error => {
        console.error("Error:", error.message);
    });

// With try/catch (async/await)
async function example() {
    try {
        const data = await fetchData();
        return process(data);
    } catch (error) {
        console.error("Error:", error.message);
        return null;
    }
}
```

---

## 8. Common Patterns

### Parallel Execution
```javascript
async function parallel() {
    // Start all at once
    const [users, posts, comments] = await Promise.all([
        fetchUsers(),
        fetchPosts(),
        fetchComments()
    ]);
    return { users, posts, comments };
}
```

### Sequential Execution
```javascript
async function sequential() {
    const user = await fetchUser(1);
    const posts = await fetchPosts(user.id);  // Needs user first
    return posts;
}
```

### Timeout
```javascript
function withTimeout(promise, ms) {
    const timeout = new Promise((_, reject) =>
        setTimeout(() => reject(new Error("Timeout")), ms)
    );
    return Promise.race([promise, timeout]);
}

withTimeout(fetch("/api/slow"), 5000)
    .catch(error => console.log(error.message));  // "Timeout"
```

---

## 9. Practice Exercises

### Exercise 1: Retry Logic
Implement a function that retries a failed async operation.

```typescript
async function retry<T>(
    fn: () => Promise<T>,
    maxAttempts: number
): Promise<T> {
    // TODO: Retry up to maxAttempts times
}

// Usage
await retry(() => fetch("/api/unstable"), 3);
```

### Exercise 2: Rate Limiter
Process items with a delay between each.

```typescript
async function rateLimit<T, R>(
    items: T[],
    fn: (item: T) => Promise<R>,
    delayMs: number
): Promise<R[]> {
    // TODO: Process with delay
}
```

---

## 10. Palantir Context

**OSDK Client** uses async/await for all API calls:

```typescript
// Fetching Ontology objects
const users = await client.ontology.objects.list("User");

// Applying actions
await client.ontology.actions.apply("createUser", { name: "Alice" });
```

**React Query** (used in Foundry) provides hooks for async data:
```typescript
const { data, isLoading, error } = useQuery("users", fetchUsers);
```

---

## 11. Adaptive Next Steps

- **If you understood this module**: Proceed to [00e_typescript_intro.md](./00e_typescript_intro.md) for TypeScript fundamentals.
- **If you need more practice**: Implement the retry exercise.
- **For deeper exploration**: Read about the [Event Loop](https://developer.mozilla.org/en-US/docs/Web/JavaScript/EventLoop).
