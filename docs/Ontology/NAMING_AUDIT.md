# Palantir Ontology: Naming Consistency Audit (네이밍 감사)

> **Version:** 1.0.0 | **Audit Date:** 2026-02-06
> **Scope:** session1.md through session6.md + G5 gap report
> **Auditor:** Claude-Opus-4.6 automated naming compliance check

---

## 1. Convention Summary (네이밍 규칙 요약)

| Component | Convention | Pattern | Examples |
|-----------|-----------|---------|----------|
| ObjectType apiName | PascalCase | `^[A-Z][a-zA-Z0-9_]*$` | LinearEquation, MathProblem |
| Property apiName | camelCase | `^[a-z][a-zA-Z0-9]*$` | equationId, gradeLevel |
| SharedProperty apiName | camelCase | `^[a-z][a-zA-Z0-9]*$` | gradeLevel, displayNotation |
| Interface apiName | camelCase | `^[a-z][a-zA-Z0-9]*$` | educationalContent |
| LinkType apiName | camelCase | `^[a-z][a-zA-Z0-9]*$` | isPrerequisiteOf |
| ActionType apiName | camelCase | `^[a-z][a-zA-Z0-9]*$` | createEquation |
| Function apiName | camelCase | `^[a-z][a-zA-Z0-9]*$` | detectCircularPrerequisites |

### Interface apiName Clarification (G5 Resolution)

The official Palantir documentation specifies Interface apiName as **camelCase**: `^[a-z][a-zA-Z0-9]*$`

session2.md provides the authoritative JSON schema (line 455):
```yaml
apiName:
  type: "string"
  pattern: "^[a-z][a-zA-Z0-9]*$"
```

And session2.md K-12 examples correctly demonstrate camelCase (line 1089):
```yaml
api_name: "educationalContent"
```

However, session1.md K-12 Interface Hierarchy (lines 1626-1665) used PascalCase identifiers as YAML keys without an explicit `apiName` field:
- `EducationalContent:` (no apiName field)
- `MathematicalConceptInterface:` (no apiName field)
- `AlgebraicExpression:` (no apiName field)

This creates **ambiguity**: the PascalCase keys could be mistaken for apiNames.

**Resolution:** Interface apiNames must be camelCase per session2 schema.
- "EducationalContent" -> `educationalContent`
- "MathematicalConceptInterface" -> `mathematicalConceptInterface` (or `mathematicalConcept`)
- "AlgebraicExpression" -> `algebraicExpression`

**Note:** Interface **display names** can be Title Case ("Educational Content"), but apiNames must be camelCase.

---

## 2. Reserved Words Registry (예약어 목록)

| Component | Reserved Words (case-insensitive) |
|-----------|----------------------------------|
| ObjectType | Ontology, Object, Property, Link, Relation, Rid, PrimaryKey, TypeId, OntologyObject |
| Property | ontology, object, property, link, relation, rid, primaryKey, typeId |
| SharedProperty | (same as Property) |
| Interface | (same as Property) |
| ActionType | ontology, object, property, link, relation, rid, primaryKey, typeId |
| LinkType | (same as Property) |

**Source:** session1.md lines 74, 247, 649, 860; session3.md line 168

---

## 3. Session File Audit Results (세션 파일 감사 결과)

### 3.1 session1.md Audit

**File:** `/home/palantir/docs/Ontology/session1.md`
**Components covered:** ObjectType, Property, SharedProperty

#### ObjectType apiNames (PascalCase check)

| apiName | Line(approx) | Status | Notes |
|---------|------|--------|-------|
| LinearEquation | 299 | PASS | PascalCase |
| MathematicalConcept | 370 | PASS | PascalCase |
| Polynomial | 422 | PASS | PascalCase |
| MathProblem | 505 | PASS | PascalCase (anti-pattern example) |
| CurriculumUnit | 75 | PASS | PascalCase (examples list) |
| Coefficient | 477 | N/A | Anti-pattern counter-example |

