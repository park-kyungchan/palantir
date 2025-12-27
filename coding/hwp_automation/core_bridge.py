
import os
import subprocess
import shlex
import logging

# Configure logging for the bridge
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WSLBridge")

class WSLBridge:
    """
    ODA Transport Layer for Cross-OS Execution.
    Handles strict path conversion and execution of Windows-side Python scripts.
    """
    def __init__(self):
        self.powershell_bin = "powershell.exe"

    def convert_to_windows_path(self, wsl_path: str) -> str:
        """
        Converts a WSL path (e.g. /home/palantir/...) to a Windows path.
        Uses `wslpath -w` for robust resolution.
        """
        if not wsl_path:
            raise ValueError("Path cannot be empty")

        # Ensure absolute path
        abs_path = os.path.abspath(wsl_path)
        
        try:
            # -w: translate from WSL path to Windows path
            result = subprocess.check_output(["wslpath", "-w", abs_path], text=True)
            win_path = result.strip()
            logger.debug(f"Path Converted: {abs_path} -> {win_path}")
            return win_path
        except subprocess.CalledProcessError as e:
            logger.error(f"wslpath conversion failed for {abs_path}: {e}")
            raise ValueError(f"Could not convert path: {wsl_path}. Ensure it is accessible from Windows.")

    def run_python_script(self, script_path: str, payload_path: str, wait: bool = True) -> int:
        """
        Executes a Python script on the WINDOWS host.
        
        Args:
            script_path: Path to the executor script (e.g. executor_win.py)
            payload_path: Path to the JSON payload file (Action Request)
            wait: Whether to wait for completion.
        
        Returns:
            Return code of the subprocess.
        """
        win_script_path = self.convert_to_windows_path(script_path)
        win_payload_path = self.convert_to_windows_path(payload_path)
        
        # We quote the paths in single quotes to handle spaces and backslashes in PowerShell
        # Command: python 'C:\Path\To\Script.py' 'C:\Path\To\Payload.json'
        command_str = f"python '{win_script_path}' '{win_payload_path}'"
        
        logger.info(f"Executing on Host: {command_str}")
        
        subprocess_args = [self.powershell_bin, "-Command", command_str]
        
        if wait:
            result = subprocess.run(subprocess_args)
            return result.returncode
        else:
            subprocess.Popen(subprocess_args)
            return 0
