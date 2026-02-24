import os
import sys
from win32com.client import Dispatch

def create_shortcut():
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Define paths for the target and icon files
    target_path = os.path.join(script_dir, "run.cmd")
    icon_path = os.path.join(script_dir, "icon.ico")

    # Get the desktop directory
    desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")

    # Define the shortcut path
    shortcut_path = os.path.join(desktop, "QuickMi2e.lnk")

    # Create the shortcut
    shell = Dispatch("WScript.Shell")
    shortcut = shell.CreateShortcut(shortcut_path)
    shortcut.TargetPath = target_path
    shortcut.IconLocation = icon_path
    shortcut.WorkingDirectory = script_dir
    shortcut.Save()

    print(f"Shortcut created successfully at: {shortcut_path}")

if __name__ == "__main__":
    create_shortcut()
