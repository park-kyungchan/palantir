# OWPML Header Management Logic

The `HeaderManager` class handles the complex task of managing shared resources (styles, borders, fonts) in the HWPX `header.xml` file.

## Core Logic: `itemCnt` and Unique IDs

OWPML uses a strict ID-based reference system. Every item in a reference list (e.g., `hh:borderFills`) must have a unique numeric ID and the parent list must maintain an accurate `itemCnt`.

### 1. ID Scavenging
Upon instantiation, the manager scans the injected `header.xml` element to find the current maximum ID for each resource type.

```python
def _init_max_id(self, parent_tag: str, child_tag: str) -> int:
    parent = self.header.find(f'.//hh:{parent_tag}', self.ns)
    if parent is None: return 0
    max_id = 0
    for child in parent.findall(f'hh:{child_tag}', self.ns):
        cid = int(child.get('id', '0'))
        if cid > max_id: max_id = cid
    return max_id
```

### 2. BorderFill Registration
The `get_or_create_border_fill` method ensures that new border styles (lines, colors) are registered and assigned an ID that the body (`section0.xml`) can reference.

#### OWPML Construction Example (Solid Border):
```python
bf = ET.SubElement(container, _hh('borderFill'), {'id': new_id, ...})
sides = ['leftBorder', 'rightBorder', 'topBorder', 'bottomBorder']
for side in sides:
    ET.SubElement(bf, _hh(side), {
        'type': 'SOLID',
        'width': '0.12mm',
        'color': '#000000'
    })
```

## Special Cases: ID 1
Audit of `Skeleton.hwpx` showed that **ID 1** is a default `NONE` border. 
- **Pattern**: If `border_type == "NONE"`, the manager should return `1` immediately rather than creating a new ID.

## Impact on DocumentBuilder
The `HwpxDocumentBuilder` integrates `HeaderManager` during its `_init_document` phase. This allows all subsequently created objects (Tables, TextBoxes) to request styling IDs dynamically.

- **Previous**: Hardcoded `borderFillIDRef='1'`.
- **New**: `borderFillIDRef=self.header_manager.get_or_create_border_fill('SOLID')`.

## 4. Persistence (The `_save` Hook)

Because OWPML requires all styles to be registered in `Contents/header.xml`, any dynamic additions made by `HeaderManager` must be written back to the package during the final serialization.

```python
def _save(self, output_path: str):
    # Write back modified section
    self.pkg.set_xml(self._section_path, self.section_elem)
    
    # Write back modified header (crucial for persistence)
    self.pkg.set_xml('Contents/header.xml', self.header_manager.header)
    
    # Save package
    self.pkg.save(output_path)
```

## 5. Optimization: Resource Reuse

To prevent header bloat (creating thousands of identical styling elements), the integration pattern follows a **Generate-Once-per-Object** reuse strategy.

### Implementation Pattern (Table Borders):
In `_create_table`, a single border ID is requested from the `HeaderManager` at the beginning of the table construction and reused for all constituent cells (`hp:tc`).

```python
# Generate border ID once for the table
table_border_id = self.header_manager.get_or_create_border_fill('SOLID')

# Reuse for all cells
tc = ET.SubElement(tr, _hp('tc'), {'borderFillIDRef': table_border_id})
```

This ensures that a document with a 10x10 table only adds **one** new `borderFill` entry to `header.xml` instead of 100, maintaining document performance and spec compliance.

Without this write-back step, the generated document would contain "broken" ID references that do not exist in the header, leading to document corruption or loss of styling upon opening in Hancom Office.
