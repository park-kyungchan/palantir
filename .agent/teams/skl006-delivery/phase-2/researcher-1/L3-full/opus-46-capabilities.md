# Opus 4.6 Model Capabilities — Raw Research Data

## Sources
- https://www.anthropic.com/news/claude-opus-4-6
- https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-6
- https://platform.claude.com/docs/en/build-with-claude/effort
- https://platform.claude.com/docs/en/build-with-claude/compaction

## 1. Model Specifications

### Context Window
- **Standard:** 200K tokens
- **Extended (beta):** 1M tokens with premium pricing ($10/$37.50 per MTok)
- **Max output tokens:** 128K (doubled from 64K in Opus 4.5)

### Model ID
- `claude-opus-4-6`

### Pricing
- Standard: $5/$25 per million tokens (input/output)
- 1M context premium: $10/$37.50 per MTok
- US-only inference: 1.1x multiplier
- Fast mode: $30/$150 per MTok (2.5x speed, premium pricing)

## 2. New Features in Opus 4.6

### Adaptive Thinking Mode (NEW — replaces budget_tokens)
- `thinking: {type: "adaptive"}` is the RECOMMENDED mode
- Claude dynamically decides when and how much to think
- At default effort (high), Claude almost always thinks
- At lower effort, may skip thinking for simpler problems
- `thinking: {type: "enabled"}` and `budget_tokens` are DEPRECATED on Opus 4.6
- Adaptive thinking automatically enables interleaved thinking

### Effort Parameter (GA — no beta header required)
- Four levels: `low`, `medium`, `high` (default), `max`
- `max` is Opus 4.6 ONLY — returns error on other models
- Affects ALL tokens: text, tool calls, AND extended thinking
- Does NOT require thinking to be enabled
- Configured via `output_config.effort` in API
- Works alongside extended thinking AND independently

#### Effort Level Details:
| Level  | Description | Use Case |
|--------|-------------|----------|
| max    | Absolute maximum, no constraints | Deepest reasoning, Opus 4.6 only |
| high   | Default, same as not setting | Complex reasoning, agentic tasks |
| medium | Balanced token savings | Speed/cost/performance balance |
| low    | Most efficient, significant savings | Simple tasks, subagents |

#### Effort + Tool Use:
- Lower effort → fewer tool calls, less preamble, terse confirmations
- Higher effort → more tool calls, explains plans, detailed summaries

### Compaction API (Beta)
- Server-side context summarization for infinite conversations
- Beta header: `compact-2026-01-12`
- Only supported on Opus 4.6
- Trigger: configurable, default 150K tokens, minimum 50K
- Custom summarization instructions supported
- `pause_after_compaction` option for control
- Works with streaming, prompt caching, server tools
- Same model used for summarization (no cheaper model option)
- Usage reported in `iterations` array
- Can be combined with token counting endpoint

### Fast Mode (Research Preview)
- `speed: "fast"` — up to 2.5x faster output
- Premium pricing: $30/$150 per MTok
- Same model, same intelligence — just faster inference
- Beta header: `fast-mode-2026-02-01`

### 128K Output Tokens
- Doubled from 64K
- Enables longer thinking budgets
- Requires streaming for large max_tokens

### Data Residency Controls
- `inference_geo` parameter: `"global"` (default) or `"us"`
- US-only: 1.1x pricing on Opus 4.6+

### Fine-grained Tool Streaming (GA)
- Now GA on all models, no beta header required

## 3. Breaking Changes

### Prefill Removal
- Prefilling assistant messages NOT SUPPORTED on Opus 4.6
- Returns 400 error
- Alternatives: structured outputs, system prompt, output_config.format

### Tool Parameter Quoting
- Slightly different JSON string escaping in tool call arguments
- Standard parsers handle automatically
- Custom string parsing may need verification

### Deprecations
- `thinking: {type: "enabled", budget_tokens: N}` — deprecated, use adaptive thinking
- `interleaved-thinking-2025-05-14` beta header — deprecated, safely ignored
- `output_format` — moved to `output_config.format`

## 4. Benchmark Performance

- **Terminal-Bench 2.0:** Highest score (agentic coding)
- **Humanity's Last Exam:** Leads (multidisciplinary reasoning)
- **BrowseComp:** Best performance (information retrieval)
- **GDPval-AA:** 190 Elo advantage, outperforms GPT-5.2 by ~144 Elo
- **MRCR v2:** 76% on hardest variant (8 needles, 1M tokens) vs 18.5% prior
- **BigLaw Bench:** 90.2% (legal reasoning)
- **Computational biology/chemistry:** 2x improvement
- **Context rot:** Substantially reduced

## 5. Key Strengths for Multi-Agent Systems

### Agentic Capabilities
- Autonomously closed 13 issues, assigned 12 to correct teams in one day
- Managed ~50-person org across 6 repositories
- Handles product AND organizational decisions
- Knows when to escalate to human

### Long-Context Performance
- 76% on 8-needle-in-1M-token retrieval
- Drastically reduces "context rot"
- Plans more carefully
- Sustains agentic tasks longer
- Operates more reliably in larger codebases

### Safety Profile
- Low rates of misaligned behavior
- Lowest over-refusal rate among recent Claude models
- Enhanced with six new cybersecurity probes

## 6. Optimization Strategies

### Token Efficiency
1. Use `effort: "low"` for simple/subagent tasks
2. Use `effort: "medium"` for balanced agentic work
3. Reserve `effort: "high"/"max"` for complex reasoning
4. Dynamic effort adjustment based on task complexity

### Context Management
1. Server-side compaction for long conversations
2. Custom compaction instructions to preserve critical info
3. `pause_after_compaction` for injecting preserved messages
4. Token counting endpoint to check effective context

### Performance
1. Fast mode for latency-sensitive tasks
2. Streaming for large outputs
3. Parallel tool calls where possible
4. Adaptive thinking instead of fixed budget_tokens
