# Implementer MEMORY

## math-question-bank Project Patterns

### Type sharing across client components (2026-02-19)
- When extracting a sub-component to its own file, ensure the exported type's interface
  matches the consuming module's expected shape (structural typing still requires matching fields).
- Pattern: export the full interface from the "source of truth" file; import type from there.
- Error seen: partial interface in modal file vs full interface in utils file → type mismatch at call site.

### Next.js App Router: Server Components in Client Components
- Server components used only in client component context become bundled as client code.
- Safe when: no server-only imports (`next/headers`, etc.), only pure React + synchronous libs (katex).
- SolutionExplanation + SolutionStepCard are safe to import from 'use client' parents.

### scroll-reveal with IntersectionObserver
- Custom hook pattern: `useRef` + `useEffect` attaches observer to ref.current.
- Adds `revealed` CSS class when element enters viewport.
- For step cards already rendered by a sub-component, use a separate `useEffect` that
  queries `.math-step-enter` in the DOM and adds `is-visible`. Run when `solutionSteps.length` changes.

### CSS @layer components — stagger-children specificity
- `.stagger-children.revealed > *` must come AFTER the per-nth-child delay rules.
  CSS specificity order in source matters for overrides within the same layer.
