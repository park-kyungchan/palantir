# Knowledge Base 00b: Functions and Scope
> **Module ID**: `00b_functions_and_scope`
> **Prerequisites**: 00a_programming_fundamentals
> **Estimated Time**: 25 Minutes
> **Tier**: 1 (Beginner)

---

## 1. Universal Concept: Abstraction and Encapsulation

Functions are the fundamental unit of **abstraction**:
- **Abstraction**: Hide complexity behind a simple interface
- **Encapsulation**: Bundle related code together

**Analogy**: A function is like a machine. You put inputs in, it does work, and outputs a result. You don't need to know how it works inside.

---

## 2. Function Basics

### Declaring Functions
```javascript
// Function Declaration (hoisted)
function greet(name) {
    return `Hello, ${name}!`;
}

// Function Expression (not hoisted)
const greet2 = function(name) {
    return `Hello, ${name}!`;
};

// Arrow Function (ES6+)
const greet3 = (name) => `Hello, ${name}!`;

// Calling a function
console.log(greet("Alice"));  // "Hello, Alice!"
```

### TypeScript Typed Functions
```typescript
// Explicit parameter and return types
function add(a: number, b: number): number {
    return a + b;
}

// Arrow function with types
const multiply = (a: number, b: number): number => a * b;

// Type error prevention
add("1", 2);  // ERROR: Argument of type 'string' is not assignable to type 'number'
```

**Palantir Context**: All OSDK functions are strictly typed. This prevents production errors like passing a string where a number is expected.

---

## 3. Parameters and Arguments

### Required vs Optional Parameters
```typescript
// Required parameter
function required(name: string): string {
    return `Hello, ${name}`;
}

// Optional parameter (?)
function optional(name?: string): string {
    return `Hello, ${name ?? "Guest"}`;
}

// Default parameter
function withDefault(name: string = "Guest"): string {
    return `Hello, ${name}`;
}

optional();           // "Hello, Guest"
withDefault();        // "Hello, Guest"
withDefault("Alice"); // "Hello, Alice"
```

### Rest Parameters
```typescript
// Accept any number of arguments
function sum(...numbers: number[]): number {
    return numbers.reduce((acc, n) => acc + n, 0);
}

sum(1, 2, 3);       // 6
sum(1, 2, 3, 4, 5); // 15
```

---

## 4. Scope: Where Variables Live

### Global Scope
```javascript
// Available everywhere (avoid if possible)
var globalVar = "I'm global";

function example() {
    console.log(globalVar);  // Accessible here
}
```

### Function Scope
```javascript
function example() {
    var localVar = "I'm local";
    console.log(localVar);  // OK
}

// console.log(localVar);  // ERROR: localVar is not defined
```

### Block Scope (let/const)
```javascript
if (true) {
    let blockScoped = "Inside block";
    const alsoBlockScoped = "Also inside";
}

// console.log(blockScoped);  // ERROR: not accessible outside block
```

### Cross-Stack Comparison
| Scope Type | JavaScript | Python | Java |
|------------|------------|--------|------|
| Global | `var` (avoid) | Module level | `static` field |
| Function | `var`, `let`, `const` | Function local | Method local |
| Block | `let`, `const` | ❌ (no block scope) | `{}` block |

---

## 5. Closures: Functions Remember

A **closure** is a function that "remembers" variables from its outer scope.

```javascript
function createCounter() {
    let count = 0;  // Private variable
    
    return function() {
        count++;    // Accesses outer variable
        return count;
    };
}

const counter = createCounter();
console.log(counter());  // 1
console.log(counter());  // 2
console.log(counter());  // 3

// count is NOT directly accessible
// console.log(count);  // ERROR
```

### Practical Example: Event Handler Factory
```javascript
function createButtonHandler(buttonId) {
    return function() {
        console.log(`Button ${buttonId} clicked!`);
    };
}

const handleBtn1 = createButtonHandler(1);
const handleBtn2 = createButtonHandler(2);

handleBtn1();  // "Button 1 clicked!"
handleBtn2();  // "Button 2 clicked!"
```

**Palantir Context**: React hooks like `useState` and `useEffect` rely on closures. Understanding closures is essential for debugging "stale closure" bugs in Foundry UI development.

---

## 6. Higher-Order Functions

Functions that take functions as arguments or return functions.

```javascript
// Function as argument
function executeWithLogging(fn, arg) {
    console.log(`Calling with: ${arg}`);
    const result = fn(arg);
    console.log(`Result: ${result}`);
    return result;
}

const double = (x) => x * 2;
executeWithLogging(double, 5);
// "Calling with: 5"
// "Result: 10"
```

### Common Higher-Order Functions
```javascript
const numbers = [1, 2, 3, 4, 5];

// map: transform each element
numbers.map(n => n * 2);  // [2, 4, 6, 8, 10]

// filter: keep matching elements
numbers.filter(n => n > 2);  // [3, 4, 5]

// find: get first match
numbers.find(n => n > 3);  // 4

// every: check all match
numbers.every(n => n > 0);  // true

// some: check any match
numbers.some(n => n > 4);  // true
```

---

## 7. Pure Functions

A **pure function**:
1. Always returns the same output for the same input
2. Has no side effects (doesn't modify external state)

```javascript
// ✅ Pure function
function add(a, b) {
    return a + b;
}

// ❌ Impure function (modifies external state)
let total = 0;
function addToTotal(n) {
    total += n;  // Side effect!
    return total;
}
```

**Why Pure Functions Matter**:
- Easier to test
- Easier to reason about
- Can be safely cached (memoization)
- Essential for React (components should be pure)

---

## 8. Practice Exercises

### Exercise 1: Currying
Transform a multi-argument function into a chain of single-argument functions.

```typescript
// Regular function
function add(a: number, b: number): number {
    return a + b;
}

// TODO: Convert to curried form
function curriedAdd(a: number): (b: number) => number {
    // Implement here
}

// Usage
const add5 = curriedAdd(5);
console.log(add5(3));  // 8
console.log(add5(10)); // 15
```

### Exercise 2: Memoization
Create a function that caches results for expensive operations.

```typescript
function memoize<T, R>(fn: (arg: T) => R): (arg: T) => R {
    const cache = new Map<T, R>();
    
    return function(arg: T): R {
        // TODO: Check cache first, compute if not found
    };
}

// Usage
const expensiveSquare = memoize((n: number) => {
    console.log("Computing...");
    return n * n;
});

expensiveSquare(4);  // "Computing..." -> 16
expensiveSquare(4);  // (no log, from cache) -> 16
```

---

## 9. Design Philosophy

> **"Functions should do one thing. They should do it well. They should do it only."**
> — Robert C. Martin, *Clean Code*

> **"The function of good software is to make the complex appear to be simple."**
> — Grady Booch

---

## 10. Adaptive Next Steps

- **If you understood this module**: Proceed to [00c_data_structures_intro.md](./00c_data_structures_intro.md) to learn about arrays, objects, and collections.
- **If you need more practice**: Implement the currying and memoization exercises.
- **For deeper exploration**: Read about [JavaScript execution context](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/this) to understand `this` binding.
