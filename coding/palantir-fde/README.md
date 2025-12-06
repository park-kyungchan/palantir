# Palantir Frontend Engineer Interview Preparation

**Target Position:** Palantir Frontend Engineer (US)  
**Preparation Strategy:** Agile Learning with AI-Generated Knowledge Bases  
**Timeline:** 5-6 months (2-4 hours/day)  
**Tech Stack Coverage:** 26 technologies organized into 8 research groups

---

## 🎯 Project Overview

This repository contains a **hyper-personalized learning system** for Palantir FDE interview preparation, combining:

1. **8 Deep Research Knowledge Bases** (generated via Gemini Deep Research)
2. **Agile Learning Main Agent** (Gemini 3.0 Pro in Antigravity IDE)
3. **Practice Projects & Exercises** (hands-on coding)
4. **Interview-Ready Q&A Database** (extracted from KBs)

### Why This Approach?

- **No Generic Curriculum:** Learning path emerges from your questions, not pre-planned sequences
- **Palantir-Specific:** Every KB connects to Blueprint, Redoodle, Plottable, and Foundry
- **Universal Concepts:** Extract language-agnostic principles, not just framework syntax
- **Main Agent Integration:** AI tutor reads KBs on-demand, synthesizes cross-stack knowledge

---

## 📁 Project Structure

```
/home/palantir/coding/palantir-fde-prep/
├── 00_RESEARCH_PROMPTS.md          # 8 Deep Research prompts for Gemini
├── 01_PROJECT_STRUCTURE.md         # This directory layout explained
├── 02_MAIN_AGENT_DIRECTIVE.md      # Main Agent behavioral rules (for GEMINI.md)
├── 03_CROSS_REFERENCE_INDEX.md     # KB interconnections and concept links
├── README.md                        # This file
│
├── knowledge_bases/                 # Generated Deep Research outputs (8 markdown files)
│   ├── 01_language_foundation.md   # JavaScript ES6+, TypeScript (foundational)
│   ├── 02_react_ecosystem.md       # React, Blueprint, Redux/Redoodle (core)
│   ├── 03_styling_systems.md       # Sass/SCSS, CSS-in-JS (styling)
│   ├── 04_data_layer.md            # React Query, GraphQL, REST (data)
│   ├── 05_testing_pyramid.md       # Jest, RTL, Cypress/Playwright (testing)
│   ├── 06_build_tooling.md         # Webpack, Vite, Gradle (build)
│   ├── 07_version_control.md       # Git Advanced, GitHub/PR (collaboration)
│   └── 08_advanced_capabilities.md # D3.js, Web Workers, WebSocket, a11y (advanced)
│
├── practice/                        # Hands-on exercises
│   ├── algorithms/                  # LeetCode problems (Palantir interview patterns)
│   ├── blueprint-demos/             # Blueprint component practice
│   ├── system-design/               # Frontend architecture exercises
│   └── decomposition/               # Palantir-style decomposition problems
│
├── interview_prep/                  # Interview materials
│   ├── behavioral_qa.md             # Behavioral question responses
│   ├── technical_qa.md              # Compiled Q&A from all KBs
│   └── palantir_research.md         # Company mission, products, culture notes
│
└── projects/                        # Portfolio projects
    ├── data-dense-dashboard/        # Main project: Blueprint + D3 + Redux + GraphQL
    ├── d3-visualization/            # D3.js practice project
    └── mini-foundry/                # Simplified Foundry-style app
```

---

## 🚀 Quick Start Guide

### Phase 1: Generate Knowledge Bases (1-2 hours)

1. **Open Gemini Deep Research** (gemini.google.com/app - requires AI Ultra subscription)
2. **Upload Context File:** Create `palantir-fde-context.md` with:
   ```markdown
   # Palantir FDE Interview Preparation Context
   Target Position: Palantir Frontend Engineer (US)
   Candidate Background: Mathematics Education B.A., AI/ML systems expert
   Interview Focus: React, TypeScript, Blueprint UI, data-dense visualization
   Complete Technology List (26 total):
   TIER 1: TypeScript, JavaScript ES6+, React, Blueprint UI Toolkit
   TIER 2: Redux/Redux Toolkit, React Query, Sass/SCSS, CSS-in-JS, GraphQL, REST API
   TIER 3: Webpack, Vite, Gradle, Jest, React Testing Library, Cypress/Playwright
   TIER 4: Git Advanced, GitHub/PR, D3.js, Web Workers, WebSocket, Service Workers, a11y
   TIER 5: Node.js, Java basics, Go basics
   ```
3. **Run 8 Deep Research Queries** (copy from `00_RESEARCH_PROMPTS.md`)
   - Run 3-5 queries in parallel (separate browser tabs)
   - Each takes 5-10 minutes
   - Total: ~1-2 hours for all 8
4. **Export as Markdown** using "Gem Chat Exporter" Chrome extension
5. **Save to `knowledge_bases/`** with naming convention: `{NN}_{name}.md`

### Phase 2: Configure Main Agent (5 minutes)

