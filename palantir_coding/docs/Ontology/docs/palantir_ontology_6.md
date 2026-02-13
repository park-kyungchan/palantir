# Palantir Foundry Application & API Layer: Complete Reference

Palantir Foundry's Application & API Layer consists of **five components** that enable building operational applications on top of the Ontology: Workshop (no-code), OSDK (pro-code SDK), Slate (legacy custom apps), REST API (HTTP endpoints), and Automate (workflow automation). This document provides machine-readable specifications for each component, targeting K-12 Education Platform implementations with Claude-Opus-4.5 as the primary consumer.

---

## Component 1: Workshop

### 1.1 Official Definition

Workshop enables application builders to create interactive, high-quality applications for operational users through three principles: **Object Data** (using the Ontology as the primary building block), **Consistent Design** (unified design system across components), and **Interactivity and Complexity** (dynamic applications rivaling custom React apps). All data is read from the Object Data Layer; Actions handle writeback; Functions provide business logic.

### 1.2 Semantic Definition

**Analogies:**
- Workshop is Notion/Airtable for enterprise Ontology data
- Visual IDE for operational applications where widgets are components and variables manage state
- PowerApps + Dataverse equivalent for Palantir's ecosystem

**Similar Concepts:**

| Platform | Equivalent |
|----------|-----------|
| Microsoft | PowerApps + Dataverse |
| Salesforce | Lightning App Builder |
| ServiceNow | App Engine Studio |
| Mendix/OutSystems | Low-code app builders |

**Anti-Concepts (What Workshop is NOT):**
- NOT a BI/reporting tool like Tableau/Power BI—designed for operational workflows
- NOT a database tool—reads from/writes to Ontology, doesn't manage raw data
- NOT for public-facing websites—designed for authenticated internal users
- NOT a replacement for Slate—Slate offers more HTML/CSS/JS customization

### 1.3 Structural Schema

```json
{
  "$schema": "workshop-module-v1",
  "type": "object",
  "properties": {
    "moduleId": { "type": "string", "format": "ri.workshop.main.module.*" },
    "moduleName": { "type": "string" },
    "mobileEnabled": { "type": "boolean", "default": false },
    "layout": {
      "type": "object",
      "properties": {
        "header": {
          "title": { "type": "string" },
          "orientation": { "enum": ["horizontal", "vertical"] }
        },
        "pages": {
          "type": "array",
          "items": {
            "pageId": { "type": "string" },
            "pageName": { "type": "string" },
            "sections": { "type": "array" }
          }
        },
        "overlays": {
          "type": "array",
          "items": {
            "overlayName": { "type": "string" },
            "overlayType": { "enum": ["drawer", "modal"] }
          }
        }
      }
    },
    "variables": {
      "type": "array",
      "items": {
        "variableName": { "type": "string" },
        "variableType": { 
          "enum": ["Object", "ObjectSet", "String", "Number", "Boolean", "Date", "Timestamp", "Array", "ObjectSetFilter", "Struct", "TimeSeriesSet", "Scenario"]
        },
        "definitionType": { "enum": ["Static", "Function", "ObjectProperty", "VariableTransformation", "ObjectSetDefinition"] },
        "externalId": { "type": "string" },
        "moduleInterface": { "type": "boolean" },
        "stateSaving": { "type": "boolean" }
      }
    }
  }
}
```

**Complete Widget Types by Category:**

| Category | Widgets |
|----------|---------|
| **Ontology Widgets** | Object Table, Object List, Object View, Object Chips, Property List, Links (Search Around), Object Set Title |
| **Chart Widgets** | Chart XY (Bar/Line/Scatter), Chart Pie, Chart Vega, Chart Waterfall, Gantt Chart, Pivot Table |
| **Input Widgets** | Filter List, Object Dropdown, Object Selector, String Selector, Text Input, Numeric Input, Date/Time Picker, Checkbox |
| **Action Widgets** | Button Group, Inline Action, Media Uploader, Audio Recorder |
| **AI Widgets** | AIP Agent, AIP Analyst, AIP Generated Content |
| **Mobile Widgets** | Mobile Navigation Bar (max 4 tabs), QR Code Reader, Current Location Manager |
| **Visualization** | Map, Timeline, Metric Card, Markdown, Media Preview, PDF Viewer, Video/Audio Display |

### 1.4 Decision Tree

```
USE WORKSHOP WHEN:
├── Building operational applications (inboxes, task management, dashboards)
├── Rapid prototyping needed (hours/days vs weeks)
├── Application is Ontology-centric (objects, links, actions)
├── Multi-widget interactivity with events and variables required
├── Writeback via Actions needed
├── Mobile-optimized field applications required
└── State saving and sharing of application views needed

USE SLATE INSTEAD WHEN:
├── Heavy UI customization (custom CSS, complex JavaScript)
├── Pixel-perfect design control required
└── Direct SQL/API queries without Ontology needed

USE OSDK/REACT INSTEAD WHEN:
├── Complex custom widgets not available in Workshop
├── Third-party library integration (D3, Three.js)
├── Offline-first capabilities required
└── Building standalone applications outside Palantir platform
```

### 1.5 Validation Rules

```typescript
const WorkshopValidationRules = {
  objectTable: {
    mustHaveObjectSet: true,
    maxColumns: 50,
    exportLimit: 200000,
    exportLimitFunctionBacked: 10000
  },
  variables: {
    externalIdRequired: ["moduleInterface", "stateSaving", "routing"],
    stateSavingSupportedTypes: ["Array", "Boolean", "Date", "Number", "String", "Timestamp", "Object", "ObjectSet", "ObjectSetFilter"]
  },
  mobile: {
    disabledWidgets: ["ObjectTable", "Chart", "Map"],
    embeddedModulesMustBeMobile: true,
    maxNavigationTabs: 4
  },
  performance: {
    maxEmbeddedModulesOnScreen: 1,
    browserRequestLimit: 6
  }
};
```

### 1.6 Canonical Examples (K-12 Education)

**Example 1: Student Roster Dashboard**

