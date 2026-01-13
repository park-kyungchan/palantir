from typing import List
from lib.models import (
    HwpAction, InsertText, SetFontSize, SetFontBold, SetAlign, 
    SetParaShape, CreateTable, SetCellBorder, MoveToCell, 
    InsertImage, InsertEquation, BreakSection, MultiColumn, BreakColumn
)

class Builder:
    """
    Translates HwpAction objects into a standalone Python script 
    that uses win32com to reconstruct the document in HWP.
    """
    def __init__(self):
        self.lines = []
        self.indent_level = 0

    def build(self, actions: List[HwpAction], output_script: str):
        """
        Main entry point. Generates the Python script.
        """
        self.lines = []
        self._add_header()
        
        for action in actions:
            self._dispatch(action)
            
        self._add_footer()
        
        with open(output_script, "w", encoding="utf-8") as f:
            f.write("\n".join(self.lines))
            
    def _add_line(self, line: str):
        indent = "    " * self.indent_level
        self.lines.append(f"{indent}{line}")

    def _add_header(self):
        self._add_line("import win32com.client as win32")
        self._add_line("import os")
        self._add_line("")
        self._add_line("def reconstruct():")
        self.indent_level += 1
        self._add_line("hwp = win32.gencache.EnsureDispatch('HWPFrame.HwpObject')")
        self._add_line("hwp.RegisterModule('FilePathCheckDLL', 'SecurityModule')")
        self._add_line("hwp.XHwpWindows.Item(0).Visible = True")
        self._add_line("hwp.HAction.Run('FileNew')")
        self._add_line("")

    def _add_footer(self):
        self._add_line("print('Reconstruction Complete.')")
        self.indent_level -= 1
        self._add_line("")
        self._add_line("if __name__ == '__main__':")
        self.indent_level += 1
        self._add_line("reconstruct()")

    def _dispatch(self, action: HwpAction):
        method_name = f"_build_{action.action_type}"
        if hasattr(self, method_name):
            getattr(self, method_name)(action)
        else:
            self._add_line(f"# TODO: Implement builder for {action.action_type}")

    # --- Action Builders ---

    def _build_InsertText(self, action: InsertText):
        safe_text = action.text.replace("'", "\\'").replace("\n", "\\n").replace("\r", "")
        self._add_line(f"hwp.HAction.GetDefault('InsertText', hwp.HParameterSet.HInsertText.HSet)")
        self._add_line(f"hwp.HParameterSet.HInsertText.Text = '{safe_text}'")
        self._add_line(f"hwp.HAction.Execute('InsertText', hwp.HParameterSet.HInsertText.HSet)")

    def _build_SetParaShape(self, action: SetParaShape):
        self._add_line(f"# SetParaShape: indent={action.indent}, left={action.left_margin}")
        self._add_line("hwp.HAction.GetDefault('ParagraphShape', hwp.HParameterSet.HParaShape.HSet)")
        self._add_line(f"hwp.HParameterSet.HParaShape.LeftMargin = hwp.PointToSet({action.left_margin})")
        self._add_line(f"hwp.HParameterSet.HParaShape.RightMargin = hwp.PointToSet({action.right_margin})")
        self._add_line(f"hwp.HParameterSet.HParaShape.Item('Indent') = hwp.PointToSet({action.indent})") 
        self._add_line("hwp.HAction.Execute('ParagraphShape', hwp.HParameterSet.HParaShape.HSet)")

    def _build_SetFontSize(self, action: SetFontSize):
        self._add_line(f"hwp.HAction.GetDefault('CharShape', hwp.HParameterSet.HCharShape.HSet)")
        self._add_line(f"hwp.HParameterSet.HCharShape.Height = hwp.PointToSet({action.size})")
        self._add_line("hwp.HAction.Execute('CharShape', hwp.HParameterSet.HCharShape.HSet)")

    def _build_SetFontBold(self, action: SetFontBold):
        val = 1 if action.is_bold else 0
        self._add_line(f"hwp.HAction.GetDefault('CharShape', hwp.HParameterSet.HCharShape.HSet)")
        self._add_line(f"hwp.HParameterSet.HCharShape.FontType = {val}") # Actually Bold is a specific bit property usually? 
        # API says Bold is usually UserProperty on CharShape.
        # Simplistic approach: Use basic bold toggle or dedicated call if exists. 
        # Often: hwp.HParameterSet.HCharShape.Bold = 1
        self._add_line(f"hwp.HParameterSet.HCharShape.Bold = {val}") 
        self._add_line("hwp.HAction.Execute('CharShape', hwp.HParameterSet.HCharShape.HSet)")

    def _build_CreateTable(self, action: CreateTable):
        self._add_line(f"# CreateTable {action.rows}x{action.cols}")
        self._add_line("hwp.HAction.GetDefault('TableCreate', hwp.HParameterSet.HTableCreation.HSet)")
        self._add_line(f"hwp.HParameterSet.HTableCreation.Rows = {action.rows}")
        self._add_line(f"hwp.HParameterSet.HTableCreation.Cols = {action.cols}")
        self._add_line(f"hwp.HParameterSet.HTableCreation.WidthType = {action.width_type}")
        self._add_line(f"hwp.HParameterSet.HTableCreation.HeightType = {action.height_type}")
        self._add_line("hwp.HAction.Execute('TableCreate', hwp.HParameterSet.HTableCreation.HSet)")

    def _build_SetCellBorder(self, action: SetCellBorder):
        # This usually applies to selected cells.
        # "CellBorderFill"
        self._add_line(f"# SetCellBorder: {action.border_type}")
        self._add_line("hwp.HAction.GetDefault('CellBorderFill', hwp.HParameterSet.HCellBorderFill.HSet)")
        # Map BorderType string to HWP Integer constants if needed. 
        # For now, simplistic.
        if action.border_type == "None":
            bs = "hwp.HwpLineType('None')" # Pseudo-code, win32 constants usually integers
            # 0=None, 1=Solid
            self._add_line("border_type = 0 # None")
        else:
            self._add_line("border_type = 1 # Solid")
            
        self._add_line("hwp.HParameterSet.HCellBorderFill.TypeHorz = border_type")
        self._add_line("hwp.HParameterSet.HCellBorderFill.TypeVert = border_type")
        self._add_line("hwp.HParameterSet.HCellBorderFill.TypeTop = border_type")
        self._add_line("hwp.HParameterSet.HCellBorderFill.TypeBottom = border_type")
        self._add_line("hwp.HAction.Execute('CellBorderFill', hwp.HParameterSet.HCellBorderFill.HSet)")

    def _build_MoveToCell(self, action: MoveToCell):
        # Requires Table interaction. 
        # HWP doesn't have a direct "MoveToCell(r, c)" global action. 
        # It typically requires: Table cursor context -> TableParaList.
        # Or simplistic: "MovePos(201)" loops?
        # For V1, we assume linear writing. 
        # If we just created the table, cursor is in (0,0).
        # To move, we might need "TableRightCell" action.
        pass

    def _build_InsertImage(self, action: InsertImage):
         path = action.path.replace("\\", "\\\\")
         self._add_line(f"hwp.InsertPicture('{path}', True, {1 if action.treat_as_char else 0}, False, False, 0, 0, 0)")

    def _build_InsertEquation(self, action: InsertEquation):
        script = action.script.replace("'", "\\'")
        self._add_line(f"act = hwp.CreateAction('Equation')")
        self._add_line(f"set = act.CreateSet()")
        self._add_line(f"act.GetDefault(set)")
        self._add_line(f"set.SetItem('String', '{script}')")
        self._add_line(f"act.Execute(set)")
