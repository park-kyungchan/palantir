# F32: Exception Handling (예외 처리)

> **Concept ID**: F32
> **Category**: Error Handling & Control Flow
> **Difficulty**: Intermediate → Advanced
> **Prerequisites**: F01 (Variables), F05 (Control Flow), F10 (Functions)

---

## Section 1: Universal Concept (언어 공통 개념)

### 1.1 Exception vs Error vs Panic: Mental Model

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ERROR HANDLING SPECTRUM                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  RECOVERABLE                                              UNRECOVERABLE     │
│  ←─────────────────────────────────────────────────────────────────────→    │
│                                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐             │
│  │  Result  │    │Exception │    │  Error   │    │  Panic   │             │
│  │  /Option │    │(Checked) │    │(Runtime) │    │  /Fatal  │             │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘             │
│       │               │               │               │                    │
│  Expected        Anticipated      Unexpected      Catastrophic             │
│  outcomes        failures         failures        failures                 │
│                                                                             │
│  Go, Rust        Java             Python, JS      Go panic                 │
│  Result<T,E>     IOException      RuntimeError    C++ terminate            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Call Stack Unwinding

When an exception is thrown, the runtime **unwinds the call stack** searching for a handler:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CALL STACK UNWINDING                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   CALL STACK                          UNWINDING PROCESS                     │
│   ──────────                          ─────────────────                     │
│                                                                             │
│   ┌─────────────┐                                                          │
│   │   main()    │ ←─────────── 4. Handler found! Catch here               │
│   │ try{...}    │                                                          │
│   │ catch(e)    │                                                          │
│   └──────┬──────┘                                                          │
│          ↓                                                                  │
│   ┌─────────────┐                                                          │
│   │  process()  │ ←─────────── 3. No handler, continue unwinding          │
│   │             │                                                          │
│   └──────┬──────┘                                                          │
│          ↓                                                                  │
│   ┌─────────────┐                                                          │
│   │  validate() │ ←─────────── 2. No handler, continue unwinding          │
│   │             │                                                          │
│   └──────┬──────┘                                                          │
│          ↓                                                                  │
│   ┌─────────────┐                                                          │
│   │   parse()   │ ←─────────── 1. Exception thrown here!                  │
│   │ throw new   │                                                          │
│   │ ParseError  │                                                          │
│   └─────────────┘                                                          │
│                                                                             │
│   If no handler found → Program terminates with stack trace                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Why Proper Error Handling Matters

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ERROR HANDLING QUALITY IMPACT                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   POOR ERROR HANDLING              GOOD ERROR HANDLING                      │
│   ────────────────────             ────────────────────                      │
│                                                                             │
│   ❌ Silent failures               ✅ Explicit error types                  │
│   ❌ Lost context/stack traces     ✅ Preserved error chains                │
│   ❌ Resource leaks                ✅ Guaranteed cleanup (finally/defer)    │
│   ❌ Security vulnerabilities      ✅ Graceful degradation                  │
│   ❌ Debugging nightmares          ✅ Clear error messages                  │
│   ❌ Cascading failures            ✅ Fault isolation                       │
│                                                                             │
│   COST OF POOR ERROR HANDLING:                                              │
│   • 50%+ of production incidents from unhandled edge cases                  │
│   • Average debugging time 3x longer without proper error context          │
│   • Security breaches from leaked exception details                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.4 The Two Schools of Thought

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              EXCEPTION-BASED vs VALUE-BASED ERROR HANDLING                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   EXCEPTION-BASED (Java, Python, C++, TypeScript)                          │
│   ─────────────────────────────────────────────────                         │
│   • Errors are "exceptional" - thrown/raised                                │
│   • Control flow jumps to handler                                           │
│   • Can propagate implicitly                                                │
│   • try/catch/finally pattern                                               │
│                                                                             │
│   Pros: Clean happy path, automatic propagation                             │
│   Cons: Hidden control flow, performance overhead                           │
│                                                                             │
│   VALUE-BASED (Go, Rust, Functional)                                       │
│   ─────────────────────────────────────                                     │
│   • Errors are values - returned explicitly                                 │
│   • Must handle at call site                                                │
│   • Result<T, E> / Option<T> types                                         │
│   • No hidden control flow                                                  │
│                                                                             │
│   Pros: Explicit, predictable, composable                                   │
│   Cons: Verbose, manual propagation                                         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Section 2: Semantic Comparison Matrix (언어별 비교)

### 2.1 Quick Reference Table

| Dimension | Java | Python | TypeScript | Go | SQL | C++ | Spark |
|-----------|------|--------|------------|-----|-----|-----|-------|
| **Exception syntax** | `try-catch-finally` | `try-except-finally` | `try-catch-finally` | `if err != nil` | `TRY...CATCH` | `try-catch` | `try-except` (Python) |
| **Checked exceptions** | ✅ Yes | ❌ No | ❌ No | ❌ No (no exceptions) | ❌ No | ❌ No (deprecated) | ❌ No |
| **Finally/cleanup** | `finally` | `finally` | `finally` | `defer` | N/A | RAII/destructors | `finally` |
| **Throw keyword** | `throw` | `raise` | `throw` | `return err` | `THROW` | `throw` | `raise` |
| **Exception base** | `Throwable` | `BaseException` | `Error` | `error` interface | N/A | `std::exception` | Python's |
| **Custom exceptions** | `extends Exception` | `class MyError(Exception)` | `extends Error` | `errors.New()` | N/A | `class: public exception` | Python's |
| **Multi-catch** | `catch(A \| B e)` | `except (A, B)` | Multiple catch blocks | `switch err.(type)` | N/A | `catch(...)` | `except (A, B)` |
| **Error chaining** | `initCause()` | `raise from` | `cause` property | `fmt.Errorf("%w")` | N/A | `std::nested_exception` | `raise from` |
| **Panic mechanism** | `Error` subclass | `SystemExit` | N/A | `panic()` | N/A | `std::terminate` | N/A |

### 2.2 Exception Syntax Comparison

#### Basic try-catch Pattern

```java
// ═══════════════════════════════════════════════════════════════════════════
// JAVA - try-catch-finally
// ═══════════════════════════════════════════════════════════════════════════
public class ExceptionDemo {
    public static void main(String[] args) {
        try {
            int result = divide(10, 0);
            System.out.println("Result: " + result);
        } catch (ArithmeticException e) {
            System.err.println("Math error: " + e.getMessage());
        } catch (Exception e) {
            System.err.println("General error: " + e.getMessage());
        } finally {
            System.out.println("Cleanup always runs");
        }
    }

    public static int divide(int a, int b) {
        if (b == 0) {
            throw new ArithmeticException("Division by zero");
        }
        return a / b;
    }
}
```

