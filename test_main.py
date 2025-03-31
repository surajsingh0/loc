import unittest
import os
import tempfile
import shutil
from pathlib import Path
import sys
import subprocess # Import subprocess globally

# Add the directory containing the modules to the Python path
script_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(script_dir))

# Import the refactored classes and config
try:
    import config
    from file_processor import FileProcessor
    from path_spec_builder import PathSpecBuilder
    # LocCounterApp and DirectoryScanner might not be needed directly for unit tests below
    # but are part of the project structure.
    # from app import LocCounterApp
    # from directory_scanner import DirectoryScanner
    import pathspec # Required for tests, especially integration tests
except ImportError as e:
    print(f"Error: Could not import necessary modules (config, file_processor, path_spec_builder, pathspec). Ensure they exist and dependencies are installed. Details: {e}", file=sys.stderr)
    sys.exit(1)


class TestFileProcessor(unittest.TestCase):
    """Tests for the FileProcessor class."""

    def setUp(self):
        """Set up temporary directory and default processor."""
        self.test_dir = tempfile.mkdtemp()
        # Default processor uses config values
        self.processor = FileProcessor()

    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)
        # No need to restore config as we instantiate processors

    def _create_temp_file(self, content, filename="testfile.txt", encoding='utf-8'):
        """Helper to create a temporary file with specific content."""
        filepath = Path(self.test_dir) / filename
        try:
            with open(filepath, 'w', encoding=encoding, errors='ignore') as f:
                f.write(content)
        except Exception as e:
             # Handle potential errors during file creation if needed
             print(f"Error creating temp file {filepath}: {e}", file=sys.stderr)
        return filepath

    def _create_binary_file(self, content=b'\x00\x01\x02', filename="binaryfile.bin"):
        """Helper to create a temporary binary file."""
        filepath = Path(self.test_dir) / filename
        with open(filepath, 'wb') as f:
            f.write(content)
        return filepath

    # --- Tests for is_likely_text_file ---

    def test_is_likely_text_file_true(self):
        """Test is_likely_text_file with a standard text file."""
        filepath = self._create_temp_file("This is a text file.\nWith multiple lines.")
        self.assertTrue(self.processor.is_likely_text_file(filepath))

    def test_is_likely_text_file_empty(self):
        """Test is_likely_text_file with an empty file."""
        filepath = self._create_temp_file("")
        self.assertTrue(self.processor.is_likely_text_file(filepath)) # Empty is considered text

    def test_is_likely_text_file_false_null_byte(self):
        """Test is_likely_text_file with a file containing null bytes."""
        filepath = self._create_binary_file(b"text\x00with\x00nulls")
        self.assertFalse(self.processor.is_likely_text_file(filepath))

    def test_is_likely_text_file_false_binary(self):
        """Test is_likely_text_file with a simple binary file."""
        filepath = self._create_binary_file()
        self.assertFalse(self.processor.is_likely_text_file(filepath))

    def test_is_likely_text_file_non_utf8(self):
        """Test is_likely_text_file with non-UTF8 encodable bytes (should be false)."""
        # Example using latin-1 bytes that are invalid UTF-8
        filepath = Path(self.test_dir) / "latin1.txt"
        with open(filepath, 'wb') as f:
            f.write("olé".encode('latin-1')) # 'é' in latin-1 is 0xE9
        # Re-evaluating: The strict decode should catch this.
        self.assertFalse(self.processor.is_likely_text_file(filepath))


    def test_is_likely_text_file_nonexistent(self):
        """Test is_likely_text_file with a non-existent file."""
        filepath = Path(self.test_dir) / "nonexistent.txt"
        self.assertFalse(self.processor.is_likely_text_file(filepath)) # Should return False on IOError

    # --- Tests for count_lines_in_file ---

    def test_count_lines_empty_file(self):
        """Test count_lines_in_file with an empty file."""
        filepath = self._create_temp_file("")
        self.assertEqual(self.processor.count_lines_in_file(filepath), 0)

    def test_count_lines_only_comments(self):
        """Test count_lines_in_file with only comment lines (using default markers)."""
        content = """
# This is a comment
// Another comment style
-- SQL style comment
; Lisp style comment
REM Batch style comment
' VB style comment
"""
        filepath = self._create_temp_file(content)
        self.assertEqual(self.processor.count_lines_in_file(filepath), 0)

    def test_count_lines_only_whitespace_default(self):
        """Test count_lines_in_file with only whitespace lines (default: ignored)."""
        # Default processor has count_whitespace_only_lines=False (from config)
        processor_default = FileProcessor(count_whitespace_only_lines=False)
        content = """

        \t

 \r\n
"""
        filepath = self._create_temp_file(content)
        self.assertEqual(processor_default.count_lines_in_file(filepath), 0)

    def test_count_lines_only_whitespace_counted(self):
        """Test count_lines_in_file with only whitespace lines (config: counted)."""
        # Create a processor configured to count whitespace lines
        processor_ws = FileProcessor(count_whitespace_only_lines=True)
        content = "  \n\t\n" # Two lines with only whitespace
        filepath = self._create_temp_file(content)
        # The logic should now count these lines.
        self.assertEqual(processor_ws.count_lines_in_file(filepath), 2)

    def test_count_lines_mixed_content(self):
        """Test count_lines_in_file with mixed content (using default processor)."""
        content = """
# Comment line
Actual code line 1

  Another code line (with leading space)
// Comment
Code line 3 # Trailing comment (should still count)

""" # Includes empty lines, comments, code
        filepath = self._create_temp_file(content)
        # Expected LOC:
        # - Actual code line 1
        # - Another code line (with leading space)
        # - Code line 3 # Trailing comment
        self.assertEqual(self.processor.count_lines_in_file(filepath), 3)

    def test_count_lines_different_comment_markers(self):
        """Test count_lines_in_file respects various comment markers via processor init."""
        # Create a processor with specific comment markers
        custom_markers = ['--', ';']
        processor_custom = FileProcessor() # Start with default whitespace setting
        processor_custom.comment_markers = custom_markers # Override markers

        content = """
-- SQL comment
Valid line 1
# Not a comment now
; Lisp comment
Valid line 2 // Not a comment now
"""
        filepath = self._create_temp_file(content)
        # Expected LOC:
        # - Valid line 1
        # - # Not a comment now
        # - Valid line 2 // Not a comment now
        self.assertEqual(processor_custom.count_lines_in_file(filepath), 3)

    def test_count_lines_nonexistent_file(self):
        """Test count_lines_in_file with a non-existent file."""
        filepath = Path(self.test_dir) / "nonexistent.txt"
        # Should print a warning and return 0
        # We can capture stderr if needed, but for now just check the return value
        self.assertEqual(self.processor.count_lines_in_file(filepath), 0)

    def test_count_lines_encoding_error(self):
        """Test count_lines_in_file with incompatible encoding."""
        filepath = Path(self.test_dir) / "bad_encoding.txt"
        # Write bytes that are invalid in UTF-8
        with open(filepath, 'wb') as f:
            f.write(b'\x80\xff')
        # errors='ignore' should skip bad bytes, potentially resulting in 0 LOC
        # or a partial count depending on where the error occurs.
        # Let's expect 0 as it's likely to fail early or ignore the content.
        self.assertEqual(self.processor.count_lines_in_file(filepath), 0)
        # Add check for warning message in stderr if necessary


