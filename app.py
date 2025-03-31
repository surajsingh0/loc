import argparse
from pathlib import Path

# Import our refactored components
import config # To potentially access default config values if needed
from file_processor import FileProcessor
from path_spec_builder import PathSpecBuilder
from directory_scanner import DirectoryScanner

class LocCounterApp:
    """Main application class for the LOC counter."""

    def __init__(self):
        self.args = self._parse_arguments()
        self.base_dir = Path.cwd()

    def _parse_arguments(self):
        """Parses command-line arguments."""
        parser = argparse.ArgumentParser(
            description="Count lines of code (LOC) in specified files/directories, respecting gitignore patterns.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Count LOC in the current directory, using ./.gitignore if it exists
  python main.py .

  # Count LOC in specific files and a directory
  python main.py src/main.py src/utils.py tests/

  # Count LOC in 'src', excluding all '.log' files and the 'build' directory
  python main.py src --exclude "*.log" --exclude "build/"

  # Count LOC using a specific .gitignore file
  python main.py project_root --gitignore project_root/.custom_ignore

  # Count LOC ignoring any found .gitignore, only use command-line excludes
  python main.py src --exclude "*.tmp" --gitignore ""
"""
        )
        parser.add_argument(
            'targets',
            metavar='PATH',
            nargs='+',
            help='One or more file or directory paths to scan.'
        )
        parser.add_argument(
            '--exclude',
            metavar='PATTERN',
            action='append',
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

        return parser.parse_args()

    def run(self):
        """Executes the LOC counting process."""

        # Determine gitignore parameter and whether to use built-in ignores
        gitignore_param = self.args.gitignore
        use_builtin_ignores = True
        if isinstance(gitignore_param, str) and gitignore_param.strip() == "":
            gitignore_param = "" # Normalize to empty string
            use_builtin_ignores = False

        # Initialize components
        file_processor = FileProcessor(count_whitespace_only_lines=self.args.count_whitespace)
        path_spec_builder = PathSpecBuilder(
            gitignore_path=gitignore_param,
            exclude_patterns=self.args.exclude,
            use_builtin_patterns=use_builtin_ignores
        )
        scanner = DirectoryScanner(
            file_processor=file_processor,
            path_spec_builder=path_spec_builder,
            base_dir=self.base_dir,
            verbose=self.args.verbose
        )

        # Perform the scan
        total_loc, total_files_processed, processed_files_list = scanner.scan(self.args.targets)

        # Print the results
        print("\n--- LOC Count Summary ---")
        print(f"Total Lines of Code (LOC): {total_loc}")
        print(f"Total Files Processed:      {total_files_processed}")

        # Optionally print processed files list (currently disabled)
        # if self.args.verbose and processed_files_list:
        #     print("\nProcessed Files:")
        #     for f in sorted(processed_files_list):
        #         print(f"  - {f}")

if __name__ == '__main__':
    # Allows running app.py directly for simple testing
    print("Running LocCounterApp directly...")
    app = LocCounterApp()
    app.run()
