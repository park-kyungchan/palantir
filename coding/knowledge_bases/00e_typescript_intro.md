# Knowledge Base 00e: TypeScript Introduction
> **Module ID**: `00e_typescript_intro`
> **Prerequisites**: 00a_programming_fundamentals, 00b_functions_and_scope
> **Estimated Time**: 40 Minutes
> **Tier**: 1 (Beginner)

---

## 1. Universal Concept: Static Type Safety

**TypeScript** = JavaScript + Types

| JavaScript | TypeScript |
|------------|------------|
| Types checked at runtime | Types checked at compile time |
| Errors discovered in production | Errors discovered in editor |
| Dynamic | Static |

**Analogy**: TypeScript is like spell-check for code. It catches mistakes before you hit "send."

---

## 2. Basic Type Annotations

```typescript
// Primitive types
let name: string = "Alice";
let age: number = 30;
let isActive: boolean = true;
let data: null = null;
let missing: undefined = undefined;

// Type inference (TypeScript infers the type)
let inferred = "Hello";  // TypeScript knows this is string
inferred = 42;  // ERROR: Type 'number' is not assignable to type 'string'
```

---

## 3. Arrays and Objects

### Array Types
```typescript
// Two syntaxes (equivalent)
let numbers: number[] = [1, 2, 3];
let strings: Array<string> = ["a", "b", "c"];

// Mixed types
let mixed: (string | number)[] = [1, "two", 3];
```

### Object Types
```typescript
// Inline object type
let person: { name: string; age: number } = {
    name: "Alice",
    age: 30
};

// Optional properties
let config: { host: string; port?: number } = {
    host: "localhost"  // port is optional
};
```

---

## 4. Interfaces

Interfaces define the **shape** of objects.

```typescript
interface User {
    id: number;
    name: string;
    email: string;
    age?: number;  // Optional
}

function greet(user: User): string {
    return `Hello, ${user.name}!`;
}

const alice: User = {
    id: 1,
    name: "Alice",
    email: "alice@example.com"
};

greet(alice);  // "Hello, Alice!"
```

### Extending Interfaces
```typescript
interface Person {
    name: string;
}

interface Employee extends Person {
    employeeId: number;
    department: string;
}

const emp: Employee = {
    name: "Bob",
    employeeId: 123,
    department: "Engineering"
};
```

---

## 5. Type Aliases

```typescript
// Simple alias
type ID = string | number;

// Object type
type Point = {
    x: number;
    y: number;
};

// Union type
type Status = "active" | "inactive" | "pending";

// Function type
type Callback = (data: string) => void;
```

### Interface vs Type
| Feature | Interface | Type |
|---------|-----------|------|
| Extend | `extends` | `&` (intersection) |
| Declaration merging | ✅ | ❌ |
| Union types | ❌ | ✅ |
| Primitives | ❌ | ✅ |

**Rule of thumb**: Use `interface` for objects, `type` for everything else.

---

## 6. Union and Intersection Types

### Union (`|`)
A value can be one of several types.

```typescript
type StringOrNumber = string | number;

function display(value: StringOrNumber) {
    if (typeof value === "string") {
        console.log(value.toUpperCase());  // TypeScript knows it's string
    } else {
        console.log(value.toFixed(2));  // TypeScript knows it's number
    }
}
```

### Intersection (`&`)
A value must satisfy all combined types.

```typescript
interface Printable {
    print(): void;
}

interface Loggable {
    log(): void;
}

type PrintableAndLoggable = Printable & Loggable;

const obj: PrintableAndLoggable = {
    print() { console.log("Printing..."); },
    log() { console.log("Logging..."); }
};
```

---

## 7. Generics

Write reusable code that works with any type.

```typescript
// Generic function
function identity<T>(value: T): T {
    return value;
}

identity<string>("hello");  // "hello"
identity<number>(42);       // 42
identity("inferred");       // TypeScript infers T = string

// Generic interface
interface Box<T> {
    value: T;
}

const stringBox: Box<string> = { value: "hello" };
const numberBox: Box<number> = { value: 42 };
```

### Generic Constraints
```typescript
interface HasLength {
    length: number;
}

function logLength<T extends HasLength>(value: T): void {
    console.log(value.length);
}

logLength("hello");     // 5 ✅
logLength([1, 2, 3]);   // 3 ✅
logLength(42);          // ERROR: number doesn't have length
```

---

## 8. Type Narrowing

TypeScript narrows types based on conditions.

```typescript
function process(value: string | number | null) {
    if (value === null) {
        return "No value";  // value: null
    }
    
    if (typeof value === "string") {
        return value.toUpperCase();  // value: string
    }
    
    return value.toFixed(2);  // value: number
}
```

### Type Guards
```typescript
interface Dog {
    bark(): void;
}

interface Cat {
    meow(): void;
}

function isDog(animal: Dog | Cat): animal is Dog {
    return (animal as Dog).bark !== undefined;
}

function speak(animal: Dog | Cat) {
    if (isDog(animal)) {
        animal.bark();  // TypeScript knows it's Dog
    } else {
        animal.meow();  // TypeScript knows it's Cat
    }
}
```

---

## 9. Utility Types

Built-in types for common transformations.

```typescript
interface User {
    id: number;
    name: string;
    email: string;
}

// Make all properties optional
type PartialUser = Partial<User>;

// Make all properties required
type RequiredUser = Required<User>;

// Pick specific properties
type UserName = Pick<User, "name" | "email">;

// Omit specific properties
type UserWithoutId = Omit<User, "id">;

// Make all properties readonly
type ReadonlyUser = Readonly<User>;
```

---

## 10. Practice Exercises

### Exercise 1: Type-Safe API Response
Create a generic type for API responses.

```typescript
// TODO: Define ApiResponse<T>
type ApiResponse<T> = {
    // success case: data
    // error case: error message
};

const success: ApiResponse<User> = { /* ... */ };
const error: ApiResponse<User> = { /* ... */ };
```

### Exercise 2: Type-Safe Event Handler
Create a typed event system.

```typescript
type Events = {
    click: { x: number; y: number };
    keypress: { key: string };
    load: undefined;
};

// TODO: Implement typed emit function
function emit<K extends keyof Events>(
    event: K,
    data: Events[K]
): void {
    // ...
}

emit("click", { x: 10, y: 20 });  // ✅
emit("click", { key: "a" });       // ❌ Wrong payload type
```

---

## 11. Palantir Context

**OSDK** generates TypeScript interfaces from Ontology:

```typescript
// Auto-generated from Ontology
interface Employee {
    employeeId: string;
    name: string;
    department: Department;  // Linked object
    hireDate: Date;
}

// Type-safe queries
const engineers = await client.ontology
    .objects<Employee>("Employee")
    .filter(e => e.department.name === "Engineering")
    .list();
```

**Blueprint** uses generics extensively:
```typescript
<Table<User>
    columns={columns}
    data={users}
/>
```

---

## 12. Design Philosophy

> **"TypeScript is JavaScript that scales."**
> — TypeScript Team

> **"The goal of TypeScript is not to be a new language, but to add static typing to JavaScript."**
> — Anders Hejlsberg

---

## 13. Adaptive Next Steps

- **If you understood this module**: Proceed to [01_language_foundation.md](./01_language_foundation.md) for advanced JavaScript concepts.
- **If you need more practice**: Implement the API response exercise.
- **For deeper exploration**: Read [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/).