**ObjectType apiName result: 0 violations**

#### Property apiNames (camelCase check)

All property apiNames in session1 follow camelCase:

- equationId, displayNotation, latexNotation, variableSymbol, coefficient, constantLeft, constantRight, solution, gradeLevel, difficultyLevel (LinearEquation, lines 316-365)
- conceptId, conceptName, conceptNameKo, definition, curriculumDomain, exampleNotations (MathematicalConcept, lines 382-417)
- polynomialId, degree, coefficients, terms, isMonomial (Polynomial, lines 431-467)
- solutionSteps (line 983), conceptEmbedding (line 1022), schoolLocation (line 1036)

**Property apiName result: 0 violations**

#### SharedProperty apiNames (camelCase check)

| apiName | Line(approx) | Status |
|---------|------|--------|
| gradeLevel | 1390 | PASS |
| displayNotation | 1422 | PASS |
| difficultyLevel | 1445 | PASS |
| curriculumStandard | 1472 | PASS |

**SharedProperty apiName result: 0 violations**

#### Interface Naming (G5 Issue)

| Identifier | Line(approx) | Status | Issue |
|------------|------|--------|-------|
| EducationalContent | 1628 | VIOLATION | PascalCase YAML key; no explicit apiName field |
| MathematicalConceptInterface | 1642 | VIOLATION | PascalCase YAML key; no explicit apiName field |
| AlgebraicExpression | 1655 | VIOLATION | PascalCase YAML key; no explicit apiName field |

The `usedByInterfaces` references in SharedProperty examples also use PascalCase:

| Reference | Line(approx) | Status | Issue |
|-----------|------|--------|-------|
| usedByInterfaces: ["EducationalContent", "MathematicalConcept"] | 1414-1417 | VIOLATION | Should reference camelCase apiNames |
| usedByInterfaces: ["AlgebraicExpression"] | 1439 | VIOLATION | Should be "algebraicExpression" |
| usedByInterfaces: ["EducationalContent"] | 1466, 1491 | VIOLATION | Should be "educationalContent" |

**Interface naming result: 6 violations (G5 category)**

#### Reserved Word Check

No reserved word violations found in session1.

#### session1.md Total: 6 violations (all Interface naming / G5)

---

### 3.2 session2.md Audit

**File:** `/home/palantir/docs/Ontology/session2.md`
**Components covered:** LinkType, Interface

#### LinkType apiName (camelCase check)

The session2 JSON schema correctly defines `apiName pattern: "^[a-z][a-zA-Z0-9]*$"` (line 55).

K-12 examples use PascalCase as **YAML section keys** (NOT explicit apiName fields):

| YAML Key | Line(approx) | Status | Issue |
|----------|------|--------|-------|
| ConceptPrerequisite | 961 | WARNING | PascalCase section key; could be confused as apiName |
| ConceptToExamples | 1000 | WARNING | PascalCase section key |
| ConceptToFormulas | 1021 | WARNING | PascalCase section key |
| StudentLearning | 1048 | WARNING | PascalCase section key |

The actual traversal api_names within each LinkType are camelCase and correct:
- prerequisites, enables (line 973-974) - PASS
- exampleProblems, demonstratedConcept (line 1012-1013) - PASS
- relatedFormulas, applicableConcepts (line 1033-1034) - PASS
- learnedConcepts, studentLearners (line 1060-1061) - PASS

**LinkType apiName result: 4 warnings (ambiguous PascalCase section keys)**

#### Interface apiName (camelCase check)

session2 JSON schema correctly defines Interface apiName as camelCase (line 455). K-12 examples provide correct apiNames:

| YAML Key | api_name field | Line(approx) | Status |
|----------|---------------|------|--------|
| EducationalContent | educationalContent | 1089 | PASS (api_name field is correct) |
| Assessable | assessable | 1207 | PASS (api_name field is correct) |

