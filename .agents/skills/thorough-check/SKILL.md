---
name: thorough-check
description: Comprehensive adaptive project scanner for security, quality, testing, and performance checks across Python and Node.js codebases.
---

This skill provides a self-contained project health check tool for repositories with Python and Node.js components.
It detects secrets, audits dependencies, identifies complexity issues, evaluates test coverage, scans for TODOs, and flags potential N+1 query patterns.

## When to Invoke This Skill

Automatically activate for:
- Repository or workspace health checks
- Security and dependency auditing
- Code quality and complexity review
- Test coverage validation
- CI readiness checks

## What It Checks

- **Security**
  - Secrets exposure scan for API keys, tokens, passwords, and sensitive strings
  - Python dependency audit via `pip-audit`
  - Node.js dependency audit via `npm audit --json`
- **Quality**
  - Python complexity via `pylint` rules R0912, R0914, R0915
  - Node.js complexity via `eslint` max-statements
- **Tests**
  - Python coverage via `pytest --cov`; flags below 70%, notes above 90%
  - Reports test failures with truncated output
- **Housekeeping** (`todos`)
  - TODO / FIXME / HACK detection with file path and line number; caps at 20 items
- **Performance** *(prompts in interactive mode; runs automatically in `--ci`)*
  - N+1 query pattern detection across Python and Node.js source files

## Output

Reports are written to the target directory by default, or to `--output DIR` if specified.

| File | Description |
|---|---|
| `thorough-report.md` | Human-readable findings grouped by severity |
| `thorough-report.json` | Machine-readable report for CI assertions |
| `.thorough-history.json` | Persisted across runs; surfaces new critical issues since the last run |

The history file is only written after a **complete** run — an interrupted run does not corrupt it.

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | No critical issues found |
| `1` | One or more critical issues found |
| `130` | Run interrupted by user (Ctrl-C) |

## Valid `--skip` Categories

`security` · `quality` · `todos` · `tests` · `performance`

## Usage

```bash
# Interactive — prompts before slow scans
python thorough-check.py

# Scan a specific project
python thorough-check.py /path/to/project

# CI mode — non-interactive, performance check runs automatically, exits 1 on critical issues
python thorough-check.py --ci

# Write reports to a separate directory (useful for read-only project roots)
python thorough-check.py /path/to/project --output ./reports

# Skip specific categories
python thorough-check.py --skip todos,performance

# Full CI example with all flags
python thorough-check.py /path/to/project --ci --skip todos --output ./reports
```

## Integration Notes

- Missing tools (`pip-audit`, `pylint`, `pytest-cov`, `npm`) are reported as `Important` findings and the run continues — the script never crashes on absence.
- Go and Rust project roots are detected but no active scans run for those ecosystems yet.
- All file scanning is done in pure Python — no `grep` or shell commands — making the script fully portable across Linux, macOS, and Windows.
- This skill is a good fit for scheduled repository audits, pre-merge checks, and developer health reports.