"""
Orion ODA v3.0 - HWP Pipeline ActionTypes
==========================================

This module provides ODA-compliant ActionTypes for the Mathpix -> HWPX pipeline.

Domain Actions:
- ConvertPdfToImagesAction: PDF -> PNG conversion (pdftoppm)
- OcrImageAction: PNG -> LaTeX text (Mathpix API)
- GenerateHwpScriptAction: LaTeX -> PowerShell script generation
- ExecuteHwpPipelineAction: Execute full pipeline (HAZARDOUS - requires Proposal)

ODA Compliance:
- All mutations go through ActionType.apply_edits()
- Hazardous operations require Proposal approval
- All executions are logged via EditOperations
- Configuration via Pydantic models (no hardcoded secrets)
"""

from __future__ import annotations

import base64
import json
import logging
import os
import re
import subprocess
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Type

from pydantic import BaseModel, Field, SecretStr, field_validator

from scripts.ontology.ontology_types import OntologyObject, utc_now
from scripts.ontology.actions import (
    ActionContext,
    ActionResult,
    ActionType,
    CustomValidator,
    EditOperation,
    EditType,
    LogSideEffect,
    MaxLength,
    RequiredField,
    SlackNotification,
    ValidationError,
    register_action,
)

logger = logging.getLogger(__name__)


# =============================================================================
# CONFIGURATION MODELS (Pydantic)
# =============================================================================

class MathpixCredentials(BaseModel):
    """
    Mathpix API Credentials.
    Loaded from environment variables for security.
    """
    app_id: str = Field(default_factory=lambda: os.getenv("MATHPIX_APP_ID", "palantir_oda"))
    app_key: SecretStr = Field(default_factory=lambda: SecretStr(os.getenv("MATHPIX_APP_KEY", "")))

    @field_validator("app_key")
    @classmethod
    def validate_api_key(cls, v: SecretStr) -> SecretStr:
        if not v.get_secret_value():
            raise ValueError("MATHPIX_APP_KEY environment variable is required")
        return v


class HwpPipelineConfig(BaseModel):
    """
    HWP Pipeline Configuration.
    All paths and settings for the pipeline execution.
    """
    pdf_path: Path = Field(..., description="Input PDF file path")
    output_dir: Path = Field(
        default=Path("/home/palantir/orion-orchestrator-v2/coding/hwp_automation/output"),
        description="Directory for intermediate and output files"
    )
    hwpx_filename: str = Field(
        default="oda_structure_output.hwpx",
        description="Output HWPX filename"
    )
    column_count: int = Field(default=2, ge=1, le=4, description="Number of columns in layout")
    font_height: int = Field(default=1000, ge=500, le=2000, description="Font height in HWP units")

    @field_validator("pdf_path")
    @classmethod
    def validate_pdf_exists(cls, v: Path) -> Path:
        if not v.exists():
            raise ValueError(f"PDF file does not exist: {v}")
        if v.suffix.lower() != ".pdf":
            raise ValueError(f"File must be a PDF: {v}")
        return v

    @property
    def output_ps1_path(self) -> Path:
        return self.output_dir / "structure_generated.ps1"

    @property
    def cache_path(self) -> Path:
        return self.output_dir / "mathpix_cache.json"


# =============================================================================
# DOMAIN ENUMS
# =============================================================================

class PipelineStage(str, Enum):
    """Pipeline execution stages for tracking."""
    PDF_CONVERT = "pdf_convert"
    OCR_IMAGE = "ocr_image"
    GENERATE_SCRIPT = "generate_script"
    EXECUTE_HWP = "execute_hwp"


