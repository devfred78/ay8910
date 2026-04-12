import argparse
import os
import subprocess
import sys
import tempfile


def run_command(command, shell=False, env=None):
    """Executes a system command and displays its output in real time."""
    print(f"\n> Running: {' '.join(command) if isinstance(command, list) else command}")
    try:
        # Use check=True to raise an exception if the command fails
        subprocess.run(command, check=True, shell=shell, env=env)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error during command execution: {e}")
        return False
    except FileNotFoundError:
        print(f"Command not found: {command[0] if isinstance(command, list) else command}")
        return False


def check_uv_installed():
    """Checks if 'uv' is installed, and attempts to install it if not."""
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("uv not found. Attempting to install 'uv'...")
        try:
            # Install uv using pip if available
            subprocess.run([sys.executable, "-m", "pip", "install", "uv"], check=True)
            return True
        except subprocess.CalledProcessError:
            print("Failed to install 'uv'. Please install it manually: https://github.com/astral-sh/uv")
            return False


def run_tests_for_python_version(python_version, root_dir, fix=False):
    """Creates a temporary venv and runs tests for a specific Python version using uv."""
    print("\n" + "=" * 50)
    print(f"Testing with Python {python_version}")
    print("=" * 50)

    # Create a temporary directory for the virtual environment
    # Using tempfile.mkdtemp instead of TemporaryDirectory context manager for more control if needed,
    # but the context manager is generally fine.
    with tempfile.TemporaryDirectory(prefix=f"venv_py{python_version}_") as venv_dir:
        print(f"Creating temporary venv in: {venv_dir}")

        # 1. Create venv with specific python version
        # We use --python to force the version and let uv download it if missing
        if not run_command(["uv", "venv", venv_dir, "--python", python_version, "--python-preference", "only-managed"]):
            print(f"Failed to create venv for Python {python_version}")
            return False

        # Determine the path to the python executable in the new venv
        if sys.platform == "win32":
            python_exe = os.path.join(venv_dir, "Scripts", "python.exe")
        else:
            python_exe = os.path.join(venv_dir, "bin", "python")

        # 2. Install dependencies using uv pip
        # We use --python pointing to the python executable in the venv to ensure isolation
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        env.pop("VIRTUAL_ENV", None)

        print(f"\n--- Installing dependencies for Python {python_version} ---")
        # We must use 'uv pip install' with the --python flag to target our temporary venv
        if not run_command(["uv", "pip", "install", "--python", python_exe, ".[test,dev]"], env=env):
            print(f"Failed to install dependencies for Python {python_version}")
            return False

        # 3. Static analysis (Ruff)
        print(f"\n--- Static analysis (Ruff) for Python {python_version} ---")
        # Ensure we use the python in the venv to run the module
        ruff_cmd = [python_exe, "-m", "ruff", "check", "."]
        if fix:
            ruff_cmd.append("--fix")

        if not run_command(ruff_cmd, env=env):
            print(f"X Ruff found issues under Python {python_version}")
            return False
        else:
            print(f"✓ Ruff: OK (Python {python_version})")

        # 4. Running tests (Pytest)
        print(f"\n--- Running tests (Pytest) for Python {python_version} ---")
        if not run_command([python_exe, "-m", "pytest", "tests/"], env=env):
            print(f"X Some tests failed under Python {python_version}")
            return False
        else:
            print(f"✓ Tests: OK (Python {python_version})")

    return True


def main():
    parser = argparse.ArgumentParser(description="Run tests locally using uv across multiple Python versions.")
    parser.add_argument("--fix", action="store_true", help="Tell Ruff to automatically fix linting issues.")
    parser.add_argument("--all", action="store_true", help="Run tests for all supported Python versions.")
    args = parser.parse_args()

    # Determine the project root (one level above the scripts/ folder)
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root_dir)
    print(f"Working directory: {root_dir}")

    if not check_uv_installed():
        sys.exit(1)

    python_versions = ["3.9", "3.10", "3.11", "3.12", "3.13", "3.14"]
    versions_to_test = python_versions if args.all else [python_versions[-1]]

    if not args.all:
        print(f"Running tests for the latest Python version only: {versions_to_test[0]}")
        print("To run tests for all versions, use the --all flag.")

    overall_success = True
    failed_versions = []

    for version in versions_to_test:
        try:
            if not run_tests_for_python_version(version, root_dir, fix=args.fix):
                overall_success = False
                failed_versions.append(version)
        except Exception as e:
            print(f"An unexpected error occurred while testing Python {version}: {e}")
            overall_success = False
            failed_versions.append(version)

    # Final summary
    print("\n" + "=" * 50)
    if overall_success:
        print(f"SUMMARY: All tests passed for versions: {', '.join(versions_to_test)}!")
        sys.exit(0)
    else:
        print(f"SUMMARY: Errors were detected for versions: {', '.join(failed_versions)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