```python
# ═══════════════════════════════════════════════════════════════════════════
# PYTHON - try-except-finally
# ═══════════════════════════════════════════════════════════════════════════
def divide(a: int, b: int) -> float:
    if b == 0:
        raise ZeroDivisionError("Division by zero")
    return a / b

def main():
    try:
        result = divide(10, 0)
        print(f"Result: {result}")
    except ZeroDivisionError as e:
        print(f"Math error: {e}")
    except Exception as e:
        print(f"General error: {e}")
    else:
        print("No exception occurred")  # Python's unique 'else' clause
    finally:
        print("Cleanup always runs")

if __name__ == "__main__":
    main()
```

```typescript
// ═══════════════════════════════════════════════════════════════════════════
// TYPESCRIPT - try-catch-finally (exceptions are untyped!)
// ═══════════════════════════════════════════════════════════════════════════
function divide(a: number, b: number): number {
    if (b === 0) {
        throw new Error("Division by zero");
    }
    return a / b;
}

function main(): void {
    try {
        const result = divide(10, 0);
        console.log(`Result: ${result}`);
    } catch (e) {
        // TypeScript: 'e' is 'unknown' type (since TS 4.4)
        if (e instanceof Error) {
            console.error(`Error: ${e.message}`);
        } else {
            console.error(`Unknown error: ${e}`);
        }
    } finally {
        console.log("Cleanup always runs");
    }
}

main();
```

```go
// ═══════════════════════════════════════════════════════════════════════════
// GO - NO EXCEPTIONS! Errors are values.
// ═══════════════════════════════════════════════════════════════════════════
package main

import (
    "errors"
    "fmt"
)

// Go functions return error as second value
func divide(a, b int) (int, error) {
    if b == 0 {
        return 0, errors.New("division by zero")
    }
    return a / b, nil
}

func main() {
    result, err := divide(10, 0)
    if err != nil {
        fmt.Printf("Math error: %v\n", err)
        return
    }
    fmt.Printf("Result: %d\n", result)

    // defer is Go's "finally" equivalent
    defer func() {
        fmt.Println("Cleanup always runs")
    }()
}
```

```sql
-- ═══════════════════════════════════════════════════════════════════════════
-- SQL (T-SQL) - TRY...CATCH in stored procedures
-- ═══════════════════════════════════════════════════════════════════════════
CREATE PROCEDURE DivideNumbers
    @a INT,
    @b INT,
    @result INT OUTPUT
AS
BEGIN
    BEGIN TRY
        IF @b = 0
            THROW 50001, 'Division by zero', 1;

        SET @result = @a / @b;
    END TRY
    BEGIN CATCH
        -- Error handling
        SELECT
            ERROR_NUMBER() AS ErrorNumber,
            ERROR_MESSAGE() AS ErrorMessage,
            ERROR_SEVERITY() AS ErrorSeverity,
            ERROR_STATE() AS ErrorState,
            ERROR_LINE() AS ErrorLine;

        -- Re-throw or handle
        THROW;  -- Re-throws the caught exception
    END CATCH
END;
```

```cpp
// ═══════════════════════════════════════════════════════════════════════════
// C++ - try-catch with RAII for cleanup
// ═══════════════════════════════════════════════════════════════════════════
#include <iostream>
#include <stdexcept>
#include <memory>

int divide(int a, int b) {
    if (b == 0) {
        throw std::runtime_error("Division by zero");
    }
    return a / b;
}

int main() {
    // RAII: Resource cleanup via destructor
    auto cleanup = std::make_unique<int>(42);  // Will be cleaned up automatically

    try {
        int result = divide(10, 0);
        std::cout << "Result: " << result << std::endl;
    } catch (const std::runtime_error& e) {
        std::cerr << "Runtime error: " << e.what() << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "General error: " << e.what() << std::endl;
    } catch (...) {
        std::cerr << "Unknown exception" << std::endl;
    }

    std::cout << "Cleanup happens via RAII destructors" << std::endl;
    return 0;
}
```

```python
# ═══════════════════════════════════════════════════════════════════════════
# SPARK (PySpark) - Exception handling in distributed context
# ═══════════════════════════════════════════════════════════════════════════
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col
from pyspark.sql.types import IntegerType
from py4j.protocol import Py4JJavaError

spark = SparkSession.builder.appName("ExceptionDemo").getOrCreate()

# UDF with exception handling
def safe_divide(a: int, b: int) -> int:
    try:
        if b == 0:
            raise ZeroDivisionError("Division by zero")
        return a // b
    except ZeroDivisionError:
        return None  # Return null for bad records

safe_divide_udf = udf(safe_divide, IntegerType())

# DataFrame operations with error handling
try:
    df = spark.createDataFrame([(10, 2), (20, 0), (30, 5)], ["a", "b"])
    result = df.withColumn("result", safe_divide_udf(col("a"), col("b")))
    result.show()
except Py4JJavaError as e:
    # Spark-specific exception from JVM
    print(f"Spark error: {e.java_exception.getMessage()}")
except Exception as e:
    print(f"General error: {e}")
finally:
    # Always stop Spark session in production
    # spark.stop()
    pass
```

### 2.3 Checked vs Unchecked Exceptions (Java's Unique Feature)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    JAVA EXCEPTION HIERARCHY                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                         ┌───────────────┐                                   │
│                         │   Throwable   │                                   │
│                         └───────┬───────┘                                   │
│                    ┌────────────┴────────────┐                              │
│                    ↓                         ↓                              │
│           ┌────────────────┐        ┌────────────────┐                      │
│           │     Error      │        │   Exception    │                      │
│           │  (unchecked)   │        └───────┬────────┘                      │
│           └────────────────┘           ┌────┴────┐                          │
│                    │                   ↓         ↓                          │
│           • OutOfMemoryError    ┌──────────┐ ┌──────────────────┐          │
│           • StackOverflowError  │ Checked  │ │RuntimeException  │          │
│           • VirtualMachineError │Exceptions│ │   (unchecked)    │          │
│                                 └──────────┘ └──────────────────┘          │
│                                      │               │                      │
│                              • IOException    • NullPointerException        │
│                              • SQLException   • IllegalArgumentException    │
│                              • ParseException • IndexOutOfBoundsException   │
│                                                                             │
│   CHECKED: Must be declared (throws) or caught                              │
│   UNCHECKED: Optional to handle, often programming errors                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

