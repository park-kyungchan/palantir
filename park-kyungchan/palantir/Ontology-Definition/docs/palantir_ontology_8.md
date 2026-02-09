# Palantir Ontology: Security & Governance — Complete YAML Reference

**Version**: 2.0.0 | **Verification Date**: February 8, 2026 | **Target Consumer**: Claude-Opus-4.6

## Executive Summary

This document provides the complete security model for Palantir Foundry Ontology, covering **data-level access control** (markings), **multi-tenant isolation** (organizations), **feature permissions** (RBAC), **filtered data exposure** (restricted views), **schema governance** (proposals), **audit trails**, **compliance templates** (GDPR, HIPAA, SOX), **service mesh security**, **OSDK authentication**, and **granular object/property security policies** with full depth on the 8-operator comparison system, weight limits, and cell-level security patterns.

> **Cross-references:**
> - ObjectType definitions → `palantir_ontology_1.md`
> - ActionType permissions → `palantir_ontology_3.md`
> - OSDK authentication patterns → `palantir_ontology_6.md`
> - Versioning & Governance workflow → `palantir_ontology_7.md`
> - Function & Automation security → `palantir_ontology_3.md` §2
> - Ontology Decomposition security phase → `palantir_ontology_9.md` Phase 7

---

# 1. Marking-Based Access Control

## official_definition

> "Markings provide data-level access control that enforces who can see specific objects, properties, or rows based on classification and mandatory marking membership."

## Schema

```yaml
markings:
  purpose: "Row-level and column-level access control"
  types:
    MANDATORY_MARKING:
      description: "User must have marking to access data"
      enforcement: "Additive — user needs ALL mandatory markings on a row"
      scope: "Applied at property level"
    CLASSIFICATION_MARKING:
      description: "Hierarchical classification levels"
      enforcement: "User needs equal or higher classification"
      scope: "Applied at property or object level"

  application:
    property_level: "Mark specific properties as restricted"
    row_level: "Marking column in backing dataset filters object visibility"
  enforcement: "Applied at query time — users never see unauthorized data"
```

## structural_schema

```yaml
structural_schema:
  marking_system:
    definition: "Named access control labels applied to data and resources"
    enforcement: "Server-side at query time; client never receives unauthorized data"
    inheritance: "Child resources inherit parent markings unless explicitly overridden"
    precedence: "Most restrictive marking wins when multiple apply"

    marking_types:
      MANDATORY_MARKING:
        description: "Requires explicit membership to access marked data"
        behavior: "Additive restriction — user must be member of ALL mandatory markings"
        example: "CONFIDENTIAL, TOP_SECRET, EXPORT_CONTROLLED"
        membership: "Managed by marking administrators"
      CLASSIFICATION_MARKING:
        description: "Hierarchical security classification levels"
        behavior: "User clearance must meet or exceed classification level"
        hierarchy: "Higher clearance includes access to lower levels"

    marking_scoping:
      organization_scoped: "Marking only valid within a single organization"
      global: "Marking valid across all organizations"

  property_level_markings:
    granularity: "Per-property per-ObjectType"
    configuration: "Ontology Manager → ObjectType → Property → Security"
    behavior:
      unauthorized_user:
        property_visibility: "Property column hidden entirely"
        object_visibility: "Object still visible (other properties shown)"
        query_filter: "Cannot filter on marked property"
        aggregation: "Cannot aggregate on marked property"
      authorized_user:
        property_visibility: "Full access to property values"
        query_filter: "Can filter on marked property"
        aggregation: "Can aggregate on marked property"
    example:
      object_type: Employee
      properties:
        fullName: { markings: [] }  # Public within org
        salary: { markings: [HR_CONFIDENTIAL] }  # Only HR can see
        socialSecurityNumber: { markings: [HR_CONFIDENTIAL, PII_RESTRICTED] }  # HR + PII clearance
        department: { markings: [] }  # Public within org

  row_level_markings:
    granularity: "Per-object-instance"
    configuration:
      backing_column: "Marking column in backing dataset"
      column_type: "String (marking identifier) or Array<String>"
      mapping: "Configured in Object Storage sync pipeline"
    behavior:
      unauthorized_user:
        object_visibility: "Object completely hidden from queries"
        link_traversal: "Object not returned in link results"
        aggregation: "Object excluded from aggregation counts"
    combined_with_property_markings:
      description: "Row and property markings are AND-ed together"
      example: "User needs BOTH SECRET clearance AND HR_CONFIDENTIAL marking to see salary of a SECRET-marked object"
```

## CBAC Classification Hierarchy