1. **Open GEMINI.md:** `/home/palantir/.gemini/GEMINI.md`
2. **Add Directive:** Copy `<palantir_fde_learning_protocol>` section from `02_MAIN_AGENT_DIRECTIVE.md`
3. **Insert Location:** After `<orion_framework_directives>` section (around line 150)
4. **Save & Verify:** Test with question "Explain TypeScript generics"

### Phase 3: Start Learning (Ongoing)

1. **Activate Learning Mode in Antigravity:**
   ```
   [SYSTEM MODE: Palantir FDE Learning]
   Knowledge Bases: /home/palantir/coding/palantir-fde-prep/knowledge_bases/
   Learning Mode: Completely Agile (student-driven)
   Response Structure: 7-component mandatory
   
   Ready for questions.
   ```
2. **Ask Questions** - Main Agent will:
   - Read relevant KB file(s) using `read_file` tool
   - Provide 7-component response:
     1. Universal Concept
     2. Technical Explanation (with code)
     3. Cross-Stack Comparison
     4. Palantir Context
     5. Design Philosophy (cited sources)
     6. Practice Exercise
     7. Adaptive Next Steps
3. **Build Projects** as you learn concepts
4. **Track Progress** in `interview_prep/technical_qa.md`

---

## 📊 26 Technologies by Priority

### MUST-MASTER (Priority 1)
✅ JavaScript ES6+  
✅ TypeScript  
✅ React  
✅ Blueprint UI Toolkit  
✅ Redux/Redux Toolkit  

**Why:** Palantir's core stack, directly tested in interviews

### SHOULD-KNOW (Priority 2)
✅ React Query  
✅ GraphQL  
✅ REST API  
✅ Sass/SCSS  
✅ Jest  
✅ React Testing Library  
✅ Git Advanced  

**Why:** Production-ready FDE profile, system design discussions

### NICE-TO-HAVE (Priority 3)
✅ D3.js  
✅ Webpack  
✅ Vite  
✅ CSS-in-JS  
✅ Cypress/Playwright  
✅ Web Workers  
✅ WebSocket  
✅ Service Workers  
✅ Accessibility  
✅ GitHub/PR workflows  

**Why:** Differentiate candidates, advanced capabilities

### CONTEXTUAL (Priority 4)
✅ Gradle  
✅ Node.js  
✅ Java basics  
✅ Go basics  

**Why:** Backend context for full-stack discussions

---

## 🎓 Learning Philosophy

### Agile Learning (No Pre-Planned Curriculum)

**Traditional Approach (Rejected):**
```
Week 1-2: JavaScript fundamentals
Week 3-4: TypeScript
Week 5-8: React
... (rigid sequence)
```

**Agile Approach (Adopted):**
```
You: "How do React hooks work?"
Agent: [Reads KB 02, synthesizes 7-component response]

You: "Wait, what's the event loop?" (random jump)
Agent: [Reads KB 01, explains event loop, connects back to hooks]

You: "Actually, show me Blueprint Table instead"
Agent: [Reads KB 02, explains Table, maintains coherence via universal concepts]
```

**Benefits:**
- ✅ Natural curiosity-driven learning
- ✅ Connects concepts organically (not artificial sequences)
- ✅ Mimics real interview flow (random topic jumps)
- ✅ Reveals gaps through questioning

### 7-Component Response Structure

Every Main Agent response includes:

1. **Universal Concept:** Language-agnostic principle
2. **Technical Explanation:** Code examples + reasoning
3. **Cross-Stack Comparison:** TypeScript/React/Java/Go/Python table
4. **Palantir Context:** Blueprint/Foundry usage with sources
5. **Design Philosophy:** Creator quotes (Anders Hejlsberg, Dan Abramov, etc.)
6. **Practice Exercise:** Interview-appropriate coding task
7. **Adaptive Next Steps:** Wait for student (no pre-planning)

---

## 🧪 Testing Your Setup

### Verification Checklist

**Knowledge Bases Generated:**
- [ ] 8 markdown files in `knowledge_bases/` directory
- [ ] Each file 2,000-3,000 words
- [ ] Bracketed citations [1], [2] present
- [ ] Cross-references to other groups included

**Main Agent Configured:**
- [ ] `02_MAIN_AGENT_DIRECTIVE.md` content added to GEMINI.md
- [ ] Test question: "Explain TypeScript generics"
- [ ] Response includes all 7 components
- [ ] Agent reads `01_language_foundation.md` via `read_file` tool

**Project Structure:**
- [ ] All directories created (`practice/`, `projects/`, `interview_prep/`)
- [ ] Git repository initialized
- [ ] README.md present (this file)

### Test Questions (Expected Behavior)

| Test Question | Expected KBs Read | Key Response Elements |
|---------------|-------------------|----------------------|
| "How do React hooks work?" | 02 (React), 01 (event loop) | useState example, lifecycle binding, Dan Abramov quote |
| "Explain TypeScript generics" | 01 (TS), 02 (Blueprint) | `<T>` syntax, Blueprint ITreeNode<T>, Anders Hejlsberg quote |
| "When to use Redux vs React Query?" | 02 (Redux), 04 (React Query) | Client vs server state decision matrix |
| "How to optimize Blueprint Table with 10K rows?" | 02 (Blueprint), 08 (Web Workers) | Virtualization, memoization, code examples |