```java
// ═══════════════════════════════════════════════════════════════════════════
// JAVA - Checked vs Unchecked Exceptions
// ═══════════════════════════════════════════════════════════════════════════
import java.io.*;

public class CheckedVsUnchecked {

    // Checked exception: MUST be declared with 'throws' or caught
    public static String readFile(String path) throws IOException {
        BufferedReader reader = new BufferedReader(new FileReader(path));
        try {
            return reader.readLine();
        } finally {
            reader.close();
        }
    }

    // Unchecked exception: Does NOT need to be declared
    public static int divide(int a, int b) {
        if (b == 0) {
            throw new IllegalArgumentException("Divisor cannot be zero");
        }
        return a / b;  // Could also throw ArithmeticException
    }

    // Custom CHECKED exception
    public static class DataValidationException extends Exception {
        public DataValidationException(String message) {
            super(message);
        }
    }

    // Custom UNCHECKED exception
    public static class InvalidConfigException extends RuntimeException {
        public InvalidConfigException(String message) {
            super(message);
        }
    }

    // Method with checked exception must be handled
    public static void main(String[] args) {
        // Checked: Compiler FORCES you to handle
        try {
            String content = readFile("data.txt");
        } catch (IOException e) {
            System.err.println("File error: " + e.getMessage());
        }

        // Unchecked: Compiler does NOT force handling
        // This could throw IllegalArgumentException at runtime
        int result = divide(10, 2);
    }
}
```

### 2.4 Custom Exception Classes

```java
// ═══════════════════════════════════════════════════════════════════════════
// JAVA - Custom Exception with rich context
// ═══════════════════════════════════════════════════════════════════════════
public class OrderProcessingException extends Exception {
    private final String orderId;
    private final ErrorCode errorCode;

    public enum ErrorCode {
        INVALID_QUANTITY,
        INSUFFICIENT_STOCK,
        PAYMENT_FAILED,
        SHIPPING_UNAVAILABLE
    }

    public OrderProcessingException(String orderId, ErrorCode errorCode, String message) {
        super(message);
        this.orderId = orderId;
        this.errorCode = errorCode;
    }

    public OrderProcessingException(String orderId, ErrorCode errorCode,
                                    String message, Throwable cause) {
        super(message, cause);
        this.orderId = orderId;
        this.errorCode = errorCode;
    }

    public String getOrderId() { return orderId; }
    public ErrorCode getErrorCode() { return errorCode; }

    @Override
    public String toString() {
        return String.format("OrderProcessingException[order=%s, code=%s]: %s",
                           orderId, errorCode, getMessage());
    }
}

// Usage
public void processOrder(Order order) throws OrderProcessingException {
    if (order.getQuantity() <= 0) {
        throw new OrderProcessingException(
            order.getId(),
            OrderProcessingException.ErrorCode.INVALID_QUANTITY,
            "Quantity must be positive"
        );
    }
}
```

```python
# ═══════════════════════════════════════════════════════════════════════════
# PYTHON - Custom Exception hierarchy
# ═══════════════════════════════════════════════════════════════════════════
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ErrorCode(Enum):
    INVALID_QUANTITY = "INVALID_QUANTITY"
    INSUFFICIENT_STOCK = "INSUFFICIENT_STOCK"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    SHIPPING_UNAVAILABLE = "SHIPPING_UNAVAILABLE"


class OrderError(Exception):
    """Base exception for order processing."""
    pass


@dataclass
class OrderProcessingError(OrderError):
    """Rich exception with structured data."""
    order_id: str
    error_code: ErrorCode
    message: str
    cause: Optional[Exception] = None

    def __str__(self) -> str:
        return f"OrderProcessingError[order={self.order_id}, code={self.error_code.value}]: {self.message}"


class ValidationError(OrderError):
    """Input validation failed."""
    pass


class PaymentError(OrderError):
    """Payment processing failed."""
    pass


# Usage with exception chaining
def process_payment(order_id: str, amount: float) -> None:
    try:
        # External payment call
        raise ConnectionError("Payment gateway timeout")
    except ConnectionError as e:
        raise PaymentError(f"Payment failed for order {order_id}") from e


def process_order(order_id: str, quantity: int) -> None:
    if quantity <= 0:
        raise OrderProcessingError(
            order_id=order_id,
            error_code=ErrorCode.INVALID_QUANTITY,
            message="Quantity must be positive"
        )

    try:
        process_payment(order_id, quantity * 10.0)
    except PaymentError as e:
        raise OrderProcessingError(
            order_id=order_id,
            error_code=ErrorCode.PAYMENT_FAILED,
            message="Could not process payment",
            cause=e
        ) from e


# Catching with context
try:
    process_order("ORD-123", 5)
except OrderProcessingError as e:
    print(f"Order error: {e}")
    if e.cause:
        print(f"Caused by: {e.cause}")
except OrderError as e:
    print(f"General order error: {e}")
```

```typescript
// ═══════════════════════════════════════════════════════════════════════════
// TYPESCRIPT - Custom Error classes (with type narrowing)
// ═══════════════════════════════════════════════════════════════════════════
enum ErrorCode {
    INVALID_QUANTITY = "INVALID_QUANTITY",
    INSUFFICIENT_STOCK = "INSUFFICIENT_STOCK",
    PAYMENT_FAILED = "PAYMENT_FAILED",
}

// Base custom error
class AppError extends Error {
    constructor(message: string, public readonly code: string) {
        super(message);
        this.name = this.constructor.name;
        // Fix prototype chain for instanceof to work correctly
        Object.setPrototypeOf(this, new.target.prototype);
    }
}

// Specific error types
class OrderError extends AppError {
    constructor(
        public readonly orderId: string,
        public readonly errorCode: ErrorCode,
        message: string,
        public readonly cause?: Error
    ) {
        super(message, errorCode);
    }
}

class ValidationError extends AppError {
    constructor(
        public readonly field: string,
        message: string
    ) {
        super(message, "VALIDATION_ERROR");
    }
}

// Type guard for error narrowing
function isOrderError(error: unknown): error is OrderError {
    return error instanceof OrderError;
}

// Usage
function processOrder(orderId: string, quantity: number): void {
    if (quantity <= 0) {
        throw new OrderError(
            orderId,
            ErrorCode.INVALID_QUANTITY,
            "Quantity must be positive"
        );
    }
}

try {
    processOrder("ORD-123", -1);
} catch (e: unknown) {
    // TypeScript 4.4+: catch variables are 'unknown'
    if (isOrderError(e)) {
        console.error(`Order ${e.orderId} failed: ${e.errorCode}`);
    } else if (e instanceof Error) {
        console.error(`Error: ${e.message}`);
    } else {
        console.error(`Unknown error: ${e}`);
    }
}
```

