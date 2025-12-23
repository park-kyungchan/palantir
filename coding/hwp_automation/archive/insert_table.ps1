
# [HWP Automation: Insert Table into Active Window]
# Connects to the CURRENTLY OPEN Hwp instance and adds a table.

Write-Host "🚀 Connecting to active HWP window..." -ForegroundColor Cyan

try {
    # 1. Attach to running HWP instance
    # Note: Requires HWP to be running. If multiple instances, it picks the first registered one.
    $hwp = [Runtime.InteropServices.Marshal]::GetActiveObject("HWPFrame.HwpObject")
    
    # 2. Insert Table (3 Rows, 3 Columns)
    # Move to end of document first
    $hwp.Run("MoveDocEnd")
    $hwp.Run("BreakPara") # New line

    # Create Table Action
    $act = $hwp.CreateAction("TableCreate")
    $set = $act.CreateSet()
    $act.GetDefault($set)
    
    $set.SetItem("Rows", 3)
    $set.SetItem("Cols", 3)
    $set.SetItem("WidthType", 2) # Width relative to text area
    $set.SetItem("HeightType", 1) # Auto height
    
    $act.Execute($set)
    Write-Host "✅ Table (3x3) inserted." -ForegroundColor Green

    # 3. Fill Table Cells (Sample Data)
    # The cursor automatically moves into the first cell after creation.
    
    $data = @("Header A", "Header B", "Header C", "Data 1", "Data 2", "Data 3")
    
    foreach ($text in $data) {
        $act = $hwp.CreateAction("InsertText")
        $pset = $act.CreateSet()
        $act.GetDefault($pset)
        $pset.SetItem("Text", $text)
        $act.Execute($pset)
        
        # Move to next cell
        $hwp.Run("TableRightCell")
    }

    Write-Host "✨ Sample content filled!" -ForegroundColor Cyan

}
catch {
    Write-Error "Failed to connect to HWP or insert table. Is HWP open?"
    Write-Error $_
}