```json
{
  "widgets": [
    {
      "type": "FilterList",
      "name": "studentFilters",
      "config": {
        "objectSet": "$allStudents",
        "filters": [
          { "property": "gradeLevel", "displayName": "Grade Level" },
          { "property": "enrollmentStatus", "displayName": "Enrollment Status" }
        ],
        "filterOutput": "$studentFilters"
      }
    },
    {
      "type": "ObjectTable",
      "name": "studentRoster",
      "config": {
        "objectSet": "$filteredStudents",
        "columns": [
          { "property": "studentId", "displayName": "Student ID", "frozen": true },
          { "property": "fullName", "displayName": "Full Name" },
          { "property": "gradeLevel", "displayName": "Grade" }
        ],
        "activeObject": "$selectedStudent",
        "inlineEditingEnabled": true,
        "inlineEditingAction": "updateStudentRecord"
      }
    }
  ],
  "variables": [
    { "name": "$allStudents", "type": "ObjectSet", "definition": "studentRecord:All" },
    { "name": "$selectedStudent", "type": "Object" }
  ]
}
```

**Example 2: Attendance Tracking with Action Buttons**

```json
{
  "widgets": [
    {
      "type": "ButtonGroup",
      "name": "attendanceActions",
      "config": {
        "buttons": [
          {
            "text": "Present",
            "intent": "success",
            "onClick": {
              "type": "Action",
              "actionType": "markStudentPresent",
              "parameters": {
                "student": "$selectedStudentForAttendance",
                "date": "$attendanceDate"
              }
            }
          },
          {
            "text": "Absent",
            "intent": "danger",
            "onClick": {
              "type": "Action",
              "actionType": "markStudentAbsent",
              "parameters": {
                "student": "$selectedStudentForAttendance",
                "date": "$attendanceDate"
              }
            }
          }
        ]
      }
    }
  ]
}
```

### 1.7 Anti-Patterns

**Anti-Pattern 1: Variable Dependency Chains Without Event Sequencing**

Events execute sequentially but do NOT wait for downstream variable computations. Setting Variable A, then Variable B (depends on A), then opening an overlay expecting B to be updated will fail.

**Fix:** Use Function-backed variables that compute dependencies internally, or split into separate user-triggered events.

**Anti-Pattern 2: Overusing Embedded Modules/iFrames**

Each iframe requires additional memory; creates "waterfall" effect. Maximum recommended: **1 iframe widget on screen at a time**.

**Fix:** Use pages or drawers to show one embedded module at a time; consolidate widgets into parent module.

### 1.8 Integration Points

| Dependency | Type | Description |
|------------|------|-------------|
| Ontology | Required | All Workshop data from Object Types |
| Action Types | Required for writeback | Data modification |
| Functions | Optional | Custom logic, derived columns |
| Link Types | Optional | Search Around navigation |
| AIP | Optional | For AI widgets |

**Dependents:** Object Views (embedded tabs), Carbon Workspaces, Automate workflows, OSDK applications (via iframe), Marketplace products.

---

## Component 2: OSDK (Ontology Software Development Kit)

### 2.1 Official Definition

The OSDK allows developers to access the full power of the Ontology directly from development environments. It treats Foundry as backend, leveraging the Ontology's high-scale queries and writeback alongside granular governance controls. Supports **NPM for TypeScript**, **Pip/Conda for Python**, **Maven for Java**, and **OpenAPI spec** for other languages.

**Key Benefits:** Accelerated development, strong type-safety with generated functions/types, centralized maintenance, secure-by-design with scoped tokens.

### 2.2 Semantic Definition

**Analogies:**
- GraphQL/Prisma client for Palantir's Ontology
- Strongly-typed ORM generated from Ontology schema
- Apollo Client targeting Foundry specifically

**Similar Concepts:**

| Concept | Similarity | Key Difference |
|---------|-----------|----------------|
| Prisma Client | Generated type-safe client | OSDK operates on semantic Ontology, not raw database |
| Apollo Client | Type generation | OSDK targets Foundry Ontology specifically |
| Firebase SDK | Backend-as-a-Service | OSDK is enterprise-focused with governance |

**Anti-Concepts:**
- NOT a raw REST API wrapper—provides semantic, type-safe abstractions
- NOT a database driver—operates at Ontology semantic layer
- NOT a generic Foundry SDK—Platform SDK handles non-Ontology APIs
- NOT a Workshop replacement—OSDK is for pro-code development

### 2.3 Structural Schema

**TypeScript Configuration:**

```typescript
interface OSDKClientConfig {
  foundryUrl: string;       // "https://mystack.palantirfoundry.com"
  ontologyRid: string;      // "ri.ontology.main.ontology.12345678-abcd-..."
  auth: OAuthClient;
}

// Package names:
// @osdk/client - Core client
// @osdk/oauth - OAuth utilities  
// @osdk/foundry - Platform SDK (optional)
// <your-generated-sdk-package> - Generated Ontology types
```

**Python Configuration:**

```python
from ontology_sdk import FoundryClient

# Environment variables:
# PALANTIR_HOSTNAME = "example.palantirfoundry.com"
# PALANTIR_TOKEN = "<personal-access-token>"

client = FoundryClient(
    auth=auth,
    hostname="example.palantirfoundry.com"
)
```

### 2.4 Decision Tree

```
BUILDING A FOUNDRY-CONNECTED APPLICATION?
├── Custom coded application?
│   ├── YES → Need Ontology data (objects, links, Actions)?
│   │   ├── YES → USE OSDK
│   │   │   ├── Frontend React app → TypeScript OSDK + @osdk/react
│   │   │   ├── Python backend/notebook → Python OSDK
│   │   │   ├── Java/Kotlin service → Java OSDK
│   │   │   └── Other language → Generate OpenAPI spec, use REST
│   │   └── NO (admin/governance) → Use Platform SDK
│   └── NO → Need configurable UI? → USE WORKSHOP

OSDK SELECTION CRITERIA:
✓ Type-safe Ontology access needed
✓ Building React/frontend apps on Foundry
✓ Executing ActionTypes programmatically
✓ Real-time subscriptions (TypeScript only)
```

### 2.5 Validation Rules

