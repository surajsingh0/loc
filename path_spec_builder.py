import pathspec
from pathlib import Path
import config

class PathSpecBuilder:
    """Builds a pathspec object from .gitignore, exclude patterns, and built-in patterns."""

    def __init__(self, gitignore_path=None, exclude_patterns=None, use_builtin_patterns=True):
        """
        Initializes the PathSpecBuilder.

        Args:
            gitignore_path: Path to a specific .gitignore file. None=auto-detect, ""=disable.
            exclude_patterns: List of patterns from CLI to exclude.
            use_builtin_patterns: Whether to include built-in patterns (like .git/).
        """
        self.gitignore_path_param = gitignore_path
        self.cli_exclude_patterns = exclude_patterns or []
        # Only use built-ins if gitignore isn't explicitly disabled
        self.use_builtin_patterns = use_builtin_patterns and (gitignore_path != "")

        self._resolved_gitignore_file: Path | None = self._find_gitignore()
        self.spec = self._build_spec()

    def _find_gitignore(self) -> Path | None:
        """Attempts to find the relevant .gitignore file based on gitignore_path_param."""
        if isinstance(self.gitignore_path_param, (str, Path)) and self.gitignore_path_param != "":
            # Explicit path provided
            potential_gitignore = Path(self.gitignore_path_param)
            if potential_gitignore.is_file():
                return potential_gitignore.resolve()
            else:
                print(f"Warning: Specified gitignore file not found: {self.gitignore_path_param}")
                return None
        elif self.gitignore_path_param is None:
             # Auto-detect in CWD
             potential_gitignore = Path('.gitignore')
             if potential_gitignore.is_file():
                 return potential_gitignore.resolve()
        # If disabled or auto-detect failed
        return None

    def _load_patterns_from_file(self, gitignore_file: Path) -> list[str]:
        """Loads patterns from a gitignore file."""
        patterns = []
        try:
            with gitignore_file.open('r', encoding='utf-8') as f:
                patterns.extend(f.readlines())
                print(f"Loaded patterns from: {gitignore_file}")
        except IOError as e:
            print(f"Warning: Could not read gitignore file {gitignore_file}: {e}")
        except Exception as e:
            print(f"Warning: Error parsing gitignore file {gitignore_file}: {e}")
        return patterns

    def _build_spec(self) -> pathspec.PathSpec:
        """Builds the final pathspec object by combining patterns from various sources."""
        raw_patterns = []

        if self._resolved_gitignore_file:
            raw_patterns.extend(self._load_patterns_from_file(self._resolved_gitignore_file))

        if self.use_builtin_patterns:
            # Add essential built-ins if not already present
            essential_builtins = ['.git/', '__pycache__/']
            for pattern in essential_builtins:
                 if pattern not in raw_patterns and pattern not in self.cli_exclude_patterns:
                     raw_patterns.append(pattern)
            # Potential extension: add config.AUTO_GENERATED_PATTERNS here

        if self.cli_exclude_patterns:
            raw_patterns.extend(self.cli_exclude_patterns)
            print(f"Added command-line exclude patterns: {self.cli_exclude_patterns}")

        final_spec = pathspec.PathSpec([])
        if raw_patterns:
            try:
                final_spec = pathspec.PathSpec.from_lines('gitwildmatch', raw_patterns)
            except Exception as e:
                print(f"Error: Could not compile pathspec patterns: {e}")
                print("Problematic patterns might be:", raw_patterns)

        return final_spec

    def get_spec(self) -> pathspec.PathSpec:
        """Returns the compiled pathspec object."""
        return self.spec

    def matches(self, path_to_check: Path, base_dir: Path, is_dir: bool) -> bool:
        """
        Checks if a given path matches the ignore patterns.
        """
        try:
            abs_base_dir = base_dir.resolve()
            abs_path_to_check = path_to_check.resolve()

            relative_path = abs_path_to_check.relative_to(abs_base_dir)
            # Use POSIX separators for matching, add trailing slash for directories
            relative_path_str = str(relative_path.as_posix())
            if is_dir:
                relative_path_str += '/'
            return self.spec.match_file(relative_path_str)
        except ValueError:
            # Target is outside the base directory; treat as not ignored by this spec.
            return False
        except Exception as e:
            print(f"Error checking ignore status for {path_to_check}: {e}")
            return True # Treat as ignored on error
