---
description: Implement the approved plan with code generation and self-correction
---
1. **[Protocol Enforcement]**:
   - Run the enforcement script to verify context awareness.
   - If this fails, the workflow MUST stop.
// turbo
2. Run `python3 scripts/enforce_protocol.py --target={user_request_target}`

3. **[Execution]**:
   - Execute the approved plan using Orion Engine.
   - This includes built-in Causality Checks via WDE.
// turbo
4. Run `python3 scripts/orion.py --mode=execute`
5. If step 4 failed, STOP. Trigger Self-Improvement Loop.
// turbo
2. Run `make check-plan`
3. **[Counterpart Reading]**:
    - Before writing code, READ the consumer/producer code.
    - Example: If writing `backend/api/math.py`, READ `frontend/src/api/math.ts`.
4. Implement the changes defined in the plan.
    - Use `write_to_file` for new files.
    - Use `replace_file_content` or `multi_replace_file_content` for existing files.
    - **Rule**: Always update `package.json` or `requirements.txt` immediately if adding dependencies.
4. Perform a self-review of the generated code (Reflection).
    - Check for type safety.
    - Check for error handling.
    - Check for adherence to project style.