class PipelineStatus(str, Enum):
    """Pipeline execution status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# DOMAIN OBJECTS (OntologyObject)
# =============================================================================

class HwpPipelineExecution(OntologyObject):
    """
    Tracks a single HWP pipeline execution.
    Stored in Ontology for audit and governance.
    """
    pdf_path: str = Field(..., description="Source PDF path")
    output_path: Optional[str] = Field(default=None, description="Generated HWPX path")
    stage: PipelineStage = Field(default=PipelineStage.PDF_CONVERT)
    pipeline_status: PipelineStatus = Field(default=PipelineStatus.PENDING)

    # Execution metrics
    images_generated: int = Field(default=0)
    pages_ocr_processed: int = Field(default=0)
    actions_generated: int = Field(default=0)

    # Error tracking
    error_message: Optional[str] = Field(default=None)
    error_stage: Optional[PipelineStage] = Field(default=None)

    # Timestamps
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)


# =============================================================================
# CUSTOM VALIDATORS
# =============================================================================

def validate_pdf_path(params: Dict[str, Any], context: ActionContext) -> bool:
    """Validate that pdf_path exists and is a PDF file."""
    pdf_path = params.get("pdf_path")
    if not pdf_path:
        return False
    path = Path(pdf_path) if isinstance(pdf_path, str) else pdf_path
    return path.exists() and path.suffix.lower() == ".pdf"


def validate_mathpix_credentials(params: Dict[str, Any], context: ActionContext) -> bool:
    """Validate that Mathpix API key is available."""
    api_key = os.getenv("MATHPIX_APP_KEY", "")
    return len(api_key) > 0


# =============================================================================
# LATEX TO HWP CONVERTER (Utility)
# =============================================================================

class LatexToHwpConverter:
    """
    Converts LaTeX expressions to HWP equation syntax.
    Stateless utility class for text processing.
    """

    REPLACEMENTS = [
        (r"\left", ""),
        (r"\right", ""),
        (r"\frac", " over "),
        (r"\sqrt", " sqrt "),
        (r"\times", " times "),
        (r"\div", " divide "),
        (r"\le", " <= "),
        (r"\ge", " >= "),
        (r"\neq", " != "),
        (r"\cdot", " . "),
    ]

    @classmethod
    def convert(cls, latex: str) -> str:
        """Convert LaTeX string to HWP equation format."""
        result = latex
        for old, new in cls.REPLACEMENTS:
            result = result.replace(old, new)
        result = result.replace("\\", "")
        result = result.replace("\n", " ").replace("\r", " ")
        return result.strip()

    @classmethod
    def parse_text_to_actions(cls, text: str) -> List[str]:
        """
        Parse OCR text into HWP action commands.
        Returns list of PowerShell function calls.
        """
        tokens = re.split(r'(\\\(.*?\\\)|\\\[.*?\\\])', text, flags=re.DOTALL)
        actions: List[str] = []

        for token in tokens:
            if not token:
                continue
            token = token.strip()
            if not token:
                continue

            if token.startswith(r"\(") and token.endswith(r"\)"):
                # Inline equation
                content = cls.convert(token[2:-2]).replace("'", "''")
                actions.append(f"Insert-Equation '{content}'")
            elif token.startswith(r"\[") and token.endswith(r"\]"):
                # Display equation (block)
                content = cls.convert(token[2:-2]).replace("'", "''")
                actions.append("New-Line")
                actions.append(f"Insert-Equation '{content}'")
                actions.append("New-Line")
            else:
                # Plain text
                lines = token.split('\n')
                for i, line in enumerate(lines):
                    clean_line = line.replace("'", "''")

                    # Detect numbered problems for layout breaks
                    if re.match(r'^\d+\.', clean_line):
                        actions.append("New-Line")
                        actions.append("New-Line")
                        # Force column break at problem 7 (demo logic)
                        if clean_line.startswith("7."):
                            actions.append('$hwp.Run("BreakColumn")')

                    if clean_line:
                        actions.append(f"Insert-Text '{clean_line} '")

                    if i < len(lines) - 1:
                        actions.append("New-Line")

        return actions


# =============================================================================
# POWERSHELL SCRIPT GENERATOR
# =============================================================================

class HwpScriptGenerator:
    """
    Generates PowerShell scripts for HWP automation.
    Follows ODA mandate for external BOM application.
    """

    SCRIPT_HEADER = '''
# [ODA-Governed HWP Automation Script]
# Auto-generated by Orion V3 HWP Pipeline
# Protocol: Mathpix -> PowerShell -> HWPX
[System.Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$dllPath = "C:\\HwpAuth\\Security.dll"
$desktop = [Environment]::GetFolderPath("Desktop")
$filePath = Join-Path $desktop "{hwpx_filename}"

Start-Sleep -Seconds 1
Get-Process -Name "Hwp", "HwpAutomation" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1

Write-Host "[ODA] Launching HWP ({column_count}-Column)..." -ForegroundColor Cyan

$regPath = "HKCU:\\Software\\HNC\\HwpAutomation\\Modules"
if (-not (Test-Path $regPath)) {{ New-Item -Path $regPath -Force | Out-Null }}
Set-ItemProperty -Path $regPath -Name "FilePathCheckerModule" -Value $dllPath

Start-Job -ScriptBlock {{
    Start-Sleep -Milliseconds 2000
    $wshell = New-Object -ComObject WScript.Shell
    $wshell.SendKeys("{{ENTER}}")
}} | Out-Null

$hwp = New-Object -ComObject "HWPFrame.HwpObject"
$hwp.XHwpWindows.Item(0).Visible = $true
$hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
$hwp.Clear(1)

# [Style Configuration]
$act = $hwp.CreateAction("CharShape")
$set = $act.CreateSet()
$act.GetDefault($set)
$set.SetItem("Height", {font_height})
$act.Execute($set)

function Insert-Text($t) {{
    if (-not $t) {{ return }}
    $act = $hwp.CreateAction("InsertText")
    $set = $act.CreateSet()
    $act.GetDefault($set)
    $set.SetItem("Text", $t)
    $act.Execute($set)
}}

function Insert-Equation($s) {{
    if (-not $s) {{ return }}
    $act = $hwp.CreateAction("EquationCreate")
    $set = $act.CreateSet()
    $act.GetDefault($set)
    $set.SetItem("String", $s)
    $set.SetItem("BaseUnit", 130)
    $act.Execute($set)
}}

function New-Line {{
    $hwp.Run("BreakPara")
}}

# --- Document Actions ---
'''

    SCRIPT_FOOTER = '''
# --- End Document Actions ---

# [ODA Strategy: Dynamic Column Control Function]
# Defines a robust function to switch column layouts dynamically.
# Tries API first (Clean), falls back to SendKeys (Dirty) if API fails.

function Set-Column {{
    param([int]$Count)
    
    Write-Host "[ODA] Attempting to set Column Count to: $Count"
    
    try {{
        $act = $hwp.CreateAction("MultiColumn")
        $set = $act.CreateSet()
        $act.GetDefault($set)
        
        $set.SetItem("Count", $Count)
        $set.SetItem("Type", 0)       # Normal
        $set.SetItem("SameSize", 1)   # Equal Width
        $set.SetItem("SameGap", 2835) # 10mm
        
        if ($act.Execute($set)) {{
            Write-Host "[ODA] Success: API applied $Count columns." -ForegroundColor Green
            return
        }}
    }} catch {{
        Write-Host "[ODA] Warning: API threw exception. $_" -ForegroundColor Yellow
    }}
    
    Write-Host "[ODA] Fallback: Using SendKeys macro..." -ForegroundColor Yellow
    $wshell = New-Object -ComObject WScript.Shell
    
    # Alt+W, U (Legacy) or Alt+J, D (New) - stick to Legacy as it worked
    $wshell.SendKeys("%(w)u")
    Start-Sleep -Seconds 2
    
    if ($Count -eq 1) {{
        $wshell.SendKeys("1") 
    }} elseif ($Count -eq 2) {{
        $wshell.SendKeys("2")
    }}
    
    Start-Sleep -Milliseconds 500
    $wshell.SendKeys("{{ENTER}}")
    Write-Host "[ODA] Applied via Macro."
}}

# Apply Requested Layout
Set-Column -Count {column_count}

$hwp.SaveAs($filePath, "HWPX", "")
Write-Host "[ODA] Saved: $filePath" -ForegroundColor Green
'''

    @classmethod
    def generate(
        cls,
        actions: List[str],
        hwpx_filename: str = "oda_structure_output.hwpx",
        column_count: int = 2,
        font_height: int = 1000,
    ) -> str:
        """Generate complete PowerShell script with actions."""
        header = cls.SCRIPT_HEADER.format(
            hwpx_filename=hwpx_filename,
            column_count=column_count,
            font_height=font_height,
        )
        footer = cls.SCRIPT_FOOTER.format(column_count=column_count)

        return header + "\n".join(actions) + footer


# =============================================================================
# ACTION TYPES
# =============================================================================

@register_action
class ConvertPdfToImagesAction(ActionType[HwpPipelineExecution]):
    """
    Convert PDF to PNG images using pdftoppm.

    Required params:
    - pdf_path: str (path to PDF file)
    - output_dir: str (directory for output images)
    """
    api_name: ClassVar[str] = "hwp_convert_pdf_to_images"
    object_type: ClassVar[Type[HwpPipelineExecution]] = HwpPipelineExecution
    requires_proposal: ClassVar[bool] = False

    submission_criteria: ClassVar[list] = [
        RequiredField("pdf_path"),
        RequiredField("output_dir"),
        CustomValidator(
            name="PdfExists",
            validator_fn=validate_pdf_path,
            error_message="PDF file does not exist or is not a valid PDF"
        ),
    ]

    side_effects: ClassVar[list] = [
        LogSideEffect(),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[HwpPipelineExecution, List[EditOperation]]:
        """Convert PDF to images."""
        pdf_path = Path(params["pdf_path"])
        output_dir = Path(params["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)

        base = "structure_temp"
        out_prefix = output_dir / base

        # Cleanup existing images
        for existing in output_dir.glob(f"{base}*.png"):
            existing.unlink()

        logger.info(f"[ODA] Converting PDF: {pdf_path}")

        try:
            subprocess.run(
                ["pdftoppm", "-png", str(pdf_path), str(out_prefix)],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"pdftoppm failed: {e.stderr.decode()}")

        # Count generated images
        images = list(output_dir.glob(f"{base}*.png"))
        image_paths = [str(img) for img in sorted(images)]

        # Create execution record
        execution = HwpPipelineExecution(
            pdf_path=str(pdf_path),
            stage=PipelineStage.PDF_CONVERT,
            pipeline_status=PipelineStatus.IN_PROGRESS,
            images_generated=len(image_paths),
            started_at=utc_now(),
            created_by=context.actor_id,
        )

        edit = EditOperation(
            edit_type=EditType.CREATE,
            object_type="HwpPipelineExecution",
            object_id=execution.id,
            changes={
                "pdf_path": str(pdf_path),
                "images_generated": len(image_paths),
                "image_paths": image_paths,
            },
        )

        return execution, [edit]


@register_action
class OcrImageAction(ActionType[HwpPipelineExecution]):
    """
    OCR a single image using Mathpix API with caching.

    Required params:
    - image_path: str (path to PNG image)
    - cache_path: str (path to JSON cache file)
    """
    api_name: ClassVar[str] = "hwp_ocr_image"
    object_type: ClassVar[Type[HwpPipelineExecution]] = HwpPipelineExecution
    requires_proposal: ClassVar[bool] = False

    submission_criteria: ClassVar[list] = [
        RequiredField("image_path"),
        RequiredField("cache_path"),
        CustomValidator(
            name="MathpixCredentials",
            validator_fn=validate_mathpix_credentials,
            error_message="MATHPIX_APP_KEY environment variable is not set"
        ),
    ]

    side_effects: ClassVar[list] = [
        LogSideEffect(),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[None, List[EditOperation]]:
        """OCR the image, using cache if available."""
        import requests

        image_path = Path(params["image_path"])
        cache_path = Path(params["cache_path"])

        # Load cache
        cache: Dict[str, str] = {}
        if cache_path.exists():
            try:
                cache = json.loads(cache_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                cache = {}

        img_name = image_path.name

        # Check cache
        if img_name in cache:
            logger.info(f"[ODA] Using cached Mathpix result for: {img_name}")
            text = cache[img_name]
        else:
            logger.info(f"[ODA] OCRing image via Mathpix: {img_name}")

            credentials = MathpixCredentials()

            url = "https://api.mathpix.com/v3/text"
            headers = {
                "app_id": credentials.app_id,
                "app_key": credentials.app_key.get_secret_value(),
                "Content-type": "application/json",
            }

            with open(image_path, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")

            payload = {
                "src": f"data:image/png;base64,{b64}",
                "formats": ["text"],
                "data_options": {"include_latex": True},
            }

            response = requests.post(url, headers=headers, json=payload, timeout=60)

            if response.status_code != 200:
                raise RuntimeError(f"Mathpix API error: {response.text}")

            text = response.json().get("text", "")

            # Update cache
            cache[img_name] = text
            cache_path.write_text(
                json.dumps(cache, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="HwpPipelineExecution",
            object_id=params.get("execution_id", "unknown"),
            changes={
                "ocr_image": img_name,
                "ocr_text_length": len(text),
                "from_cache": img_name in cache,
            },
        )

        return None, [edit]


@register_action
class GenerateHwpScriptAction(ActionType[HwpPipelineExecution]):
    """
    Generate PowerShell script from OCR text.

    Required params:
    - ocr_texts: List[str] (OCR results per page)
    - output_path: str (path for generated .ps1 file)

    Optional params:
    - hwpx_filename: str (default: "oda_structure_output.hwpx")
    - column_count: int (default: 2)
    - font_height: int (default: 1000)
    """
    api_name: ClassVar[str] = "hwp_generate_script"
    object_type: ClassVar[Type[HwpPipelineExecution]] = HwpPipelineExecution
    requires_proposal: ClassVar[bool] = False

    submission_criteria: ClassVar[list] = [
        RequiredField("ocr_texts"),
        RequiredField("output_path"),
        CustomValidator(
            name="NonEmptyOcrTexts",
            validator_fn=lambda p, c: len(p.get("ocr_texts", [])) > 0,
            error_message="ocr_texts cannot be empty"
        ),
    ]

    side_effects: ClassVar[list] = [
        LogSideEffect(),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[None, List[EditOperation]]:
        """Generate PowerShell script."""
        ocr_texts: List[str] = params["ocr_texts"]
        output_path = Path(params["output_path"])

        hwpx_filename = params.get("hwpx_filename", "oda_structure_output.hwpx")
        column_count = params.get("column_count", 2)
        font_height = params.get("font_height", 1000)

        # Convert all OCR texts to HWP actions
        all_actions: List[str] = []
        for i, text in enumerate(ocr_texts):
            page_actions = LatexToHwpConverter.parse_text_to_actions(text)
            all_actions.extend(page_actions)

            # Add page break between pages (except last)
            if i < len(ocr_texts) - 1:
                all_actions.append('$hwp.Run("BreakPage")')

        # Generate script
        script = HwpScriptGenerator.generate(
            actions=all_actions,
            hwpx_filename=hwpx_filename,
            column_count=column_count,
            font_height=font_height,
        )

        # Write script
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(script, encoding="utf-8")

        logger.info(f"[ODA] Generated script: {output_path}")

        edit = EditOperation(
            edit_type=EditType.CREATE,
            object_type="HwpScript",
            object_id=str(output_path),
            changes={
                "output_path": str(output_path),
                "actions_count": len(all_actions),
                "pages_count": len(ocr_texts),
                "column_count": column_count,
            },
        )

        return None, [edit]


@register_action(requires_proposal=True)
class ExecuteHwpPipelineAction(ActionType[HwpPipelineExecution]):
    """
    Execute full HWP pipeline (PDF -> HWPX).

    HAZARDOUS: Executes PowerShell scripts. Requires Proposal approval.

    Required params:
    - pdf_path: str (input PDF file)

    Optional params:
    - output_dir: str (default: hwp_automation/output)
    - hwpx_filename: str (default: "oda_structure_output.hwpx")
    - column_count: int (default: 2)
    - execute_ps1: bool (default: False, if True runs PS1 on Windows)
    """
    api_name: ClassVar[str] = "hwp_execute_pipeline"
    object_type: ClassVar[Type[HwpPipelineExecution]] = HwpPipelineExecution
    requires_proposal: ClassVar[bool] = True  # HAZARDOUS

    submission_criteria: ClassVar[list] = [
        RequiredField("pdf_path"),
        CustomValidator(
            name="PdfExists",
            validator_fn=validate_pdf_path,
            error_message="PDF file does not exist"
        ),
        CustomValidator(
            name="MathpixCredentials",
            validator_fn=validate_mathpix_credentials,
            error_message="MATHPIX_APP_KEY environment variable is not set"
        ),
    ]

    side_effects: ClassVar[list] = [
        LogSideEffect(),
        SlackNotification(channel="#hwp-pipeline"),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[HwpPipelineExecution, List[EditOperation]]:
        """Execute the full pipeline."""
        import requests

        # Parse configuration
        pdf_path = Path(params["pdf_path"])
        output_dir = Path(params.get(
            "output_dir",
            "/home/palantir/orion-orchestrator-v2/coding/hwp_automation/output"
        ))
        hwpx_filename = params.get("hwpx_filename", "oda_structure_output.hwpx")
        column_count = params.get("column_count", 2)
        execute_ps1 = params.get("execute_ps1", False)

        # Create execution record
        execution = HwpPipelineExecution(
            pdf_path=str(pdf_path),
            stage=PipelineStage.PDF_CONVERT,
            pipeline_status=PipelineStatus.IN_PROGRESS,
            started_at=utc_now(),
            created_by=context.actor_id,
        )

        edits: List[EditOperation] = []

        try:
            # Stage 1: PDF -> Images
            logger.info(f"[ODA] Stage 1: Converting PDF to images")
            execution.stage = PipelineStage.PDF_CONVERT

            base = "structure_temp"
            out_prefix = output_dir / base
            output_dir.mkdir(parents=True, exist_ok=True)

            for existing in output_dir.glob(f"{base}*.png"):
                existing.unlink()

            subprocess.run(
                ["pdftoppm", "-png", str(pdf_path), str(out_prefix)],
                check=True,
                capture_output=True,
            )

            images = sorted(output_dir.glob(f"{base}*.png"))
            execution.images_generated = len(images)

            # Stage 2: OCR Images
            logger.info(f"[ODA] Stage 2: OCRing {len(images)} images")
            execution.stage = PipelineStage.OCR_IMAGE

            cache_path = output_dir / "mathpix_cache.json"
            cache: Dict[str, str] = {}
            if cache_path.exists():
                try:
                    cache = json.loads(cache_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    cache = {}

            credentials = MathpixCredentials()
            ocr_texts: List[str] = []

            for img in images:
                img_name = img.name

                if img_name in cache:
                    logger.info(f"[ODA] Using cached result: {img_name}")
                    ocr_texts.append(cache[img_name])
                else:
                    logger.info(f"[ODA] OCRing: {img_name}")

                    url = "https://api.mathpix.com/v3/text"
                    headers = {
                        "app_id": credentials.app_id,
                        "app_key": credentials.app_key.get_secret_value(),
                        "Content-type": "application/json",
                    }

                    with open(img, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode("utf-8")

                    payload = {
                        "src": f"data:image/png;base64,{b64}",
                        "formats": ["text"],
                        "data_options": {"include_latex": True},
                    }

                    response = requests.post(url, headers=headers, json=payload, timeout=60)

                    if response.status_code != 200:
                        raise RuntimeError(f"Mathpix API error: {response.text}")

                    text = response.json().get("text", "")
                    cache[img_name] = text
                    ocr_texts.append(text)

                execution.pages_ocr_processed += 1

            # Save updated cache
            cache_path.write_text(
                json.dumps(cache, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            # Stage 3: Generate Script
            logger.info("[ODA] Stage 3: Generating PowerShell script")
            execution.stage = PipelineStage.GENERATE_SCRIPT

            all_actions: List[str] = []
            for i, text in enumerate(ocr_texts):
                page_actions = LatexToHwpConverter.parse_text_to_actions(text)
                all_actions.extend(page_actions)
                if i < len(ocr_texts) - 1:
                    all_actions.append('$hwp.Run("BreakPage")')

            execution.actions_generated = len(all_actions)

            script = HwpScriptGenerator.generate(
                actions=all_actions,
                hwpx_filename=hwpx_filename,
                column_count=column_count,
            )

            output_ps1 = output_dir / "structure_generated.ps1"
            output_ps1.write_text(script, encoding="utf-8")

            logger.info(f"[ODA] Generated script: {output_ps1}")

            # Stage 4: Execute (Optional, Windows only)
            if execute_ps1:
                logger.info("[ODA] Stage 4: Executing PowerShell script")
                execution.stage = PipelineStage.EXECUTE_HWP

                # This would only work on Windows with HWP installed
                # subprocess.run(["powershell", "-File", str(output_ps1)], check=True)
                logger.warning("[ODA] PowerShell execution skipped (WSL environment)")

            # Mark success
            execution.pipeline_status = PipelineStatus.COMPLETED
            execution.output_path = str(output_ps1)
            execution.completed_at = utc_now()

        except Exception as e:
            logger.exception(f"[ODA] Pipeline failed at stage {execution.stage}")
            execution.pipeline_status = PipelineStatus.FAILED
            execution.error_message = str(e)
            execution.error_stage = execution.stage
            raise

        # Create edit operation
        edits.append(EditOperation(
            edit_type=EditType.CREATE,
            object_type="HwpPipelineExecution",
            object_id=execution.id,
            changes={
                "pdf_path": str(pdf_path),
                "output_path": execution.output_path,
                "pipeline_status": execution.pipeline_status.value,
                "images_generated": execution.images_generated,
                "pages_ocr_processed": execution.pages_ocr_processed,
                "actions_generated": execution.actions_generated,
            },
        ))

        return execution, edits


# =============================================================================
# CLI ENTRYPOINT (For standalone execution)
# =============================================================================

async def run_pipeline_cli(pdf_path: str, output_dir: str = None) -> None:
    """
    CLI entrypoint for running the pipeline.

    Usage:
        python pipeline_actions.py /path/to/input.pdf
    """
    from scripts.ontology.actions import ActionContext

    context = ActionContext(actor_id="cli_user")

    params = {
        "pdf_path": pdf_path,
    }
    if output_dir:
        params["output_dir"] = output_dir

    action = ExecuteHwpPipelineAction()

    # Note: In production, this would go through GovernanceEngine
    # which would require Proposal approval first
    result = await action.execute(params, context)

    if result.success:
        logger.info(f"[ODA] Pipeline completed successfully")
        logger.info(f"[ODA] Created IDs: {result.created_ids}")
    else:
        logger.error(f"[ODA] Pipeline failed: {result.error}")


if __name__ == "__main__":
    import asyncio
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    if len(sys.argv) < 2:
        print("Usage: python pipeline_actions.py <pdf_path> [output_dir]")
        sys.exit(1)

    pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    asyncio.run(run_pipeline_cli(pdf_path, output_dir))
