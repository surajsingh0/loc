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
  python main.py .  # Note: Run via main.py

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
            default=None, # None means auto-detect in cwd
            help='Path to a specific .gitignore file to use. Pass "" (empty string) to disable loading any .gitignore.'
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

        # Handle the edge case where user explicitly passes "" for gitignore
        gitignore_param = self.args.gitignore
        if self.args.gitignore is not None and self.args.gitignore.strip() == "":
            gitignore_param = "" # Represent disabling auto-detect/loading

        # 1. Initialize components
        file_processor = FileProcessor(count_whitespace_only_lines=self.args.count_whitespace)
        path_spec_builder = PathSpecBuilder(
            gitignore_path=gitignore_param,
            exclude_patterns=self.args.exclude
        )
        scanner = DirectoryScanner(
            file_processor=file_processor,
            path_spec_builder=path_spec_builder,
            base_dir=self.base_dir,
            verbose=self.args.verbose
        )

        # 2. Perform the scan
        total_loc, total_files_processed, processed_files_list = scanner.scan(self.args.targets)

        # 3. Print the results
        print("\n--- LOC Count Summary ---")
        print(f"Total Lines of Code (LOC): {total_loc}")
        print(f"Total Files Processed:      {total_files_processed}")

        # Optionally print all processed files if verbose (can be long)
        # if self.args.verbose and processed_files_list:
        #     print("\nProcessed Files:")
        #     # Sort for consistent output
        #     for f in sorted(processed_files_list):
        #         print(f"  - {f}")

if __name__ == '__main__':
    # This allows running app.py directly for testing if needed,
    # but the primary entry point will be main.py
    print("Running LocCounterApp directly...")
    app = LocCounterApp()
    app.run()