**Interface apiName result: 0 violations (session2 K-12 examples are correct)**

#### Property apiNames in K-12 ObjectType Definitions (CRITICAL)

Session2 K-12 ObjectType examples (lines 815-953) use **snake_case** for property names, which **VIOLATES** the camelCase convention from session1.

**MathematicalConcept properties (lines 818-847):**

| Property Name | Line(approx) | Status | Corrected |
|--------------|------|--------|-----------|
| concept_id | 821 | VIOLATION | conceptId |
| title | 825 | PASS | (single word) |
| description | 828 | PASS | (single word) |
| grade_level | 830 | VIOLATION | gradeLevel |
| subject | 833 | PASS | (single word) |
| difficulty | 836 | PASS | (single word) |
| domain | 839 | PASS | (single word) |
| standard_codes | 842 | VIOLATION | standardCodes |
| created_at | 845 | VIOLATION | createdAt |
| updated_at | 846 | VIOLATION | updatedAt |

**ExampleProblem properties (lines 849-881):**

| Property Name | Line(approx) | Status | Corrected |
|--------------|------|--------|-----------|
| problem_id | 852 | VIOLATION | problemId |
| title | 855 | PASS | |
| problem_statement | 858 | VIOLATION | problemStatement |
| solution_explanation | 861 | VIOLATION | solutionExplanation |
| answer | 864 | PASS | |
| grade_level | 866 | VIOLATION | gradeLevel |
| subject | 868 | PASS | |
| difficulty | 870 | PASS | |
| total_points | 874 | VIOLATION | totalPoints |
| estimated_time_minutes | 876 | VIOLATION | estimatedTimeMinutes |
| rubric | 878 | PASS | |
| concept_id | 880 | VIOLATION | conceptId |

**Student properties (lines 883-901):**

| Property Name | Line(approx) | Status | Corrected |
|--------------|------|--------|-----------|
| student_id | 889 | VIOLATION | studentId |
| first_name | 892 | VIOLATION | firstName |
| last_name | 895 | VIOLATION | lastName |
| current_grade | 898 | VIOLATION | currentGrade |
| enrollment_date | 899 | VIOLATION | enrollmentDate |
| school_id | 901 | VIOLATION | schoolId |

**StudentConceptMastery properties (lines 903-930):**

| Property Name | Line(approx) | Status | Corrected |
|--------------|------|--------|-----------|
| mastery_id | 910 | VIOLATION | masteryId |
| student_id | 913 | VIOLATION | studentId |
| concept_id | 916 | VIOLATION | conceptId |
| learning_date | 918 | VIOLATION | learningDate |
| mastery_level | 920 | VIOLATION | masteryLevel |
| mastery_score | 924 | VIOLATION | masteryScore |
| time_spent_minutes | 927 | VIOLATION | timeSpentMinutes |
| attempts_count | 929 | VIOLATION | attemptsCount |
| last_assessed | 930 | VIOLATION | lastAssessed |

**Formula properties (lines 932-953):**

| Property Name | Line(approx) | Status | Corrected |
|--------------|------|--------|-----------|
| formula_id | 939 | VIOLATION | formulaId |
| name | 941 | PASS | |
| latex_notation | 943 | VIOLATION | latexNotation |
| plain_text | 946 | VIOLATION | plainText |
| description | 948 | PASS | |
| category | 950 | PASS | |

**Property apiName result: 33 snake_case violations**

#### Reserved Word Check

No reserved word violations found.

#### session2.md Total: 33 violations + 4 warnings

---

### 3.3 session3.md Audit

**File:** `/home/palantir/docs/Ontology/session3.md`
**Components covered:** ActionType, Function, Rule_Constraint

#### ActionType apiNames (camelCase check)