```yaml
cbac_hierarchy:
  description: "Classification-Based Access Control with hierarchical levels"
  pattern: "Higher classification grants access to lower levels"

  levels:
    UNCLASSIFIED:
      clearance_required: NONE
      abbreviation: "U"
      access: "All authenticated users"
    CONTROLLED_UNCLASSIFIED:
      clearance_required: BASIC
      abbreviation: "CUI"
      access: "Users with basic clearance"
    CONFIDENTIAL:
      clearance_required: CONFIDENTIAL
      abbreviation: "C"
      access: "Users with Confidential clearance or above"
    SECRET:
      clearance_required: SECRET
      abbreviation: "S"
      access: "Users with Secret clearance or above"
    TOP_SECRET:
      clearance_required: TOP_SECRET
      abbreviation: "TS"
      access: "Users with Top Secret clearance only"

  hierarchy_rule: "Higher clearance includes access to all lower levels"
  enforcement: "Server-side at query time; same as markings"

  cross_classification:
    description: "Multiple independent classification dimensions"
    example: "SENSITIVITY (Public < Internal < Confidential < Secret) × REGION (US, EU, APAC)"
    enforcement: "User must meet each dimension independently"

  multi_classification_objects:
    description: "Single object with properties at different classification levels"
    behavior: "Each property independently enforced based on user clearance"
    example:
      object_type: MilitaryAsset
      properties:
        asset_id: { classification: UNCLASSIFIED }
        location: { classification: CONFIDENTIAL }
        mission_assignment: { classification: SECRET }
        capabilities: { classification: TOP_SECRET }

  classification_plus_markings:
    rule: "User must satisfy BOTH classification clearance AND marking membership"
    example: "Property 'operationalDetails' requires Secret clearance AND NATO_RESTRICTED marking"

  aggregation_security:
    warning: "Users may infer classified data from aggregation results (statistical disclosure)"
    mitigation: "Apply minimum aggregation thresholds (e.g., suppress groups with < 5 members)"
```

## query_enforcement

```yaml
query_enforcement:
  flow:
    1: "Client sends query via OSDK or REST API"
    2: "Server authenticates user identity (OAuth2 token)"
    3: "Server resolves user's marking memberships"
    4: "Query planner applies marking filters before data retrieval"
    5: "Results returned contain only authorized rows and properties"
  performance_implications:
    row_markings: "Additional filter predicate in query plan"
    property_markings: "Column projection excludes marked columns"
    complex_markings: "Multiple AND conditions may slow queries"
  consistency:
    realtime: "Marking changes take effect within seconds"
    caching: "Client-side caches may serve stale data briefly"
    recommendation: "Use short TTL for security-sensitive queries"
```

---

# 2. Organizations & Multi-Tenancy

## structural_schema

```yaml
organizations:
  definition: "Top-level isolation boundary for resources and users"
  purpose: "Multi-tenant data isolation within a single Foundry stack"

  scoping:
    resources: ["Datasets", "ObjectTypes", "Actions", "Functions", "Workflows", "Pipelines"]
    users:
      - "User accounts are scoped to organization"
      - "Users can belong to multiple organizations"
      - "Permissions are per-organization"

  visibility:
    within_org: "Resources visible to org members (subject to RBAC)"
    cross_org: "Resources invisible by default; requires explicit sharing"

  project_based_isolation:
    definition: "Logical grouping of resources within an organization"
    access_model:
      project_membership: "Required to see project resources"
      role_within_project: "Determines read/write/admin capabilities"
      cross_project_access: "Must be explicitly granted"
    ontology_impact:
      object_types: "Can reference types from other projects if shared"
      links: "Cross-project links require both project memberships"
      actions: "Execution requires project membership + action-level permissions"

  cross_org_patterns:
    shared_ontology_types:
      workflow:
        1: "Source org admin grants type access to target org"
        2: "Target org admin accepts and configures permissions"
        3: "Users in target org can query shared types"
      limitations:
        - "Read-only by default; write requires explicit grant"
        - "Markings still enforced at source org level"
    federated_queries:
      requirement: "User must have memberships in both organizations"
      performance: "May be slower due to cross-org resolution"
    service_accounts:
      use_case: "Automated pipelines processing cross-org data"
      security: "Scoped tokens with minimal necessary permissions"
```

---

# 3. Role-Based Access Control (RBAC)

## structural_schema