# --- Tests for PathSpecBuilder ---
class TestPathSpecBuilder(unittest.TestCase):

     def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.original_cwd = Path.cwd()
        os.chdir(self.test_dir) # Change CWD for auto-detection tests

     def tearDown(self):
        os.chdir(self.original_cwd) # Change back CWD
        shutil.rmtree(self.test_dir)

     def _create_temp_file(self, content, filename):
        filepath = self.test_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath

     # Add tests for build_pathspec here...
     # e.g., test_build_pathspec_no_gitignore
     # e.g., test_build_pathspec_auto_detect
     # e.g., test_build_pathspec_specific_gitignore
     # e.g., test_build_pathspec_cmd_exclude
     # e.g., test_build_pathspec_combined
     # e.g., test_build_pathspec_disable_gitignore
     def test_builder_no_gitignore_no_exclude(self):
         """Test PathSpecBuilder with no gitignore and no excludes."""
         builder = PathSpecBuilder(gitignore_path="", exclude_patterns=None)
         spec = builder.get_spec()
         self.assertIsNotNone(spec)
         # An empty spec should not match anything
         self.assertFalse(builder.matches(self.test_dir / "some_file.py", self.test_dir, is_dir=False))
         self.assertFalse(builder.matches(self.test_dir / "some_dir/file.txt", self.test_dir, is_dir=False))

     def test_builder_auto_detect_gitignore(self):
         """Test PathSpecBuilder automatically detects .gitignore in cwd."""
         self._create_temp_file("*.log\nbuild/", ".gitignore")
         builder = PathSpecBuilder(gitignore_path=None, exclude_patterns=None) # None triggers auto-detect
         # Need absolute paths for matching method
         self.assertTrue(builder.matches(self.test_dir / "file.log", self.test_dir, is_dir=False))
         self.assertTrue(builder.matches(self.test_dir / "build", self.test_dir, is_dir=True)) # Check dir match
         self.assertTrue(builder.matches(self.test_dir / "build/somefile", self.test_dir, is_dir=False)) # Check file within dir
         self.assertFalse(builder.matches(self.test_dir / "src/file.py", self.test_dir, is_dir=False))

     def test_builder_specific_gitignore(self):
         """Test PathSpecBuilder uses the specified gitignore file."""
         ignore_path = self.test_dir / ".custom_ignore"
         self._create_temp_file("*.tmp\ndata/", str(ignore_path))
         # Create a default .gitignore too, to ensure it's not used
         self._create_temp_file("*.log", ".gitignore")

         builder = PathSpecBuilder(gitignore_path=str(ignore_path), exclude_patterns=None)
         self.assertTrue(builder.matches(self.test_dir / "file.tmp", self.test_dir, is_dir=False))
         self.assertTrue(builder.matches(self.test_dir / "data", self.test_dir, is_dir=True))
         self.assertTrue(builder.matches(self.test_dir / "data/file", self.test_dir, is_dir=False))
         self.assertFalse(builder.matches(self.test_dir / "file.log", self.test_dir, is_dir=False)) # Should not be ignored
         self.assertFalse(builder.matches(self.test_dir / "src/file.py", self.test_dir, is_dir=False))

     def test_builder_cmd_exclude(self):
         """Test PathSpecBuilder uses command-line exclude patterns."""
         builder = PathSpecBuilder(gitignore_path="", exclude_patterns=["*.pyc", "dist/"])
         self.assertTrue(builder.matches(self.test_dir / "file.pyc", self.test_dir, is_dir=False))
         self.assertTrue(builder.matches(self.test_dir / "dist", self.test_dir, is_dir=True))
         self.assertTrue(builder.matches(self.test_dir / "dist/app.exe", self.test_dir, is_dir=False))
         self.assertFalse(builder.matches(self.test_dir / "file.py", self.test_dir, is_dir=False))

     def test_builder_combined(self):
         """Test PathSpecBuilder combines gitignore and command-line excludes."""
         self._create_temp_file("*.log\nbuild/", ".gitignore")
         builder = PathSpecBuilder(gitignore_path=None, exclude_patterns=["*.pyc", "dist/"])
         self.assertTrue(builder.matches(self.test_dir / "file.log", self.test_dir, is_dir=False))
         self.assertTrue(builder.matches(self.test_dir / "build", self.test_dir, is_dir=True))
         self.assertTrue(builder.matches(self.test_dir / "build/somefile", self.test_dir, is_dir=False))
         self.assertTrue(builder.matches(self.test_dir / "another.pyc", self.test_dir, is_dir=False))
         self.assertTrue(builder.matches(self.test_dir / "dist", self.test_dir, is_dir=True))
         self.assertTrue(builder.matches(self.test_dir / "dist/other.txt", self.test_dir, is_dir=False))
         self.assertFalse(builder.matches(self.test_dir / "src/main.py", self.test_dir, is_dir=False))

     def test_builder_disable_gitignore(self):
         """Test PathSpecBuilder disables gitignore loading with empty string."""
         self._create_temp_file("*.log", ".gitignore") # This should be ignored
         builder = PathSpecBuilder(gitignore_path="", exclude_patterns=["*.pyc"])
         self.assertFalse(builder.matches(self.test_dir / "file.log", self.test_dir, is_dir=False)) # Not ignored
         self.assertTrue(builder.matches(self.test_dir / "file.pyc", self.test_dir, is_dir=False)) # Excluded via cmd line

     def test_builder_gitignore_not_found(self):
         """Test PathSpecBuilder handles non-existent specified gitignore."""
         # Should print a warning but return an empty spec (or spec from excludes)
         builder = PathSpecBuilder(gitignore_path="nonexistent/.gitignore", exclude_patterns=["*.tmp"])
         # We can capture stderr to check for the warning if needed
         self.assertFalse(builder.matches(self.test_dir / "file.log", self.test_dir, is_dir=False))
         self.assertTrue(builder.matches(self.test_dir / "file.tmp", self.test_dir, is_dir=False)) # Exclude should still work


