# E2E TEST PLAN: Palantir FDE Learning System
**Target:** Validate End-to-End User Flow
**Date:** 2026-01-01
**Tester:** Gemini 3.0 Pro

## 1. Objective
To verify that the "Amnesiac Bug" is truly fixed and that the system supports a full learning cycle:
1.  **Recommendation** (What should I learn?)
2.  **Action** (I learned it!)
3.  **Update** (System updates BKT model)
4.  **Adaptation** (System recommends *new* topic)

## 2. Test Scenario: "The OSDK Journey"
**Actor:** `learner_e2e_001`
**Flow:**
1.  **Initial State Check:** Verify learner does not exist or is empty.
2.  **Step 1: Get Initial Recommendation.**
    - Expectation: `osdk.beginner.intro` (or similar foundational topic).
    - Action: Call `GetRecommendationAction`.
3.  **Step 2: Simulate Learning & Success.**
    - Action: Call `RecordAttemptAction` for the recommended topic with `correct=True`.
    - Repetition: Do this 3-4 times to ensure Mastery threshold (0.95) is reached.
4.  **Step 3: Get Follow-up Recommendation.**
    - Expectation: System should **NOT** recommend `osdk.beginner.intro` anymore.
    - Expectation: System **SHOULD** recommend `osdk.beginner.install` (the prerequisite unlocked).

## 3. Implementation Strategy
We will create a standalone Python script `tests/e2e/verify_flow.py` that:
- Imports the Action classes from `scripts/ontology/fde_learning/actions.py`.
- Mocks the `ActionContext` (since we are running outside the full Orion Kernel).
- Executes `apply_edits` directly.
- Asserts results programmatically.

## 4. Success Criteria
- [ ] Database file `learner_state.db` is created/updated.
- [ ] Mastery score increases monotonically.
- [ ] Recommendations change dynamically based on mastery.
