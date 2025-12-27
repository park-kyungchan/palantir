import winreg
import sys

def set_registry_value():
    """
    Sets the HWP 2024 Security ModuleUsage to Low (Level 2 or specific configuration)
    to bypass standard automation pop-ups.
    """
    # Target Key for HWP 2024
    # Note: Structure might vary by exact version. 
    # 'ModuleUsage' and 'FilePathCheckerModule' are the standard keys.
    # Target Keys - We try coverage of both HNC and Hancom paths
    targets = [
        r"Software\HNC\HwpAutomation\Modules",
        r"Software\Hancom\HwpAutomation\Modules"
    ]
    
    success_count = 0
    
    for base_key_path in targets:
        try:
            # 1. Open/Create Modules Key
            print(f"Targeting: {base_key_path}")
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, base_key_path)
            
            # 2. Whitelist 'FilePathCheckerModuleExample'
            # Point to the REAL deployed DLL in C:\Temp to ensure export checks pass.
            target_dll = r"C:\Temp\FilePathCheckerModuleExample.dll"
            
            # Use the robust name often found in examples
            value_name = "FilePathCheckerModuleExample"
            
            winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, target_dll)
            print(f"  [SUCCESS] Set '{value_name}' -> {target_dll}")
            
            winreg.CloseKey(key)
            success_count += 1
            
        except Exception as e:
            print(f"  [Partial Error] {base_key_path}: {e}")

    if success_count > 0:
        print("Registry updated successfully (At least one key set).")
        return True
    else:
        print("Failed to set any registry keys.")
        return False

if __name__ == "__main__":
    success = set_registry_value()
    if not success:
        sys.exit(1)
