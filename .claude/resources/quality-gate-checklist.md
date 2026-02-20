# Quality Gate Checklist

> Shared resource for all pipeline skills. Defines the standard Quality Gate framework.

## Universal Quality Gate Criteria

Every skill output must satisfy:

| # | Criterion | Check | Required? |
|---|---|---|---|
| 1 | All findings have evidence | Every claim references `file:line` or source URL | ✅ All skills |
| 2 | L1 micro-signal is valid | Parseable `STATUS\|metrics\|ref:path` format | ✅ All skills |
| 3 | Output file exists | Written to `tasks/{work_dir}/{phase}-{skill}.md` | ✅ All skills |
| 4 | Coverage reported | Scope completed vs total scope | ✅ Analysis skills |
| 5 | No out-of-scope modifications | Agent stayed within tool and scope boundaries | ✅ All skills |
| 6 | Failure handling applied | Failures documented with D12 level classification | ✅ On failure |

## Skill-Specific Criteria

Each skill adds domain-specific criteria on top of universals. These are defined in the skill's own `## Quality Gate` section and should NOT be duplicated here. Examples:

- **audit-static**: Every dependency edge has file:line evidence for both source and target
- **execution-code**: All tests pass after implementation
- **verify-quality**: Quality scores calculated for all files in scope

## PASS/FAIL Decision

```
IF all universal criteria MET AND all skill-specific criteria MET:
  → PASS
ELIF universal criteria MET but skill-specific PARTIAL:
  → PARTIAL (with coverage percentage)
ELSE:
  → FAIL (with failure classification per D12 ladder)
```

## Lead Autonomous Safety

> [!IMPORTANT]
> When Lead operates autonomously, Quality Gate is the PRIMARY safety mechanism. A skill reporting PASS when it should be FAIL can cascade errors through the entire pipeline. When in doubt, report PARTIAL — not PASS.
