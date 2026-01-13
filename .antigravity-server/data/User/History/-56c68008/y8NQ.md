### 📠 AUDIT REPORT: KS X 6101 Supplementary Resources (v5.0)

**Target:** OWPML (KS X 6101) Specification Supplements
**Date:** 2026-01-08
**Protocol:** `/deep-audit` (RSIL)

---

#### Stage_A_Blueprint (Surface Scan)
- **Target_Query**: "KS X 6101", "OWPML", "HWPX specification"
- **Web_Results**: Hancom official, Namuwiki, Scribd.
- **GitHub_Results**: 7 relevant repositories identified.

#### Stage_B_Trace (Deep Dive)

| Resource | Type | URL | Notes |
|:---|:---|:---|:---|
| **Hancom Official Spec** | PDF/Docs | [hancom.com/hwpDownload](https://www.hancom.com/etc/hwpDownload.do) | Canonical source for OWPML schema (KS X 6101). Download via KSSN portal. |
| **python-hwpx Docs** | Web | [airmang.github.io/python-hwpx](https://airmang.github.io/python-hwpx/) | Korean usage guide. Good for API patterns. |
| **hancom-io/hwpx-owpml-model** | GitHub (C++) | [Link](https://github.com/hancom-io/hwpx-owpml-model) | Official Hancom OWPML filter model. MIT Licensed. Useful for element names reference. |
| **mete0r/pyhwp** | GitHub (Python) | [Link](https://github.com/mete0r/pyhwp) | Established HWP v5 parser. 14+ years. Binary format insights. |
| **hione0413/hwp-parser** | GitHub (Python) | [Link](https://github.com/hione0413/hwp-parser) | Recent (Dec 2025). Extracts text, tables, images from HWP/HWPX. |
| **Scribd: HWP Structure** | Doc | [Scribd](https://www.scribd.com/document/647809301/HWP-structure-in-English) | English explanation of HWP binary format. |
| **Arunpandi77/pypandoc-hwpx** | GitHub (Python) | [Link](https://github.com/Arunpandi77/pypandoc-hwpx) | Pandoc-based converter for HWPX. |

#### Stage_C_Quality (Gap Analysis)

| Gap | Description | Mitigation |
|:---|:---|:---|
| **KSSN Portal Access** | Official PDF requires KSSN login (Korean standards site). | Use existing Skeleton.hwpx + python-hwpx source as reference. |
| **Advanced Elements** | Missing deep-dive on `eqEdit`, `ctrl`, `table` complex nesting. | Reverse-engineer from python-hwpx internals and hancom-io model. |
| **English Docs** | Most resources are Korean-only. | Use AI translation or rely on code comments. |

#### Status
- **Current_State**: Resource Inventory Complete.
- **New_Resources_Found**: YES (7 repositories, 2 documentation sites).
- **Actionable**: Clone `hancom-io/hwpx-owpml-model` for C++ element reference. Consult `python-hwpx` source for Python API patterns.

---

### Recommendation

1.  **High Priority**: Download official OWPML spec from Hancom if KSSN access is possible.
2.  **Medium Priority**: Clone `hwpx-owpml-model` to cross-reference C++ element definitions with Python implementation.
3.  **Low Priority**: Review `pyhwp` for historical HWP v5 insights (useful for legacy format understanding).
