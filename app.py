import argparse
from pathlib import Path
import tempfile
import shutil
import sys

# Import our refactored components
import config # To potentially access default config values if needed
from file_processor import FileProcessor
from path_spec_builder import PathSpecBuilder
from directory_scanner import DirectoryScanner

# Import GitPython (make sure it's installed via requirements.txt)
try:
    import git # Added
except ImportError:
    print("Error: 'GitPython' library not found.", file=sys.stderr)
    print("Please install it using: pip install GitPython", file=sys.stderr)
    sys.exit(1)

class LocCounterApp:
    """Main application class for the LOC counter."""

    def __init__(self):
        self.args = self._parse_arguments()
        self.base_dir = Path.cwd()

    def _parse_arguments(self):
        """Parses command-line arguments."""
        parser = argparse.ArgumentParser(
            description="Count lines of code (LOC) in local paths or a remote Git repository.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Count LOC in the current directory
  python main.py .

  # Count LOC in specific files and a directory
  python main.py src/main.py src/utils.py tests/

  # Count LOC in 'src', excluding '.log' files and 'build' directory
  python main.py src --exclude \"*.log\" --exclude \"build/\"

  # Count LOC using a specific .gitignore file
  python main.py project_root --gitignore project_root/.custom_ignore

  # Count LOC ignoring any found .gitignore
  python main.py src --exclude \"*.tmp\" --gitignore \"\"

  # Count LOC in a public GitHub repository
  python main.py --repo https://github.com/user/repo.git

  # Count LOC in a repo, excluding certain patterns
  python main.py --repo https://github.com/user/repo.git --exclude \"docs/\"
"""
        )

        # Group for mutually exclusive arguments: local paths or remote repo
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            'targets',
            metavar='PATH',
            nargs='*', # Use '*' for optional positional arguments when in a group
            default=[], # Default to empty list if not provided (repo case)
            help='One or more local file or directory paths to scan.'
        )
        group.add_argument(
            '--repo',
            metavar='URL',
            help='URL of a public Git repository to clone and scan.'
        )
        parser.add_argument(
            '--exclude',
            metavar='PATTERN',
            action='append',
            default=[], # Ensure default is a list
            help='Add a gitignore-style pattern to exclude files/directories. Can be used multiple times.'
        )
        parser.add_argument(
            '--gitignore',
            metavar='FILE',
            default=None, # None = auto-detect
            help='Path to a specific .gitignore file. Pass "" to disable .gitignore processing.'
        )
        parser.add_argument(
            '-v', '--verbose',
            action='store_true',
            help='Print names of files being processed and ignored.'
        )
        # Add argument for whitespace counting, defaulting to config
        parser.add_argument(
            '--count-whitespace',
            action='store_true',
            default=config.COUNT_WHITESPACE_ONLY_LINES,
            help=f'Count lines containing only whitespace (Default: {config.COUNT_WHITESPACE_ONLY_LINES}).'
        )

        args = parser.parse_args()

        # Ensure targets are provided if --repo is not used
        if not args.repo and not args.targets:
             parser.error("You must specify either local PATHs or a --repo URL.") # Added validation

        return args

    def run(self):
        """Executes the LOC counting process, handling local paths or remote repo."""
        temp_dir = None # Initialize temporary directory path
        scan_targets = []
        run_base_dir = self.base_dir # Default to current working directory

        try:
            if self.args.repo:
                # Create a temporary directory for cloning
                temp_dir = tempfile.mkdtemp(prefix="loc_counter_repo_")
                print(f"Cloning repository '{self.args.repo}' into '{temp_dir}'...")
                try:
                    git.Repo.clone_from(self.args.repo, temp_dir, depth=1) # Shallow clone
                    print("Clone successful.")
                    scan_targets = [Path(temp_dir)] # Scan the root of the cloned repo
                    run_base_dir = Path(temp_dir) # Base directory for scanning is the temp dir
                except git.GitCommandError as e:
                    print(f"\nError cloning repository: {e}", file=sys.stderr)
                    # Clean up the potentially partially created directory
                    if Path(temp_dir).exists():
                        shutil.rmtree(temp_dir)
                    sys.exit(1)
                except Exception as e: # Catch other potential errors during clone
                     print(f"\nAn unexpected error occurred during cloning: {e}", file=sys.stderr)
                     if Path(temp_dir).exists():
                         shutil.rmtree(temp_dir)
                     sys.exit(1)
            else:
                # Use the provided local targets
                scan_targets = self.args.targets
                # Keep run_base_dir as self.base_dir (cwd)

            # Determine gitignore parameter and whether to use built-in ignores
            gitignore_param = self.args.gitignore
            use_builtin_ignores = True
            if isinstance(gitignore_param, str) and gitignore_param.strip() == "":
                gitignore_param = ""
                use_builtin_ignores = False
            # Handle potential relative gitignore path when cloning
            elif gitignore_param is not None and self.args.repo:
                 # If a gitignore path is given for a repo, assume it's relative to the repo root
                 # If the provided path is absolute, Path() will handle it correctly.
                 # If it's relative, it will be relative to the temp_dir (run_base_dir)
                 gitignore_param = run_base_dir / gitignore_param

            # Initialize components
            file_processor = FileProcessor(count_whitespace_only_lines=self.args.count_whitespace)
            path_spec_builder = PathSpecBuilder(
                # Pass run_base_dir to correctly find .gitignore in cloned repo or local context
                base_dir=run_base_dir,
                gitignore_path=gitignore_param,
                exclude_patterns=self.args.exclude,
                use_builtin_patterns=use_builtin_ignores
            )
            scanner = DirectoryScanner(
                file_processor=file_processor,
                path_spec_builder=path_spec_builder,
                base_dir=run_base_dir, # Use the potentially updated base directory
                verbose=self.args.verbose
            )

            # Perform the scan using the determined targets
            total_loc, total_files_processed, processed_files_list = scanner.scan(scan_targets)

            print("\n--- LOC Count Summary ---")
            print(f"Source: {'Repository ' + self.args.repo if self.args.repo else 'Local paths ' + ', '.join(map(str, self.args.targets))}") # Indicate source
            print(f"Total Lines of Code (LOC): {total_loc}")
            print(f"Total Files Processed:      {total_files_processed}")

            # Optionally print processed files list (currently disabled)
            # if self.args.verbose and processed_files_list:
            #     print("\nProcessed Files:")
            #     for f in sorted(processed_files_list):
            #         print(f"  - {f}")

        finally:
            # Clean up the temporary directory if it was created
            if temp_dir and Path(temp_dir).exists():
                try:
                    print(f"Cleaning up temporary directory '{temp_dir}'...")
                    shutil.rmtree(temp_dir)
                    print("Cleanup successful.")
                except OSError as e:
                    print(f"\nWarning: Could not remove temporary directory '{temp_dir}': {e}", file=sys.stderr)

if __name__ == '__main__':
    # Allows running app.py directly for simple testing
    print("Running LocCounterApp directly...")
    app = LocCounterApp()
    app.run()