```go
// ═══════════════════════════════════════════════════════════════════════════
// GO - Custom errors (values, not exceptions!)
// ═══════════════════════════════════════════════════════════════════════════
package main

import (
    "errors"
    "fmt"
)

// Sentinel errors - predefined error values
var (
    ErrInvalidQuantity   = errors.New("invalid quantity")
    ErrInsufficientStock = errors.New("insufficient stock")
    ErrPaymentFailed     = errors.New("payment failed")
)

// Custom error type with context
type OrderError struct {
    OrderID   string
    ErrorCode string
    Message   string
    Cause     error
}

func (e *OrderError) Error() string {
    if e.Cause != nil {
        return fmt.Sprintf("OrderError[order=%s, code=%s]: %s (caused by: %v)",
            e.OrderID, e.ErrorCode, e.Message, e.Cause)
    }
    return fmt.Sprintf("OrderError[order=%s, code=%s]: %s",
        e.OrderID, e.ErrorCode, e.Message)
}

// Unwrap for errors.Is() and errors.As() support
func (e *OrderError) Unwrap() error {
    return e.Cause
}

// Constructor function
func NewOrderError(orderID, code, message string, cause error) *OrderError {
    return &OrderError{
        OrderID:   orderID,
        ErrorCode: code,
        Message:   message,
        Cause:     cause,
    }
}

func processOrder(orderID string, quantity int) error {
    if quantity <= 0 {
        return NewOrderError(orderID, "INVALID_QUANTITY",
            "Quantity must be positive", nil)
    }

    // Wrap errors with context
    if err := processPayment(orderID); err != nil {
        return fmt.Errorf("order %s: payment processing: %w", orderID, err)
    }

    return nil
}

func processPayment(orderID string) error {
    return ErrPaymentFailed  // Simulated failure
}

func main() {
    err := processOrder("ORD-123", -1)
    if err != nil {
        // Check specific error types
        var orderErr *OrderError
        if errors.As(err, &orderErr) {
            fmt.Printf("Order error: %s (code: %s)\n",
                orderErr.Message, orderErr.ErrorCode)
        }

        // Check sentinel errors
        if errors.Is(err, ErrPaymentFailed) {
            fmt.Println("Payment failed - retry or notify customer")
        }
    }
}
```

```cpp
// ═══════════════════════════════════════════════════════════════════════════
// C++ - Custom exception classes
// ═══════════════════════════════════════════════════════════════════════════
#include <exception>
#include <string>
#include <sstream>

enum class ErrorCode {
    INVALID_QUANTITY,
    INSUFFICIENT_STOCK,
    PAYMENT_FAILED
};

class OrderException : public std::exception {
private:
    std::string orderId_;
    ErrorCode errorCode_;
    std::string message_;
    mutable std::string fullMessage_;

public:
    OrderException(const std::string& orderId,
                   ErrorCode code,
                   const std::string& message)
        : orderId_(orderId), errorCode_(code), message_(message) {

        std::ostringstream oss;
        oss << "OrderException[order=" << orderId_
            << ", code=" << static_cast<int>(errorCode_)
            << "]: " << message_;
        fullMessage_ = oss.str();
    }

    const char* what() const noexcept override {
        return fullMessage_.c_str();
    }

    const std::string& getOrderId() const { return orderId_; }
    ErrorCode getErrorCode() const { return errorCode_; }
};

// Usage with noexcept specification
void processOrder(const std::string& orderId, int quantity) {
    if (quantity <= 0) {
        throw OrderException(orderId, ErrorCode::INVALID_QUANTITY,
                           "Quantity must be positive");
    }
}

// noexcept guarantees no exceptions will be thrown
int safeOperation() noexcept {
    return 42;  // If this throws, std::terminate() is called
}

int main() {
    try {
        processOrder("ORD-123", -1);
    } catch (const OrderException& e) {
        std::cerr << "Order error: " << e.what() << std::endl;
        std::cerr << "Order ID: " << e.getOrderId() << std::endl;
    } catch (const std::exception& e) {
        std::cerr << "Standard error: " << e.what() << std::endl;
    }
    return 0;
}
```

### 2.5 Go's "Errors Are Values" Philosophy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    GO ERROR HANDLING PATTERNS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   PATTERN 1: Simple Error Return                                            │
│   ─────────────────────────────────                                         │
│   result, err := operation()                                                │
│   if err != nil {                                                           │
│       return err  // Propagate                                              │
│   }                                                                         │
│                                                                             │
│   PATTERN 2: Error Wrapping (Go 1.13+)                                     │
│   ─────────────────────────────────────                                     │
│   if err != nil {                                                           │
│       return fmt.Errorf("context: %w", err)  // %w wraps                   │
│   }                                                                         │
│                                                                             │
│   PATTERN 3: Sentinel Errors                                                │
│   ──────────────────────────────                                            │
│   var ErrNotFound = errors.New("not found")                                │
│   if errors.Is(err, ErrNotFound) { ... }                                   │
│                                                                             │
│   PATTERN 4: Custom Error Types                                             │
│   ─────────────────────────────────                                         │
│   var pathErr *os.PathError                                                │
│   if errors.As(err, &pathErr) { ... }                                      │
│                                                                             │
│   PATTERN 5: defer for Cleanup                                              │
│   ─────────────────────────────────                                         │
│   f, err := os.Open(path)                                                  │
│   if err != nil { return err }                                             │
│   defer f.Close()  // ALWAYS runs when function returns                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

```go
// ═══════════════════════════════════════════════════════════════════════════
// GO - Complete error handling patterns
// ═══════════════════════════════════════════════════════════════════════════
package main

import (
    "errors"
    "fmt"
    "io"
    "os"
)

// Pattern 1: Sentinel errors
var (
    ErrNotFound     = errors.New("resource not found")
    ErrUnauthorized = errors.New("unauthorized access")
    ErrInternal     = errors.New("internal error")
)

// Pattern 2: Custom error type
type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation failed for %s: %s", e.Field, e.Message)
}

// Pattern 3: Error wrapping for context
func readConfig(path string) ([]byte, error) {
    data, err := os.ReadFile(path)
    if err != nil {
        // Wrap with context, preserve original error
        return nil, fmt.Errorf("reading config %s: %w", path, err)
    }
    return data, nil
}

// Pattern 4: defer for resource cleanup (like finally)
func processFile(path string) error {
    f, err := os.Open(path)
    if err != nil {
        return fmt.Errorf("opening file: %w", err)
    }
    defer f.Close()  // GUARANTEED to run, even if panic occurs

    // Process file...
    _, err = io.ReadAll(f)
    if err != nil {
        return fmt.Errorf("reading file: %w", err)
    }

    return nil
}

// Pattern 5: Multiple defers (LIFO order)
func multiDefer() {
    defer fmt.Println("Third")   // Runs last
    defer fmt.Println("Second")  // Runs second
    defer fmt.Println("First")   // Runs first
}

// Pattern 6: Named return for defer modification
func divideWithRecovery(a, b int) (result int, err error) {
    defer func() {
        if r := recover(); r != nil {
            err = fmt.Errorf("panic recovered: %v", r)
        }
    }()

    if b == 0 {
        panic("division by zero")  // Normally use error, panic for truly exceptional
    }

    return a / b, nil
}

func main() {
    // Using errors.Is for sentinel check
    err := processOrder("123")
    if errors.Is(err, ErrNotFound) {
        fmt.Println("Order not found - create new one")
    }

    // Using errors.As for type assertion
    var valErr *ValidationError
    if errors.As(err, &valErr) {
        fmt.Printf("Field %s invalid: %s\n", valErr.Field, valErr.Message)
    }

    // Error chain inspection
    fmt.Println("Full error chain:")
    for err != nil {
        fmt.Printf("  - %v\n", err)
        err = errors.Unwrap(err)
    }
}

func processOrder(id string) error {
    return fmt.Errorf("processing order %s: %w", id,
        fmt.Errorf("validation: %w",
            &ValidationError{Field: "quantity", Message: "must be positive"}))
}
```