```typescript
const OSDKValidationRules = {
  environment: {
    nodeVersion: ">= 18.0.0",
    pythonVersion: ">= 3.9 && < 3.13"
  },
  configuration: {
    foundryUrlPattern: /^https:\/\/.+\.palantirfoundry\.com$/,
    ontologyRidPattern: /^ri\.ontology\.main\.ontology\.[a-f0-9-]+$/
  },
  subscriptions: {
    pivotToNotSupported: true  // Cannot subscribe to pivotTo ObjectSets
  },
  actions: {
    allModificationsThroughActions: true  // Objects are immutable; Actions required
  }
};
```

### 2.6 Canonical Examples (K-12 Education)

**TypeScript: Query Students with Pagination**

```typescript
import { createClient } from "@osdk/client";
import { createPublicOauthClient } from "@osdk/oauth";
import { Student } from "@k12-district/ontology-sdk";

const client = createClient(
  "https://k12district.palantirfoundry.com",
  "ri.ontology.main.ontology.k12-education",
  auth
);

async function getStudentsByGradeLevel(gradeLevel: number): Promise<Student[]> {
  const students: Student[] = [];
  let result = await client(Student)
    .where({ gradeLevel: { $eq: gradeLevel } })
    .fetchPage({ $pageSize: 100, $orderBy: { lastName: "asc" } });
  
  students.push(...result.data);
  
  while (result.nextPageToken) {
    result = await client(Student)
      .where({ gradeLevel: { $eq: gradeLevel } })
      .fetchPage({ $pageSize: 100, $pageToken: result.nextPageToken });
    students.push(...result.data);
  }
  return students;
}
```

**TypeScript: Search Around (Link Navigation)**

```typescript
async function getStudentCourses(studentId: string) {
  return await client(Student)
    .where({ studentId: { $eq: studentId } })
    .pivotTo("enrollmentRecords")
    .pivotTo("course")
    .fetchPage();
}
```

**TypeScript: Real-Time Subscriptions**

```typescript
function subscribeToStudentChanges(gradeLevel: number) {
  return client(Student)
    .where({ gradeLevel: { $eq: gradeLevel } })
    .subscribe({
      onChange: (update) => {
        if (update.state === "ADDED_OR_UPDATED") {
          console.log(`Student updated: ${update.object.firstName}`);
        }
      },
      onSuccessfulSubscription: () => console.log("Active"),
      onError: (err) => console.error(err)
    }, { properties: ["firstName", "lastName", "gradeLevel", "gpa"] });
}
```

**TypeScript: Action Execution**

```typescript
async function recordGrade(studentId: string, assignmentId: string, score: number) {
  return await client(RecordAssignmentGrade).applyAction({
    studentId,
    assignmentId,
    pointsEarned: score,
    gradedAt: new Date().toISOString()
  });
}
```

**Python: Create Attendance Records**

```python
from ontology_sdk import FoundryClient

client = FoundryClient()

def record_attendance(student_id: str, status: str, date: str):
    return client.ontology.actions.RecordAttendance.apply(
        student_id=student_id,
        date=date,
        status=status
    )
```

### 2.7 Anti-Patterns

**Anti-Pattern 1: Direct Object Mutation**

```typescript
// ❌ WRONG - Objects are immutable
const student = await client(Student).fetchOne("student-123");
student.gpa = 3.8;  // Has no effect

// ✅ CORRECT - Use Actions
await client(UpdateStudentGpa).applyAction({ studentId: "student-123", newGpa: 3.8 });
```

**Anti-Pattern 2: Ignoring Pagination**

```typescript
// ❌ WRONG - Misses data beyond first page
const allStudents = await client(Student).fetchPage({ $pageSize: 10000 });

// ✅ CORRECT - Iterate through all pages
let page = await client(Student).fetchPage({ $pageSize: 100 });
while (page.nextPageToken) {
  page = await client(Student).fetchPage({ $pageToken: page.nextPageToken });
}
```

### 2.8 Integration Points

```
ONTOLOGY DEFINITION
    │
    │ Code Generation
    ▼
GENERATED OSDK PACKAGE
    │
    │ Import
    ▼
APPLICATION CODE
    │
    │ API Calls
    ▼
FOUNDRY PLATFORM (REST API v2 underneath)
```

| Component | Relationship |
|-----------|-------------|
| Workshop | Alternative for no-code; calls same Actions |
| REST API | OSDK is type-safe abstraction over REST |
| Platform SDK | Handles non-Ontology APIs; used alongside OSDK |
| Functions | TypeScript v2 Functions have first-class OSDK support |

### 2.9 OSDK 2025-2026 Updates

> Source: OSDK_Reference.md — OSDK 2025-2026 Updates (verified 2026-02-08)

**TypeScript OSDK v2 (GA — recommended for all new projects):**

| Aspect | v1 Syntax | v2 Syntax |
|--------|-----------|-----------|
| Query | `client.ontology.objects.MyObject.where(q => q.prop.eq('value'))` | `client(MyObject).where({ prop: 'value' })` |
| Filter | `query => query.prop.startsWith('foo')` | `{ prop: { $startsWith: 'foo' } }` |
| OrderBy | `.orderBy(sortBy => sortBy.prop.asc()).fetchPageWithErrors({ pageSize: 30 })` | `.fetchPage({ $orderBy: { prop: 'asc' }, $pageSize: 30 })` |
| Aggregation | Builder pattern with `.groupBy().aggregate()` | Object-based: `.aggregate({ $count: true, avg: { $avg: 'prop' } })` |
| DateTime | Various formats | ISO 8601 strings (`2010-10-01T00:00:00Z`) |

New v2 features:
- Interface support (query across multiple ObjectTypes polymorphically)
- Media support (read and upload media references)
- Derived properties support
- Enhanced subscription API
- Improved type safety with generated type guards

Type changes: `OntologyObject` replaced by `OsdkBase` from `@osdk/api`; `IsOntologyObject` removed.

**Python OSDK v2 (GA — July 2025):**

