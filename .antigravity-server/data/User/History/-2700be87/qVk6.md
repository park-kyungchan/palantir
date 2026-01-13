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
