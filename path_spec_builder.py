import pathspec
from pathlib import Path

class PathSpecBuilder:
    """Builds a pathspec object from .gitignore and exclude patterns."""

    def __init__(self, gitignore_path=None, exclude_patterns=None):
        """
        Initializes the PathSpecBuilder.

        Args:
            gitignore_path (str | None): Path to a specific .gitignore file.
                                         None means auto-detect in cwd.
                                         "" (empty string) disables loading any .gitignore.
            exclude_patterns (list[str] | None): List of gitignore-style patterns to exclude.
        """
        self.gitignore_path = gitignore_path
        self.exclude_patterns = exclude_patterns or []
        self.spec = self._build_spec()

    def _find_gitignore(self) -> Path | None:
        """Attempts to find the relevant .gitignore file."""
        if self.gitignore_path: # Explicit path provided (could be "")
            potential_gitignore = Path(self.gitignore_path)
            if potential_gitignore.is_file():
                return potential_gitignore
            else:
                print(f"Warning: Specified gitignore file not found: {self.gitignore_path}")
                return None
        elif self.gitignore_path is None: # Auto-detect in CWD
            potential_gitignore = Path('.gitignore')
            if potential_gitignore.is_file():
                return potential_gitignore
        # If gitignore_path is "" (disabled) or auto-detect failed, return None
        return None

    def _load_patterns_from_file(self, gitignore_file: Path) -> list[str]:
        """Loads patterns from a gitignore file."""
        patterns = []
        try:
            with gitignore_file.open('r', encoding='utf-8') as f:
                patterns.extend(f.readlines())
                print(f"Loaded patterns from: {gitignore_file.resolve()}")
        except IOError as e:
            print(f"Warning: Could not read gitignore file {gitignore_file}: {e}")
        except Exception as e:
            print(f"Warning: Error parsing gitignore file {gitignore_file}: {e}")
        return patterns

    def _build_spec(self) -> pathspec.PathSpec:
        """Builds the final pathspec object."""
        raw_patterns = []

        # 1. Load patterns from .gitignore if applicable
        gitignore_file = self._find_gitignore()
        if gitignore_file:
            raw_patterns.extend(self._load_patterns_from_file(gitignore_file))

        # 2. Add explicit exclude patterns
        if self.exclude_patterns:
            raw_patterns.extend(self.exclude_patterns)
            print(f"Added command-line exclude patterns: {self.exclude_patterns}")

        # 3. Compile patterns
        try:
            # Use 'gitwildmatch' style for all patterns.
            spec = pathspec.PathSpec.from_lines('gitwildmatch', raw_patterns)
        except Exception as e:
            print(f"Error: Could not compile pathspec patterns: {e}")
            print("Problematic patterns might be:", raw_patterns)
            # Return an empty spec on error to avoid crashing
            spec = pathspec.PathSpec([])

        return spec

    def get_spec(self) -> pathspec.PathSpec:
        """Returns the compiled pathspec object."""
        return self.spec

    def matches(self, path_to_check: Path, base_dir: Path, is_dir: bool) -> bool:
        """
        Checks if a given path matches the ignore patterns.

        Args:
            path_to_check (Path): The absolute path to check.
            base_dir (Path): The base directory for relative path calculation.
            is_dir (bool): Whether the path_to_check is a directory.

        Returns:
            bool: True if the path should be ignored, False otherwise.
        """
        try:
            relative_path = path_to_check.relative_to(base_dir)
            # Use POSIX separators for matching, add trailing slash for directories
            relative_path_str = str(relative_path.as_posix())
            if is_dir:
                relative_path_str += '/'
            return self.spec.match_file(relative_path_str)
        except ValueError:
            # Target is outside the base directory. Ignore checks based on base_dir spec might not apply.
            # Consider how to handle this - maybe match against basename only?
            # For now, assume it's not ignored by the base spec.
            # print(f"Debug: Path {path_to_check} outside base {base_dir}, not applying base spec.")
            return False
        except Exception as e:
            print(f"Error checking ignore status for {path_to_check}: {e}")
            return True # Treat as ignored on error to be safe