### 2.6 Result/Option Pattern (Functional Error Handling)

```typescript
// ═══════════════════════════════════════════════════════════════════════════
// TYPESCRIPT - Result pattern (Rust-inspired)
// ═══════════════════════════════════════════════════════════════════════════

// Result type - either success with value or failure with error
type Result<T, E> =
    | { ok: true; value: T }
    | { ok: false; error: E };

// Helper constructors
const Ok = <T>(value: T): Result<T, never> => ({ ok: true, value });
const Err = <E>(error: E): Result<never, E> => ({ ok: false, error });

// Option type - value may or may not exist
type Option<T> =
    | { some: true; value: T }
    | { some: false };

const Some = <T>(value: T): Option<T> => ({ some: true, value });
const None: Option<never> = { some: false };

// Example: Parsing that can fail
function parseNumber(input: string): Result<number, string> {
    const num = Number(input);
    if (isNaN(num)) {
        return Err(`Cannot parse "${input}" as number`);
    }
    return Ok(num);
}

// Example: Lookup that may not find value
function findUser(id: string): Option<{ name: string }> {
    const users: Record<string, { name: string }> = {
        "1": { name: "Alice" },
        "2": { name: "Bob" }
    };
    const user = users[id];
    return user ? Some(user) : None;
}

// Chaining Results (like Rust's and_then)
function map<T, U, E>(result: Result<T, E>, fn: (t: T) => U): Result<U, E> {
    if (result.ok) {
        return Ok(fn(result.value));
    }
    return result;
}

function flatMap<T, U, E>(
    result: Result<T, E>,
    fn: (t: T) => Result<U, E>
): Result<U, E> {
    if (result.ok) {
        return fn(result.value);
    }
    return result;
}

// Usage
function processInput(input: string): Result<number, string> {
    const parsed = parseNumber(input);
    return map(parsed, (n) => n * 2);
}

const result = processInput("42");
if (result.ok) {
    console.log(`Success: ${result.value}`);  // 84
} else {
    console.log(`Error: ${result.error}`);
}
```

```python
# ═══════════════════════════════════════════════════════════════════════════
# PYTHON - Result pattern with dataclasses
# ═══════════════════════════════════════════════════════════════════════════
from dataclasses import dataclass
from typing import TypeVar, Generic, Callable, Union

T = TypeVar('T')
E = TypeVar('E')
U = TypeVar('U')


@dataclass
class Ok(Generic[T]):
    value: T

    def is_ok(self) -> bool:
        return True

    def is_err(self) -> bool:
        return False

    def map(self, fn: Callable[[T], U]) -> 'Result[U, E]':
        return Ok(fn(self.value))

    def flat_map(self, fn: Callable[[T], 'Result[U, E]']) -> 'Result[U, E]':
        return fn(self.value)

    def unwrap(self) -> T:
        return self.value

    def unwrap_or(self, default: T) -> T:
        return self.value


@dataclass
class Err(Generic[E]):
    error: E

    def is_ok(self) -> bool:
        return False

    def is_err(self) -> bool:
        return True

    def map(self, fn: Callable) -> 'Result[T, E]':
        return self

    def flat_map(self, fn: Callable) -> 'Result[T, E]':
        return self

    def unwrap(self) -> T:
        raise ValueError(f"Called unwrap on Err: {self.error}")

    def unwrap_or(self, default: T) -> T:
        return default


Result = Union[Ok[T], Err[E]]


# Usage
def parse_int(s: str) -> Result[int, str]:
    try:
        return Ok(int(s))
    except ValueError:
        return Err(f"Cannot parse '{s}' as int")


def divide(a: int, b: int) -> Result[float, str]:
    if b == 0:
        return Err("Division by zero")
    return Ok(a / b)


# Chaining
result = (
    parse_int("10")
    .flat_map(lambda x: divide(x, 2))
    .map(lambda x: x * 100)
)

match result:
    case Ok(value):
        print(f"Success: {value}")
    case Err(error):
        print(f"Error: {error}")
```

### 2.7 finally vs return Value (Interview Trap!)

```java
// ═══════════════════════════════════════════════════════════════════════════
// JAVA - finally always runs, but what about return?
// ═══════════════════════════════════════════════════════════════════════════
public class FinallyTrap {

    // TRAP 1: What does this return?
    public static int trap1() {
        try {
            return 1;
        } finally {
            return 2;  // WARNING: finally overrides try's return!
        }
    }
    // Answer: 2 (finally's return overrides try's return)

    // TRAP 2: What does this return?
    public static int trap2() {
        int x = 0;
        try {
            x = 1;
            return x;  // Return value is CAPTURED here (1)
        } finally {
            x = 2;     // Modifies x but NOT the captured return value
        }
    }
    // Answer: 1 (return value was captured before finally ran)

    // TRAP 3: What happens here?
    public static int trap3() {
        try {
            throw new RuntimeException("Error!");
        } finally {
            return 3;  // WARNING: Swallows the exception!
        }
    }
    // Answer: 3 (return in finally suppresses the exception - very bad!)

    // BEST PRACTICE: Never return or throw in finally
    public static int correct() {
        int result = 0;
        try {
            result = computeValue();
            return result;
        } catch (Exception e) {
            // Handle or rethrow
            throw new RuntimeException("Computation failed", e);
        } finally {
            // Only cleanup here, no return or throw
            cleanup();
        }
    }

    private static int computeValue() { return 42; }
    private static void cleanup() { System.out.println("Cleanup!"); }

    public static void main(String[] args) {
        System.out.println("trap1: " + trap1());  // 2
        System.out.println("trap2: " + trap2());  // 1
        System.out.println("trap3: " + trap3());  // 3 (exception swallowed!)
    }
}
```

