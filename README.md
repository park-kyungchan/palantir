# Palantir Development Workspace

A personal development workspace featuring Ontology-Driven Architecture (ODA) for AI agent orchestration, document processing utilities, and Personal AI Infrastructure (PAI) integration.

## Workspace Structure

```
/home/palantir/
├── .agent/                    # Agent state, database, and runtime files
├── .claude/                   # Claude Code configuration with ODA governance
│   ├── CLAUDE.md              # Main agent orchestration rules (ODA v4.0)
│   ├── references/            # Protocol references and capability docs
│   ├── skills/                # Workflow definitions (/plan, /audit, etc.)
│   └── agents/                # Specialized agent behaviors
├── park-kyungchan/palantir/   # Main ODA project (Python/Pydantic)
│   ├── lib/oda/               # ODA kernel and ontology system
│   └── governance/            # Governance rules and policies
├── hwpx/                      # HWPX document reconstruction pipeline
├── lib/                       # Shared libraries
│   └── owpml/                 # OWPML namespace definitions
└── docs/                      # Documentation
```

## Key Projects

### ODA Framework
Ontology-Driven Architecture implementation with 3-Stage Protocol:
1. **Stage A (SCAN)**: Establish reality with evidence
2. **Stage B (TRACE)**: Verify before changes
3. **Stage C (VERIFY)**: Quality gates

### HWPX Pipeline
PDF/HWPX document conversion for Hancom Office 2024.

## Getting Started

```bash
cd park-kyungchan/palantir
source .venv/bin/activate
python scripts/engine.py init
```

## ODA Skills

| Command | Purpose |
|---------|--------|
| `/plan` | 3-Stage planning |
| `/audit` | Code audit |
| `/deep-audit` | Deep analysis |

---
*Powered by ODA v4.0*
