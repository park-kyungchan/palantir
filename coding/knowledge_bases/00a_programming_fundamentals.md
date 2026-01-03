# Knowledge Base 00a: Programming Fundamentals
> **Module ID**: `00a_programming_fundamentals`
> **Prerequisites**: None (Complete Beginner)
> **Estimated Time**: 30 Minutes
> **Tier**: 1 (Beginner)

---

## 1. Universal Concept: Data and Instructions

Programming is fundamentally about two things:
1. **Data** - Information stored in memory (numbers, text, etc.)
2. **Instructions** - Commands that transform data

**Analogy**: Think of a recipe. Ingredients = Data, Steps = Instructions.

---

## 2. Variables: Named Containers

A **variable** is a named container that holds a value.

### JavaScript/TypeScript
```javascript
// Declaring variables
let age = 25;           // Can change later
const name = "Alice";   // Cannot change (constant)
var legacy = "old";     // Avoid - old syntax

// Reassignment
age = 26;  // OK
// name = "Bob";  // ERROR - const cannot be reassigned
```

### Python
```python
# Python uses dynamic typing
age = 25
name = "Alice"

# Reassignment (all allowed)
age = 26
name = "Bob"
```

### Cross-Stack Comparison
| Feature | JavaScript | Python | Java |
|---------|------------|--------|------|
| Mutable | `let` | `variable = value` | `int x = 5;` |
| Immutable | `const` | Convention only | `final int x = 5;` |
| Type Declaration | Optional (TS) | No | Required |

---

## 3. Data Types: Categories of Data

### Primitive Types
| Type | JavaScript Example | Python Example | Meaning |
|------|-------------------|----------------|---------|
| **Number** | `42`, `3.14` | `42`, `3.14` | Integers, decimals |
| **String** | `"hello"` | `"hello"` | Text |
| **Boolean** | `true`, `false` | `True`, `False` | Yes/No |
| **Null/None** | `null`, `undefined` | `None` | No value |

### TypeScript Type Annotations
```typescript
// Explicit type declaration
let age: number = 25;
let name: string = "Alice";
let isActive: boolean = true;

// TypeScript prevents type errors at compile time
age = "twenty-five";  // ERROR: Type 'string' is not assignable to type 'number'
```

**Palantir Context**: TypeScript's type system is foundational to Palantir's OSDK. Every Ontology object has strictly typed properties, preventing runtime errors in production.

---

## 4. Operators: Transforming Data

### Arithmetic Operators
```javascript
let a = 10, b = 3;

console.log(a + b);   // 13  (Addition)
console.log(a - b);   // 7   (Subtraction)
console.log(a * b);   // 30  (Multiplication)
console.log(a / b);   // 3.33... (Division)
console.log(a % b);   // 1   (Modulo - remainder)
console.log(a ** b);  // 1000 (Exponentiation)
```

### Comparison Operators
```javascript
let x = 5;

console.log(x === 5);   // true  (Strict equality)
console.log(x !== 5);   // false (Strict inequality)
console.log(x > 3);     // true
console.log(x <= 5);    // true

// IMPORTANT: Always use === instead of ==
console.log("5" == 5);   // true  (Type coercion - dangerous!)
console.log("5" === 5);  // false (Type-safe comparison)
```

### Logical Operators
```javascript
let a = true, b = false;

console.log(a && b);  // false (AND - both must be true)
console.log(a || b);  // true  (OR - at least one true)
console.log(!a);      // false (NOT - invert)
```

---

## 5. Conditionals: Making Decisions

### if/else Statement
```javascript
let score = 85;

if (score >= 90) {
    console.log("A");
} else if (score >= 80) {
    console.log("B");  // This runs
} else if (score >= 70) {
    console.log("C");
} else {
    console.log("F");
}
```

### Ternary Operator (Shorthand)
```javascript
let age = 20;
let status = age >= 18 ? "Adult" : "Minor";
// status = "Adult"
```

### TypeScript Pattern Matching
```typescript
type Status = "active" | "inactive" | "pending";

function getColor(status: Status): string {
    switch (status) {
        case "active":
            return "green";
        case "inactive":
            return "gray";
        case "pending":
            return "yellow";
    }
}
```

---

## 6. Loops: Repeating Actions

### for Loop
```javascript
// Print numbers 0-4
for (let i = 0; i < 5; i++) {
    console.log(i);
}

// Iterate over array
const fruits = ["apple", "banana", "cherry"];
for (const fruit of fruits) {
    console.log(fruit);
}
```

### while Loop
```javascript
let count = 0;
while (count < 5) {
    console.log(count);
    count++;
}
```

### Array Methods (Functional Style)
```javascript
const numbers = [1, 2, 3, 4, 5];

// Transform each element
const doubled = numbers.map(n => n * 2);
// [2, 4, 6, 8, 10]

// Filter elements
const evens = numbers.filter(n => n % 2 === 0);
// [2, 4]

// Reduce to single value
const sum = numbers.reduce((acc, n) => acc + n, 0);
// 15
```

**Palantir Context**: Functional array methods (`map`, `filter`, `reduce`) are heavily used in Blueprint UI components for data transformation before rendering.

---

## 7. Practice Exercises

### Exercise 1: FizzBuzz (Classic)
Write a program that prints numbers 1-100. For multiples of 3, print "Fizz". For multiples of 5, print "Buzz". For multiples of both, print "FizzBuzz".

```javascript
// Starter Code
for (let i = 1; i <= 100; i++) {
    // TODO: Implement FizzBuzz logic
}
```

### Exercise 2: Temperature Converter
Create a function that converts Celsius to Fahrenheit.
Formula: F = C × 9/5 + 32

```typescript
function celsiusToFahrenheit(celsius: number): number {
    // TODO: Implement conversion
}

// Test
console.log(celsiusToFahrenheit(0));   // 32
console.log(celsiusToFahrenheit(100)); // 212
```

---

## 8. Design Philosophy

> **"Programs must be written for people to read, and only incidentally for machines to execute."**
> — Harold Abelson, *Structure and Interpretation of Computer Programs*

> **"Make it work, make it right, make it fast."**
> — Kent Beck

**Palantir Interview Relevance**: Interviewers test fundamental understanding. Can you explain *why* `===` is preferred over `==`? Can you articulate the trade-offs of `const` vs `let`?

---

## 9. Adaptive Next Steps

- **If you understood this module**: Proceed to [00b_functions_and_scope.md](./00b_functions_and_scope.md) to learn about functions, parameters, and scope.
- **If you need more practice**: Try building a simple calculator that takes two numbers and an operator, then returns the result.
- **For deeper exploration**: Read [MDN JavaScript Guide](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide) for the official reference.