If all 4 test questions return correct behavior → Setup successful ✅

---

## 📅 Suggested Timeline

### Months 1-2: Foundation
- **Focus:** JavaScript ES6+, TypeScript, React fundamentals
- **KBs:** 01, 02 (first half)
- **Practice:** 20-30 algorithm problems, basic React components
- **Project:** Start data-dense dashboard skeleton

### Months 3-4: Core Stack
- **Focus:** Blueprint UI, Redux/Redoodle, GraphQL, Testing
- **KBs:** 02 (second half), 04, 05
- **Practice:** Blueprint component demos, Jest+RTL tests
- **Project:** Complete dashboard with Blueprint + Redux + GraphQL

### Months 5-6: Advanced & Polish
- **Focus:** D3.js, WebSocket, System Design, Interview Prep
- **KBs:** 08, 03, 06, 07
- **Practice:** Decomposition exercises, mock interviews
- **Project:** Add D3 visualizations, real-time data, comprehensive tests

**Total:** 5-6 months at 2-4 hours/day

---

## 🎯 Interview Success Metrics

### Technical Mastery
- [ ] Can explain any of 26 technologies without notes
- [ ] Can code Blueprint components from scratch
- [ ] Can build full-stack feature (React + TypeScript + GraphQL + Tests)
- [ ] Can debug buggy code systematically (Palantir re-engineering interview)

### System Design
- [ ] Can decompose ambiguous problems (Palantir decomposition interview)
- [ ] Can design data-dense dashboard architecture
- [ ] Can justify technology choices with Palantir context

### Behavioral
- [ ] Can articulate why Palantir (mission, products, culture fit)
- [ ] Can discuss code review practices
- [ ] Can describe collaboration in complex projects

### Portfolio
- [ ] 1 major project (data-dense dashboard with Blueprint + D3 + Redux)
- [ ] Comprehensive tests (Jest + RTL + Playwright)
- [ ] Production deployment with CI/CD
- [ ] README explaining architecture decisions

---

## 🔧 Troubleshooting

### Issue: Agent doesn't read KB files
**Solution:** Verify files exist in `/home/palantir/coding/palantir-fde-prep/knowledge_bases/`
```bash
ls -la knowledge_bases/
```

### Issue: Agent suggests learning sequence
**Solution:** Remind agent of Rule #1: Never Pre-Plan
```
[REMINDER: Agile Learning Mode - respond to actual question only, do not suggest sequences]
```

### Issue: Missing Palantir context
**Solution:** Agent should cite Blueprint/Redoodle/Plottable GitHub sources
Check `03_CROSS_REFERENCE_INDEX.md` for Palantir-specific cross-references

### Issue: Code examples don't work
**Solution:** All code in KBs should be tested. If examples fail, update KB files

---

## 📚 Additional Resources

### Palantir-Specific
- [Blueprint UI GitHub](https://github.com/palantir/blueprint)
- [Redoodle GitHub](https://github.com/palantir/redoodle)
- [Plottable GitHub](https://github.com/palantir/plottable)
- [Palantir Engineering Blog](https://blog.palantir.com/engineering/home)

### Interview Preparation
- [Glassdoor Palantir Reviews](https://www.glassdoor.com/Interview/Palantir-Technologies-Software-Engineer-Interview-Questions-EI_IE236375.0,21_KO22,39.htm)
- [Interviewing.io Palantir Guide](https://interviewing.io/palantir-interview-questions)
- [LeetCode Palantir Tagged Problems](https://leetcode.com/company/palantir/)

### Technology Documentation
- [React Docs](https://react.dev)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [GraphQL Spec](https://graphql.org/learn/)
- [D3.js Docs](https://d3js.org/)

---

## 🤝 Contributing

This is a personal interview prep repository, but you can:
- Fork for your own Palantir FDE preparation
- Adapt the 8 KB structure for other companies (FAANG, etc.)
- Submit issues if you find errors in research prompts

---

## 📝 License

MIT License - Use freely for your own learning

---

## ✅ Final Checklist

**Setup Complete:**
- [ ] 8 Deep Research queries run successfully
- [ ] 8 KB markdown files exported to `knowledge_bases/`
- [ ] Main Agent directive added to GEMINI.md
- [ ] Test questions verify 7-component responses
- [ ] Project structure initialized with Git
- [ ] Learning mode activated in Antigravity

**Ready to Learn:**
- [ ] First question asked → Main Agent responds correctly
- [ ] Practice exercises started
- [ ] First project initialized

**Estimated Time to Interview-Ready:** 5-6 months with consistent daily practice

---

**Last Updated:** 2025-12-06  
**Version:** 1.0  
**Author:** 박경찬  
**Target:** Palantir Frontend Engineer (US), Fall 2026-2028 PhD admission timeline