```python
# ═══════════════════════════════════════════════════════════════════════════
# PYTHON - Same traps exist!
# ═══════════════════════════════════════════════════════════════════════════

def trap1():
    try:
        return 1
    finally:
        return 2  # Overrides!

def trap2():
    x = 0
    try:
        x = 1
        return x  # Value captured
    finally:
        x = 2  # Too late, return value already captured

def trap3():
    try:
        raise Exception("Error!")
    finally:
        return 3  # Swallows exception!

print(f"trap1: {trap1()}")  # 2
print(f"trap2: {trap2()}")  # 1
print(f"trap3: {trap3()}")  # 3

# Python's unique 'else' clause
def with_else():
    try:
        result = 10 / 2
    except ZeroDivisionError:
        print("Division by zero!")
        result = 0
    else:
        # Only runs if NO exception occurred
        print("Success, no exception!")
    finally:
        print("Always cleanup")
    return result

with_else()  # Prints: Success, no exception! then Always cleanup
```

### 2.8 Python's Exception Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PYTHON EXCEPTION HIERARCHY                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                         BaseException                                       │
│                              │                                              │
│        ┌───────────┬────────┼────────┬───────────┐                         │
│        │           │        │        │           │                         │
│   SystemExit  KeyboardInterrupt  GeneratorExit  Exception                  │
│                                                       │                     │
│        ┌──────────┬───────────┬───────────┬──────────┼──────────┐          │
│        │          │           │           │          │          │          │
│   StopIteration  ArithmeticError  LookupError  OSError  ValueError  ...    │
│                       │               │          │                         │
│              ┌────────┴────┐    ┌─────┴─────┐    │                         │
│              │             │    │           │    │                         │
│        ZeroDivisionError  │  KeyError  IndexError  │                       │
│                     OverflowError          FileNotFoundError               │
│                                            PermissionError                 │
│                                                                             │
│   RULE: `except Exception` catches most errors but NOT:                    │
│         - SystemExit (sys.exit())                                          │
│         - KeyboardInterrupt (Ctrl+C)                                       │
│         - GeneratorExit                                                    │
│                                                                             │
│   NEVER: `except BaseException` (catches too much!)                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

```python
# ═══════════════════════════════════════════════════════════════════════════
# PYTHON - Proper exception handling patterns
# ═══════════════════════════════════════════════════════════════════════════
import sys

# BAD: Catches Ctrl+C and sys.exit()!
def bad_catch():
    try:
        sys.exit(1)
    except:  # Bare except = except BaseException
        print("Caught everything!")  # This runs!

# GOOD: Let system exceptions propagate
def good_catch():
    try:
        risky_operation()
    except Exception as e:  # Only application errors
        print(f"Application error: {e}")
        # Ctrl+C and sys.exit() will propagate normally

# Exception chaining
def outer():
    try:
        inner()
    except ValueError as e:
        raise RuntimeError("Outer failed") from e  # Chains exceptions

def inner():
    raise ValueError("Inner failed")

# Suppress exception chain (not recommended usually)
def suppress_chain():
    try:
        inner()
    except ValueError:
        raise RuntimeError("Outer failed") from None  # Hides original

# Re-raise with context
def reraise():
    try:
        inner()
    except ValueError:
        # Log, cleanup, then re-raise original
        print("Logging error...")
        raise  # Re-raises the current exception with traceback intact

# Context manager for exception handling
from contextlib import contextmanager

@contextmanager
def handle_errors(error_type, message):
    try:
        yield
    except error_type as e:
        raise RuntimeError(message) from e

# Usage
with handle_errors(ValueError, "Processing failed"):
    int("not a number")
```

### 2.9 Spark Exception Handling (Distributed!)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SPARK EXCEPTION CHALLENGES                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   CHALLENGE 1: Exceptions in Transformations                                │
│   ─────────────────────────────────────────────                             │
│   • map(), filter() run on EXECUTORS, not driver                           │
│   • Exception must be serializable to cross network                        │
│   • Stack traces are from executor, not driver context                     │
│                                                                             │
│   CHALLENGE 2: Lazy Evaluation                                              │
│   ─────────────────────────────────                                         │
│   • Errors don't occur until ACTION is called                              │
│   • try/catch at definition time catches NOTHING                           │
│                                                                             │
│   CHALLENGE 3: Partial Failures                                             │
│   ───────────────────────────────                                           │
│   • One executor fails but others succeed                                  │
│   • Re-computation of failed partitions                                    │
│   • Non-deterministic UDFs cause inconsistency                             │
│                                                                             │
│   BEST PRACTICES:                                                           │
│   ✅ Use try-except INSIDE UDFs (catch per-record errors)                  │
│   ✅ Return null/None for bad records, filter later                        │
│   ✅ Use accumulators to track error counts                                │
│   ✅ Wrap actions (collect, show) in try-except                            │
│   ❌ Don't use mutable state in UDFs                                       │
│   ❌ Don't throw exceptions that break entire job                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

