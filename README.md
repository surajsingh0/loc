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

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

(Specify your license here, e.g., MIT License)