| apiName | Line(approx) | Status |
|---------|------|--------|
| addLearningRecord | 191 | PASS |
| linkPrerequisiteConcept | 208 | PASS |
| unlinkPrerequisiteConcept | 222 | PASS |
| modifyConceptDifficulty | 228 | PASS |
| gradeQuizAndSaveResults | 240 | PASS |

#### Function apiNames (camelCase check)

| apiName | Line(approx) | Status |
|---------|------|--------|
| detectCircularPrerequisites | 411 | PASS |
| gradeQuizAndSaveResultsFunction | 440 | PASS |

#### Property references in constraint examples

| Property Reference | Line(approx) | Status |
|-------------------|------|--------|
| difficultyLevel | 683 | PASS |
| subjectType | 689 | PASS |
| conceptCode | 699 | PASS |

#### Naming Convention Section (lines 783-797)

Correctly documents: `api_names: { format: camelCase }` and `forbidden_patterns: [PascalCase, snake_case]`.

**session3.md Total: 0 violations**

---

### 3.4 session4.md Audit

**File:** `/home/palantir/docs/Ontology/session4.md`
**Components covered:** Dataset, Pipeline, Transform, OntologySync

#### Dataset field names (camelCase check)

All dataset field names use camelCase correctly: conceptId, conceptName, gradeLevel, domain, standardCode, difficultyLevel, lastUpdatedTimestamp, recordId, studentId, activityType, scorePercentage, etc.

**Dataset field name result: 0 violations**

#### OntologySync ObjectType references (PascalCase check)

The `objectTypeId` field is described as "Target object type API name" (line 1092). ObjectType apiNames must be PascalCase. The examples use camelCase:

| Reference | Line(approx) | Status | Corrected |
|-----------|------|--------|-----------|
| objectTypeId: mathematicalConcept | 1276 | VIOLATION | MathematicalConcept |
| objectTypeId: student | 1305 | VIOLATION | Student |
| sourceObjectType: mathematicalConcept | 1338 | VIOLATION | MathematicalConcept |
| targetObjectType: problem | 1339 | VIOLATION | Problem |
| sourceObjectType: studentLearningRecord | 1356 | VIOLATION | StudentLearningRecord |
| targetObjectType: mathematicalConcept | 1357 | VIOLATION | MathematicalConcept |

**OntologySync ObjectType reference result: 6 violations (camelCase used instead of PascalCase for ObjectType apiNames)**

#### Pipeline and Transform naming

No naming violations found. Configuration names are descriptive strings, not apiNames.

**session4.md Total: 6 violations**

---

### 3.5 session5.md Audit

**File:** `/home/palantir/docs/Ontology/session5.md`
**Components covered:** ObjectSet, TimeSeries, MediaSet

No explicit apiName definitions in this file. References to ObjectType and Property names use appropriate conventions in code examples (PascalCase for types like `Student`, `Employee`, `Aircraft`; camelCase for properties like `gradeLevel`, `studentId`).

**session5.md Total: 0 violations**

---

### 3.6 session6.md Audit

**File:** `/home/palantir/docs/Ontology/session6.md`
**Components covered:** Workshop, OSDK, Slate, REST API, Automate

#### K-12 Object Model Reference (lines 1241-1269)

ObjectType apiNames listed as camelCase, which VIOLATES the PascalCase convention:

| Listed apiName | Line(approx) | Status | Corrected |
|---------------|------|--------|-----------|
| studentRecord | 1246 | VIOLATION | StudentRecord |
| classSection | 1247 | VIOLATION | ClassSection |
| enrollmentRecord | 1248 | VIOLATION | EnrollmentRecord |
| attendanceRecord | 1249 | VIOLATION | AttendanceRecord |
| gradeEntry | 1250 | VIOLATION | GradeEntry |
| assignment | 1251 | VIOLATION | Assignment |
| gradingPeriod | 1252 | VIOLATION | GradingPeriod |
| schoolCalendar | 1253 | VIOLATION | SchoolCalendar |

