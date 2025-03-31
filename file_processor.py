import config
from pathlib import Path
import sys

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

    def is_code_file(self, filepath: Path) -> bool:
        """
        Determines if a file should be counted based on config and content checks.
        """
        extension = filepath.suffix.lower()
        name = filepath.name.lower()

        # 1. Check explicit exclusions
        if extension in config.EXCLUDED_EXTENSIONS or name in config.EXCLUDED_EXTENSIONS:
            return False

        # 2. Check explicit inclusions
        if config.INCLUDED_EXTENSIONS and extension and extension in config.INCLUDED_EXTENSIONS:
             return True

        # 3. Fallback: Check if it's likely a text file
        return self.is_likely_text_file(filepath)

    def is_likely_text_file(self, filepath: Path) -> bool:
        """
        Tries to determine if a file is text-based (not binary).
        Uses null byte check, non-ASCII ratio, and UTF-8 decode attempt.
        """
        try:
            with open(filepath, 'rb') as f:
                chunk = f.read(1024)
                if not chunk: # Empty file is text
                    return True
                if b'\0' in chunk: # Null byte -> binary
                    return False

                # Check for high concentration of non-ASCII bytes
                non_ascii_count = sum(1 for byte in chunk if byte > 127)
                if len(chunk) > 0 and non_ascii_count / len(chunk) > 0.3:
                    return False

            # Final check: Can it be decoded as UTF-8?
            with open(filepath, 'r', encoding='utf-8', errors='strict') as f:
                f.read(512)
            return True
        except (IOError, OSError): # File not found or readable
            return False
        except UnicodeDecodeError: # Definitely not UTF-8 text
            return False
        except Exception: # Other errors
             return False # Be cautious

    def count_lines_in_file(self, filepath: Path) -> int:
        """
        Counts non-empty, non-comment lines in a file, assuming it IS a code file.
        The check `is_code_file` should be done before calling this.
        """
        loc = 0
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    original_line_content = line.rstrip('\n\r')

                    if not original_line_content: # Skip empty lines
                        continue

                    stripped_line = original_line_content.strip()
                    if not stripped_line:  # Line has only whitespace
                        if self.count_whitespace_only_lines:
                            loc += 1 # Count if configured to do so
                        continue # Otherwise skip

                    # Check for comment markers
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
            print(f"Warning: Error processing file {filepath}: {e}")
        return loc
