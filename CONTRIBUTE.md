# Contributing Guide

Thank you for your interest in `ay8910_wrapper`! This document explains how to contribute to the project.

## GitHub Flow

We follow the standard **GitHub Flow** for development. Here is a concrete example of the commands to use:

1.  **Fork the repository** on GitHub by clicking the "Fork" button.
2.  **Clone your fork** locally:
    ```powershell
    git clone https://github.com/YOUR_USERNAME/ay8910.git
    cd ay8910
    ```
3.  **Keep your fork up to date** (to be done before each new modification):
    If you haven't added the **original** (upstream) repository yet:
    ```powershell
    git remote add upstream https://github.com/devfred78/ay8910.git
    ```
    Then, synchronize your `main` branch:
    ```powershell
    git checkout main
    git fetch upstream
    git merge upstream/main
    git push origin main
    ```
4.  **Create a descriptive branch** for your modification:
    ```powershell
    git checkout -b fix-envelope-bug
    ```
5.  **Make your changes** and commit them:
    ```powershell
    # After editing files
    git add .
    git commit -m "Fix: correct envelope period calculation in ay8912_cap32"
    ```
6.  **Push** your branch to your fork:
    ```powershell
    git push origin fix-envelope-bug
    ```
7.  **Open a Pull Request (PR)**: Go to the original repository on GitHub. You should see a "Compare & pull request" button for your recently pushed branch.

### Handling Merge Conflicts

Sometimes, GitHub may detect conflicts in your Pull Request because someone else modified the same lines of code in the `main` branch. To resolve them, you need to synchronize your local repository with the **original** (upstream) repository (as described in step 3 above) and merge it into your branch:

1.  **Update your local `main` branch from upstream** (see step 3 for details).

2.  **Merge `main` into your feature branch**:
    ```powershell
    git checkout fix-envelope-bug
    git merge main
    ```

3.  **Resolve conflicts**: Git will mark the files with conflicts. Open them in your editor, look for `<<<<<<<`, `=======`, and `>>>>>>>` markers, and choose which version to keep.

4.  **Commit the resolution**:
    ```powershell
    git add .
    git commit -m "Merge main and resolve conflicts"
    ```

5.  **Push the updated branch**:
    ```powershell
    git push origin fix-envelope-bug
    ```
    The Pull Request will be updated automatically on GitHub.

## Development Environment Setup

We recommend using **[uv](https://github.com/astral-sh/uv)** for fast and efficient management of Python virtual environments.

### 1. Install `uv`
If you don't have `uv` yet, install it:
- **Windows**: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`
- **macOS/Linux**: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### 2. Initialize the Environment
From the project root:
```powershell
# Create the virtual environment and install development dependencies
uv sync --all-extras
```

This command automatically installs the dependencies needed for:
- Compiling the C++ extension
- Running tests (`pytest`)
- Linting (`ruff`)

## Development and Compilation

As the project contains a C++ extension, you need to compile it to test your modifications:

```powershell
# Install in editable mode (compiles the C++ module)
uv pip install -e .
```

If you modify the C++ code (`src/ay8910_wrapper/wrapper.cpp` or files in `ay8910_cpp_lib/`), you will need to rerun this command for the changes to take effect in Python.

## Unit Tests

### Run Tests Locally
Before submitting a PR, make sure all tests pass:

```powershell
# Run all tests with pytest
uv run pytest tests/
```

### Linting
We use `ruff` to ensure code quality:
```powershell
# Check code style
uv run ruff check .
```

## Continuous Integration (GitHub Actions)

When a Pull Request is opened, the following actions are automatically launched on GitHub:

1.  **Linting**: Code style check with `ruff`.
2.  **Build & Test**: 
    - Compilation of the project on **Linux, Windows, and macOS**.
    - Execution of unit tests on **Python 3.8 and 3.13** versions.

Additionally, when a **version tag** (starting with `v`) is pushed to the repository, the **Build and Publish** workflow is triggered to automatically build wheels for all platforms and publish them to **PyPI**.

---

Once your modification is ready and tested, feel free to submit your Pull Request!