#### ActionType apiNames (camelCase check)

| apiName | Line(approx) | Status |
|---------|------|--------|
| markStudentPresent | 1255 | PASS |
| markStudentAbsent | 1256 | PASS |
| enterGrade | 1257 | PASS |
| updateGrade | 1258 | PASS |
| enrollStudentInCourse | 1259 | PASS |
| initiateStudentOnboarding | 1260 | PASS |
| sendParentNotification | 1261 | PASS |

#### Automate apiNames (camelCase check)

| apiName | Line(approx) | Status |
|---------|------|--------|
| dailyAttendanceReport | 1039 | PASS |
| lowGradeAlert | 1065 | PASS |
| newStudentOnboarding | 1095 | PASS |
| chronicAbsenceWebhook | 1122 | PASS |

#### Slate Naming Conventions (lines 566-574)

Correctly documents: `w_` prefix + camelCase for widgets, `q_` prefix + camelCase for queries, `f_` prefix + camelCase for functions, camelCase for variables. These are Slate-specific conventions, not Ontology apiName conventions.

**session6.md Total: 8 violations (ObjectType apiNames in camelCase instead of PascalCase)**

---

## 4. Correction Registry (교정 목록)

### 4.1 Interface Naming Corrections (G5 - session1.md)

| File | Line(approx) | Current (YAML Key) | Corrected apiName | Issue |
|------|------|---------|-----------|-------|
| session1.md | 1628 | EducationalContent | educationalContent | G5: PascalCase key; no apiName field |
| session1.md | 1642 | MathematicalConceptInterface | mathematicalConceptInterface | G5: PascalCase key; no apiName field |
| session1.md | 1655 | AlgebraicExpression | algebraicExpression | G5: PascalCase key; no apiName field |
| session1.md | 1414 | usedByInterfaces: ["EducationalContent"] | ["educationalContent"] | G5: PascalCase reference |
| session1.md | 1417 | usedByInterfaces: ["MathematicalConcept"] | ["mathematicalConcept"] | G5: PascalCase reference |
| session1.md | 1439 | usedByInterfaces: ["AlgebraicExpression"] | ["algebraicExpression"] | G5: PascalCase reference |

### 4.2 Property snake_case Corrections (session2.md K-12 Examples)

| File | Line(approx) | Current (snake_case) | Corrected (camelCase) | ObjectType |
|------|------|---------|-----------|-------|
| session2.md | 821 | concept_id | conceptId | MathematicalConcept |
| session2.md | 830 | grade_level | gradeLevel | MathematicalConcept |
| session2.md | 842 | standard_codes | standardCodes | MathematicalConcept |
| session2.md | 845 | created_at | createdAt | MathematicalConcept |
| session2.md | 846 | updated_at | updatedAt | MathematicalConcept |
| session2.md | 852 | problem_id | problemId | ExampleProblem |
| session2.md | 858 | problem_statement | problemStatement | ExampleProblem |
| session2.md | 861 | solution_explanation | solutionExplanation | ExampleProblem |
| session2.md | 866 | grade_level | gradeLevel | ExampleProblem |
| session2.md | 874 | total_points | totalPoints | ExampleProblem |
| session2.md | 876 | estimated_time_minutes | estimatedTimeMinutes | ExampleProblem |
| session2.md | 880 | concept_id | conceptId | ExampleProblem |
| session2.md | 889 | student_id | studentId | Student |
| session2.md | 892 | first_name | firstName | Student |
| session2.md | 895 | last_name | lastName | Student |
| session2.md | 898 | current_grade | currentGrade | Student |
| session2.md | 899 | enrollment_date | enrollmentDate | Student |
| session2.md | 901 | school_id | schoolId | Student |
| session2.md | 910 | mastery_id | masteryId | StudentConceptMastery |
| session2.md | 913 | student_id | studentId | StudentConceptMastery |
| session2.md | 916 | concept_id | conceptId | StudentConceptMastery |
| session2.md | 918 | learning_date | learningDate | StudentConceptMastery |
| session2.md | 920 | mastery_level | masteryLevel | StudentConceptMastery |
| session2.md | 924 | mastery_score | masteryScore | StudentConceptMastery |
| session2.md | 927 | time_spent_minutes | timeSpentMinutes | StudentConceptMastery |
| session2.md | 929 | attempts_count | attemptsCount | StudentConceptMastery |
| session2.md | 930 | last_assessed | lastAssessed | StudentConceptMastery |
| session2.md | 939 | formula_id | formulaId | Formula |
| session2.md | 943 | latex_notation | latexNotation | Formula |
| session2.md | 946 | plain_text | plainText | Formula |