- Major version bump with breaking changes from 1.x (new query syntax)
- Improved type safety
- Derived properties support (beta), Media sets support (beta)
- Interface support: load, filter, order, paginate interfaces (Dec 2025)
- Code snippets available in Developer Console for interface operations
- Convert between interface instances and specific object types

**Platform SDKs (June 2025):**

- New SDKs separate from Ontology SDK for TypeScript, Python, Java
- Purpose: Interact with Palantir platform services beyond Ontology (resources, permissions, admin)
- Distinction: Platform SDK = platform admin ops; OSDK = Ontology data access

**TypeScript v2 Functions Runtime (GA — July 2025):**

- Full Node.js runtime (previously V8 isolate with limitations)
- Resources: **5GB memory, 8 CPUs**
- Full npm ecosystem, OSDK-native, streaming support
- Key features:
  - Full OSDK access within server-side functions
  - NPM library support (publish and consume from TypeScript v2 repos)
  - Marketplace integration (distribute functions as products)
  - API call support via `@palantir/functions-sources` library
  - Streaming support for real-time data processing
- Python and TypeScript v2 Functions with OSDKs are Marketplace-compatible

**Python Functions (GA — July 2025):**

- OSDK first-class citizen (not just pandas DataFrames — direct Ontology object access)
- External API access via `functions.sources` configuration
- Lightweight Functions for simple transforms (reduced overhead)
- Configurable resources (memory, CPU allocation)
- Distinction: Python Functions are callable from OSDK/Actions/AIP; Transforms are pipeline-only

**Palantir MCP (Model Context Protocol):**

| Timeline | Capability |
|----------|-----------|
| October 2025 | Initial MCP server for IDE integration (OSDK development tools) |
| January 2026 | Ontology MCP — Developer Console apps exposed as MCP tools for external AI agents |

IDE tools:
- View SDK name, version, object types, properties, links, actions, functions
- Manage SDK resources: add/remove, generate new versions, install from IDE
- Enhanced context: AI coding assistant aware of full OSDK capabilities

Ontology MCP:
- External AI agents (Claude, GPT, etc.) can query Ontology objects
- External AI agents can execute Ontology Actions
- MCP tools auto-generated from Developer Console application definitions

**Development Tooling Updates:**

- VS Code Workspaces: Continue extension pre-installed with Palantir-provided models (Mar 2025)
- Python knowledge: Continue has knowledge of dataset metadata + Python transforms SDKs
- TypeScript knowledge: Continue has full OSDK context (objects, properties, links, actions, functions)
- Python 3.12 supported across all environments (Jun 2025) — faster startup, lower memory
- SQL in Workspaces: Query dataset views including object materializations in JupyterLab/RStudio (Dec 2025)

---

## Component 3: Slate

### 3.1 Official Definition

Slate enables application developers to construct dynamic, responsive applications with custom design using drag-and-drop interface. Fully customizable using **HTML**, **CSS (Less)**, and **JavaScript**. Built on Palantir's open-source **Blueprint framework**. Uses **Handlebars templating** for dynamic content.

**Current Status:** Fully supported alongside Workshop. Legacy features in maintenance mode:
- **Phonograph writeback:** Legacy phase, no additional development expected
- **Postgres/SQL sync:** Supported but not in development; migrate to Ontology

### 3.2 Semantic Definition

**Analogies:**
- Custom web application framework within Foundry
- Internal tool builder like Retool/Appsmith with deeper Foundry integration
- Single-page application (SPA) builder

**Anti-Concepts:**
- NOT a no-code tool—requires HTML, CSS, JavaScript, SQL knowledge
- NOT mobile-first—unlike Workshop, no dedicated mobile support
- NOT prescriptive—provides "few built-in rails" compared to Workshop
- NOT for quick prototypes—Workshop better for rapid, low-maintenance apps

### 3.3 Structural Schema

```json
{
  "slateDocument": {
    "version": "string",
    "permalink": "string",
    "pages": [{
      "pageId": "string",
      "displayName": "Title Case Page Name",
      "widgets": [{
        "widgetId": "w_widgetName",
        "widgetType": "string",
        "position": { "x": 0, "y": 0, "width": 100, "height": 50 },
        "styles": "string (Less/CSS)"
      }]
    }],
    "queries": [{
      "queryId": "q_queryName",
      "queryType": "POSTGRES | API_GATEWAY | OBJECT_SET",
      "source": "string"
    }],
    "functions": [{
      "functionId": "f_functionName",
      "code": "string (JavaScript)"
    }],
    "variables": [{
      "variableId": "var_variableName",
      "type": "LOCAL | SHARED"
    }],
    "globalStyles": "string (Less/CSS)"
  }
}
```

**Naming Conventions:**

| Element | Convention | Example |
|---------|------------|---------|
| Widgets | `w_` + camelCase | `w_studentGradeTable` |
| Queries | `q_` + camelCase | `q_allStudentRecords` |
| Functions | `f_` + camelCase | `f_calculateGradeAverage` |
| Variables | camelCase | `selectedStudentId` |
| Pages | Title Case | `Student Dashboard` |

### 3.4 Decision Tree

```
USE SLATE WHEN:
├── Custom JavaScript logic required (complex calculations)
├── Pixel-perfect custom branding required (full CSS/Less control)
├── Public access needed (no Foundry accounts)
├── Maintaining existing Slate applications
└── Blueprint CSS design system requirements

USE WORKSHOP INSTEAD WHEN:
├── Simple operational workflow (inbox, dashboard, form)
├── Rapid development timeline
├── Mobile support needed
├── Non-technical maintenance required
└── Standard Ontology-centric application

MIGRATE EXISTING SLATE WHEN:
├── Major feature additions needed
├── Functionality now available in Workshop
├── Maintenance burden is high
├── Using deprecated features (Phonograph, Postgres sync)
```

### 3.5 Validation Rules

