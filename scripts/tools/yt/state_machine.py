"""
Orion ODA V3 - YouTube Automation - State Machine
==================================================
Workflow state machine for YouTube metadata generation.

Maps to IndyDevDan's idt yt workflow command.
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class WorkflowState(str, Enum):
    """YouTube workflow states."""
    INIT = "init"
    DOWNLOADING = "downloading"
    TRANSCRIBING = "transcribing"
    GENERATING = "generating"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowContext:
    """Workflow execution context."""
    source: str
    output_dir: Path
    state: WorkflowState = WorkflowState.INIT
    transcript: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "output_dir": str(self.output_dir),
            "state": self.state.value,
            "transcript_length": len(self.transcript) if self.transcript else 0,
            "metadata": self.metadata,
            "error": self.error,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class YouTubeWorkflow:
    """
    State machine for YouTube metadata generation workflow.
    
    Maps to IndyDevDan's idt yt workflow.
    
    States:
        INIT -> DOWNLOADING -> TRANSCRIBING -> GENERATING -> REVIEWING -> COMPLETED
                                                                       \-> FAILED
    
    Usage:
        workflow = YouTubeWorkflow("https://youtube.com/watch?v=...")
        result = await workflow.run()
    """
    
    def __init__(
        self,
        source: str,
        output_dir: str = "./output",
    ):
        self.context = WorkflowContext(
            source=source,
            output_dir=Path(output_dir),
        )
        self.context.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def run(self) -> WorkflowContext:
        """
        Execute the full workflow.
        
        Returns:
            WorkflowContext with results
        """
        from scripts.tools.yt.transcriber import Transcriber
        from scripts.tools.yt.generator import MetadataGenerator
        
        transcriber = Transcriber()
        generator = MetadataGenerator()
        
        try:
            # Download/Prepare
            self._transition(WorkflowState.DOWNLOADING)
            logger.info(f"Processing source: {self.context.source}")
            
            # Transcribe
            self._transition(WorkflowState.TRANSCRIBING)
            self.context.transcript = await transcriber.transcribe(
                self.context.source,
                output_format="text",
            )
            logger.info(f"Transcription complete: {len(self.context.transcript)} chars")
            
            # Save transcript
            transcript_path = self.context.output_dir / "transcript.txt"
            transcript_path.write_text(self.context.transcript)
            logger.info(f"Saved transcript to: {transcript_path}")
            
            # Generate metadata
            self._transition(WorkflowState.GENERATING)
            self.context.metadata = await generator.generate(
                self.context.transcript,
            )
            logger.info("Metadata generation complete")
            
            # Save metadata
            metadata_path = self.context.output_dir / "metadata.json"
            metadata_path.write_text(json.dumps(self.context.metadata, indent=2))
            logger.info(f"Saved metadata to: {metadata_path}")
            
            # Review (in interactive mode, would pause here)
            self._transition(WorkflowState.REVIEWING)
            
            # Complete
            self._transition(WorkflowState.COMPLETED)
            self.context.completed_at = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            self.context.error = str(e)
            self._transition(WorkflowState.FAILED)
        
        # Save state
        self._save_state()
        
        return self.context
    
    def _transition(self, new_state: WorkflowState) -> None:
        """Transition to a new state."""
        old_state = self.context.state
        self.context.state = new_state
        logger.info(f"Workflow: {old_state.value} -> {new_state.value}")
    
    def _save_state(self) -> None:
        """Save workflow state to disk."""
        state_path = self.context.output_dir / "workflow_state.json"
        state_path.write_text(json.dumps(self.context.to_dict(), indent=2))
    
    @classmethod
    def resume(cls, output_dir: str) -> "YouTubeWorkflow":
        """Resume a workflow from saved state."""
        state_path = Path(output_dir) / "workflow_state.json"
        
        if not state_path.exists():
            raise ValueError(f"No saved state in {output_dir}")
        
        data = json.loads(state_path.read_text())
        
        workflow = cls(
            source=data["source"],
            output_dir=data["output_dir"],
        )
        
        workflow.context.state = WorkflowState(data["state"])
        workflow.context.error = data.get("error")
        
        # Load transcript if exists
        transcript_path = Path(output_dir) / "transcript.txt"
        if transcript_path.exists():
            workflow.context.transcript = transcript_path.read_text()
        
        # Load metadata if exists
        metadata_path = Path(output_dir) / "metadata.json"
        if metadata_path.exists():
            workflow.context.metadata = json.loads(metadata_path.read_text())
        
        return workflow
    
    def get_status(self) -> Dict[str, Any]:
        """Get current workflow status."""
        return {
            "state": self.context.state.value,
            "source": self.context.source,
            "output_dir": str(self.context.output_dir),
            "has_transcript": self.context.transcript is not None,
            "has_metadata": self.context.metadata is not None,
            "error": self.context.error,
        }
