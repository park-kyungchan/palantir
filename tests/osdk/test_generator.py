import pytest
import ast
from lib.oda.osdk.generator import OSDKGenerator

def test_generate_simple_query_class():
    generator = OSDKGenerator()
    ontology_def = {
        "objects": [
            {
                "name": "Task",
                "properties": [
                    {"name": "status", "type": "string"},
                    {"name": "priority", "type": "string"}
                ]
            }
        ]
    }
    
    result = generator.generate_from_ontology(ontology_def)
    
    assert "task_query.py" in result.files
    code = result.files["task_query.py"]
    
    # 1. Syntax Check
    try:
        ast.parse(code)
    except SyntaxError as e:
        pytest.fail(f"Generated code has syntax error: {e}")

    # 2. Content Check
    assert "class TaskQuery(ObjectQuery[Task]):" in code
    assert "def by_status(cls, status: str)" in code
    assert "def by_priority(cls, priority: str)" in code
    # Check logic inside method
    assert 'where("status", "eq", status)' in code

def test_generate_multiple_objects():
    generator = OSDKGenerator()
    ontology_def = {
        "objects": [
            {"name": "Task", "properties": []},
            {"name": "User", "properties": []}
        ]
    }
    result = generator.generate_from_ontology(ontology_def)
    assert len(result.files) == 2
    assert "task_query.py" in result.files
    assert "user_query.py" in result.files
