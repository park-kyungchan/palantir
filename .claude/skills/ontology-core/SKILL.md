# /ontology-core - Core Ontology Schema Validator

> **Version:** 1.0.0
> **Model:** opus
> **User-Invocable:** true

---

## 1. Purpose

Validates and assists with **Core Ontology Types** in Ontology-Driven-Architecture (ODA) codebases:

| Type | Description | Key Validations |
|------|-------------|-----------------|
| **ObjectType** | Entity schema definition | Primary key, properties, backing dataset |
| **LinkType** | Relationship between ObjectTypes | Cardinality, foreign key, cascade policy |
| **ActionType** | User action schema | Parameters, affected types, edit specs |
| **PropertyDefinition** | Property within ObjectType | Data type, constraints, visibility |

---

## 2. Invocation

```bash
# Validate a specific file
/ontology-core validate src/ontology/employee.py

# Validate all ontology definitions in directory
/ontology-core validate-all src/ontology/

# Generate ObjectType scaffold
/ontology-core scaffold ObjectType Employee

# Check consistency across linked types
/ontology-core check-links src/ontology/
```

---

## 3. Command Parsing

```python
args = "{user_args}"
command = args.split()[0] if args else "help"

commands = {
    "validate": "Validate single file",
    "validate-all": "Validate all files in directory",
    "scaffold": "Generate type template",
    "check-links": "Cross-validate LinkType references",
    "help": "Show usage"
}

if command == "validate":
    file_path = args.split()[1]
    # Read file, apply validation rules

elif command == "validate-all":
    directory = args.split()[1]
    # Glob *.py files, validate each

elif command == "scaffold":
    type_name = args.split()[1]  # ObjectType, LinkType, ActionType
    entity_name = args.split()[2]  # e.g., Employee
    # Generate template

elif command == "check-links":
    directory = args.split()[1]
    # Find all LinkTypes, verify source/target exist
```

---

## 4. Validation Rules

### 4.1 ObjectType Validation

| Rule ID | Name | Severity | Description |
|---------|------|----------|-------------|
| OT-001 | Primary Key Required | ERROR | Every ObjectType must have primary_key |
| OT-002 | Primary Key Property Exists | ERROR | primary_key must reference existing property |
| OT-003 | Unique Property Names | ERROR | All property api_names must be unique |
| OT-004 | Valid Status | ERROR | status must be ACTIVE/DEPRECATED/EXPERIMENTAL |
| OT-005 | Endorsed Requires Active | WARNING | endorsed=True requires status=ACTIVE |
| OT-006 | Backing Dataset RID Format | ERROR | Must match Foundry RID pattern |
| OT-007 | Property Data Type Valid | ERROR | Each property must have valid DataType |

### 4.2 LinkType Validation

| Rule ID | Name | Severity | Description |
|---------|------|----------|-------------|
| LT-001 | Source ObjectType Required | ERROR | source_object_type must exist |
| LT-002 | Target ObjectType Required | ERROR | target_object_type must exist |
| LT-003 | Cardinality Required | ERROR | Must specify cardinality |
| LT-004 | Foreign Key Implementation | ERROR | FOREIGN_KEY requires foreign_key_property |
| LT-005 | Backing Table for N:N | ERROR | MANY_TO_MANY requires BACKING_TABLE |
| LT-006 | No Endorsed Status | WARNING | LinkType doesn't support 'endorsed' |
| LT-007 | Cascade Policy Consistency | WARNING | CASCADE only with ONE_TO_MANY from parent |

### 4.3 ActionType Validation

| Rule ID | Name | Severity | Description |
|---------|------|----------|-------------|
| AT-001 | Unique Parameter Names | ERROR | All parameter api_names must be unique |
| AT-002 | Required Parameters First | WARNING | Required params before optional |
| AT-003 | Affected ObjectType Exists | ERROR | Must reference valid ObjectType |
| AT-004 | Hazardous Flag | WARNING | DELETE should mark hazardous=True |
| AT-005 | Edit Spec Property Valid | ERROR | Must reference valid properties |
| AT-006 | Implementation Required | ERROR | Must have implementation spec |
| AT-007 | No Endorsed Status | WARNING | ActionType doesn't support 'endorsed' |

### 4.4 PropertyDefinition Validation

| Rule ID | Name | Severity | Description |
|---------|------|----------|-------------|
| PD-001 | Valid Data Type | ERROR | Must be valid DataType enum |
| PD-002 | Array Item Type | ERROR | ARRAY requires item_type |
| PD-003 | Struct Reference | ERROR | STRUCT requires struct_type_ref |
| PD-004 | Required Without Default | WARNING | Required props shouldn't have defaults |
| PD-005 | Primary Key Constraints | ERROR | PK must be required=True, unique=True |

---

## 5. Execution Protocol

### 5.1 validate Command

```python
async def execute_validate(file_path):
    # 1. Read file
    content = await Read({ "file_path": file_path })

    # 2. Parse Python AST to find ontology definitions
    definitions = parse_ontology_definitions(content)

    # 3. Apply validation rules
    results = []
    for defn in definitions:
        if defn.type == "ObjectType":
            results.extend(validate_object_type(defn))
        elif defn.type == "LinkType":
            results.extend(validate_link_type(defn))
        elif defn.type == "ActionType":
            results.extend(validate_action_type(defn))

    # 4. Output results
    return format_validation_results(results)
```

