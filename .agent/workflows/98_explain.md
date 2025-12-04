---
description: [SYSTEM] Explain technical concepts in plain language for the user
---
1. **[Context Analysis]**:
   - Identify the technical term or concept that confused the user (e.g., "Exit Code 1").
   - Determine the user's current understanding level based on conversation history.

2. **[Translation Strategy]**:
   - **Technical Natural Language**: Use precise terms but explain the *logic flow* in plain English.
   - **Pseudo-code Style**: "If X happens, then Y executes."
   - **Avoid Metaphors**: Do not use analogies like traffic lights. Focus on the actual mechanism.

3. **[Execution]**:
   - Output the explanation in a dedicated section: `### 🔍 Technical Logic: [Term]`
   - Explain the *Cause -> Effect* relationship clearly.

// turbo
4. Run `echo "✅ Explanation Protocol Loaded"`