```javascript
const slateValidationRules = {
  namingConventions: {
    widgets: /^w_[a-z][a-zA-Z0-9]*$/,
    queries: /^q_[a-z][a-zA-Z0-9]*$/,
    functions: /^f_[a-z][a-zA-Z0-9]*$/
  },
  performance: {
    maxQueryRows: 10000,
    maxQueryTimeout: 20000,
    maxConfigurationSize: 2000000
  },
  dataAccess: {
    preferredMethod: "ONTOLOGY",
    legacyMethod: "POSTGRES",
    deprecatedWriteback: "PHONOGRAPH"
  },
  antiPatterns: [
    { id: "LARGE_POSTGRES_QUERY", check: "SELECT * without LIMIT" },
    { id: "BASE64_IMAGE", check: "data:image/ in config" },
    { id: "PHONOGRAPH_USAGE", check: "writeback to Phonograph" }
  ]
};
```

### 3.6 Canonical Examples (K-12 Education)

**Custom Weighted GPA Calculator:**

```javascript
// f_calculateWeightedGpa
const gradeData = {{q_studentGrades}};
const gradePoints = {
  'A+': 4.0, 'A': 4.0, 'A-': 3.7,
  'B+': 3.3, 'B': 3.0, 'B-': 2.7,
  'C+': 2.3, 'C': 2.0, 'C-': 1.7,
  'D': 1.0, 'F': 0.0
};

const weightedCredits = gradeData.map(course => {
  const points = gradePoints[course.letterGrade] || 0;
  const weight = course.isHonors ? 0.5 : (course.isAp ? 1.0 : 0);
  return {
    weightedPoints: (points + weight) * course.creditHours,
    creditHours: course.creditHours
  };
});

const totalWeightedPoints = weightedCredits.reduce((sum, c) => sum + c.weightedPoints, 0);
const totalCredits = weightedCredits.reduce((sum, c) => sum + c.creditHours, 0);

return { weightedGpa: (totalWeightedPoints / totalCredits).toFixed(2) };
```

**District-Branded Parent Portal (Less/CSS):**

```less
@district-primary: #1B4D89;
@district-secondary: #F5A623;

.pt-button.pt-intent-primary {
  background-color: @district-primary;
  &:hover { background-color: darken(@district-primary, 10%); }
}

.announcement-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  padding: 16px;
}
```

### 3.7 Anti-Patterns

**Anti-Pattern 1: Starting New Projects in Slate When Workshop Suffices**

Building a simple attendance dashboard in Slate (3-4 weeks development) when Workshop can accomplish the same in 1-2 days with built-in widgets.

**Anti-Pattern 2: Not Planning Migration for Legacy Features**

Continuing to use Phonograph writeback and Postgres sync without migration plan despite "legacy phase" status. Migrate to Ontology-based Actions.

### 3.8 Integration Points

| Dependency | Type | Notes |
|------------|------|-------|
| Blueprint CSS | Built-in | Palantir's open-source framework |
| Handlebars.js | Built-in | Dynamic templating |
| Lodash, Moment.js, Math.js, Numeral.js | Built-in | JavaScript utilities |
| Less CSS | Built-in | CSS preprocessor |

**Ontology Connection Methods:**

| Method | Use Case |
|--------|----------|
| OSDK | Full code-based access (preferred) |
| Object Set Panel | Simple tabular retrieval |
| Object Context Panel | Individual object lookup |
| Actions Widget | Data writeback (preferred over Phonograph) |
| Postgres | Legacy SQL queries (migrate to Ontology) |

---

## Component 4: REST API (Foundry API v2)

### 4.1 Official Definition

The Foundry API is a developer-friendly REST API for interacting with Palantir's Foundry platform. Consists of HTTP endpoints using OAuth 2.0 for authentication, designed with JSON requests/responses. Enables programmatic access to Ontology (Objects, Links, Actions), datasets, files, users, groups, and permissions.

**Base URL Pattern:** `https://{hostname}/api/v2/ontologies/{ontologyApiName}/...`

### 4.2 Semantic Definition

**Analogies:**
- RESTful API for Ontology access (like database API for semantically-linked objects)
- Enterprise GraphQL alternative
- Similar to Salesforce REST API, ServiceNow Table API

**Anti-Concepts:**
- NOT the OSDK—OSDK provides type-safe, generated code; REST is generic HTTP
- NOT Workshop—Workshop is UI builder; REST is for backend integrations
- NOT real-time streaming—use Streams API for real-time
- NOT SQL interface—use SQL Queries API for direct SQL

### 4.3 Structural Schema

**Search Request:**

```json
{
  "where": {
    "type": "and | or | not | eq | lt | gt | lte | gte | contains | isNull | prefix",
    "value": [
      { "type": "gte", "field": "gpa", "value": 3.5 },
      { "type": "eq", "field": "districtId", "value": "DIST-001" }
    ]
  },
  "orderBy": {
    "fields": [{ "field": "gpa", "direction": "desc" }]
  },
  "pageSize": 1000,
  "pageToken": "<optional>"
}
```

**Search Response:**

```json
{
  "data": [
    {
      "rid": "ri.phonograph2-objects.main.object.{uuid}",
      "properties": { "propertyName": "value" }
    }
  ],
  "nextPageToken": "v1.{base64-token}",
  "totalCount": 100
}
```

**Filter Types Reference:**

| Type | Example |
|------|---------|
| `eq` | `{"type": "eq", "field": "gradeLevel", "value": 10}` |
| `gt` / `gte` | `{"type": "gt", "field": "gpa", "value": 3.5}` |
| `lt` / `lte` | `{"type": "lte", "field": "absences", "value": 5}` |
| `contains` | `{"type": "contains", "field": "courses", "value": "AP-CALC"}` |
| `isNull` | `{"type": "isNull", "field": "graduationDate", "value": true}` |
| `prefix` | `{"type": "prefix", "field": "lastName", "value": "Sm"}` |
| `and` / `or` / `not` | Compound conditions (max 3 levels deep) |

### 4.4 Decision Tree

```
PROGRAMMATIC INTEGRATION?
├── YES → Need type-safety and generated code?
│   ├── YES → USE OSDK
│   └── NO → USE REST API
└── NO → End-user UI?
    ├── YES → USE WORKSHOP
    └── NO → Consider Slate or custom frontend with OSDK
```

### 4.5 Validation Rules