```yaml
rbac_roles:
  Viewer:
    description: "Read-only access to resources"
    capabilities:
      objects: "View object instances and properties"
      object_types: "View schema definition"
      links: "Traverse links (read)"
      actions: "Cannot execute"
      functions: "Cannot execute"
  Editor:
    description: "Read and write access"
    capabilities:
      objects: "View and modify (via Actions)"
      links: "Traverse and modify (via Actions)"
      actions: "Execute permitted actions"
      functions: "Execute permitted functions"
  Owner:
    description: "Full control including administration"
    capabilities:
      objects: "Full CRUD"
      object_types: "Schema modification"
      actions: "Execute and configure"
      administration: "Manage permissions, markings, governance"
  Discoverer:
    description: "Can find but not read resources"
    capabilities:
      objects: "See existence in search results but not property values"
      object_types: "See type name and description"
      links: "See link existence but not traverse"
      use_case: "Data catalog browsing without data access"

object_type_permissions:
  configuration: "Ontology Manager → ObjectType → Permissions"
  permission_levels:
    view_objects: { default: "All authenticated users in org" }
    edit_objects: { default: "Editors and above" }
    view_schema: { default: "All authenticated users" }
    edit_schema: { default: "Owners only" }
    manage_permissions: { default: "Owners only" }
  grant_targets: ["Individual users", "Groups", "Organizations", "Service accounts"]

property_permissions:
  mechanisms:
    markings: "Primary mechanism — marking membership required"
    visibility: "NORMAL | PROMINENT | HIDDEN"
  visibility_levels:
    NORMAL: "Shown in standard views"
    PROMINENT: "Highlighted in views (important properties)"
    HIDDEN: "Not shown in standard views; accessible via API"

link_permissions:
  read_access: "View permission on both source and target ObjectTypes required"
  write_access: "Edit permission on link + permission on both endpoints"
  marking_interaction:
    source_marked: "User must have source marking to see link exists"
    target_marked: "User must have target marking to see linked object"
    both_marked: "User needs both markings to traverse link"

action_permissions:
  configuration: "Ontology Manager → ActionType → Permissions"
  permission_types:
    execute: { grant_to: "Users, groups, or roles" }
    configure: { grant_to: "Owners and designated admins" }
  submission_criteria:
    purpose: "Dynamic permission checks at action execution time"
    types:
      parameter_based: "Check parameter values before execution"
      user_based: "Check current user attributes"
      object_based: "Check properties of referenced objects"
```

---

# 4. Restricted Views

## structural_schema

```yaml
restricted_views:
  definition: "Filtered views of ObjectTypes that limit visible objects based on marking membership"
  purpose: "Provide scoped access without modifying the underlying ObjectType"

  configuration:
    location: "Ontology Manager → ObjectType → Restricted Views"
    steps:
      1: "Define filter criteria (marking-based)"
      2: "Assign view to user groups"
      3: "Users see only objects matching their view filter"

  behavior:
    query_rewriting: "Server adds view filter to all queries automatically"
    transparency: "Users are unaware of the restriction"
    composability: "Multiple views can be combined (AND logic)"

  example:
    object_type: Employee
    views:
      us_employees_view:
        filter: "country == 'US'"
        granted_to: ["us-team-group"]
        effect: "US team only sees US employees"
      engineering_view:
        filter: "department == 'Engineering'"
        granted_to: ["eng-managers-group"]
        effect: "Engineering managers only see engineers"
      combined:
        user_in_both_groups: "Sees only US engineers (AND of both filters)"

  performance:
    query_overhead: "Additional filter predicate added to every query"
    indexing_recommendation:
      - "Ensure filter columns are indexed in Object Storage"
      - "Use simple equality or range filters for best performance"
      - "Avoid complex nested conditions in view definitions"
    comparison_with_markings:
      markings: "Native enforcement; optimized query path"
      restricted_views: "Application-level filtering; slight overhead"
      recommendation: "Use markings for security; restricted views for business segmentation"
```

---

# 5. Ontology Proposals & Governance

## Schema

```yaml
ontology_proposals:
  purpose: "Git-like branching model for Ontology schema changes"

  workflow:
    1_branch_creation: "Derived from main version; isolated experimentation"
    2_proposal: "Contains reviews and metadata; each resource = separate Task"
    3_rebase: "Manual incorporation of Main changes; conflict resolution"
    4_review: "Reviewer assignment; individual task approval"
    5_merge: "Integration into Main (atomic)"

  review_actions:
    approve: "Reviewer approves the change"
    request_changes: "Reviewer asks for modifications"
    reject: "Reviewer rejects the change"
    comment: "Reviewer adds feedback without decision"

  per_task_review:
    description: "Each resource change reviewed independently"

  conflict_resolution:
    detection: "Automatic on rebase"
    types:
      schema_conflict: "Same property modified in both branch and main"
      dependency_conflict: "Branch depends on main change that was reverted"
    resolution:
      auto_resolution: "Simple non-overlapping changes resolved automatically"
      manual_rebase: "Incorporate main changes → resolve → re-validate"

  migration_approval:
    breaking_changes: "Require explicit migration approval"
    migrations: ["drop_property_edits", "cast_property_type", "move_edits", "drop_all_edits"]
```

