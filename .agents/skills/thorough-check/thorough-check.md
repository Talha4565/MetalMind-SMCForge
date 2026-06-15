# Skill: Project Thorough Check

## Purpose
Perform a comprehensive, adaptive analysis of any software project.
This skill defines the *what* — the companion script `thorough-check.py` implements it.

## Dynamic Adaptation
- Detect all languages present (Python, Node.js, Go, Rust)
- Scale depth by project size: <20 files = deep scan, >200 = hotspot scan
- Prioritize: Critical (security, crashes) > Important (correctness) > Nice-to-have (docs, style)

## Required Tools
The script will print an install command and continue if any tool is missing — it never crashes on absence.

| Language | Tools |
|---|---|
| Python | `pylint`, `pytest`, `pytest-cov`, `pip-audit` |
| Node.js | `eslint`, `npm` |
| Go | *(detection only — tool checks not yet implemented)* |
| Rust | *(detection only — tool checks not yet implemented)* |

## Implemented Check List

### 1. Security (Critical)
- **Secrets detection** — pure-Python line scan for `API_KEY`, `SECRET`, `PASSWORD`, `TOKEN`; configurable whitelist avoids false positives on env-var assignments, examples, and test fixtures
- **Dependency audit** — `pip-audit` for Python, `npm audit --json` for Node.js

### 2. Code Quality (Important)
- **Complexity** — pylint rules R0912/R0914/R0915 (too many branches, locals, statements) for Python; eslint `max-statements` for Node.js; target path passed explicitly to avoid scanning the wrong directory

### 3. Testing & Reliability (Important)
- **Test coverage** — `pytest --cov`; flags projects below 70%, commends above 90%
- Prompts before running if no pytest config is found (skipped entirely in `--ci` mode)

### 4. Documentation / Housekeeping (Nice-to-have)
- **TODO/FIXME/HACK scan** — pure-Python walk; reports file, line number, and snippet; caps output at 20 items with a count of the remainder

### 5. Performance (Optional — prompts user; always runs in `--ci` mode)
- **N+1 query detection** — multi-line Python `re` scan for ORM calls (`query`, `filter`, `get`, `objects.all`) inside `for` loops; works correctly across line boundaries unlike grep-based approaches

## Checks Planned but Not Yet Implemented
The following items from the original spec are not in the current script. Contributions welcome.
- `eval()` / `exec()` / SQL string-concatenation detection
- Dead code: unused imports and variables
- Empty catch / swallowed exception detection
- Architecture checks: files with >15 imports, circular dependencies (`madge`, `pydeps`), layering violations
- README and API documentation completeness
- Go vulnerability scan (`govulncheck`) and test runner (`go test`)
- Flaky test pattern detection (`sleep()`, unmocked network calls)
- Missing cache headers in web responses

## Output

| File | Description |
|---|---|
| `thorough-report.md` | Human-readable findings grouped by severity |
| `thorough-report.json` | Machine-readable; use with CI assertions |
| `.thorough-history.json` | Persisted between runs to surface *new* critical issues |

Reports are written to the target directory by default, or to `--output DIR` if specified.
The history file is only written after a **complete** run — an interrupted run does not corrupt it.

**Exit codes:** `0` = no critical issues, `1` = one or more critical issues found, `130` = interrupted by user.

## Exception Handling
- Missing tool → prints install command, records as `Important` finding, continues
- Command timeout → skips that check, logs warning, continues
- Target directory not found → logs error and exits immediately with code 1
- Unreadable files → silently skipped
- History file unreadable → logs warning, starts fresh (does not crash)
- Ctrl-C → exits cleanly with code 130; partial report may have been written
- Unhandled exception → logs error, suggests manual check, exits with code 1

## Usage

```bash
# Interactive (prompts before slow scans)
python thorough-check.py

# CI mode (non-interactive, fails on critical issues)
python thorough-check.py --ci

# Skip specific categories
python thorough-check.py --skip performance,todos

# Scan a specific project path
python thorough-check.py /path/to/project

# Write reports to a separate output directory (useful for read-only projects)
python thorough-check.py /path/to/project --output /tmp/reports

# Combine flags
python thorough-check.py /path/to/project --ci --skip todos --output ./reports
```

**Valid `--skip` categories:** `security`, `quality`, `todos`, `tests`, `performance`

## Severity Levels

| Level | Meaning | Effect on exit code |
|---|---|---|
| Critical | Security issue or likely crash | Exit 1 |
| Important | Correctness, reliability, or coverage concern | Exit 0 |
| Nice-to-have | Style, docs, housekeeping | Exit 0 |