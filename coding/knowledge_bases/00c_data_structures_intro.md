# Knowledge Base 00c: Data Structures Introduction
> **Module ID**: `00c_data_structures_intro`
> **Prerequisites**: 00b_functions_and_scope
> **Estimated Time**: 30 Minutes
> **Tier**: 1 (Beginner)

---

## 1. Universal Concept: Organizing Data

Data structures are ways to **organize and access data efficiently**.

| Structure | Analogy | Access Pattern |
|-----------|---------|----------------|
| Array | Numbered list | By index |
| Object | Dictionary | By key |
| Set | Unique collection | By membership |
| Map | Key-value store | By key |

---

## 2. Arrays: Ordered Collections

### Creating Arrays
```javascript
// Array literal
const fruits = ["apple", "banana", "cherry"];

// Array constructor
const numbers = new Array(5);  // [undefined × 5]

// Array.from
const chars = Array.from("hello");  // ["h", "e", "l", "l", "o"]
```

### Accessing Elements
```javascript
const fruits = ["apple", "banana", "cherry"];

fruits[0];        // "apple" (first)
fruits[2];        // "cherry" (third)
fruits.at(-1);    // "cherry" (last - ES2022)
fruits.length;    // 3
```

### Modifying Arrays
```javascript
const arr = [1, 2, 3];

// Add elements
arr.push(4);       // [1, 2, 3, 4] - end
arr.unshift(0);    // [0, 1, 2, 3, 4] - start

// Remove elements
arr.pop();         // [0, 1, 2, 3] - from end
arr.shift();       // [1, 2, 3] - from start

// Splice (insert/remove at index)
arr.splice(1, 1, "a", "b");  // [1, "a", "b", 3]
```

### TypeScript Typed Arrays
```typescript
// Typed arrays
const numbers: number[] = [1, 2, 3];
const mixed: (string | number)[] = [1, "two", 3];

// Generic syntax
const names: Array<string> = ["Alice", "Bob"];

// Readonly
const frozen: readonly number[] = [1, 2, 3];
frozen.push(4);  // ERROR: Property 'push' does not exist on readonly array
```

---

## 3. Objects: Key-Value Pairs

### Creating Objects
```javascript
// Object literal
const person = {
    name: "Alice",
    age: 30,
    isActive: true
};

// Accessing properties
person.name;        // "Alice" (dot notation)
person["age"];      // 30 (bracket notation)

// Dynamic keys
const key = "name";
person[key];        // "Alice"
```

### TypeScript Interfaces
```typescript
// Define shape
interface Person {
    name: string;
    age: number;
    email?: string;  // Optional
}

// Use interface
const alice: Person = {
    name: "Alice",
    age: 30
};

// Index signature for dynamic keys
interface Dictionary {
    [key: string]: string;
}
```

### Object Methods
```javascript
const obj = { a: 1, b: 2, c: 3 };

Object.keys(obj);     // ["a", "b", "c"]
Object.values(obj);   // [1, 2, 3]
Object.entries(obj);  // [["a", 1], ["b", 2], ["c", 3]]

// Spread operator
const extended = { ...obj, d: 4 };  // { a: 1, b: 2, c: 3, d: 4 }
```

---

## 4. Set: Unique Values

```javascript
// Create from array (removes duplicates)
const numbers = [1, 2, 2, 3, 3, 3];
const unique = new Set(numbers);  // Set {1, 2, 3}

// Operations
unique.add(4);      // Set {1, 2, 3, 4}
unique.has(2);      // true
unique.delete(1);   // Set {2, 3, 4}
unique.size;        // 3

// Convert back to array
const arr = [...unique];  // [2, 3, 4]
```

### TypeScript Set
```typescript
const strings = new Set<string>();
strings.add("hello");
strings.add(123);  // ERROR: Argument of type 'number' is not assignable
```

---

## 5. Map: Key-Value with Any Key Type

```javascript
// Unlike objects, Map keys can be any type
const map = new Map();

map.set("name", "Alice");
map.set(42, "the answer");
map.set({ id: 1 }, "object key");

map.get("name");  // "Alice"
map.get(42);      // "the answer"
map.has("name");  // true
map.size;         // 3

// Iterate
for (const [key, value] of map) {
    console.log(`${key}: ${value}`);
}
```

### TypeScript Map
```typescript
const userScores = new Map<string, number>();
userScores.set("Alice", 100);
userScores.set("Bob", 85);

userScores.get("Alice");  // 100
```

---

## 6. Comparison Table

| Feature | Array | Object | Set | Map |
|---------|-------|--------|-----|-----|
| **Ordered** | ✅ | ❌ (ES2015+: insertion order) | ✅ | ✅ |
| **Key Type** | number | string/symbol | any | any |
| **Duplicate Keys** | N/A | ❌ | ❌ | ❌ |
| **Duplicate Values** | ✅ | ✅ | ❌ | ✅ |
| **Size Property** | `.length` | `Object.keys().length` | `.size` | `.size` |
| **Iterable** | ✅ | ❌ (use Object.entries) | ✅ | ✅ |

---

## 7. Destructuring

```javascript
// Array destructuring
const [first, second, ...rest] = [1, 2, 3, 4, 5];
// first = 1, second = 2, rest = [3, 4, 5]

// Object destructuring
const { name, age } = { name: "Alice", age: 30 };

// Renaming
const { name: userName } = { name: "Alice" };
// userName = "Alice"

// Defaults
const { city = "Unknown" } = {};
// city = "Unknown"
```

---

## 8. Practice Exercises

### Exercise 1: Remove Duplicates
Write a function that removes duplicates from an array.

```typescript
function removeDuplicates<T>(arr: T[]): T[] {
    // TODO: Implement using Set
}

removeDuplicates([1, 2, 2, 3, 3, 3]);  // [1, 2, 3]
```

### Exercise 2: Group By
Group an array of objects by a property.

```typescript
interface Item {
    category: string;
    name: string;
}

function groupBy(items: Item[], key: keyof Item): Map<string, Item[]> {
    // TODO: Implement
}

const items = [
    { category: "fruit", name: "apple" },
    { category: "fruit", name: "banana" },
    { category: "vegetable", name: "carrot" }
];

groupBy(items, "category");
// Map { "fruit" => [...], "vegetable" => [...] }
```

---

## 9. Palantir Context

**Blueprint UI** heavily uses typed data structures:
- `ITreeNode<T>` for hierarchical data
- `IColumnProps<T>` for table columns
- `IListItemsProps<T>` for select/combobox

**OSDK** returns objects with strict interfaces matching Ontology definitions.

---

## 10. Adaptive Next Steps

- **If you understood this module**: Proceed to [00d_async_basics.md](./00d_async_basics.md) to learn about asynchronous programming.
- **If you need more practice**: Implement the groupBy exercise.
- **For deeper exploration**: Study [Array methods](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Array) in depth.
