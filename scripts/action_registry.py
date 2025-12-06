import os
import subprocess
import shlex
import urllib.request
import ast
import difflib
import uuid
from datetime import datetime
from typing import Dict, Any, Callable, List, Optional
from functools import wraps
from pydantic import ValidationError

# Import Ontology Models (Auto-generated)
from scripts.ontology import Action

class ActionRegistry:
    """Singleton registry for all executable Actions in the Orion System."""
    _instance = None
    _actions: Dict[str, Callable] = {}
    _metadata: Dict[str, Action] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ActionRegistry, cls).__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, name: str, description: str, parameters: Dict[str, Any], permissions: List[str] = None):
        """Decorator to register a function as an Ontology Action."""
        def decorator(func: Callable):
            # 1. Create Ontology Object
            action_obj = Action(
                id=f"action_{name}",
                type="Action",
                created_at=datetime.now().isoformat(),
                meta_version=1,
                name=name,
                description=description,
                parameters=parameters,
                required_permissions=permissions or []
            )
            
            # 2. Store in Registry
            cls._actions[name] = func
            cls._metadata[name] = action_obj
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Lazy import to avoid circular dependency
                from scripts.observer import Observer
                from scripts.ontology import Event
                
                # TODO: Add runtime schema validation for kwargs against parameters
                
                # 3. Governance: Audit Log (Start)
                try:
                    event_id = str(uuid.uuid4())
                    Observer.emit(Event(
                        id=event_id,
                        type="ActionStarted",
                        source="ActionRegistry",
                        content={
                            "action": name,
                            "params": {k: str(v) for k, v in kwargs.items() if k != "CodeContent"} # Truncate large content in logs
                        },
                        timestamp=datetime.now().isoformat()
                    ))
                    
                    # 4. Execute
                    result = func(*args, **kwargs)
                    
                    # 5. Governance: Audit Log (Success)
                    Observer.emit(Event(
                        id=str(uuid.uuid4()),
                        type="ActionCompleted",
                        source="ActionRegistry",
                        content={
                            "action": name,
                            "related_event_id": event_id,
                            "status": "success"
                        },
                        timestamp=datetime.now().isoformat()
                    ))
                    return result

                except Exception as e:
                    # 6. Governance: Audit Log (Failure)
                    Observer.emit(Event(
                        id=str(uuid.uuid4()),
                        type="ActionFailed",
                        source="ActionRegistry",
                        content={
                            "action": name,
                            "error": str(e)
                        },
                        timestamp=datetime.now().isoformat()
                    ))
                    raise e
                    
            return wrapper
        return decorator

    @classmethod
    def get_action(cls, name: str) -> Optional[Callable]:
        return cls._actions.get(name)

    @classmethod
    def list_actions(cls) -> List[Action]:
        return list(cls._metadata.values())

# --- Core Actions ---

WORKSPACE_ROOT = os.path.abspath("/home/palantir")

def validate_path(path: str) -> str:
    """Ensure path is within the workspace."""
    abs_path = os.path.abspath(path)
    if not abs_path.startswith(WORKSPACE_ROOT):
        raise ValueError(f"Security Violation: Access denied to {path}")
    return abs_path

@ActionRegistry.register(
    name="read_file",
    description="Read the contents of a file.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Absolute path to the file"}
        },
        "required": ["path"]
    }
)
def read_file(path: str) -> str:
    safe_path = validate_path(path)
    if not os.path.exists(safe_path):
        raise FileNotFoundError(f"File not found: {safe_path}")
    with open(safe_path, 'r') as f:
        return f.read()

