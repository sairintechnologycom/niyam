import os
import subprocess
import sys

def build():
    print("Building Sutra CLI standalone binary...")
    
    # Check if pyinstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("Error: PyInstaller is not installed. Run: pip install pyinstaller")
        sys.exit(1)

    # Command to build the binary using sutra/__main__.py as entrypoint
    cmd = [
        "pyinstaller",
        "--onefile",
        "--name", "sutra",
        "--clean",
        "sutra/__main__.py"
    ]

    try:
        subprocess.run(cmd, check=True)
        print("\nBuild successful! The binary is located in the 'dist' folder.")
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    build()
