## OWPML 2024 Namespace Migration Plan

Purpose
- Add optional support for the 2024 OWPML namespace URIs while preserving
  current 2011/2016 compatibility.

Scope
- Builders/generators/parsers/validators that hardcode 2011/2016 URIs.
- HWPX templates and version.xml defaults.
- Test artifacts and validation coverage.

Non-goals
- Replace 2011/2016 namespaces globally without a compatibility flag.
- Guarantee full compliance with the official 2024 spec without authoritative
  reference material.

Current baseline
- Outputs use `http://www.hancom.co.kr/hwpml/2011/*` and `.../2016/*`.
- `version.xml` uses the 2011 namespace and xmlVersion `1.5`.
- HWP 2024 opens 2011/2016 namespace outputs today.

Constraints
- Community sources indicate 2024 URIs (`http://www.owpml.org/owpml/2024/*`),
  but official spec access is limited; treat as best-effort.
- HWP 2024 compatibility must remain intact.

Decision points
- Whether to introduce a new 2024 template or transform the existing template.
- Whether to support dual-namespace parsing in `lib/ingest_hwpx.py`.
- Whether validator should accept both namespace families.

Plan
1) Namespace map abstraction
   - Centralize namespace URIs into a versioned map (2011/2016 vs 2024).
   - Introduce a `NamespaceProfile` and select it per build/parse run.

2) Template strategy
   - Option A: Create a 2024 template `.hwpx` with 2024 URIs.
   - Option B: Start from current template and namespace-transform section/header
     XML at build time.
   - Choose A if a valid 2024 template is available; otherwise B with strict
     transformation rules.

3) Builder/generator updates
   - `lib/owpml/document_builder.py`: build using the chosen namespace profile.
   - `lib/owpml/generator.py`: replace hardcoded `OWPML_NAMESPACES` with profile.
   - Ensure `ET.register_namespace` uses profile-defined prefixes/URIs.

4) Parser/ingestor updates
   - `lib/ingest_hwpx.py`: support both 2011 and 2024 namespace profiles.
   - Detect namespace from XML root and select the matching profile.

5) Validator updates
   - `lib/owpml/validator.py`: accept both namespace families.
   - Validate structural rules independent of namespace version.

6) Version metadata
   - Determine `version.xml` namespace and `xmlVersion` for 2024 profile.
   - Keep 2011 defaults for current profile.

7) Tests and fixtures
   - Add golden outputs for both namespace profiles (2011 and 2024).
   - Ensure `output_styles_test.hwpx` has a 2024 counterpart.

Deliverables
- Namespace profile module (versioned URIs + prefix registration).
- Optional 2024 template or XML transform step.
- Dual-mode builder/generator/parser/validator.
- Tests confirming both profiles open in HWP 2024.

Risks
- 2024 namespace URIs might not be accepted by HWP 2024 despite spec updates.
- Transforming 2011 XML to 2024 may miss new required attributes/elements.

Exit criteria
- Both profiles produce valid HWPX packages.
- HWP 2024 opens files from each profile without crashing.