**Note on session2 property naming context:** Session2 K-12 ObjectType examples (lines 815-953) appear to use **dataset column naming** (snake_case) rather than **Ontology Property apiName** convention (camelCase). This is consistent with how Palantir backing datasets use snake_case column names which get mapped to camelCase Property apiNames via OntologySync. However, the examples are labeled as "ObjectType definitions" with `properties:` containing `name:` fields, which readers may interpret as Property apiNames. This ambiguity should be resolved with a clarifying note.

### 4.3 OntologySync ObjectType Reference Corrections (session4.md)

| File | Line(approx) | Current (camelCase) | Corrected (PascalCase) | Context |
|------|------|---------|-----------|-------|
| session4.md | 1276 | mathematicalConcept | MathematicalConcept | objectTypeId |
| session4.md | 1305 | student | Student | objectTypeId |
| session4.md | 1338 | mathematicalConcept | MathematicalConcept | sourceObjectType |
| session4.md | 1339 | problem | Problem | targetObjectType |
| session4.md | 1356 | studentLearningRecord | StudentLearningRecord | sourceObjectType |
| session4.md | 1357 | mathematicalConcept | MathematicalConcept | targetObjectType |

### 4.4 ObjectType apiName Corrections (session6.md)

| File | Line(approx) | Current (camelCase) | Corrected (PascalCase) | Context |
|------|------|---------|-----------|-------|
| session6.md | 1246 | studentRecord | StudentRecord | K-12 Object Model |
| session6.md | 1247 | classSection | ClassSection | K-12 Object Model |
| session6.md | 1248 | enrollmentRecord | EnrollmentRecord | K-12 Object Model |
| session6.md | 1249 | attendanceRecord | AttendanceRecord | K-12 Object Model |
| session6.md | 1250 | gradeEntry | GradeEntry | K-12 Object Model |
| session6.md | 1251 | assignment | Assignment | K-12 Object Model |
| session6.md | 1252 | gradingPeriod | GradingPeriod | K-12 Object Model |
| session6.md | 1253 | schoolCalendar | SchoolCalendar | K-12 Object Model |

**Note:** These corrections apply to session files preserved as-is (originals). The corrected names should be used in all new component definition files.

---

## 5. Audit Summary (감사 요약)

### Violation Counts by Session

| Session | File | Violations | Warnings | Categories |
|---------|------|------------|----------|------------|
| session1.md | ObjectType/Property/SharedProperty | 6 | 0 | Interface naming (G5) |
| session2.md | LinkType/Interface | 33 | 4 | Property snake_case; LinkType key ambiguity |
| session3.md | ActionType/Function/Constraint | 0 | 0 | Clean |
| session4.md | Dataset/Pipeline/Transform/OntologySync | 6 | 0 | ObjectType ref casing |
| session5.md | ObjectSet/TimeSeries/MediaSet | 0 | 0 | Clean |
| session6.md | Workshop/OSDK/Slate/REST/Automate | 8 | 0 | ObjectType apiName casing |
| **TOTAL** | | **53** | **4** | |

### Violation Categories

