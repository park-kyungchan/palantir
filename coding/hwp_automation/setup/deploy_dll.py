import shutil
import os
import subprocess

def deploy_dll():
    # Source in WSL
    source_path = "/home/palantir/보안모듈(Automation)/FilePathCheckerModuleExample.dll"
    
    # Destination on Windows (via /mnt/c)
    # WSL mounts C: at /mnt/c
    dest_dir = "/mnt/c/Temp"
    dest_path = os.path.join(dest_dir, "FilePathCheckerModuleExample.dll")
    
    print(f"Deploying Security DLL...")
    print(f"Source: {source_path}")
    print(f"Dest: {dest_path}")
    
    # Ensure destination directory exists
    if not os.path.exists(dest_dir):
        try:
            os.makedirs(dest_dir)
            print("Created C:\\Temp directory.")
        except Exception as e:
            print(f"Error creating dir: {e}")
            return False

    try:
        shutil.copy2(source_path, dest_path)
        print("DLL copied successfully.")
        return True
    except Exception as e:
        print(f"Copy failed: {e}")
        return False

if __name__ == "__main__":
    deploy_dll()
