

# [HWP/HWPX Automation Standard Template]
# Environment: VS Code (WSL/Linux) -> Windows PowerShell Extension
# Prerequisite: "Security.dll" must be registered in Registry

$dllPath = "C:\HwpAuth\Security.dll"
# Target File Path (Example: Desktop)
$desktop = [Environment]::GetFolderPath("Desktop")
$filePath = Join-Path $desktop "Automation_Result.hwpx"

Write-Host "🚀 HWP Automation Started..." -ForegroundColor Cyan

# 1. Registry Enforcement (Safe Guard)
try {
    $regPath = "HKCU:\Software\HNC\HwpAutomation\Modules"
    if (-not (Test-Path $regPath)) {
        New-Item -Path $regPath -Force | Out-Null
    }
    Set-ItemProperty -Path $regPath -Name "FilePathCheckerModule" -Value $dllPath
}
catch {
    Write-Warning "Registry Access Failed (Might persist if already set): $_"
}

try {
    # 2. Initialize HWP Object
    $hwp = New-Object -ComObject "HWPFrame.HwpObject"
    $hwp.XHwpWindows.Item(0).Visible = $true
    
    # 3. Security Module Registration
    # Note: Even if this returns False, if Registry is correct, it works silently.
    $hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")

    # 4. Automate Tasks
    $hwp.Clear(1) # New Document
    
    $act = $hwp.CreateAction("InsertText")
    $set = $act.CreateSet()
    $act.GetDefault($set)
    $set.SetItem("Text", "Automation Successful!`nSaved as HWPX.")
    $act.Execute($set)

    # 5. Save (Format: "HWPX" or "HWP")
    $hwp.SaveAs($filePath, "HWPX")
    Write-Host "✨ Process Completed: $filePath" -ForegroundColor Cyan

}
catch {
    Write-Error "Critical Error: $_"
}

