# HWPX Control Patterns

Based on the deep audit of the `ActionTable_2504.pdf` (containing 1,027 actions), three distinct control patterns have been identified. These patterns dictate how the `Compiler` and `Executor` interact with the Hancom Office API.

## Pattern A: Direct Run (Immediate Command)
Actions with no associated `ParameterSet ID` (marked as `-` or `None` in the database). These are simple toggle or navigator commands that require no configuration.
- **Count**: 394 Actions.
- **Examples**: `BreakPage` (Page Break), `Cancel` (ESC), `Copy`, `Paste`.
- **Implementation**:
  ```python
  hwp.Run("ActionID")
  ```

## Pattern B: Parameterized Action (Constructed Set)
Actions that require a `ParameterSet ID`. These represent the majority of document engineering tasks (approx. 60% of the database). They follow a 4-step lifecycle.
- **Count**: 633 Actions.
- **Examples**: `InsertText`, `TableCreate`, `CharShape`.
- **Implementation Lifecycle**:
  1. **CreateAction**: Instantiate the action object on the host.
  2. **CreateSet**: Create the associated parameter set object.
  3. **GetDefault**: Load current context into the set.
  4. **SetItem/Execute**: Modify parameters and commit the action.

## Pattern C: Dialog/Indirect Control (`*` Marked)
Actions marked with a `*` (e.g., `FindReplace*`) indicate that the action typically invokes a User Interface dialog or requires specialized OLE object manipulation beyond a simple `Execute` call.
- **Context**: Often requires `run_blocked = True` in the database to prevent hanging on modal dialogs during automated execution.
- **Strategy**: Use specialized compiler logic for these high-complexity tasks (e.g., global replacement).

## Governance Summary
The `ActionDatabase` serves as the arbiter for which pattern to apply. If a requested intent in the IR is mapped to an action with a `ParameterSet`, the compiler is governed to produce a multi-step command set rather than a raw `Run` call.