@ActionRegistry.register(
    name="write_to_file",
    description="Write content to a file. Overwrites existing content.",
    parameters={
        "type": "object",
        "properties": {
            "TargetFile": {"type": "string", "description": "Absolute path to the file"},
            "CodeContent": {"type": "string", "description": "Content to write"}
        },
        "required": ["TargetFile", "CodeContent"]
    }
)
def write_to_file(TargetFile: str, CodeContent: str, **kwargs) -> str:
    safe_path = validate_path(TargetFile)
    os.makedirs(os.path.dirname(safe_path), exist_ok=True)
    with open(safe_path, 'w') as f:
        f.write(CodeContent)
    return f"Successfully wrote to {safe_path}"

@ActionRegistry.register(
    name="run_command",
    description="Execute a shell command. RESTRICTED.",
    parameters={
        "type": "object",
        "properties": {
            "CommandLine": {"type": "string", "description": "Shell command to execute"},
            "Cwd": {"type": "string", "description": "Current working directory"}
        },
        "required": ["CommandLine"]
    },
    permissions=["admin"]
)
def run_command(CommandLine: str, Cwd: str = WORKSPACE_ROOT, **kwargs) -> str:
    # Security: Whitelist or strict parsing needed here.
    # For now, we block dangerous commands.
    forbidden = ["rm -rf", "mkfs", "dd", ":(){ :|:& };:"]
    for bad in forbidden:
        if bad in CommandLine:
            raise ValueError(f"Security Violation: Forbidden command '{bad}'")
    
    # Execute
    try:
        # Validate Cwd if provided
        work_dir = WORKSPACE_ROOT
        if Cwd != WORKSPACE_ROOT:
            work_dir = validate_path(Cwd)

        result = subprocess.run(
            CommandLine, 
            shell=True, 
            check=True, 
            capture_output=True, 
            text=True,
            cwd=work_dir
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

@ActionRegistry.register(
    name="analyze_dependency",
    description="Get list of files that the target file depends on (Imports).",
    parameters={
        "type": "object",
        "properties": {
            "TargetFile": {"type": "string", "description": "Absolute path to the file"}
        },
        "required": ["TargetFile"]
    }
)
def analyze_dependency(TargetFile: str) -> List[str]:
    from scripts.static_analyzer import DependencyAnalyzer
    analyzer = DependencyAnalyzer(WORKSPACE_ROOT)
    analyzer.build_graph()
    return analyzer.get_dependencies(TargetFile)

@ActionRegistry.register(
    name="calculate_impact",
    description="Get list of files that depend on the target file (Reverse Dependency).",
    parameters={
        "type": "object",
        "properties": {
            "TargetFile": {"type": "string", "description": "Absolute path to the file"}
        },
        "required": ["TargetFile"]
    }
)
def calculate_impact(TargetFile: str) -> List[str]:
    from scripts.static_analyzer import DependencyAnalyzer
    analyzer = DependencyAnalyzer(WORKSPACE_ROOT)
    analyzer.build_graph()
    return analyzer.get_impact_set(TargetFile)

@ActionRegistry.register(
    name="read_skeleton",
    description="Read the skeleton (signatures + docstrings) of a Python file.",
    parameters={
        "type": "object",
        "properties": {
            "TargetFile": {"type": "string", "description": "Absolute path to the file"}
        },
        "required": ["TargetFile"]
    }
)
def read_skeleton(TargetFile: str) -> str:
    from scripts.context_manager import ContextManager
    cm = ContextManager(WORKSPACE_ROOT)
    return cm.generate_skeleton(TargetFile)

# --- Advanced Native Capabilities ---

@ActionRegistry.register(
    name="analyze_code_structure",
    description="Analyze the structure of a Python file (Classes/Functions) using AST.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Absolute path to the file"}
        },
        "required": ["path"]
    }
)
def analyze_code_structure(path: str) -> Dict[str, Any]:
    """
    Parses a Python file and returns a summary of its classes and functions.
    """
    safe_path = validate_path(path)
    try:
        with open(safe_path, 'r') as f:
            tree = ast.parse(f.read())
        
        structure = {"classes": [], "functions": []}
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                structure["classes"].append({"name": node.name, "methods": methods})
            elif isinstance(node, ast.FunctionDef):
                # Only list top-level functions to avoid duplication with methods
                structure["functions"].append(node.name)
                
        return structure
    except Exception as e:
        return {"error": str(e)}