---

# 6. Audit Trail

## Action Audit Logging

```yaml
action_audit:
  scope: "Every Action execution is logged"
  logged_fields:
    identity: ["user_id", "service_account_id", "timestamp"]
    action: ["action_type (apiName)", "parameters"]
    result: ["status (SUCCESS|FAILED|VALIDATION_FAILED)", "edits_applied", "validation_failures"]
    context: ["application", "ip_address", "session_id"]
  retention:
    default: "Platform-configured (typically 90 days - 1 year)"
    compliance: "Configurable per regulation (GDPR, HIPAA, SOX)"
```

## Schema Change History

```yaml
schema_audit:
  scope: "Every Ontology schema change is tracked"
  tracked_changes:
    object_types: ["Property add/modify/delete", "Primary key changes", "Status changes"]
    link_types: ["Creation/deletion", "Cardinality changes"]
    actions: ["Rule modifications", "Parameter changes", "Permission changes"]
    interfaces: ["Shared property changes", "Implementation changes"]
  metadata: ["who", "when", "what", "why (proposal description)", "how (direct vs proposal)"]
```

## Access Logging

```yaml
access_logging:
  data_access:
    logged_events: ["Object queries", "Property access", "Link traversals", "Aggregations", "Exports"]
    granularity:
      default: "Type-level (which ObjectType was queried)"
      enhanced: "Object-level (which specific objects were accessed)"
  compliance_reporting:
    gdpr: ["DSAR requests", "Right to erasure tracking", "Data processing records"]
    hipaa: ["PHI access logs", "Minimum necessary verification"]
    sox: ["Financial data access controls", "Segregation of duties enforcement"]
```

---

# 7. Compliance Templates

## GDPR Compliance Configuration

```yaml
gdpr_compliance:
  scope: "General Data Protection Regulation (EU)"
  ontology_configuration:
    personal_data_marking:
      marking_name: "PII_PERSONAL_DATA"
      type: MANDATORY_MARKING
      apply_to: "All properties containing personal data"
      properties: ["fullName", "email", "phoneNumber", "address", "dateOfBirth", "nationalId"]
    sensitive_personal_data_marking:
      marking_name: "PII_SENSITIVE"
      type: MANDATORY_MARKING
      apply_to: "Special category data (GDPR Art. 9)"
    consent_tracking:
      object_type: ConsentRecord
      properties: ["dataSubjectId (PK)", "consentDate", "consentPurpose", "withdrawalDate", "lawfulBasis"]
    data_subject_access_request:
      action_type: ProcessDSAR
      request_types: ["ACCESS", "ERASURE", "PORTABILITY", "RECTIFICATION"]
    retention_policy:
      approach: "Anonymize rather than delete — preserves analytics while removing PII"
  audit_retention: "Minimum 3 years"
```

## HIPAA Compliance Configuration

```yaml
hipaa_compliance:
  scope: "Health Insurance Portability and Accountability Act (US)"
  ontology_configuration:
    phi_marking:
      marking_name: "PHI_PROTECTED"
      type: MANDATORY_MARKING
      apply_to: "All 18 HIPAA identifiers"
    minimum_necessary_enforcement:
      strategy: "Restricted views + property-level markings"
      views:
        clinical_view: "Clinical staff — diagnosis, treatment visible"
        billing_view: "Billing department — account, insurance visible"
        research_view: "Researchers — de-identified dataset only"
    de_identification:
      safe_harbor_method: "Remove all 18 HIPAA identifiers"
    breach_tracking:
      object_type: SecurityBreach
      automation: "New breach → notify Privacy Officer + 60-day countdown"
  audit_retention: "Minimum 6 years"
```

## SOX Compliance Patterns

```yaml
sox_compliance:
  scope: "Sarbanes-Oxley Act (US) — Financial data integrity"
  ontology_configuration:
    financial_data_marking:
      marking_name: "SOX_FINANCIAL"
      type: MANDATORY_MARKING
    segregation_of_duties:
      description: "Same user cannot both create and approve"
      implementation: "Action submission criteria with CURRENT_USER conditions"
    immutable_audit_trail:
      description: "Financial transactions cannot be deleted or modified after posting"
      rules: ["Modifications create reversal + new entry", "Deletion not permitted"]
    period_close_controls:
      description: "Prevent modifications to closed financial periods"
  audit_retention: "Minimum 7 years"
```

