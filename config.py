# Configuration values for the LOC counter

# Default comment markers
COMMENT_MARKERS = ['#', '//', '--', ';', 'REM', "'"]

# Default setting for counting whitespace-only lines
COUNT_WHITESPACE_ONLY_LINES = False

# Common patterns for auto-generated files and directories to potentially ignore
# Note: These are currently NOT used directly by PathSpecBuilder by default,
# but could be integrated if more aggressive default ignoring is desired.
AUTO_GENERATED_PATTERNS = [
    # Version control
    '.git/',
    '.svn/',
    '.hg/',
    
    # Package management
    'package-lock.json',
    'yarn.lock',
    'pnpm-lock.yaml',
    'poetry.lock',
    'Pipfile.lock',
    'composer.lock',
    'Gemfile.lock',
    'cargo.lock',
    
    # Build outputs
    'dist/',
    'build/',
    'out/',
    'target/',
    '*.min.js',
    '*.min.css',
    
    # IDE and tooling
    '.idea/',
    '.vscode/',
    '.vs/',
    '*.pyc',
    '__pycache__/',
    '*.pyo',
    '*.pyd',
    '.pytest_cache/',
    '.mypy_cache/',
    '.coverage',
    'coverage/',
    
    # Generated documentation
    'docs/_build/',
    'site/',
    'public/',
    
    # Generated source maps
    '*.map',
    
    # Generated type definitions
    '*.d.ts',
    
    # Generated resources
    '*.generated.*',
    '*.auto.*',
]

# File extensions and specific filenames to always exclude
EXCLUDED_EXTENSIONS = {
    # Binary files
    '.exe', '.dll', '.so', '.dylib',
    '.zip', '.tar', '.gz', '.7z', '.rar',
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico',
    '.pdf', '.doc', '.docx', '.xls', '.xlsx',
    '.db', '.sqlite', '.sqlite3',
    '.class', '.jar', '.war',
    '.pyc', '.pyo', '.pyd',
    
    # Lock files
    '.lock',
    
    # Source maps and minified files
    '.map',
    '.min.js',
    '.min.css',
    
    # Log and temporary files
    '.log', '.tmp', '.temp',
    '.bak', '.swp', '.swo',
    '.DS_Store', 'Thumbs.db',
    
    # Documentation and Config
    '.md',
    '.gitignore', 
}

# If this set is defined, ONLY files with these extensions (or extensionless text files)
# will be considered, after checking EXCLUDED_EXTENSIONS.
# If empty or None, all non-excluded text files are considered.
INCLUDED_EXTENSIONS = {
    # Web
    '.js', '.ts', '.jsx', '.tsx',
    '.html', '.htm', '.css', '.scss', '.sass', '.less',
    '.vue', '.svelte',
    
    # Python
    '.py', '.pyi', '.pyx',
    
    # Java/Kotlin/Scala
    '.java', '.kt', '.kts', '.scala',
    
    # C/C++
    '.c', '.cpp', '.h', '.hpp',
    
    # C#
    '.cs', '.cshtml', '.csx',
    
    # Ruby
    '.rb', '.erb',
    
    # PHP
    '.php', '.phtml',
    
    # Go
    '.go',
    
    # Rust
    '.rs',
    
    # Shell
    '.sh', '.bash', '.zsh',
    '.bat', '.cmd', '.ps1',
    
    # Config and markup (Consider moving some like .md to excluded)
    '.json', '.yaml', '.yml', '.toml', '.xml',
    # '.md', # Typically excluded
    '.rst', '.tex',
    
    # Other
    '.sql', '.r', '.m', '.swift', '.f90',
    '.pl', '.pm', '.t', '.lua', '.elm'
}

# --- End Configuration ---