```python
# ═══════════════════════════════════════════════════════════════════════════
# SPARK - Exception handling in distributed context
# ═══════════════════════════════════════════════════════════════════════════
from pyspark.sql import SparkSession
from pyspark.sql.functions import udf, col, when, lit
from pyspark.sql.types import IntegerType, StringType, StructType, StructField
from pyspark.sql.utils import AnalysisException
from py4j.protocol import Py4JJavaError

spark = SparkSession.builder \
    .appName("ExceptionHandling") \
    .getOrCreate()

# ─────────────────────────────────────────────────────────────────────────────
# PATTERN 1: Safe UDF with internal error handling
# ─────────────────────────────────────────────────────────────────────────────
def safe_parse_int(value):
    """Returns None for unparseable values instead of throwing."""
    try:
        if value is None:
            return None
        return int(value)
    except (ValueError, TypeError):
        return None  # Bad record → null

safe_parse_int_udf = udf(safe_parse_int, IntegerType())

df = spark.createDataFrame([
    ("1",), ("2",), ("bad",), (None,), ("5",)
], ["value"])

result = df.withColumn("parsed", safe_parse_int_udf(col("value")))
result.show()
# +-----+------+
# |value|parsed|
# +-----+------+
# |    1|     1|
# |    2|     2|
# |  bad|  null|  ← Error handled gracefully
# | null|  null|
# |    5|     5|
# +-----+------+

# ─────────────────────────────────────────────────────────────────────────────
# PATTERN 2: Accumulator for error tracking
# ─────────────────────────────────────────────────────────────────────────────
error_count = spark.sparkContext.accumulator(0)

def parse_with_tracking(value):
    global error_count
    try:
        return int(value)
    except (ValueError, TypeError):
        error_count.add(1)  # Track error count
        return None

parse_udf = udf(parse_with_tracking, IntegerType())

result = df.withColumn("parsed", parse_udf(col("value")))
result.collect()  # Trigger computation

print(f"Total parse errors: {error_count.value}")  # 1

# ─────────────────────────────────────────────────────────────────────────────
# PATTERN 3: Handling exceptions in actions
# ─────────────────────────────────────────────────────────────────────────────
def safe_spark_operation(operation_func, error_message="Spark operation failed"):
    """Wrapper for Spark operations with proper error handling."""
    try:
        return operation_func()
    except AnalysisException as e:
        # Schema/column issues
        print(f"Analysis error: {e.desc}")
        return None
    except Py4JJavaError as e:
        # JVM-side exceptions
        java_exception = e.java_exception
        print(f"Java error: {java_exception.getMessage()}")
        return None
    except Exception as e:
        print(f"{error_message}: {e}")
        return None

# Usage
result = safe_spark_operation(
    lambda: df.select("nonexistent_column").collect(),
    "Column selection failed"
)

# ─────────────────────────────────────────────────────────────────────────────
# PATTERN 4: Handling bad records in file reads
# ─────────────────────────────────────────────────────────────────────────────

# Method A: PERMISSIVE mode (default) - nulls for corrupt fields
df_permissive = spark.read \
    .option("mode", "PERMISSIVE") \
    .option("columnNameOfCorruptRecord", "_corrupt") \
    .json("data.json")

# Method B: DROPMALFORMED - skip bad records
df_dropped = spark.read \
    .option("mode", "DROPMALFORMED") \
    .json("data.json")

# Method C: FAILFAST - fail on first bad record
try:
    df_strict = spark.read \
        .option("mode", "FAILFAST") \
        .json("data.json")
except Exception as e:
    print(f"Bad data detected: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# PATTERN 5: Custom exception handling in foreachPartition
# ─────────────────────────────────────────────────────────────────────────────
def process_partition(partition):
    """Process partition with per-record error handling."""
    results = []
    errors = []

    for row in partition:
        try:
            # Process row
            processed = row.value.upper()
            results.append(processed)
        except Exception as e:
            errors.append({
                "row": str(row),
                "error": str(e)
            })

    # Could write errors to dead-letter queue here
    if errors:
        print(f"Partition had {len(errors)} errors")

    return iter(results)

# Apply to RDD (for complex processing)
df.rdd.mapPartitions(process_partition).collect()

# ─────────────────────────────────────────────────────────────────────────────
# ANTI-PATTERN: This doesn't work as expected!
# ─────────────────────────────────────────────────────────────────────────────

# WRONG: try-except at transformation definition time
try:
    # This try-except does NOTHING because map is lazy!
    problematic_df = df.rdd.map(lambda x: int(x.value))
except ValueError:
    print("This never prints!")  # Exceptions happen at ACTION time

# The exception actually occurs here, during the action:
# problematic_df.collect()  # Would throw here
```

---

## Section 3: Design Philosophy Links (공식 문서)

### 3.1 Official Documentation