---

# 8. Service Mesh Security

## mTLS Configuration

```yaml
mtls_configuration:
  description: "Mutual TLS between OSDK service and Foundry API Gateway"
  flow:
    1: "Service account obtains client certificate from CA"
    2: "Client presents certificate during TLS handshake"
    3: "Gateway verifies client certificate against trusted CAs"
    4: "Gateway maps certificate identity to Foundry service account"
    5: "Standard OAuth2 token used for Ontology-level authorization"
  certificate_rotation:
    strategy: "Automated rotation via cert-manager or HashiCorp Vault"
    frequency: "90 days recommended"
```

## Network Policy Patterns

```yaml
network_policies:
  description: "Kubernetes NetworkPolicy to restrict OSDK service communication"
  patterns:
    egress_to_foundry_only: "OSDK service can only communicate with Foundry API Gateway"
    ingress_from_gateway_only: "OSDK service only accepts traffic from API gateway"
    inter_service_isolation: "Prevent OSDK services from communicating with each other"
  best_practices:
    - "Start with deny-all, then explicitly allow required communication"
    - "Use namespace-level isolation between environments"
    - "Log denied connections for security monitoring"
```

---

# 9. Security in OSDK

## OAuth2 Token Management

```yaml
oauth2_flows:
  authorization_code:
    use_case: "User-facing web and mobile applications"
    token_lifetime:
      access_token: "1 hour (configurable)"
      refresh_token: "30 days (configurable)"
  client_credentials:
    use_case: "Server-to-server and automated pipelines"
    security: ["Store client_secret securely", "Rotate regularly", "Minimum necessary scopes"]
```

## Service Account Authentication

```yaml
service_accounts:
  best_practices:
    - "One service account per application/pipeline"
    - "Never share credentials across applications"
    - "Rotate secrets on 90-day schedule"
    - "Use environment variables or vault for secret storage"
    - "Never commit credentials to source control"
  permissions:
    read_only: "api:ontologies-read"
    read_write: "api:ontologies-read, api:ontologies-write"
    admin: "api:admin (avoid unless absolutely necessary)"
```

## Rate Limiting

```yaml
rate_limiting:
  limits:
    per_user: "100-500 requests/second (platform-configured)"
    per_service_account: "Same as user limits; configurable by admin"
  response:
    status_code: 429
    headers: ["Retry-After", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"]
  best_practices:
    - "Implement exponential backoff for retries"
    - "Use pagination to reduce request count"
    - "Use subscriptions instead of polling"
    - "Batch operations where possible"
```

---

# 10. Object & Property Security Policies (Granular Policies)

## official_definition

> "Object and property security policies provide cell-level access control on the Ontology,
> independent of backing data source permissions. They allow row-level, column-level, and
> cell-level security to be configured directly on object types through Ontology Manager."

## structural_schema

```yaml
security_policy_model:
  object_security_policy:
    description: "Controls visibility of entire object instances (row-level security)"
    scope: "Per ObjectType — applies to all instances of that type"
    independence: "Operates independently of backing data source permissions"
    effect: "User must pass the object security policy to see any object instance"
    configuration: "Ontology Manager → ObjectType → Security → Object Security Policy"
    supported_operators: ["Equal", "Intersects", "Subset_of", "Superset_of"]
    restriction: "Object Security Policies do NOT support LT/GT/LTE/GTE"

  property_security_policy:
    description: "Controls visibility of individual property values (column-level security)"
    scope: "Per property within an ObjectType"
    relationship: "Layered on top of object security policy"
    effect: "User must pass BOTH object + property policy to see the property value"
    null_behavior: "If user passes object policy but fails property policy → sees null value"
    configuration: "Ontology Manager → ObjectType → Property → Security Policy"
    supported_operators: "All 8 comparison types"

  cell_level_security:
    description: "Combination of object + property policies achieves cell-level control"
    formula: "access(cell) = pass(object_policy) AND pass(property_policy)"
    example: |
      Employee ObjectType:
        Object Policy: "User can see employees in their own department"
        Property Policy on 'salary': "Only HR group can see salary"
        Result: Non-HR user sees department employees but salary shows null

  vs_data_source_policies:
    recommendation: "Object and property security policies are RECOMMENDED over data source policies"
    benefits:
      - "Unified cell-level security (row + column + cell) in a single configuration"
      - "Configured directly on the object type (no need to manage backing dataset permissions)"
      - "Simpler to maintain than multiple restricted views across data sources"
      - "Independent of data pipeline structure changes"
    when_to_use_data_source_policies:
      - "Legacy configurations that predate object security policies"
      - "Complex multi-source ObjectTypes where source-level control is needed"
      - "Regulatory requirements mandating source-level access control"
```

