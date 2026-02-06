# Mathpix API Constraints

> **Official Documentation:** https://docs.mathpix.com/

---

## 1. word_data vs line_data

`include_word_data`와 `include_line_data`는 **상호 배타적**. 동시 사용 불가.

```json
// ❌ Error: "Requesting both line data and word data is not supported."
{ "include_word_data": true, "include_line_data": true }

// ✅ OK
{ "include_word_data": true }
```

**COW Pipeline:** `include_word_data` 사용 (word-level bbox 제공)

---

## 2. Request Template

```json
{
  "src": "data:image/png;base64,{BASE64_DATA}",
  "formats": ["text", "latex_styled", "data"],
  "include_word_data": true,
  "data_options": {
    "include_latex": true,
    "include_asciimath": true
  }
}
```

---

## 3. Response Schema (word_data)

```yaml
word_data:
  - type: "text" | "math" | "table" | "diagram" | "header"
    cnt: [[x,y], ...]   # 4 corners (pixel)
    text: string        # Mathpix Markdown
    confidence: number  # [0, 1]
```

---

## 4. References

| Resource | Location |
|----------|----------|
| Official Docs | https://docs.mathpix.com/ |
| Full API Spec | `cow/docs/mathpix_api_spec.md` |
