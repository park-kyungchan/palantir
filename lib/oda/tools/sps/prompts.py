"""
Orion ODA V3 - Simple Prompt System (SPS) - Prompts
====================================================
Prompt template loading and management.

Maps to IndyDevDan's idt sps functionality.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

import yaml

logger = logging.getLogger(__name__)

# Jinja2 is optional - graceful fallback
try:
    from jinja2 import Environment
    HAS_JINJA2 = True
except ImportError:
    HAS_JINJA2 = False
    logger.debug("jinja2 not installed. Template variables disabled.")


class Prompt:
    """
    Represents a reusable prompt template.
    
    Maps to IndyDevDan's SPS prompt format.
    
    Usage:
        prompt = Prompt(
            name="greeting",
            template="Hello, {{name}}!",
            variables=["name"],
        )
        rendered = prompt.render(name="World")
    """
    
    def __init__(
        self,
        name: str,
        template: str,
        variables: List[str] = None,
        description: str = "",
        model: str = "default",
        metadata: Dict[str, Any] = None,
    ):
        self.name = name
        self.template = template
        self.variables = variables or []
        self.description = description
        self.model = model
        self.metadata = metadata or {}
    
    def render(self, **kwargs) -> str:
        """
        Render the prompt with variables.
        
        Uses Jinja2 if available, otherwise basic string replacement.
        """
        if HAS_JINJA2:
            env = Environment()
            template = env.from_string(self.template)
            return template.render(**kwargs)
        else:
            # Fallback: simple replacement
            result = self.template
            for key, value in kwargs.items():
                result = result.replace("{{" + key + "}}", str(value))
            return result
    
    @classmethod
    def from_file(cls, path: Path) -> "Prompt":
        """
        Load prompt from YAML file.
        
        YAML format:
            name: greeting
            description: Say hello
            template: "Hello, {{name}}!"
            variables:
              - name
            model: default
        """
        content = path.read_text()
        data = yaml.safe_load(content)
        
        return cls(
            name=data.get("name", path.stem),
            template=data.get("template", ""),
            variables=data.get("variables", []),
            description=data.get("description", ""),
            model=data.get("model", "default"),
            metadata=data.get("metadata", {}),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "template": self.template,
            "variables": self.variables,
            "description": self.description,
            "model": self.model,
            "metadata": self.metadata,
        }
    
    def save(self, path: Path) -> None:
        """Save prompt to YAML file."""
        path.write_text(yaml.dump(self.to_dict(), default_flow_style=False))


class PromptManager:
    """
    Manages prompt templates.
    
    Maps to IndyDevDan's idt sps functionality.
    
    Usage:
        manager = PromptManager("./prompts")
        prompt = manager.get("greeting")
        manager.add(new_prompt)
    """
    
    def __init__(self, prompts_dir: str = "./prompts"):
        self.prompts_dir = Path(prompts_dir)
        self._prompts: Dict[str, Prompt] = {}
        self._load_prompts()
    
    def _load_prompts(self) -> None:
        """Load all prompts from directory."""
        if not self.prompts_dir.exists():
            self.prompts_dir.mkdir(parents=True)
            logger.info(f"Created prompts directory: {self.prompts_dir}")
            return
        
        for path in self.prompts_dir.glob("*.yaml"):
            try:
                prompt = Prompt.from_file(path)
                self._prompts[prompt.name] = prompt
                logger.debug(f"Loaded prompt: {prompt.name}")
            except Exception as e:
                logger.error(f"Failed to load prompt {path}: {e}")
        
        for path in self.prompts_dir.glob("*.yml"):
            try:
                prompt = Prompt.from_file(path)
                self._prompts[prompt.name] = prompt
                logger.debug(f"Loaded prompt: {prompt.name}")
            except Exception as e:
                logger.error(f"Failed to load prompt {path}: {e}")
        
        logger.info(f"Loaded {len(self._prompts)} prompts from {self.prompts_dir}")
    
    def get(self, name: str) -> Optional[Prompt]:
        """Get a prompt by name."""
        return self._prompts.get(name)
    
    def list(self) -> List[str]:
        """List all prompt names."""
        return list(self._prompts.keys())
    
    def all(self) -> List[Prompt]:
        """Get all prompts."""
        return list(self._prompts.values())
    
    def add(self, prompt: Prompt) -> None:
        """Add or update a prompt."""
        self._prompts[prompt.name] = prompt
        
        # Save to file
        path = self.prompts_dir / f"{prompt.name}.yaml"
        prompt.save(path)
        
        logger.info(f"Saved prompt: {prompt.name}")
    
    def delete(self, name: str) -> bool:
        """Delete a prompt."""
        if name not in self._prompts:
            return False
        
        del self._prompts[name]
        
        path = self.prompts_dir / f"{name}.yaml"
        if path.exists():
            path.unlink()
        
        logger.info(f"Deleted prompt: {name}")
        return True
    
    def search(self, query: str) -> List[Prompt]:
        """Search prompts by name or description."""
        query = query.lower()
        results = []
        
        for prompt in self._prompts.values():
            if query in prompt.name.lower() or query in prompt.description.lower():
                results.append(prompt)
        
        return results
    
    def reload(self) -> None:
        """Reload prompts from disk."""
        self._prompts.clear()
        self._load_prompts()