| Language | Exception Documentation |
|----------|------------------------|
| **Java** | [Java Exception Handling](https://docs.oracle.com/javase/tutorial/essential/exceptions/) |
| **Python** | [Python Errors and Exceptions](https://docs.python.org/3/tutorial/errors.html) |
| **TypeScript** | [TypeScript Error Handling](https://www.typescriptlang.org/docs/handbook/2/narrowing.html#type-predicates) |
| **Go** | [Error Handling in Go](https://go.dev/blog/error-handling-and-go) |
| **Go** | [Working with Errors in Go 1.13](https://go.dev/blog/go1.13-errors) |
| **C++** | [C++ Exceptions](https://en.cppreference.com/w/cpp/language/exceptions) |
| **Spark** | [Spark Error Handling](https://spark.apache.org/docs/latest/sql-ref-null-semantics.html) |

### 3.2 Foundational Articles

| Topic | Resource |
|-------|----------|
| **Go Error Philosophy** | [Errors are values](https://go.dev/blog/errors-are-values) - Rob Pike |
| **Java Best Practices** | [Effective Java - Exceptions](https://www.oracle.com/technical-resources/articles/enterprise-architecture/effective-exceptions.html) |
| **Result Pattern** | [Rust Error Handling](https://doc.rust-lang.org/book/ch09-00-error-handling.html) |
| **C++ RAII** | [RAII - Resource Acquisition Is Initialization](https://en.cppreference.com/w/cpp/language/raii) |

---

## Section 4: Palantir Context Hint (팔란티어 맥락)

### 4.1 Foundry Error Handling Best Practices

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FOUNDRY ERROR HANDLING PATTERNS                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   TRANSFORMS (Spark-based)                                                  │
│   ────────────────────────                                                  │
│   • Use PERMISSIVE mode for data ingestion                                 │
│   • Implement dead-letter datasets for failed records                      │
│   • Track error metrics in dataset metadata                                │
│   • Never let one bad record kill entire pipeline                          │
│                                                                             │
│   CODE REPOSITORIES                                                        │
│   ─────────────────                                                        │
│   • Prefer Result types over exceptions for business logic                 │
│   • Use checked exceptions for I/O operations (Java repos)                 │
│   • Log errors with Foundry's logging infrastructure                       │
│   • Include correlation IDs for distributed tracing                        │
│                                                                             │
│   PIPELINE DESIGN                                                          │
│   ───────────────                                                          │
│   • Fail fast in validation transforms                                     │
│   • Implement retry logic with exponential backoff                         │
│   • Set up alerts on error rate thresholds                                 │
│   • Design for partial failure recovery                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Spark Exception Interview Topics

```python
# ═══════════════════════════════════════════════════════════════════════════
# INTERVIEW: Spark exception serialization problem
# ═══════════════════════════════════════════════════════════════════════════

# Q: Why does this code fail?
class CustomException(Exception):
    def __init__(self, message, connection):
        super().__init__(message)
        self.connection = connection  # Non-serializable!

# A: Exceptions in UDFs must be serializable because they cross network
# boundaries from executor to driver. The 'connection' object cannot be
# serialized, causing the job to fail.

# SOLUTION: Only include serializable data in exceptions
class SafeCustomException(Exception):
    def __init__(self, message, connection_info: str):
        super().__init__(message)
        self.connection_info = connection_info  # String is serializable
```

### 4.3 Common Interview Questions

#### Question 1: Java Checked vs Unchecked
```
Q: When should you use checked vs unchecked exceptions in Java?

A: Use CHECKED exceptions when:
   - Caller can reasonably be expected to recover
   - It's an anticipated failure (file not found, network error)
   - You want to force the caller to handle it

   Use UNCHECKED exceptions when:
   - It's a programming error (null pointer, bad argument)
   - Recovery is unlikely or impossible
   - Requiring handling would clutter code unnecessarily

   Modern trend: Prefer unchecked exceptions with clear documentation.
   Spring Framework uses unchecked exceptions extensively.
```

#### Question 2: Go's Error Philosophy
```
Q: Why doesn't Go have exceptions? How does this affect code design?

A: Go's philosophy: "Errors are values, not control flow."

   Benefits:
   - Explicit error handling at every step
   - No hidden control flow jumps
   - Errors can be passed, stored, manipulated like any value

   Challenges:
   - More verbose code (if err != nil everywhere)
   - Can lead to repetitive error checking

   Design impact:
   - Functions return (result, error) pairs
   - Use defer for cleanup instead of finally
   - Use panic only for truly unrecoverable situations
```

#### Question 3: TypeScript Exceptions Lose Type Info
```
Q: What's the problem with exception handling in TypeScript?

A: TypeScript cannot type catch blocks. The caught value is 'unknown'.

   Problem:
   - throw can throw ANY value (string, number, Error, etc.)
   - No way to declare what a function might throw
   - Type information is lost at catch boundaries

   Solutions:
   - Always check instanceof before using caught value
   - Use Result<T, E> pattern for type-safe error handling
   - Create type guards for custom errors

   function isMyError(e: unknown): e is MyError {
       return e instanceof MyError;
   }
```

#### Question 4: finally and return
```
Q: What does this code return? Why?

public int test() {
    try {
        return 1;
    } finally {
        return 2;
    }
}

A: Returns 2.

   Explanation:
   1. try block executes, return 1 is prepared
   2. Before returning, finally block MUST execute
   3. finally block has its own return 2
   4. finally's return replaces try's return

   This is why: NEVER put return in finally block!
   It can also suppress exceptions, which is dangerous.
```

#### Question 5: Spark Exception in map()
```
Q: How do you handle exceptions in Spark's map() operation?

A: Handle INSIDE the UDF, not outside:

   WRONG:
   try:
       df.rdd.map(risky_function).collect()  # Exception at collect time
   except:
       pass

   CORRECT:
   def safe_function(x):
       try:
           return risky_operation(x)
       except Exception:
           return None  # Or default value

   df.rdd.map(safe_function).collect()

   Key points:
   - Exceptions occur on executors, not driver
   - Must be serializable to propagate
   - Handle per-record to avoid killing entire job
   - Use accumulators to track error counts
```

---

## Section 5: Cross-References (관련 개념)

### 5.1 Related Knowledge Base Articles

| Concept ID | Topic | Relationship |
|------------|-------|--------------|
| **F05** | Control Flow | Exception handling is a form of non-local control flow |
| **F10** | Functions | Exception propagation through call stack |
| **F20** | Classes/OOP | Custom exception hierarchies |
| **F30** | File I/O | I/O operations are primary exception sources |
| **F34** | Concurrency | Thread-safe exception handling, async exceptions |
| **F40** | Testing | Testing exception scenarios |
| **F50** | Design Patterns | Error handling patterns (Result, Option) |

### 5.2 Concept Dependencies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EXCEPTION HANDLING DEPENDENCIES                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   PREREQUISITE CONCEPTS                                                     │
│   ─────────────────────                                                     │
│   F01 Variables ──→ Understanding stack allocation                         │
│   F05 Control Flow ──→ Understanding program flow                          │
│   F10 Functions ──→ Call stack concept                                     │
│   F20 Classes ──→ Exception class hierarchies                              │
│                                                                             │
│   BUILDS TOWARD                                                            │
│   ─────────────                                                            │
│   F30 File I/O ←── Primary use case for exception handling                 │
│   F34 Concurrency ←── Async exception patterns                             │
│   F50 Patterns ←── Error handling as design pattern                        │
│   Spark/Distributed ←── Serializable exceptions                            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.3 Interview Question Map

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    INTERVIEW TOPIC COVERAGE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   TOPIC                          │ SECTION │ DIFFICULTY                    │
│   ───────────────────────────────┼─────────┼─────────────────              │
│   try-catch-finally basics       │ 2.2     │ ★☆☆ Beginner                  │
│   Custom exceptions              │ 2.4     │ ★★☆ Intermediate              │
│   Java checked vs unchecked      │ 2.3     │ ★★☆ Intermediate              │
│   Go error handling              │ 2.5     │ ★★☆ Intermediate              │
│   Result/Option pattern          │ 2.6     │ ★★★ Advanced                  │
│   finally trap questions         │ 2.7     │ ★★★ Advanced                  │
│   Python exception hierarchy     │ 2.8     │ ★★☆ Intermediate              │
│   Spark exception handling       │ 2.9     │ ★★★ Advanced                  │
│   Exception serialization        │ 4.2     │ ★★★ Advanced                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Summary Cheat Sheet

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    EXCEPTION HANDLING CHEAT SHEET                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   JAVA:     try { } catch (Ex e) { } finally { }                           │
│             throw new Exception();                                          │
│             Checked: IOException (must handle)                              │
│             Unchecked: RuntimeException (optional)                          │
│                                                                             │
│   PYTHON:   try: except Ex as e: else: finally:                            │
│             raise Exception()                                               │
│             raise NewError() from original_error                            │
│             BaseException > Exception > specific                            │
│                                                                             │
│   TYPESCRIPT: try { } catch (e: unknown) { } finally { }                   │
│               throw new Error();                                            │
│               No typed catch blocks!                                        │
│                                                                             │
│   GO:       NO TRY-CATCH! Errors are values.                               │
│             result, err := func()                                          │
│             if err != nil { return err }                                   │
│             defer cleanup() // Like finally                                │
│             errors.Is() / errors.As() for checking                         │
│                                                                             │
│   C++:      try { } catch (const Ex& e) { } catch (...) { }               │
│             throw std::runtime_error("msg");                               │
│             RAII for cleanup (not finally!)                                │
│             noexcept specification                                          │
│                                                                             │
│   SQL:      BEGIN TRY ... END TRY BEGIN CATCH ... END CATCH               │
│             THROW 50001, 'msg', 1;                                         │
│             ERROR_NUMBER(), ERROR_MESSAGE()                                │
│                                                                             │
│   SPARK:    Handle INSIDE UDFs, not outside!                               │
│             Return null for bad records                                    │
│             Use accumulators for error counts                              │
│             Exceptions must be serializable                                │
│                                                                             │
│   GOLDEN RULES:                                                            │
│   • Never return in finally                                                │
│   • Never catch Exception/BaseException unless re-throwing                 │
│   • Always include context in error messages                               │
│   • In Go, always check err != nil immediately                            │
│   • In Spark, handle errors per-record, not per-job                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

> **Last Updated**: 2026-01-18
> **Version**: 1.0
> **Author**: ODA Knowledge Base Generator
> **Review Status**: Ready for Interview Prep
