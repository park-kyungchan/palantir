# Output Micro-Signal Format

> Shared resource for all pipeline skills. Defines the L1 micro-signal format that subagents write to their output files for Lead to read on completion.

## Micro-Signal Structure

```
{STATUS}|{key1}:{value1}|{key2}:{value2}|ref:{WORK_DIR}/{file}
```

- **STATUS**: `PASS`, `FAIL`, `PARTIAL`, `BLOCKED`
- **Metrics**: Pipe-delimited key:value pairs (skill-specific)
- **ref**: Path to full L2 detail file

### Examples

```
PASS|deps:12|hotspots:3|ref:tasks/w3-pipeline/p2-audit-static.md
FAIL|level:L2|missing:cycle_detection|ref:tasks/w3-pipeline/p2-audit-static.md
PARTIAL|coverage:75%|files:8/12|ref:tasks/w3-pipeline/p2-research-codebase.md
```

## L1 YAML Structure (in detail file)

Every skill output file begins with a YAML L1 block:

```yaml
domain: {skill domain}
skill: {skill name}
status: PASS|FAIL|PARTIAL
# ... skill-specific metrics
pt_signal: "metadata.phase_signals.{phase}_{domain}"
signal_format: "{STATUS}|{metrics}|ref:{WORK_DIR}/{file}"
```

## Token Budget

- Micro-signal: **≤50 tokens** (Lead context cost per agent completion)
- L1 YAML header: **≤200 tokens** (in detail file)
- L2 detail: **unlimited** (in detail file, read on-demand)

## Lead Parsing Contract

Lead parses micro-signals with this logic:
1. Split on `|` → first element = STATUS
2. If STATUS = `PASS` → continue pipeline
3. If STATUS = `FAIL` → apply D12 escalation ladder
4. If STATUS = `PARTIAL` → read ref file for coverage assessment
5. `ref:` field → path to detail file for on-demand reading