## Granular Policy Templates (Full Depth)

```yaml
granular_policy_templates:
  description: "Policies are defined as templates with dynamic parameters"

  user_attributes:
    description: "Runtime attributes of the requesting user"
    supported_types:
      string: "Single string attribute (e.g., department code, region)"
      multivalue_string: "Array of string attributes (e.g., group memberships, region list)"
      numeric: "Numeric attribute (e.g., clearance level, employee tier)"
    supported_attributes:
      organization: "ri.multipass..organization.{uuid}"
      group_membership: "User's group UUIDs (not names — prevents renaming issues)"
      user_id: "Unique user identifier"
    important: "Always use UUIDs, not display names, to prevent renaming-related security gaps"

  comparison_types:
    description: "8 comparison operators available for policy conditions"
    operators:
      Equal:
        formula: "column == value OR column == user_attribute"
        supported_by: [object_security_policy, property_security_policy]
      Intersects:
        formula: "column_collection ∩ user_attribute_collection ≠ ∅"
        supported_by: [object_security_policy, property_security_policy]
      Subset_of:
        formula: "column_collection ⊆ user_attribute_collection"
        supported_by: [object_security_policy, property_security_policy]
      Superset_of:
        formula: "column_collection ⊇ user_attribute_collection"
        supported_by: [object_security_policy, property_security_policy]
      Less_than:
        formula: "column < value"
        supported_by: [property_security_policy]
        restriction: "NOT supported by Object Security Policies"
      Greater_than:
        formula: "column > value"
        supported_by: [property_security_policy]
        restriction: "NOT supported by Object Security Policies"
      Less_than_or_equal_to:
        formula: "column <= value"
        supported_by: [property_security_policy]
        restriction: "NOT supported by Object Security Policies"
      Greater_than_or_equal_to:
        formula: "column >= value"
        supported_by: [property_security_policy]
        restriction: "NOT supported by Object Security Policies"

    summary:
      object_security_policies: "Only Equal, Intersects, Subset_of, Superset_of (4 operators)"
      property_security_policies: "All 8 operators"
      restricted_view_granular_policies: "All 8 operators"

  logical_operators:
    AND: "All conditions must be true"
    OR: "At least one condition must be true"
    nesting: "Conditions can be nested with AND/OR"

  weight_limits:
    max_comparisons: 10
    total_weight_limit: 10000
    weight_calculation:
      constant_vs_field: "1 weight unit per comparison"
      collection_vs_field: "1000 weight units per collection-to-field comparison"
      formula: "total_weight = sum(comparison_weights); must be < 10,000"
      example: "5 constant comparisons (5 weight) + 2 collection comparisons (2000 weight) = 2005 total (OK)"
    on_exceeded: "Contact Palantir Support for assistance — limits are designed for policy quality, not performance"

  policy_examples:
    basic:
      name: "Department-scoped employee access"
      description: "Users can only see employees in their own department"
      template:
        condition: "employee.department_id == user.organization_id"
        type: "Object Security Policy on Employee ObjectType"
      result: "Each user sees only their department's employees"

    advanced:
      name: "Region + role scoped access with PII protection"
      description: "Users see objects in their region; only compliance role sees PII"
      object_policy:
        condition: "object.region IN user.assigned_regions"
        operator: "Intersects"
      property_policy_on_ssn:
        condition: "user.groups CONTAINS compliance_group_uuid"
        operator: "Equal"
      result: "Users see regional objects; SSN is null unless user is in compliance group"

  mandatory_controls:
    inheritance:
      description: "Object security policies inherit mandatory controls from backing data sources"
      controls: ["markings", "organizations", "classifications"]
      behavior: "Inherited by default — can be customized (add new or remove inherited)"
      restriction: "Removing inherited controls reduces security — requires careful review"
    customization:
      add_controls: "Add new mandatory markings/organizations beyond what data sources require"
      remove_controls: "Remove inherited controls that are no longer necessary"
      override_behavior: "Custom controls are merged with inherited controls"
    agentic_access:
      description: "Granular policies also constrain AI agent access to the Ontology"
      enforcement: "Policies are dynamically computed at runtime for every interaction"
      scope: "Both human and agentic access are governed by the same policy framework"
      capabilities:
        - "Row-level restrictions on agent data access"
        - "Column-level restrictions on sensitive properties"
        - "Security markings propagated across data pipelines"
        - "User-delegation model (agent operates with delegated user attributes)"
```

