# Batch Processing and Deserialization

To facilitate high-volume document reconstruction without manual coding for each file, the pipeline supports a batch processing track initiated from serialized Action JSON.

## 1. Action Serialization Format

The `output_actions.json` file represents a serial sequence of atomic HWP actions. Each action is an object with an `action_type` field and associated parameters.

```json
[
  {
    "action_type": "SetParaShape",
    "left_margin": 20,
    "indent": -20,
    "line_spacing": 160
  },
  {
    "action_type": "InsertText",
    "text": "Hello World"
  }
]
```

## 2. Deserialization Logic

The `scripts/json_to_hwpx.py` script utilizes Pydantic to bridge raw JSON and the HWP Ontology.

### 2.1 Pydantic Mapping
Since `HwpAction` (in `lib/models.py`) is used as a base class, a registry or manual mapping is used during deserialization to instantiate the correct subclass based on `action_type`:

```python
action_map = {
    "InsertText": InsertText,
    "SetParaShape": SetParaShape,
    "CreateTable": CreateTable,
    "InsertEquation": InsertEquation,
    # ...
}

def deserialize_actions(json_data):
    actions = []
    for item in json_data:
        atype = item.get("action_type")
        if atype in action_map:
            actions.append(action_map[atype](**item))
    return actions
```

### 2.2 Advantages
- **Validation**: Pydantic automatically validates types and constraints (e.g., ensuring `left_margin` is numeric).
- **Separation of Concerns**: Decouples the "Derendering" (Vision/OCR -> JSON) from the "Reconstruction" (JSON -> HWPX/Script).

## 3. Usage

The standalone script `json_to_hwpx.py` allows for rapid generation on Linux:

```bash
python scripts/json_to_hwpx.py input.json output.hwpx
```

This bypasses the need for a persistent Windows VM for documents that can be fully represented by the Native OWPML generator.
