
# [Mathpix Generated HWP Automation]
[System.Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$dllPath = "C:\HwpAuth\Security.dll"
$desktop = [Environment]::GetFolderPath("Desktop")
$filePath = Join-Path $desktop "mathpix_output.hwpx"

Start-Sleep -Seconds 1
Get-Process -Name "Hwp", "HwpAutomation" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 1

Write-Host "🚀 Launching HWP..." -ForegroundColor Cyan

$regPath = "HKCU:\Software\HNC\HwpAutomation\Modules"
if (-not (Test-Path $regPath)) { New-Item -Path $regPath -Force | Out-Null }
Set-ItemProperty -Path $regPath -Name "FilePathCheckerModule" -Value $dllPath

Start-Job -ScriptBlock { 
    Start-Sleep -Milliseconds 2000
    $wshell = New-Object -ComObject WScript.Shell
    $wshell.SendKeys("{ENTER}")
} | Out-Null

$hwp = New-Object -ComObject "HWPFrame.HwpObject"
$hwp.XHwpWindows.Item(0).Visible = $true
$hwp.RegisterModule("FilePathCheckDLL", "FilePathCheckerModule")
$hwp.Clear(1)

# Style
$act = $hwp.CreateAction("CharShape")
$set = $act.CreateSet()
$act.GetDefault($set)
$set.SetItem("Height", 1000)
$act.Execute($set)

function Insert-Text($t) {
    $act = $hwp.CreateAction("InsertText")
    $set = $act.CreateSet()
    $act.GetDefault($set)
    $set.SetItem("Text", $t)
    $act.Execute($set)
}

function Insert-Equation($s) {
    if (-not $s) { return }
    $act = $hwp.CreateAction("EquationCreate")
    $set = $act.CreateSet()
    $act.GetDefault($set)
    $set.SetItem("String", $s)
    $act.Execute($set)
}

function New-Line {
    $hwp.Run("BreakPara")
}

# --- Actions ---
Insert-Text '4. '
Insert-Equation 'x^{2}+x-1=0'
Insert-Text '일 때, 다음 식의 값을 구하시오. '
New-Line
Insert-Text '(1) '
Insert-Equation '(x+2)(x-1)(x+4)(x-3)+5'
New-Line
Insert-Equation '16'
New-Line
Insert-Text '(2) '
Insert-Equation 'x^{5}-5 x'
New-Line
Insert-Equation '-3'
New-Line
Insert-Text '5. 다음을 만족시키는 '
Insert-Equation 'n'
Insert-Text '의 값을 구하시오. '
New-Line
Insert-Equation '(2^{2}+1)(2^{4}+1)(2^{8}+1)(2^{16}+1)(2^{32}+1)= over {1}{3}(2^{n}-1)'
New-Line
Insert-Text '6. 다음 다항식의 전개식에서 모든 계수의 합을 구하시 오. '
New-Line
Insert-Equation 'begin{array}{l} 1+(1+x)+(1+x+x^{2})^{2}+(1+x+x^{2}+x^{3})^{3}  +(1+x+x^{2}+x^{3}+x^{4})^{4} end{array}'
New-Line
Insert-Text '7. 다항식 '
Insert-Equation '(1+x+x^{2})^{2}(1+x)+(1-x+x^{2}+x^{3})^{3}'
Insert-Text '의 전개식에서 일차항의 계수를 구하시오. '
New-Line
Insert-Equation '0'
New-Line
Insert-Text '8. '
Insert-Equation 'a+b=4, a b=2'
Insert-Text '일 때, 다음 식의 값을 구하시오. (단, '
Insert-Equation 'a  >= q b'
Insert-Text ') '
New-Line
Insert-Text '(1) '
Insert-Equation 'a-b'
New-Line
Insert-Equation 'begin{array}{|l|} hline 2  sqrt {2}  hline end{array}'
New-Line
Insert-Text '(2) '
Insert-Equation 'a^{2}-b^{2}'
New-Line
Insert-Equation '8  sqrt {2}'
New-Line
Insert-Text '(3) '
Insert-Equation 'a^{3}-b^{3}'
New-Line
Insert-Equation '28  sqrt {2}'
New-Line
Insert-Text '9. '
Insert-Equation 'x+y=1, x^{3}+y^{3}=19'
Insert-Text '일 때, 다음 식의 값을 구하 시오. '
New-Line
Insert-Text '(1) '
Insert-Equation 'x y'
New-Line
Insert-Equation '-6'
New-Line
Insert-Text '(2) '
Insert-Equation 'x^{2}+y^{2}'
New-Line
Insert-Equation 'begin{array}{|l|} hline 13  hline end{array}'
New-Line
Insert-Text '(3) '
Insert-Equation 'x^{4}+y^{4}'
Insert-Text '□ '
New-Line
Insert-Text '97 '
New-Line
Insert-Text '(4) '
Insert-Equation 'x^{5}+y^{5}'
Insert-Text '211 '
New-Line
Insert-Text '8 '
New-Line
Insert-Text '1. 다항식의 연산 '
# --- End Actions ---

$hwp.SaveAs($filePath, "HWPX", "")
Write-Host "✅ Saved to $filePath" -ForegroundColor Green
Write-Host "👀 Window Open." -ForegroundColor Yellow