## Data Pipeline Integrity

```yaml
pipeline_integrity:
  description: "Granular policies depend on assumptions about backing data structure"

  assumptions_to_verify:
    - "Column names referenced in policies exist and have expected data types"
    - "User attribute columns contain valid UUIDs (not display names)"
    - "Data transformations upstream do not rename or remove policy-referenced columns"
    - "Join operations preserve the row-level semantics that policies depend on"

  monitoring_recommendations:
    - "Add pipeline checks upstream of policy-backed resources to verify data assumptions"
    - "Alert on schema changes to tables backing policy-protected ObjectTypes"
    - "Test policy behavior after any data pipeline modification"
    - "Document which pipeline outputs are consumed by granular policies"
```

---

## Code Pattern Identification Rules

```yaml
identification_rules:
  - pattern: "Row-level security (RLS) in database"
    mapping: "Markings on backing dataset columns OR Object Security Policy"
    confidence: HIGH
  - pattern: "@PreAuthorize / @Secured annotation"
    mapping: "RBAC roles on ActionType or ObjectType"
    confidence: HIGH
  - pattern: "Multi-tenant isolation middleware"
    mapping: "Organizations with project-level scoping"
    confidence: HIGH
  - pattern: "Data classification labels"
    mapping: "CLASSIFICATION_MARKING"
    confidence: HIGH
  - pattern: "Column-level encryption or masking"
    mapping: "Property-level markings + Ciphertext type"
    confidence: MEDIUM
  - pattern: "Cell-level security"
    mapping: "Combined Object + Property Security Policies"
    confidence: HIGH
  - pattern: "Attribute-based access control (ABAC)"
    mapping: "Granular Policy templates with user attribute comparisons"
    confidence: HIGH
  - pattern: "Row-level security filter (WHERE tenant_id = current_user.org)"
    mapping: "Object Security Policy with user attribute comparison"
    confidence: HIGH
  - pattern: "Column-level access control (@JsonIgnore for unauthorized roles)"
    mapping: "Property Security Policy with group-based condition"
    confidence: HIGH
  - pattern: "Multi-tenant data isolation (tenant_id foreign key)"
    mapping: "Object Security Policy with organization-based condition"
    confidence: HIGH
  - pattern: "Dynamic data masking (PII fields shown as ***)"
    mapping: "Property Security Policy (null instead of masked value)"
    confidence: MEDIUM
    note: "Palantir returns null, not masked values — adjust UI accordingly"

security_layer_mapping:
  "Authentication": "Foundry SSO / OAuth 2.0 via OSDK"
  "Authorization (feature)": "RBAC roles"
  "Authorization (data)": "Markings + Restricted Views + Granular Policies"
  "Isolation": "Organizations"
  "Encryption at rest": "Foundry platform-managed"
  "Encryption in transit": "TLS (platform-managed)"
  "Audit logging": "Foundry audit log (built-in)"
```

## Anti-Patterns

```yaml
anti_patterns:
  - id: "SEC-ANTI-001"
    name: "Over-Classification"
    bad: "Classifying everything as SECRET makes data unusable for most users"
    good: "Classify at the property level; only sensitive properties need high classification"

  - id: "SEC-ANTI-002"
    name: "Inconsistent Classification Across Related Types"
    bad: "Employee at CONFIDENTIAL but linked Salary at UNCLASSIFIED leaks salary data"
    good: "Review classification consistency across ObjectTypes and their links"

  - id: "SEC-ANTI-003"
    name: "Policy on Renamed Column"
    bad: "Column referenced in policy is renamed in upstream transform"
    result: "Policy silently fails open or closed depending on implementation"
    good: "Freeze column names for policy-backed datasets; use views to isolate"

  - id: "SEC-ANTI-004"
    name: "User Attribute by Name Instead of UUID"
    bad: "Policy references group name 'Finance Team' instead of group UUID"
    result: "Renaming the group breaks the policy"
    good: "Always use ri.multipass UUIDs in both policy column and definition"

  - id: "SEC-ANTI-005"
    name: "No Network Policy (Default Allow-All)"
    bad: "Compromised OSDK service can reach any internal resource"
    good: "Always define egress policies restricting communication to Foundry only"
```