```typescript
const RESTAPIValidationRules = {
  rateLimits: {
    individualUser: { requestsPerMinute: 5000, concurrentRequests: 30 },
    serviceUser: { requestsPerMinute: Infinity, concurrentRequests: 800 }
  },
  pagination: {
    maxPageSize: 2000,
    pageTokenPattern: /^v1\.[A-Za-z0-9+/=]+$/
  },
  authentication: {
    tokenEndpoint: "https://{hostname}/multipass/api/oauth2/token",
    tokenFormat: "Bearer {JWT}"
  }
};
```

### 4.6 Canonical Examples (K-12 Education)

**GET: List Students**

```http
GET /api/v2/ontologies/k12Education/objects/studentRecord?pageSize=100 HTTP/1.1
Host: school-district.palantirfoundry.com
Authorization: Bearer eyJhbGciOiJSUzI1NiIs...
Content-Type: application/json
```

**POST: Search Students with GPA ≥ 3.5**

```http
POST /api/v2/ontologies/k12Education/objects/studentRecord/search HTTP/1.1
Authorization: Bearer eyJhbGciOiJSUzI1NiIs...
Content-Type: application/json

{
  "where": {
    "type": "and",
    "value": [
      { "type": "gte", "field": "gpa", "value": 3.5 },
      { "type": "eq", "field": "districtId", "value": "DIST-001" }
    ]
  },
  "orderBy": { "fields": [{ "field": "gpa", "direction": "desc" }] },
  "pageSize": 50
}
```

**POST: Execute Enrollment Action**

```http
POST /api/v2/ontologies/k12Education/actions/enrollStudentInCourse/apply HTTP/1.1
Authorization: Bearer eyJhbGciOiJSUzI1NiIs...
Content-Type: application/json

{
  "parameters": {
    "studentId": "STU-2024-001",
    "courseId": "COURSE-AP-CALC-2025",
    "enrollmentDate": "2025-01-15"
  }
}
```