@ActionRegistry.register(
    name="grep_search",
    description="Search for a pattern in files using grep.",
    parameters={
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Regex pattern to search"},
            "path": {"type": "string", "description": "Directory or file to search (default: .)"}
        },
        "required": ["pattern"]
    }
)
def grep_search(pattern: str, path: str = ".") -> str:
    """
    Executes a grep search.
    """
    # Security check: prevent command injection
    if any(c in pattern for c in [";", "&", "|", "`", "$"]):
        return "Error: Invalid characters in pattern."
    
    # Validate path if it's not default
    search_path = WORKSPACE_ROOT
    if path != ".":
        search_path = validate_path(path)

    try:
        # Using subprocess for native grep
        result = subprocess.run(
            ["grep", "-r", pattern, search_path],
            capture_output=True,
            text=True,
            cwd=WORKSPACE_ROOT
        )
        if result.returncode == 0:
            return result.stdout[:5000] # Limit output
        else:
            return "No matches found."
    except Exception as e:
        return f"Error: {e}"

@ActionRegistry.register(
    name="fetch_url",
    description="Fetch text content from a URL (Native).",
    parameters={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL to fetch"}
        },
        "required": ["url"]
    }
)
def fetch_url(url: str) -> str:
    """
    Fetches content from a URL using standard library (urllib).
    """
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            return response.read().decode('utf-8')[:5000] # Limit size
    except Exception as e:
        return f"Error fetching URL: {e}"

@ActionRegistry.register(
    name="list_processes",
    description="List running processes (Native ps).",
    parameters={
        "type": "object",
        "properties": {},
        "required": []
    }
)
def list_processes() -> str:
    """
    Lists running processes using 'ps -ef'.
    """
    try:
        result = subprocess.run(
            ["ps", "-ef"],
            capture_output=True,
            text=True
        )
        return result.stdout[:5000]
    except Exception as e:
        return f"Error: {e}"

# --- Universal Custom Tools ---

@ActionRegistry.register(
    name="apply_patch",
    description="Replace a specific text block in a file with new content.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Absolute path to the file"},
            "target": {"type": "string", "description": "Exact text to replace"},
            "replacement": {"type": "string", "description": "New text content"}
        },
        "required": ["path", "target", "replacement"]
    }
)
def apply_patch(path: str, target: str, replacement: str) -> str:
    """
    Surgically replaces a block of text in a file.
    """
    safe_path = validate_path(path)
    if not os.path.exists(safe_path):
        raise FileNotFoundError(f"File not found: {safe_path}")
        
    with open(safe_path, 'r') as f:
        content = f.read()
        
    if target not in content:
        return "Error: Target text not found in file. Patch failed."
        
    # Check for multiple occurrences
    if content.count(target) > 1:
        return "Error: Target text is ambiguous (found multiple times). Provide more context."
        
    new_content = content.replace(target, replacement)
    
    with open(safe_path, 'w') as f:
        f.write(new_content)
        
    return f"Successfully patched {safe_path}"