---

## Security Checklist for OSDK Applications

```yaml
security_checklist:
  authentication:
    - "Use OAuth2 authorization code flow for user-facing apps"
    - "Use client credentials for server-to-server communication"
    - "Never hardcode credentials in source code"
    - "Store secrets in environment variables or vault"
  authorization:
    - "Request minimum necessary OAuth scopes"
    - "Verify user permissions before showing UI elements"
    - "Use markings for data-level access control"
  data_protection:
    - "Use HTTPS for all API communication"
    - "Do not cache sensitive data client-side"
    - "Use property sub-selection to avoid fetching unnecessary sensitive fields"
  development_practices:
    - "Use separate service accounts for dev/staging/production"
    - "Never use production credentials in development"
    - "Use Ontology proposals for schema changes (never direct edit in production)"
```

---

## Security Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLIENT APPLICATION                           │
│                  (OSDK TypeScript/Python/Java)                   │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐                                                 │
│  │  OAuth2      │  ← Token management + Refresh + Scope          │
│  └──────┬───────┘                                                │
│         ▼                                                        │
│  ┌─────────────┐                                                 │
│  │  OSDK Client │  ← Type-safe API calls + Rate limit handling   │
│  └──────┬───────┘                                                │
└─────────┼────────────────────────────────────────────────────────┘
          │ HTTPS (TLS 1.3)
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PALANTIR FOUNDRY                              │
│  ┌─────────────────────────────┐                                 │
│  │  API GATEWAY                 │                                 │
│  │  ├── Authentication (OAuth2) │                                 │
│  │  ├── Rate Limiting           │                                 │
│  │  └── Request Routing         │                                 │
│  └──────────┬──────────────────┘                                 │
│  ┌──────────▼──────────────────┐                                 │
│  │  AUTHORIZATION ENGINE        │                                 │
│  │  ├── RBAC Resolution         │                                 │
│  │  ├── Marking Enforcement     │                                 │
│  │  ├── Restricted View Filter  │                                 │
│  │  ├── Organization Scoping    │                                 │
│  │  ├── Object Security Policy  │  ← Row-level (4 operators)     │
│  │  └── Property Security Policy│  ← Column-level (8 operators)  │
│  └──────────┬──────────────────┘                                 │
│  ┌──────────▼──────────────────┐  ┌───────────────────────┐     │
│  │  ONTOLOGY SERVICE            │  │  AUDIT SERVICE         │     │
│  │  ├── Object Queries          │──│  ├── Action Logs       │     │
│  │  ├── Action Execution        │  │  ├── Access Logs       │     │
│  │  ├── Link Traversal          │  │  └── Compliance Report │     │
│  │  └── Aggregations            │  └───────────────────────┘     │
│  └──────────┬──────────────────┘                                 │
│  ┌──────────▼──────────────────┐                                 │
│  │  OBJECT STORAGE              │                                 │
│  │  ├── Encrypted at Rest       │                                 │
│  │  ├── Row-level Markings      │                                 │
│  │  └── Column Projections      │                                 │
│  └─────────────────────────────┘                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Cross-Document Reference Map

```yaml
cross_references:
  this_document: "palantir_ontology_8.md — Security & Governance (v2.0)"

  related_documents:
    palantir_ontology_1: "ObjectType definitions that security controls protect"
    palantir_ontology_2: "LinkType — link-level permissions, marking interaction"
    palantir_ontology_3: "ActionType permissions (RBAC, submission criteria)"
    palantir_ontology_5: "ObjectSet — restricted view query rewriting impact"
    palantir_ontology_6: "OSDK authentication, OAuth setup, rate limiting"
    palantir_ontology_7: "Versioning & Governance workflow, AIP security"
    palantir_ontology_9: "Decomposition Guide Phase 7 — Security Mapping methodology"

  source_document: "Security_and_Governance.md (v3.0) — all 10 sections + Appendix"
```

---

**Document Version:** 2.0
**Date:** 2026-02-08
**Source:** Security_and_Governance.md v3.0 (Sections 1-10 + Appendix, 1860 lines)
**Coverage:** Markings (property + row + CBAC hierarchy), Organizations (multi-tenancy + cross-org), RBAC (4 roles + 4 permission levels), Restricted Views (with performance), Proposals, Audit (action + schema + access), Compliance (GDPR/HIPAA/SOX), Service Mesh (mTLS + NetworkPolicy), OSDK Security (OAuth2 + service accounts + rate limiting), Granular Policies (8 operators + weight system + cell-level + pipeline integrity + anti-patterns)
