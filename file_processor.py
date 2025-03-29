import config
from pathlib import Path

class FileProcessor:
    """Handles processing of individual files for LOC counting."""

    def __init__(self, count_whitespace_only_lines=config.COUNT_WHITESPACE_ONLY_LINES):
        """
        Initializes the FileProcessor.

        Args:
            count_whitespace_only_lines (bool): Whether to count lines containing only whitespace.
        """
        self.comment_markers = config.COMMENT_MARKERS
        self.count_whitespace_only_lines = count_whitespace_only_lines

    def is_likely_text_file(self, filepath: Path) -> bool:
        """
        Tries to determine if a file is text-based and not binary.

        Args:
            filepath (Path): The path to the file.

        Returns:
            bool: True if the file is likely text-based, False otherwise.
        """
        try:
            # Read a small chunk; if it contains a null byte, likely binary
            with open(filepath, 'rb') as f:
                chunk = f.read(1024)
                if b'\0' in chunk:
                    return False
            # Try decoding a small chunk as UTF-8 as a further check
            with open(filepath, 'r', encoding='utf-8', errors='strict') as f:
                f.read(1024)
            return True
        except (IOError, UnicodeDecodeError):
            # Common issues indicating non-text or encoding problems
            return False
        except Exception:
            # Catch other potential issues but assume text for safety if unsure
            # or handle more specific exceptions if needed
            # Consider logging this edge case if necessary
            return True # Or False, depending on desired behavior

    def count_lines_in_file(self, filepath: Path) -> int:
        """
        Counts non-empty, non-comment lines in a single file.

        Args:
            filepath (Path): The path to the file.

        Returns:
            int: The number of lines of code (LOC) counted.
        """
        loc = 0
        try:
            # Use utf-8 encoding, common for code; handle errors gracefully
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    # 1. Strip trailing newline/carriage return first
                    original_line_content = line.rstrip('\n\r')

                    # 2. Skip truly empty lines
                    if not original_line_content:
                        continue

                    # 3. Check for whitespace-only lines
                    stripped_line = original_line_content.strip()
                    if not stripped_line:  # Line contains only whitespace
                        if not self.count_whitespace_only_lines:
                            continue  # Skip if configured to ignore

                    # 4. Check if the line starts with any known comment marker
                    is_comment = False
                    for marker in self.comment_markers:
                        if stripped_line.startswith(marker):
                            is_comment = True
                            break

                    if not is_comment:
                        loc += 1
        except IOError as e:
            print(f"Warning: Could not read file {filepath}: {e}")
        except Exception as e:
            # Catch potential decoding issues not caught by errors='ignore'
            print(f"Warning: Error processing file {filepath}: {e}")
        return loc