# --- Tests for main script integration (using subprocess) ---
# These tests run the main.py script as a separate process to test the CLI.
# They require 'pathspec' to be installed in the environment.
class TestLocCounterIntegration(unittest.TestCase):

    # Helper methods are fine here as they interact with the filesystem for the subprocess
    def _create_temp_file(self, content, filename):
        filepath = self.test_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath

    # Add helper for binary files
    def _create_binary_file(self, content, filename):
        filepath = self.test_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'wb') as f: # Open in binary write mode
            f.write(content)
        return filepath

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())
        self.original_cwd = Path.cwd()
        os.chdir(self.test_dir)
        # No need to redirect stdout/stderr, subprocess captures it.

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir)

    def _create_project_structure(self):
        # Helper to create a sample directory structure for testing main()
        (self.test_dir / "src").mkdir()
        (self.test_dir / "tests").mkdir()
        (self.test_dir / "build").mkdir()
        (self.test_dir / "data").mkdir()

        self._create_temp_file("line1\nline2\n# comment", "src/file1.py")
        self._create_temp_file("lineA\n\nlineB", "src/file2.js")
        self._create_temp_file("test1", "tests/test_a.py")
        self._create_temp_file("build artifact", "build/output.log")
        self._create_binary_file(b'\x00\x01', "data/binary.dat") # Use binary helper
        self._create_temp_file("*.log\nbuild/\ndata/", ".gitignore")

    def _run_main(self, args):
        """Helper to run the main script with specific args using subprocess."""
        python_exe = sys.executable # Path to current python interpreter
        # Ensure we point to the correct main.py entry script
        main_script_path = script_dir / "main.py"
        if not main_script_path.is_file():
             raise FileNotFoundError(f"main.py not found at {main_script_path}")

        # ALWAYS add --verbose for debugging test failures
        command = [python_exe, str(main_script_path)]
        if '--verbose' not in args:
             command.append('--verbose')
        command.extend(args)

        result = subprocess.run(command, capture_output=True, text=True, check=False)
        return result

    # --- Integration Tests ---

    def test_main_simple_file(self):
        """Test main with a single file target."""
        self._create_temp_file("line1\n# comment\nline3", "file.py")
        result = self._run_main(["file.py"])
        self.assertIn("Total Lines of Code (LOC): 2", result.stdout)
        self.assertIn("Total Files Processed:      1", result.stdout)
        self.assertEqual(result.returncode, 0)

    def test_main_directory_no_ignore(self):
        """Test main with a directory, no ignores active."""
        self._create_project_structure()
        result = self._run_main(["--verbose", "--gitignore", "", "."])
        # Expect LOC: 5, Files: 3 (ignores .log & .gitignore by config)
        self.assertIn("Total Lines of Code (LOC): 5", result.stdout)
        self.assertIn("Total Files Processed:      3", result.stdout)
        self.assertEqual(result.returncode, 0)
        # Check verbose output confirms skipping
        self.assertIn(f"Skipping excluded/binary file: {os.path.join('.gitignore')}", result.stdout)


    def test_main_directory_with_gitignore(self):
        """Test main with a directory, respecting .gitignore."""
        self._create_project_structure() # Creates .gitignore
        result = self._run_main(["--verbose", "."]) # Auto-detects .gitignore, verbose
        # Expect LOC: 5, Files: 3 (ignores *.log, build/, data/ by gitignore; .gitignore by config)
        self.assertIn("Total Lines of Code (LOC): 5", result.stdout)
        self.assertIn("Total Files Processed:      3", result.stdout)
        self.assertEqual(result.returncode, 0)
        # Check verbose output confirms skipping .gitignore and ignoring build/data
        self.assertIn(f"Skipping excluded/binary file: {os.path.join('.gitignore')}", result.stdout)
        self.assertIn(f"Ignoring: {os.path.join('build')} (matched by spec)", result.stdout)
        self.assertIn(f"Ignoring: {os.path.join('data')} (matched by spec)", result.stdout)

    def test_main_with_cmd_exclude(self):
        """Test main with command-line excludes."""
        self._create_project_structure() # Creates .gitignore
        result = self._run_main(["--verbose", "--gitignore", "", "--exclude", "*.py", "."])
        # Expect LOC: 2, Files: 1 (ignores *.py by CLI; .log & .gitignore by config)
        self.assertIn("Total Lines of Code (LOC): 2", result.stdout)
        self.assertIn("Total Files Processed:      1", result.stdout)
        self.assertEqual(result.returncode, 0)
        # Check verbose output confirms skipping
        self.assertIn(f"Ignoring: {os.path.join('src', 'file1.py')} (matched by spec)", result.stdout)
        self.assertIn(f"Ignoring: {os.path.join('tests', 'test_a.py')} (matched by spec)", result.stdout)
        self.assertIn(f"Skipping excluded/binary file: {os.path.join('.gitignore')}", result.stdout)

    def test_main_combined_ignores(self):
        """Test main combining .gitignore and command-line excludes."""
        self._create_project_structure() # Creates .gitignore
        result = self._run_main(["--verbose", "--exclude", "*.js", "."])
        # Expect LOC: 3, Files: 2 (ignores specified files/dirs)
        self.assertIn("Total Lines of Code (LOC): 3", result.stdout)
        self.assertIn("Total Files Processed:      2", result.stdout)
        self.assertEqual(result.returncode, 0)
        # Check verbose output confirms skipping/ignoring
        self.assertIn(f"Skipping excluded/binary file: {os.path.join('.gitignore')}", result.stdout)
        self.assertIn(f"Ignoring: {os.path.join('src', 'file2.js')} (matched by spec)", result.stdout)
        self.assertIn(f"Ignoring: {os.path.join('build')} (matched by spec)", result.stdout)
        self.assertIn(f"Ignoring: {os.path.join('data')} (matched by spec)", result.stdout)


    def test_main_verbose_output(self):
         """Test verbose output shows processed and ignored files."""
         self._create_project_structure() # Creates .gitignore
         result = self._run_main(["--verbose", "."]) # Use auto-detected .gitignore

         # Check for specific processed files
         self.assertIn(f"Processing file: {os.path.join('src', 'file1.py')}", result.stdout)
         self.assertIn(f"Processing file: {os.path.join('src', 'file2.js')}", result.stdout)
         self.assertIn(f"Processing file: {os.path.join('tests', 'test_a.py')}", result.stdout)
         # .gitignore should now be skipped
         self.assertNotIn(f"Processing file: {os.path.join('.gitignore')}", result.stdout)
         self.assertIn(f"Skipping excluded/binary file: {os.path.join('.gitignore')}", result.stdout)

         # Check for specific ignored items
         self.assertIn(f"Ignoring: {os.path.join('build')} (matched by spec)", result.stdout)
         self.assertIn(f"Ignoring: {os.path.join('data')} (matched by spec)", result.stdout)
         self.assertNotIn(f"Processing file: {os.path.join('build', 'output.log')}", result.stdout)
         self.assertNotIn(f"Skipping likely binary file: {os.path.join('data', 'binary.dat')}", result.stdout)
         self.assertNotIn(f"Ignoring: {os.path.join('build', 'output.log')} (matched by spec)", result.stdout)

         # Check final summary
         self.assertIn("Total Lines of Code (LOC): 5", result.stdout)
         self.assertIn("Total Files Processed:      3", result.stdout)
         self.assertEqual(result.returncode, 0)


    def test_main_nonexistent_target(self):
        """Test main handles non-existent target path gracefully."""
        target_name = "nonexistent_dir"
        result = self._run_main([target_name])
        self.assertIn(f"Warning: Target path does not exist: {target_name}", result.stdout)
        # Should still produce a summary, even if 0
        self.assertIn("Total Lines of Code (LOC): 0", result.stdout)
        self.assertIn("Total Files Processed:      0", result.stdout)
        self.assertEqual(result.returncode, 0)


if __name__ == '__main__':
    # Subprocess is now imported globally
    unittest.main(argv=['first-arg-is-ignored'], exit=False) # Prevent unittest from parsing cmd line args meant for main.py