### 5.2 scaffold Command

```python
async def execute_scaffold(type_name, entity_name):
    templates = {
        "ObjectType": generate_object_type_template,
        "LinkType": generate_link_type_template,
        "ActionType": generate_action_type_template,
    }

    if type_name not in templates:
        return f"Unknown type: {type_name}. Use: ObjectType, LinkType, ActionType"

    template = templates[type_name](entity_name)

    # Show template with TODO(human) for customization
    return template
```

### 5.3 check-links Command

```python
async def execute_check_links(directory):
    # 1. Find all Python files
    files = await Glob({ "pattern": f"{directory}/**/*.py" })

    # 2. Extract all ObjectType and LinkType definitions
    object_types = {}
    link_types = []

    for file in files:
        content = await Read({ "file_path": file })
        object_types.update(extract_object_types(content))
        link_types.extend(extract_link_types(content))

    # 3. Validate each LinkType's references
    results = []
    for link in link_types:
        if link.source not in object_types:
            results.append(f"❌ {link.name}: Source '{link.source}' not found")
        if link.target not in object_types:
            results.append(f"❌ {link.name}: Target '{link.target}' not found")
        # ... more checks

    return results
```

---

## 6. Output Format

### L1 - Summary (Default)

```
✅ Validation Complete: 3 files, 21 rules passed, 1 warning, 0 errors
```

### L2 - Per-File Results

```
Validating: src/ontology/

src/ontology/employee.py
  ObjectType: Employee ✅ (7 passed, 1 warning)
    ⚠️ OT-005: Endorsed Requires Active

src/ontology/department.py
  ObjectType: Department ✅ (7 passed)

src/ontology/links.py
  LinkType: EmployeeToDepartment ✅ (7 passed)
  LinkType: ProjectToEmployee ❌ (5 passed, 2 errors)
    ❌ LT-001: Source ObjectType 'Project' not found

Summary: 26 passed, 1 warning, 2 errors
```

### L3 - Detailed with Fix Suggestions

```
❌ LT-001: Source ObjectType Required
   File: src/ontology/links.py:45
   LinkType: ProjectToEmployee
   Issue: source_object_type references 'Project' which doesn't exist

   Fix: Create Project ObjectType first, or change source to existing type

   Available ObjectTypes:
   - Employee (src/ontology/employee.py)
   - Department (src/ontology/department.py)
```

---

## 7. Scaffold Templates

### ObjectType Template

```python
from ontology_definition.types import (
    ObjectType,
    PropertyDefinition,
    DataTypeSpec,
    PrimaryKeyDefinition,
    PropertyConstraints,
)
from ontology_definition.core.enums import DataType, ObjectStatus

{entity_name_lower}_type = ObjectType(
    api_name="{EntityName}",
    display_name="{Entity Name}",
    description="TODO: Add description",
    primary_key=PrimaryKeyDefinition(property_api_name="{entityName}Id"),
    properties=[
        PropertyDefinition(
            api_name="{entityName}Id",
            display_name="{Entity Name} ID",
            data_type=DataTypeSpec(type=DataType.STRING),
            constraints=PropertyConstraints(required=True, unique=True),
        ),
        # TODO(human): Add more properties
    ],
    status=ObjectStatus.ACTIVE,
)
```

### LinkType Template

```python
from ontology_definition.types import (
    LinkType,
    ObjectTypeReference,
    CardinalityConfig,
    LinkImplementation,
    ForeignKeyConfig,
)
from ontology_definition.core.enums import Cardinality, LinkImplementationType, ForeignKeyLocation

{source_lower}_to_{target_lower} = LinkType(
    api_name="{Source}To{Target}",
    display_name="{Source} to {Target}",
    source_object_type=ObjectTypeReference(api_name="{Source}"),
    target_object_type=ObjectTypeReference(api_name="{Target}"),
    cardinality=CardinalityConfig(type=Cardinality.MANY_TO_ONE),
    implementation=LinkImplementation(
        type=LinkImplementationType.FOREIGN_KEY,
        foreign_key=ForeignKeyConfig(
            foreign_key_property="{target}Id",
            foreign_key_location=ForeignKeyLocation.SOURCE,
        ),
    ),
)
```

---

## 8. Integration

### Package Reference

```python
# Import from ontology-definition package
from ontology_definition.types import (
    ObjectType, LinkType, ActionType, PropertyDefinition,
)
from ontology_definition.core.enums import (
    DataType, ObjectStatus, Cardinality, LinkImplementationType,
)
```

### Package Location

```
/home/palantir/park-kyungchan/palantir/Ontology-Definition/
```

---

## 9. Tools Allowed

| Tool | Purpose |
|------|---------|
| `Read` | Read ontology definition files |
| `Glob` | Find ontology files in directory |
| `Grep` | Search for patterns |
| `Write` | Generate scaffold files |

---

## 10. Future Skills (Roadmap)

| Skill | Scope | Status |
|-------|-------|--------|
| `/ontology-core` | ObjectType, LinkType, ActionType, PropertyDefinition | ✅ Current |
| `/ontology-extended` | Interface, ValueType, StructType, SharedProperty, Function, Automation, Rules, Writeback | Planned |
| `/ontology-migration` | Code analysis → ODA migration planning | Planned |

---

**End of Skill Definition**