**GET: Linked Objects (Student's Courses)**

```http
GET /api/v2/ontologies/k12Education/objects/studentRecord/STU-2024-001/links/courseEnrollment HTTP/1.1
Authorization: Bearer eyJhbGciOiJSUzI1NiIs...
```

### 4.7 Anti-Patterns

**Anti-Pattern 1: Not Handling Pagination**

```javascript
// ❌ WRONG - Only fetches first page
const response = await fetch('/api/v2/.../studentRecord');
return response.json();

// ✅ CORRECT - Iterate all pages
let allStudents = [], pageToken = null;
do {
  const url = pageToken 
    ? `/api/v2/.../studentRecord?pageToken=${pageToken}`
    : '/api/v2/.../studentRecord';
  const data = await fetch(url).then(r => r.json());
  allStudents.push(...data.data);
  pageToken = data.nextPageToken;
} while (pageToken);
```

**Anti-Pattern 2: Ignoring Rate Limits**

```javascript
// ❌ WRONG - Rapid-fire requests
await Promise.all(studentIds.map(id => fetch(`/api/.../${id}`)));

// ✅ CORRECT - Batch with backoff
for (let i = 0; i < studentIds.length; i += 25) {
  const batch = studentIds.slice(i, i + 25);
  await Promise.all(batch.map(id => fetchWithRetry(`/api/.../${id}`)));
}
```

### 4.8 Integration Points

**Complete Endpoint List (V2):**

| Category | Endpoints |
|----------|-----------|
| Objects | `GET .../objects/{type}`, `GET .../objects/{type}/{pk}`, `POST .../objects/{type}/search`, `POST .../objects/{type}/aggregate` |
| Links | `GET .../objects/{type}/{pk}/links/{linkType}` |
| Actions | `POST .../actions/{action}/apply`, `POST .../actions/{action}/validate`, `POST .../actions/{action}/applyBatch` |
| Metadata | `GET .../ontologies`, `GET .../ontologies/{id}/objectTypes`, `GET .../ontologies/{id}/actionTypes` |

**OAuth 2.0 Flows:**

| Flow | Use Case | Token Endpoint |
|------|----------|----------------|
| Authorization Code + PKCE | Web applications | `POST /multipass/api/oauth2/token` with `grant_type=authorization_code` |
| Client Credentials | Server-to-server | `POST /multipass/api/oauth2/token` with `grant_type=client_credentials` |
| Refresh Token | Token renewal | `POST /multipass/api/oauth2/token` with `grant_type=refresh_token` |

---

## Component 5: Automate (Workflows)

### 5.1 Official Definition

Automate is an application for setting up business automation. Users define **conditions** (checked continuously) and **effects** (executed when conditions met). Conditions can be time-based ("trigger every Monday at 9am"), object data conditions ("trigger when high-priority alert added"), or combinations. Effects include Foundry Actions and notifications (platform/email with attachments).

**Key Use Cases:** Scheduled reports, data alerting, workflow automation, watched searches.

### 5.2 Semantic Definition

**Analogies:**

| Platform | Comparison |
|----------|------------|
| Zapier | Similar trigger-action model |
| IFTTT | "If This Then That" pattern |
| Microsoft Power Automate | No-code automation for enterprise |
| Salesforce Flow | CRM automation equivalent |

**Anti-Concepts:**
- NOT a data pipeline scheduler—use Pipeline Builder for builds
- NOT a complex workflow orchestrator—use AIP Logic for multi-step LLM workflows
- NOT real-time streaming—latency ranges minutes to hour
- NOT a code execution environment—uses pre-defined Actions

### 5.3 Structural Schema

```json
{
  "automation": {
    "apiName": "string",
    "displayName": "string",
    "condition": {
      "type": "time | objectSetAdded | objectSetRemoved | objectSetModified | thresholdCrossed",
      "timeCondition": {
        "frequency": "hourly | daily | weekly | monthly | cron",
        "cronExpression": "0 9 * * 1",
        "timezone": "America/New_York"
      },
      "objectSetCondition": {
        "objectTypeApiName": "Student",
        "filters": [{ "property": "gradeLevel", "operator": "equals", "value": "12" }],
        "evaluationLatency": "live | scheduled",
        "watchedProperties": ["gpa", "attendanceRate"]
      }
    },
    "effects": [{
      "type": "action | notification | fallback",
      "actionEffect": {
        "actionTypeApiName": "sendParentNotification",
        "executionMode": "onceForAll | oncePerBatch | oncePerObject",
        "retryPolicy": { "type": "exponential", "maxRetries": 3 }
      },
      "notificationEffect": {
        "recipients": { "static": ["groupId"], "dynamic": { "objectProperty": "assignedCounselor" } },
        "content": { "heading": "Alert", "message": "{{student.name}}" },
        "attachments": ["notepadTemplateRid"]
      }
    }]
  }
}
```

**Cron Expression Format (5 fields):**

```
┌─────────── minute (0-59)
│ ┌───────── hour (0-23)
│ │ ┌─────── day of month (1-31)
│ │ │ ┌───── month (1-12)
│ │ │ │ ┌─── day of week (0-6, Sun=0)
* * * * *
```

| Expression | Meaning |
|------------|---------|
| `0 9 * * 1` | Every Monday at 9:00 AM |
| `0 8 1 * *` | First day of month at 8:00 AM |
| `0 15 * * 1-5` | Weekdays at 3:00 PM |
| `0 6 * * *` | Daily at 6:00 AM |

### 5.4 Decision Tree

```
NEED AUTOMATED RESPONSES TO DATA/TIME EVENTS?
├── Based on Ontology object changes?
│   ├── Notify users when objects change → AUTOMATE (Objects + Notification)
│   ├── Execute Actions automatically → AUTOMATE (Object condition + Action)
│   └── Complex multi-step LLM reasoning → AIP LOGIC (triggered by Automate)
├── Time-based only?
│   ├── Scheduled reports/digests → AUTOMATE (Time + Notification + PDF)
│   └── Pipeline/data build → PIPELINE SCHEDULER
└── User-initiated workflow → WORKSHOP ACTIONS
```

### 5.5 Validation Rules

```typescript
const AutomateValidationRules = {
  limits: {
    maxObjectsScheduledExecution: 100000,
    maxRecipientsPerAutomation: 10000,
    maxObjectsRealTimeExecution: 10000,
    maxObjectsPerObjectScheduled: 1000,
    maxBatchSize: 1000,
    historyRetention: "6 months"
  },
  cronExpression: {
    fieldCount: 5,
    minutesNotWildcard: true  // Minimum hourly frequency
  },
  permissions: {
    ownerRequires: ["Editor on save location", "Pass Action submission criteria", "Viewer on monitored objects"],
    recipientRequires: ["Viewer on automation", "Viewer on object instances"]
  }
};
```

### 5.6 Canonical Examples (K-12 Education)

**Daily Attendance Report (Time-based + Notification):**

```json
{
  "automation": {
    "apiName": "dailyAttendanceReport",
    "displayName": "Daily Attendance Report",
    "condition": {
      "type": "time",
      "timeCondition": {
        "cronExpression": "30 7 * * 1-5",
        "timezone": "America/New_York"
      }
    },
    "effects": [{
      "type": "notification",
      "notificationEffect": {
        "recipients": { "static": ["schoolAdminsGroup"] },
        "content": { "heading": "Daily Attendance Report" },
        "attachments": ["attendanceReportNotepadTemplate"]
      }
    }]
  }
}
```

**Low GPA Alert (ObjectSet Condition + Dynamic Recipient):**

```json
{
  "automation": {
    "apiName": "lowGradeAlert",
    "displayName": "Low GPA Alert to Counselor",
    "condition": {
      "type": "objectSetAdded",
      "objectSetCondition": {
        "objectTypeApiName": "Student",
        "filters": [{ "property": "currentGpa", "operator": "lt", "value": 2.0 }],
        "evaluationLatency": "live"
      }
    },
    "effects": [{
      "type": "notification",
      "notificationEffect": {
        "recipients": { "dynamic": { "objectProperty": "assignedCounselorId" } },
        "content": {
          "heading": "GPA Alert: Student Needs Intervention",
          "message": "Student {{student.fullName}} GPA dropped to {{student.currentGpa}}"
        },
        "objectGrouping": "oncePerObject"
      }
    }]
  }
}
```

**New Student Onboarding (Object Create + Action Effect):**

```json
{
  "automation": {
    "apiName": "newStudentOnboarding",
    "displayName": "New Student Onboarding Workflow",
    "condition": {
      "type": "objectSetAdded",
      "objectSetCondition": {
        "objectTypeApiName": "Student",
        "evaluationLatency": "live"
      }
    },
    "effects": [{
      "type": "action",
      "actionEffect": {
        "actionTypeApiName": "initiateStudentOnboarding",
        "parameters": { "newStudent": "$conditionEffectInput.addedObject" },
        "executionMode": "oncePerObject",
        "retryPolicy": { "type": "exponential", "maxRetries": 3 }
      }
    }]
  }
}
```

**Chronic Absence Webhook to External SIS:**

```json
{
  "automation": {
    "apiName": "chronicAbsenceWebhook",
    "condition": {
      "type": "thresholdCrossed",
      "thresholdCondition": {
        "functionApiName": "getStudentsExceedingAbsenceThreshold",
        "parameters": { "absenceThreshold": 5, "rollingDays": 30 }
      },
      "schedule": { "cronExpression": "0 6 * * *" }
    },
    "effects": [{
      "type": "action",
      "actionEffect": {
        "actionTypeApiName": "notifyExternalSisAbsenceAlert",
        "executionMode": "oncePerBatch",
        "batchSize": 100
      }
    }]
  }
}
```

### 5.7 Anti-Patterns

**Anti-Pattern 1: Infinite Loop / Self-Triggering**

Automation modifies objects matching its own trigger condition, causing infinite loop.

**Fix:** Use distinct status values; add filter for specific state transitions; disable "Include objects added/removed."

**Anti-Pattern 2: Missing Error Handling**

No fallback effect when Actions fail; failures go unnoticed.

**Fix:** Add `fallbackEffect` notification to admin group with error details.

**Anti-Pattern 3: Over-Notification Fatigue**

Every small edit triggers notification; users receive 50+ emails/day and start ignoring them.

**Fix:** Use scheduled digests; use `onceForAll` grouping; filter to significant changes only.

### 5.8 Integration Points

```
┌─────────────────────────────────────────────────────────┐
│                     AUTOMATE                            │
│  Monitors: ObjectTypes, ObjectSets, Time Schedules      │
├─────────────────────────────────────────────────────────┤
│                        │                                │
│  ┌────────────────────▼────────────────────┐           │
│  │              EFFECTS                     │           │
│  │  ┌─────────┐  ┌──────────┐  ┌─────────┐ │           │
│  │  │ Action  │  │ Notify   │  │Fallback │ │           │
│  │  └────┬────┘  └────┬─────┘  └────┬────┘ │           │
│  └───────┼────────────┼─────────────┼──────┘           │
│          │            │             │                   │
│          ▼            ▼             ▼                   │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│   │ActionType│  │Email/App │  │Admin     │             │
│   │Execution │  │Notify    │  │Alert     │             │
│   └──────────┘  └──────────┘  └──────────┘             │
│          │                                              │
│          ▼                                              │
│   ┌──────────────────────────────────────┐             │
│   │  External Systems (via Webhooks):    │             │
│   │  - Student Information Systems       │             │
│   │  - Parent Communication Platforms    │             │
│   │  - State Reporting Systems           │             │
│   └──────────────────────────────────────┘             │
└─────────────────────────────────────────────────────────┘
```

| Component | Relationship |
|-----------|-------------|
| Ontology | Source of trigger conditions (ObjectTypes, ObjectSets) |
| ActionTypes | Executed by Action effects |
| Functions | Compute thresholds, generate notification content |
| Notepad | PDF attachments for email notifications |
| Workshop | Displays automation status; Actions triggered by both |
| OSDK | Applications can create objects that trigger Automate |

---

## Cross-Cutting Concerns

### Component Integration Matrix

| From/To | Workshop | OSDK | Slate | REST API | Automate |
|---------|----------|------|-------|----------|----------|
| **Workshop** | Embedded modules | iframe bidirectional | iframe embed | Actions via backend | Triggers Actions |
| **OSDK** | Custom widgets | N/A | OSDK in Slate | Uses underneath | Creates triggering objects |
| **Slate** | iframe embed | OSDK queries | N/A | Query data | Actions trigger workflows |
| **REST API** | Backend for Actions | OSDK uses internally | Data queries | N/A | Automation APIs |
| **Automate** | Opens modules | N/A | N/A | N/A | Workflow dependencies |

### Ontology Core Dependencies

All 5 components depend on Ontology definitions from Sessions 1-3:

| Ontology Component | Workshop | OSDK | Slate | REST API | Automate |
|-------------------|----------|------|-------|----------|----------|
| **ObjectType** | Widget binding | Type-safe queries | Object Set Panel | GET/POST endpoints | Trigger conditions |
| **Property** | Column display | Filter/order | Query fields | Search filters | Watched properties |
| **LinkType** | Search Around | pivotTo() | Links panel | /links/ endpoint | Related object conditions |
| **ActionType** | Button execution | applyAction() | Action Widget | /actions/apply | Effect execution |

### Authentication Model

| Component | Auth Method | Token Scope |
|-----------|-------------|-------------|
| Workshop | Session-based (Foundry login) | User permissions |
| OSDK | OAuth 2.0 (Public/Confidential client) | Selected Ontology entities + user permissions |
| Slate | Session-based (Foundry login) | User permissions |
| REST API | OAuth 2.0 Bearer token | Scoped to OAuth app permissions |
| Automate | Owner permissions | Automation owner's access rights |

### K-12 Education Object Model Reference

```
┌─────────────────────────────────────────────────────────────────┐
│                    K-12 EDUCATION ONTOLOGY                      │
├─────────────────────────────────────────────────────────────────┤
│  ObjectTypes (apiName / displayName):                           │
│  • studentRecord / "Student Record"                             │
│  • classSection / "Class Section"                               │
│  • enrollmentRecord / "Enrollment Record"                       │
│  • attendanceRecord / "Attendance Record"                       │
│  • gradeEntry / "Grade Entry"                                   │
│  • assignment / "Assignment"                                    │
│  • gradingPeriod / "Grading Period"                            │
│  • schoolCalendar / "School Calendar"                          │
│                                                                 │
│  ActionTypes (apiName / displayName):                           │
│  • markStudentPresent / "Mark Student Present"                  │
│  • markStudentAbsent / "Mark Student Absent"                    │
│  • enterGrade / "Enter Grade"                                   │
│  • updateGrade / "Update Grade"                                 │
│  • enrollStudentInCourse / "Enroll Student in Course"          │
│  • initiateStudentOnboarding / "Initiate Student Onboarding"   │
│  • sendParentNotification / "Send Parent Notification"          │
│                                                                 │
│  LinkTypes:                                                     │
│  • studentRecord → enrollmentRecord (one-to-many)              │
│  • enrollmentRecord → classSection (many-to-one)               │
│  • studentRecord → attendanceRecord (one-to-many)              │
│  • studentRecord → gradeEntry (one-to-many)                    │
│  • assignment → gradeEntry (one-to-many)                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Conclusion

This reference document provides machine-readable specifications for Palantir Foundry's Application & API Layer. **Workshop** enables rapid no-code application development for Ontology-centric workflows. **OSDK** provides type-safe, generated code for developers building custom applications in TypeScript, Python, or Java. **Slate** remains supported for complex custom JavaScript/CSS applications but new projects should prefer Workshop. **REST API v2** offers direct HTTP access with OAuth 2.0 authentication, **5,000 requests/minute** rate limits for users, and **pageToken-based pagination** up to 2,000 records per page. **Automate** delivers condition-based workflow automation with time-based (cron) and ObjectSet triggers executing Actions and notifications.

For K-12 Education implementations, the recommended architecture combines Workshop dashboards for administrators and teachers, OSDK-powered mobile apps for field staff, Automate workflows for GPA alerts and attendance notifications, and REST API integrations with existing Student Information Systems.