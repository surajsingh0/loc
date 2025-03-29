from pathlib import Path
from typing import List, Tuple, Set
import argparse # Keep for type hinting if args object is passed directly

# Import the classes we created
from file_processor import FileProcessor
from path_spec_builder import PathSpecBuilder

class DirectoryScanner:
    """Scans directories and files, counting LOC while respecting ignore patterns."""

    def __init__(
        self,
        file_processor: FileProcessor,
        path_spec_builder: PathSpecBuilder,
        base_dir: Path,
        verbose: bool = False
    ):
        """
        Initializes the DirectoryScanner.

        Args:
            file_processor: An instance of FileProcessor.
            path_spec_builder: An instance of PathSpecBuilder containing ignore rules.
            base_dir: The base directory for relative path calculations (usually CWD).
            verbose: If True, print detailed processing information.
        """
        self.file_processor = file_processor
        self.path_spec_builder = path_spec_builder
        self.base_dir = base_dir
        self.verbose = verbose
        self.processed_paths: Set[Path] = set() # Track absolute paths to avoid duplicates

    def scan(self, targets: List[str]) -> Tuple[int, int, List[str]]:
        """
        Scans the target paths (files or directories).

        Args:
            targets: A list of string paths to scan.

        Returns:
            A tuple containing: (total_loc, total_files_processed, list_of_processed_files)
        """
        total_loc = 0
        total_files_processed = 0
        processed_files_list: List[str] = []

        for target_str in targets:
            target_path = Path(target_str)
            loc, files, processed_segment = self._process_entry(target_path)
            total_loc += loc
            total_files_processed += files
            processed_files_list.extend(processed_segment)

        return total_loc, total_files_processed, processed_files_list

    def _process_entry(self, target_path: Path) -> Tuple[int, int, List[str]]:
        """
        Recursively processes a single file or directory entry.

        Args:
            target_path: The Path object of the file or directory to process.

        Returns:
            A tuple containing: (lines_counted, files_processed_count, list_of_processed_files)
        """
        loc_count = 0
        files_processed = 0
        processed_list: List[str] = []

        try:
            # Use absolute paths for internal logic and tracking
            abs_target_path = target_path.resolve()
        except OSError as e:
             print(f"Warning: Could not resolve path {target_path}: {e}")
             return 0, 0, [] # Cannot process if path is invalid

        # 1. Check if exists
        if not abs_target_path.exists():
            print(f"Warning: Target path does not exist: {target_path}")
            return 0, 0, []

        # 2. Check if already processed (relevant for overlapping targets)
        if abs_target_path in self.processed_paths:
            return 0, 0, []

        # 3. Check if ignored
        is_dir = abs_target_path.is_dir()
        is_ignored = self.path_spec_builder.matches(abs_target_path, self.base_dir, is_dir)

        # Calculate relative path primarily for display purposes
        try:
            relative_path = abs_target_path.relative_to(self.base_dir)
        except ValueError:
            # Target is outside the base directory. Use absolute path for display.
            relative_path = abs_target_path
            if not is_ignored: # Only warn if it wasn't ignored for other reasons
                 print(f"Warning: Target {target_path} is outside the base directory {self.base_dir}. Gitignore rules from base might not apply correctly.")


        if is_ignored:
            if self.verbose:
                print(f"Ignoring: {relative_path} (matched by spec)")
            # Even if ignored, add to processed_paths to prevent re-checking if encountered again
            self.processed_paths.add(abs_target_path)
            return 0, 0, []

        # 4. Process File or Directory
        if abs_target_path.is_file():
            if self.file_processor.is_likely_text_file(abs_target_path):
                if self.verbose:
                    print(f"Processing file: {relative_path}")
                file_loc = self.file_processor.count_lines_in_file(abs_target_path)
                loc_count += file_loc
                files_processed += 1
                processed_list.append(str(relative_path))
                self.processed_paths.add(abs_target_path) # Mark as processed
            elif self.verbose:
                print(f"Skipping likely binary file: {relative_path}")
                self.processed_paths.add(abs_target_path) # Mark binary as processed too

        elif is_dir: # Use the is_dir flag we already determined
            if self.verbose:
                print(f"Scanning directory: {relative_path}")
            self.processed_paths.add(abs_target_path) # Mark dir itself as processed
            try:
                # Use scandir for potentially better performance on large directories
                for entry in abs_target_path.iterdir():
                    # Recursively process directory contents
                    entry_loc, entry_files, entry_list = self._process_entry(entry)
                    loc_count += entry_loc
                    files_processed += entry_files
                    processed_list.extend(entry_list)
            except OSError as e:
                print(f"Warning: Could not read directory {abs_target_path}: {e}")
            except Exception as e:
                 print(f"Warning: Error processing directory contents {abs_target_path}: {e}")

        else: # Neither file nor directory (e.g., broken symlink)
            print(f"Warning: Target is neither a file nor a directory: {target_path}")
            self.processed_paths.add(abs_target_path) # Mark as processed

        return loc_count, files_processed, processed_list