@ActionRegistry.register(
    name="tree_view",
    description="Show directory structure (respecting .gitignore).",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Root directory (default: workspace root)"},
            "max_depth": {"type": "integer", "description": "Max depth to traverse (default: 2)"}
        },
        "required": []
    }
)
def tree_view(path: str = ".", max_depth: int = 2) -> str:
    """
    Generates a tree-like string of the directory structure.
    """
    root_dir = WORKSPACE_ROOT if path == "." else validate_path(path)
    output = []
    
    # Simple gitignore parser (very basic)
    ignored = {'.git', '__pycache__', '.venv', 'node_modules', '.DS_Store'}
    if os.path.exists(os.path.join(WORKSPACE_ROOT, '.gitignore')):
        with open(os.path.join(WORKSPACE_ROOT, '.gitignore'), 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    ignored.add(line.replace('/', ''))

    for root, dirs, files in os.walk(root_dir):
        # Filter directories
        dirs[:] = [d for d in dirs if d not in ignored]
        
        level = root.replace(root_dir, '').count(os.sep)
        if level > max_depth:
            continue
            
        indent = ' ' * 4 * level
        output.append(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        
        # Limit files shown per dir to avoid spam
        for i, f in enumerate(files):
            if f not in ignored:
                if i < 10:
                    output.append(f"{subindent}{f}")
                elif i == 10:
                    output.append(f"{subindent}... (more files)")
                    
    return "\n".join(output)

# --- Visualization & Education Tools ---

@ActionRegistry.register(
    name="visualize_diff",
    description="Generate an HTML diff between a file and new content.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Absolute path to the file"},
            "new_content": {"type": "string", "description": "Proposed new content"}
        },
        "required": ["path", "new_content"]
    }
)
def visualize_diff(path: str, new_content: str) -> str:
    """
    Generates a side-by-side HTML diff to visualize changes.
    Returns the HTML content as a string.
    """
    safe_path = validate_path(path)
    if not os.path.exists(safe_path):
        old_content = ""
    else:
        with open(safe_path, 'r') as f:
            old_content = f.read()
            
    # Generate HTML Diff
    diff = difflib.HtmlDiff(wrapcolumn=80).make_file(
        old_content.splitlines(),
        new_content.splitlines(),
        fromdesc=f"Current: {os.path.basename(path)}",
        todesc="Proposed Change",
        context=True,
        numlines=5
    )
    return diff

@ActionRegistry.register(
    name="generate_project_map",
    description="Generate a rich, educational map of the project structure.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Root directory (default: workspace root)"}
        },
        "required": []
    }
)
def generate_project_map(path: str = ".") -> str:
    """
    Generates a Markdown map with educational descriptions of file types.
    Helps non-developers understand the 'Role' of each file.
    """
    root_dir = WORKSPACE_ROOT if path == "." else validate_path(path)
    output = ["# 🗺️ Project Structure Map", "", "| File/Folder | Type | Educational Note |", "|---|---|---|"]
    
    # Educational Heuristics
    descriptions = {
        ".py": "🐍 Python Script (Logic)",
        ".json": "⚙️ Configuration/Data (Structured)",
        ".md": "📝 Documentation (Read me)",
        ".txt": "📄 Plain Text",
        ".xml": "KX XML Data",
        "scripts": "📂 Automation Tools",
        "tests": "🧪 Quality Assurance (Tests)",
        ".agent": "🤖 AI Agent Memory",
        ".venv": "📦 Python Environment (Libraries)"
    }

    ignored = {'.git', '__pycache__', '.venv', 'node_modules', '.DS_Store', '.gemini'}
    
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in ignored]
        
        # Calculate depth to indent
        rel_path = os.path.relpath(root, root_dir)
        if rel_path == ".":
            level = 0
        else:
            level = rel_path.count(os.sep) + 1
            
        if level > 3: continue # Limit depth
        
        indent = "&nbsp;" * (level * 4)
        folder_name = os.path.basename(root)
        
        # Folder Description
        desc = descriptions.get(folder_name, "📂 Directory")
        if rel_path != ".":
            output.append(f"| {indent}**{folder_name}/** | Folder | {desc} |")
            
        # File Descriptions
        for f in files:
            if f in ignored: continue
            ext = os.path.splitext(f)[1]
            desc = descriptions.get(ext, "📄 File")
            # Special cases
            if f == "actions.py": desc = "⚡ Action Registry (My Hands)"
            if f == "ontology.py": desc = "🧠 Knowledge Schema (My Brain)"
            
            output.append(f"| {indent}{f} | File | {desc} |")
            
    return "\n".join(output)
