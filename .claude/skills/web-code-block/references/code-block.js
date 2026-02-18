/**
 * web-code-block — code-block.js
 * Copy-to-clipboard + optional regex-based syntax highlighting
 * No external dependencies. Auto-initializes on DOMContentLoaded.
 */

const CodeBlock = (() => {
  'use strict';

  /* ── Syntax highlight rules per language ─────────────────────
   * Each rule: { pattern: RegExp, className: string }
   * Applied in order; earlier rules take precedence.
   * ──────────────────────────────────────────────────────────── */
  const HIGHLIGHT_RULES = {
    javascript: [
      { pattern: /(\/\/[^\n]*)/g,                                    cls: 'hl-comment'  },
      { pattern: /("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|`(?:[^`\\]|\\.)*`)/g, cls: 'hl-string'  },
      { pattern: /\b(const|let|var|function|return|if|else|for|while|class|new|import|export|default|async|await|typeof|instanceof|null|undefined|true|false)\b/g, cls: 'hl-keyword' },
      { pattern: /\b(\d+\.?\d*)\b/g,                                cls: 'hl-number'  },
    ],
    css: [
      { pattern: /(\/\*[\s\S]*?\*\/)/g,                             cls: 'hl-comment'  },
      { pattern: /("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')/g,         cls: 'hl-string'   },
      { pattern: /([a-z-]+)(?=\s*:)/g,                              cls: 'hl-property' },
      { pattern: /:\s*([\w#%()., -]+)/g,                            cls: 'hl-string'   },
    ],
    html: [
      { pattern: /(&lt;!--[\s\S]*?--&gt;)/g,                        cls: 'hl-comment'  },
      { pattern: /("(?:[^"\\]|\\.)*")/g,                            cls: 'hl-string'   },
      { pattern: /(&lt;\/?)([\w-]+)/g,                              cls: 'hl-keyword'  },
    ],
    bash: [
      { pattern: /(#[^\n]*)/g,                                      cls: 'hl-comment'  },
      { pattern: /("(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*')/g,         cls: 'hl-string'   },
      { pattern: /\b(npm|npx|git|cd|ls|mkdir|rm|cp|mv|curl|export|echo|node|python|bun)\b/g, cls: 'hl-keyword' },
      { pattern: /(-{1,2}[\w-]+)/g,                                 cls: 'hl-number'   },
    ],
    json: [
      { pattern: /("(?:[^"\\]|\\.)*")(?=\s*:)/g,                   cls: 'hl-property' },
      { pattern: /:\s*("(?:[^"\\]|\\.)*")/g,                       cls: 'hl-string'   },
      { pattern: /\b(true|false|null)\b/g,                          cls: 'hl-keyword'  },
      { pattern: /\b(-?\d+\.?\d*)\b/g,                              cls: 'hl-number'   },
    ],
  };

  /* ── Escape HTML for safe insertion ─────────────────────────── */
  function escapeHtml(text) {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  /* ── Apply highlight rules to plain text ─────────────────────
   * Returns HTML string with <span class="hl-*"> wrappers.
   * Note: operates on already-escaped HTML to avoid double-escaping.
   * ──────────────────────────────────────────────────────────── */
  function applyHighlight(escapedText, language) {
    const rules = HIGHLIGHT_RULES[language];
    if (!rules) return escapedText;

    let result = escapedText;
    rules.forEach(({ pattern, cls }) => {
      result = result.replace(
        new RegExp(pattern.source, pattern.flags),
        (match, ...groups) => {
          const captured = groups[0] ?? match;
          return match.replace(captured, `<span class="${cls}">${captured}</span>`);
        }
      );
    });
    return result;
  }

  /* ── Syntax highlight auto-init ──────────────────────────────
   * Processes .code-block[data-language] elements that don't
   * already have highlight spans. Skips blocks with data-no-highlight.
   * ──────────────────────────────────────────────────────────── */
  function initHighlighting() {
    document.querySelectorAll('.code-block[data-language]').forEach((block) => {
      if (block.dataset.noHighlight !== undefined) return;
      const codeEl   = block.querySelector('code');
      if (!codeEl) return;
      if (codeEl.querySelector('span[class^="hl-"]')) return; // already highlighted

      const language = block.dataset.language.toLowerCase();
      const raw      = codeEl.textContent ?? '';
      codeEl.innerHTML = applyHighlight(escapeHtml(raw), language);
    });
  }

  /* ── Copy-to-clipboard ───────────────────────────────────────
   * Injects a copy button into each .code-block[data-copy].
   * Uses navigator.clipboard.writeText with graceful fallback.
   * WAAPI animation on button for copy feedback.
   * ──────────────────────────────────────────────────────────── */
  function initCopyButtons() {
    document.querySelectorAll('.code-block[data-copy]').forEach((block) => {
      if (block.querySelector('.code-block__copy-btn')) return; // already injected

      const btn = document.createElement('button');
      btn.className    = 'code-block__copy-btn';
      btn.textContent  = 'copy';
      btn.setAttribute('aria-label', 'Copy code to clipboard');
      block.appendChild(btn);

      btn.addEventListener('click', async () => {
        const codeEl = block.querySelector('code');
        const text   = codeEl?.textContent ?? '';

        try {
          await navigator.clipboard.writeText(text);
        } catch {
          /* Fallback: select + execCommand (deprecated but functional) */
          const range = document.createRange();
          range.selectNodeContents(codeEl);
          window.getSelection()?.removeAllRanges();
          window.getSelection()?.addRange(range);
          document.execCommand('copy');
          window.getSelection()?.removeAllRanges();
        }

        /* Feedback animation (WAAPI) */
        btn.textContent = '✓ copied';
        btn.classList.add('copied');

        btn.animate(
          [{ opacity: 0.6, transform: 'scale(0.9)' }, { opacity: 1, transform: 'scale(1)' }],
          { duration: 200, easing: 'ease-out', fill: 'forwards' }
        );

        setTimeout(() => {
          btn.textContent = 'copy';
          btn.classList.remove('copied');
        }, 2000);
      });
    });
  }

  /* ── Public API ──────────────────────────────────────────────── */
  function init() {
    initHighlighting();
    initCopyButtons();
  }

  /* ── Auto-init ───────────────────────────────────────────────── */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  return { init };
})();