| Category | Count | Severity | Sessions Affected |
|----------|-------|----------|-------------------|
| Property snake_case (should be camelCase) | 33 | HIGH | session2 |
| ObjectType camelCase (should be PascalCase) | 14 | HIGH | session4, session6 |
| Interface PascalCase key (should have camelCase apiName) | 6 | MEDIUM | session1 |
| LinkType PascalCase section key (ambiguous) | 4 | LOW | session2 |

---

## 6. Naming Best Practices (네이밍 모범 사례)

### Do's

- Use domain-specific, unambiguous names: `gradeLevel`, `displayNotation`, `curriculumStandard`
- ObjectType apiName should be singular noun in PascalCase: `LinearEquation` (not `LinearEquations`)
- Property apiName should describe the attribute in camelCase: `equationId`, `coefficient`
- SharedProperty should be unambiguous across all using types: `gradeLevel` not `level`
- Interface apiName should be camelCase per schema: `educationalContent` not `EducationalContent`
- LinkType traversal names should reflect cardinality: plural for many-side (`exampleProblems`), singular for one-side (`demonstratedConcept`)
- ActionType apiName should be verb-first camelCase: `addLearningRecord`, `modifyConceptDifficulty`

### Don'ts

- Do not use generic names for SharedProperties: `level`, `name`, `value`, `type`, `status` (too ambiguous)
- Do not use abbreviations: `eq_id`, `disp_notation` (use full words)
- Do not use Hungarian notation: `strEquationId`, `intGradeLevel`
- Do not use underscores in camelCase properties: `grade_level` (use `gradeLevel`)
- Do not use trailing numbers for versioning: `gradeLevel2` (create new SharedProperty instead)
- Do not use PascalCase for Interface apiNames: `EducationalContent` (use `educationalContent`)
- Do not use camelCase for ObjectType apiNames: `studentRecord` (use `StudentRecord`)
- Do not confuse dataset column names (snake_case) with Property apiNames (camelCase)

### Convention Quick Reference Card

```
ObjectType    →  PascalCase   →  LinearEquation, StudentRecord
Property      →  camelCase    →  equationId, gradeLevel
SharedProperty→  camelCase    →  gradeLevel, displayNotation
Interface     →  camelCase    →  educationalContent, assessable
LinkType      →  camelCase    →  conceptPrerequisites, studentEnrollments
ActionType    →  camelCase    →  addLearningRecord, modifyConceptDifficulty
Function      →  camelCase    →  detectCircularPrerequisites
DisplayName   →  Title Case   →  "Linear Equation", "Grade Level"
Dataset Column→  snake_case   →  concept_id, grade_level (backing dataset only)
```

---

## 7. Disambiguation: Dataset Columns vs Property apiNames

A key source of confusion (especially in session2.md) is the distinction between **dataset column names** and **Ontology Property apiNames**:

| Layer | Convention | Example | Where Used |
|-------|-----------|---------|------------|
| Dataset column | snake_case | `grade_level` | Backing dataset schema, Pipeline Builder |
| Property apiName | camelCase | `gradeLevel` | Ontology definitions, API calls, code |
| OntologySync mapping | Maps one to the other | `grade_level` -> `gradeLevel` | Sync configuration |

Session2.md K-12 ObjectType examples (lines 815-953) use snake_case `name:` fields. These likely represent **dataset column names** rather than Property apiNames, but the context (`properties:` section of ObjectType definitions) creates confusion.

**Recommendation:** Future ObjectType definition documents should explicitly distinguish:
```yaml
properties:
  gradeLevel:                          # Property apiName (camelCase)
    displayName: "Grade Level"
    baseType: "Integer"
    datasetColumn: "grade_level"       # Explicit mapping to backing dataset
```

---

## 8. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-02-06 | Initial audit of session1-6 files. Found 53 violations and 4 warnings across 6 session files. Major categories: Property snake_case (33), ObjectType casing (14), Interface naming G5 (6). |
