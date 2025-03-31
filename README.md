# LOC Counter

A command-line tool to count lines of code (LOC) in specified files and directories, while respecting `.gitignore` patterns and allowing custom exclusions.

## Features

*   Counts non-empty, non-comment lines of code.
*   Processes specified files or recursively scans directories.
*   Automatically detects and uses `.gitignore` in the current directory.
*   Allows specifying a custom `.gitignore` file.
*   Supports disabling `.gitignore` loading entirely.
*   Accepts additional custom exclusion patterns (gitignore-style).
*   Optionally counts lines containing only whitespace.
*   Verbose mode to show processed and ignored files.
*   Smart file filtering:
    * Excludes common auto-generated files (package locks, build outputs, etc.)
    * Excludes binary files and non-code files
    * Focuses on actual source code files with recognized extensions
    * Enhanced binary file detection

## Requirements

*   Python 3.x
*   `pathspec` library

## Installation

1.  **Clone the repository (if applicable):**
    ```bash
    git clone <your-repo-url>
    cd loc-counter
    ```
2.  **Install the required library:**
    ```bash
    pip install pathspec
    ```

## Usage

Run the script using `python main.py` followed by the target paths and any options.

```bash
python main.py [OPTIONS] PATH [PATH...]
```

**Examples:**

*   Count LOC in the current directory, using `./.gitignore` if it exists:
    ```bash
    python main.py .
    ```

*   Count LOC in specific files and a directory:
    ```bash
    python main.py src/main.py src/utils.py tests/
    ```

*   Count LOC in `src`, excluding all `.log` files and the `build` directory:
    ```bash
    python main.py src --exclude "*.log" --exclude "build/"
    ```

*   Count LOC using a specific `.gitignore` file:
    ```bash
    python main.py project_root --gitignore project_root/.custom_ignore
    ```

*   Count LOC ignoring any found `.gitignore`, only use command-line excludes:
    ```bash
    python main.py src --exclude "*.tmp" --gitignore ""
    ```

*   Count LOC including lines with only whitespace:
    ```bash
    python main.py . --count-whitespace
    ```

## Command-line Options

*   `PATH`: One or more file or directory paths to scan.
*   `--exclude PATTERN`: Add a gitignore-style pattern to exclude files/directories. Can be used multiple times.
*   `--gitignore FILE`: Path to a specific `.gitignore` file to use. Pass `""` (empty string) to disable loading any `.gitignore`. Defaults to auto-detecting `.gitignore` in the current directory.
*   `--count-whitespace`: Count lines containing only whitespace (Default is usually `False`, check `config.py`).
*   `-v`, `--verbose`: Print names of files being processed and ignored.
*   `-h`, `--help`: Show the help message and exit.

## File Filtering

The tool uses a multi-layered approach to ensure only relevant code files are counted:

1. **Auto-generated File Exclusions:**
   * Package management files (package-lock.json, yarn.lock, etc.)
   * Build outputs (dist/, build/, *.min.js, etc.)
   * IDE and tooling files (.idea/, .vscode/, __pycache__/, etc.)
   * Generated documentation and resources
   * Source maps and type definitions

2. **Extension-based Filtering:**
   * Excludes common binary and non-code extensions
   * Includes recognized code file extensions
   * Configurable through `config.py`

3. **Binary File Detection:**
   * Checks for null bytes
   * Analyzes byte patterns for binary content
   * Validates UTF-8 encoding

4. **Gitignore Integration:**
   * Respects project's `.gitignore` patterns
   * Supports custom ignore patterns
   * Can be disabled if needed

All filtering rules can be customized by modifying the patterns in `config.py`.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

(Specify your license here, e.g., MIT License)
