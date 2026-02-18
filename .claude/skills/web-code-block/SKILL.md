---
name: web-code-block
description: "[Atom·WebDesign·Content] Provides styled code display block with glass morphism background, line numbers, language label, and copy-to-clipboard button. Optional syntax highlighting via CSS classes. Monospace font with horizontal scroll. Use for code snippets, terminal output, or configuration examples. References web-design-tokens for glass and typography tokens."
user-invocable: true
argument-hint: "[language:js|css|html|bash|json] [line-numbers:true|false] [copy:true|false]"
---

# web-code-block

Atom-level code display block with glass morphism styling. Self-contained — no external
syntax highlighting library required. Uses regex-based highlighting for common languages.
Depends on `web-design-tokens` (tokens.css) for glass, font, and color tokens.

## Basic Usage

```html
<!-- Minimal: no extras -->
<div class="code-block">
  <pre><code>console.log('hello world');</code></pre>
</div>

<!-- With language label -->
<div class="code-block" data-language="javascript">
  <pre><code>const x = 42;</code></pre>
</div>

<!-- With copy button (requires code-block.js) -->
<div class="code-block" data-language="bash" data-copy>
  <pre><code>npm install && npm run dev</code></pre>
</div>

<!-- With line numbers -->
<div class="code-block" data-language="json" data-line-numbers>
  <pre><code>{"key": "value"}</code></pre>
</div>

<!-- All features -->
<div class="code-block" data-language="css" data-copy data-line-numbers>
  <pre><code>.glass { backdrop-filter: blur(16px); }</code></pre>
</div>
```

## Language Support (Built-in Highlighter)

| Language  | `data-language` | Highlights                              |
|-----------|----------------|-----------------------------------------|
| JavaScript| `javascript`   | keywords, strings, numbers, comments   |
| CSS       | `css`          | properties, values, selectors          |
| HTML      | `html`         | tags, attributes, strings              |
| Bash      | `bash`         | commands, flags, strings               |
| JSON      | `json`         | keys, strings, numbers, booleans       |

For languages not listed, the block renders with monospace styling but no color.

## Syntax Highlighting Classes

You can manually add these CSS classes to `<span>` elements inside `<code>`:

| Class          | Color       | Purpose              |
|----------------|-------------|----------------------|
| `.hl-keyword`  | cyan        | keywords, tags       |
| `.hl-string`   | orange      | strings, values      |
| `.hl-comment`  | muted       | comments             |
| `.hl-number`   | green       | numeric literals     |
| `.hl-property` | magenta     | CSS properties, keys |

## Copy Button Behavior

When `data-copy` is present and `code-block.js` is loaded:
1. A copy icon appears in the header
2. On click: `navigator.clipboard.writeText()` copies the raw text content
3. Icon changes to a checkmark for 2 seconds (WAAPI animation)
4. Falls back gracefully if clipboard API is unavailable

## Line Numbers

When `data-line-numbers` is present:
- CSS counter increments per line (via `::before` on each `<code>` line)
- Numbers appear in a fixed-width left column
- Scrolls with the code (not fixed position)

## Terminal / Command Output

Use the `terminal` variant for command output:
```html
<div class="code-block code-block--terminal" data-language="bash">
  <pre><code>$ npm run build
✓ Compiled in 1.2s
✓ 12 modules bundled</code></pre>
</div>
```

## Files

| File                          | Purpose                                      |
|-------------------------------|----------------------------------------------|
| `references/code-block.html` | Copy-paste HTML, all variants                |
| `references/code-block.css`  | Glass container, line numbers, highlight classes |
| `references/code-block.js`   | Copy-to-clipboard, WAAPI feedback, auto-highlighter |

## Dependencies

- `web-design-tokens` → `tokens.css` must be loaded before `code-block.css`
- No external syntax highlighting library (Prism, highlight.js) required
