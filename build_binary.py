import subprocess
import sys
import importlib.util


def build():
    print("Building Niyam CLI standalone binary...")

    # Check if pyinstaller is installed
    if importlib.util.find_spec("PyInstaller") is None:
        print("Error: PyInstaller is not installed. Run: pip install pyinstaller")
        sys.exit(1)

    # Command to build the binary using niyam/__main__.py as entrypoint
    cmd = [
        "pyinstaller",
        "--onefile",
        "--name",
        "niyam",
        "--clean",
        "niyam/__main__.py",
    ]

    try:
        subprocess.run(cmd, check=True)
        print("\nBuild successful! The binary is located in the 'dist' folder.")
    except subprocess.CalledProcessError as e:
        print(f"\nBuild failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build()
