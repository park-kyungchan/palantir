
# [HWP Automation: Recreate PDF Math Content]
# Parses the analyzed PDF content (Math) and creates a clean HWPX file.

# Force UTF-8 Output
[System.Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$dllPath = "C:\HwpAuth\Security.dll"
$desktop = [Environment]::GetFolderPath("Desktop")
$filePath = Join-Path $desktop "sample_math.hwpx"

Write-Host "🚀 Creating 'sample_math.hwpx' from extracted PDF content..." -ForegroundColor Cyan

# 0. Kill Existing Processes
Get-Process -Name "Hwp", "HwpAutomation" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1

try {
    # 1. Registry Setup
    $regPath = "HKCU:\Software\HNC\HwpAutomation\Modules"
    if (-not (Test-Path $regPath)) { New-Item -Path $regPath -Force | Out-Null }
    Set-ItemProperty -Path $regPath -Name "FilePathCheckerModule" -Value $dllPath

    # [Async Popup Killer]
    Start-Job -ScriptBlock { 
        Start-Sleep -Milliseconds 1500
        $wshell = New-Object -ComObject WScript.Shell
        $wshell.SendKeys("{ENTER}")
    } | Out-Null

    # 2. Initialize HWP
    $hwp = New-Object -ComObject "HWPFrame.HwpObject"
    $hwp.XHwpWindows.Item(0).Visible = $true
    $hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")

    # 3. New Document
    $hwp.Clear(1)

    # Function to Insert Text
    function Insert-Text ($str) {
        $act = $hwp.CreateAction("InsertText")
        $set = $act.CreateSet()
        $act.GetDefault($set)
        $set.SetItem("Text", $str)
        $act.Execute($set)
    }

    # Function to Insert Equation (HWP Syntax)
    function Insert-Equation ($eqStr) {
        $act = $hwp.CreateAction("EquationCreate")
        $set = $act.CreateSet()
        $act.GetDefault($set)
        $set.SetItem("String", $eqStr) # HWP uses its own syntax (EQEDIT)
        $set.SetItem("BaseUnit", 160)  # Font Size
        $act.Execute($set)
    }

    # Function to New Line
    function New-Line {
        $hwp.Run("BreakPara")
    }

    # ==========================================
    # Problem 4
    # ==========================================
    Insert-Text "4. "
    Insert-Equation "x^2 + x - 1 = 0"
    Insert-Text "일 때, 다음 식의 값을 구하시오."
    New-Line
    Insert-Text "(1) "
    Insert-Equation "(x+2)(x-1)(x+4)(x-3)+5"
    New-Line
    Insert-Text "   [답] 16"
    New-Line
    Insert-Text "(2) "
    Insert-Equation "x^5 - 5x"
    New-Line
    Insert-Text "   [답] -3"
    New-Line
    New-Line

    # ==========================================
    # Problem 5
    # ==========================================
    Insert-Text "5. 다음을 만족시키는 "
    Insert-Equation "n"
    Insert-Text "의 값을 구하시오."
    New-Line
    Insert-Equation "(2^2+1)(2^4+1)(2^8+1)(2^{16}+1)(2^{32}+1) = {1} over {3} (2^n-1)"
    New-Line
    Insert-Text "   [답] 64"
    New-Line
    New-Line

    # ==========================================
    # Problem 6
    # ==========================================
    Insert-Text "6. 다음 다항식의 전개식에서 모든 계수의 합을 구하시오."
    New-Line
    Insert-Equation "1+(1+x)+(1+x+x^2)^2+(1+x+x^2+x^3)^3+(1+x+x^2+x^3+x^4)^4"
    New-Line
    Insert-Text "   [답] 701"
    New-Line
    New-Line

    # ==========================================
    # Problem 7
    # ==========================================
    Insert-Text "7. 다항식 "
    Insert-Equation "(1+x+x^2)^2(1+x)+(1-x+x^2+x^3)^3"
    Insert-Text "의 전개식에서 일차항의 계수를 구하시오."
    New-Line
    Insert-Text "   [답] 0"
    New-Line
    New-Line

    # ==========================================
    # Problem 8
    # ==========================================
    Insert-Text "8. "
    Insert-Equation "a+b=4, ab=2"
    Insert-Text "일 때, 다음 식의 값을 구하시오. (단, "
    Insert-Equation "a >= b"
    Insert-Text ")"
    New-Line
    Insert-Text "(1) "
    Insert-Equation "a-b"
    New-Line
    Insert-Text "   [답] "
    Insert-Equation "2 sqrt {2}"
    New-Line
    Insert-Text "(2) "
    Insert-Equation "a^2-b^2"
    New-Line
    Insert-Text "   [답] "
    Insert-Equation "8 sqrt {2}"
    New-Line
    Insert-Text "(3) "
    Insert-Equation "a^3-b^3"
    New-Line
    Insert-Text "   [답] "
    Insert-Equation "28 sqrt {2}"
    New-Line
    New-Line

    # ==========================================
    # Problem 9
    # ==========================================
    Insert-Text "9. "
    Insert-Equation "x+y=1, x^3+y^3=19"
    Insert-Text "일 때, 다음 식의 값을 구하시오."
    New-Line
    Insert-Text "(1) "
    Insert-Equation "xy"
    New-Line
    Insert-Text "   [답] -6"
    New-Line
    Insert-Text "(2) "
    Insert-Equation "x^2+y^2"
    New-Line
    Insert-Text "   [답] 13"
    New-Line
    Insert-Text "(3) "
    Insert-Equation "x^4+y^4"
    New-Line
    Insert-Text "   [답] 97"
    New-Line
    Insert-Text "(4) "
    Insert-Equation "x^5+y^5"
    New-Line
    Insert-Text "   [답] 211"
    New-Line

    # 6. Save
    $hwp.SaveAs($filePath, "HWPX", "")
    
    Write-Host "💾 Saved: $filePath" -ForegroundColor Green
    Write-Host "👀 HWP Window Left Open for Verification." -ForegroundColor Yellow

}
catch {
    Write-Error "Error: $_"
}
