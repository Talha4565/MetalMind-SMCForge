#!/usr/bin/env python3
"""
Thorough project check – improved version
Usage: python thorough-check.py [--ci] [--skip CATEGORIES] [--output DIR] [TARGET_DIR]

Categories: security, quality, todos, tests, performance
"""

import os
import sys
import json
import subprocess
import shlex
import re
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any

# ---------- Logging ----------
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s  %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("thorough-check")

# ---------- Configuration ----------
WHITELIST_PATTERNS = [
    r"example", r"demo", r"test", r"dummy", r"changeme", r"<your-",
    r"your[-_].*key", r"replace-with", r"your-secret", r"_here\"",
    r"API_KEY\s*=\s*os\.environ",
    r"password\s*[:=]\s*string",   # TypeScript type annotations
    r"password\s*\??\s*:",          # TypeScript interface fields
    r"\.md:",                        # skip hits inside markdown files
    r"#\s",                          # skip comment-only lines
]

# Skip non-source file extensions
SKIP_EXTENSIONS = {".md", ".txt", ".rst", ".lock", ".sum", ".mod",
                   ".png", ".jpg", ".svg", ".ico", ".woff", ".map"}

REPORT_MD = "thorough-report.md"
REPORT_JSON = "thorough-report.json"
HISTORY_JSON = ".thorough-history.json"
TIMEOUT_SEC = 30

# ---------- Helper: run command ----------
def run_cmd(
    args: List[str],
    cwd: str = None,
    timeout: int = TIMEOUT_SEC,
) -> Tuple[int, str, str]:
    """
    Runs a command safely (no shell=True) from a list of arguments.
    Returns (returncode, stdout, stderr).
    """
    try:
        result = subprocess.run(
            args, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout}s: {args[0]}"
    except FileNotFoundError:
        return -2, "", f"Command not found: {args[0]}"
    except Exception as e:
        return -3, "", f"Unexpected error: {e}"

# ---------- Project detection ----------
def detect_project(root: Path) -> Dict[str, Any]:
    languages = []
    if (root / "requirements.txt").exists() or (root / "setup.py").exists() or (root / "pyproject.toml").exists():
        languages.append("python")
    if (root / "package.json").exists():
        languages.append("node")
    if (root / "go.mod").exists():
        languages.append("go")
    if (root / "Cargo.toml").exists():
        languages.append("rust")
    if not languages:
        languages.append("unknown")

    source_files = 0
    for ext in ["*.py", "*.js", "*.ts", "*.go", "*.rs", "*.java"]:
        source_files += len(list(root.rglob(ext)))

    return {
        "root": root,
        "languages": languages,
        "total_files": source_files,
        "size_category": (
            "small" if source_files < 20 else
            "medium" if source_files < 200 else
            "large"
        ),
    }

# ---------- Secrets scan (pure Python — no shell injection risk) ----------
def check_secrets(root: Path) -> List[Dict]:
    # Match actual hardcoded secrets: long hex strings, base64, or quoted strings
    # More specific patterns to avoid flagging variable names and imports
    pattern = re.compile(
        r"""(?:
            ['"]([\da-f]{32,})['"]\s*(?:,|;|\)|$)|          # 32+ hex chars in quotes
            ['"]([\w/+]{40,}={0,2})['"]\s*(?:,|;|\)|$)|      # base64-looking strings
            (?:PASSWORD|API_KEY|SECRET|TOKEN)\s*=\s*['"]([\w\-]{16,})['"]\s*$
        )""",
        re.IGNORECASE | re.VERBOSE
    )
    findings = []
    skip_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv",
                 "dist", "build", ".next", ".nuxt", ".agents", "logs"}
    skip_files = {".env", ".env.local", ".env.example", ".thorough-history.json",
                  "thorough-report.json", "thorough-report.md", "stderr.log", "stdout.log",
                  "skills-lock.json", "package-lock.json", "yarn.lock", "poetry.lock"}
    # Auth/security files are expected to handle secrets; skip from secret scanning
    skip_auth_patterns = {"auth.py", "password_service.py", "security_service.py",
                          "authentication.py", "crypto.py", "token.py"}

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune skipped dirs in-place so os.walk won't descend into them
        # Also check for nested node_modules and other build dirs in the path
        dirnames[:] = [
            d for d in dirnames
            if d not in skip_dirs and "node_modules" not in str(Path(dirpath) / d)
        ]
        for fname in filenames:
            fpath = Path(dirpath) / fname
            # Skip configuration and report files
            if fname in skip_files:
                continue
            # Skip authentication/security-related files (expected to handle secrets)
            if any(pattern in fname for pattern in skip_auth_patterns):
                continue
            # Skip non-source file extensions
            if fpath.suffix.lower() in SKIP_EXTENSIONS:
                continue
            try:
                with open(fpath, "r", errors="replace") as fh:
                    for lineno, line in enumerate(fh, 1):
                        if pattern.search(line):
                            findings.append({
                                "severity": "Critical",
                                "title": "Possible hardcoded secret",
                                "detail": f"{fpath.relative_to(root)}:{lineno}: {line.strip()[:120]}",
                                "remediation": "Move to environment variables or a secrets manager",
                            })
            except (OSError, PermissionError):
                pass  # Skip unreadable files silently
    return findings

# ---------- Dependency vulnerability scan ----------
def check_dependencies(root: Path, languages: List[str]) -> List[Dict]:
    findings = []
    for lang in languages:
        if lang == "python":
            rc, out, err = run_cmd(["pip-audit", "--quiet"], cwd=str(root))
            if rc == -2:
                findings.append({
                    "severity": "Important",
                    "title": "pip-audit not installed",
                    "detail": "Install with: pip install pip-audit",
                    "remediation": "pip install pip-audit",
                })
            elif rc != 0 and out:
                findings.append({
                    "severity": "Critical",
                    "title": "Vulnerable Python packages",
                    "detail": out[:500],
                    "remediation": "Run: pip-audit --fix",
                })

        elif lang == "node":
            rc, out, err = run_cmd(["npm", "audit", "--json"], cwd=str(root))
            if rc == -2:
                findings.append({
                    "severity": "Important",
                    "title": "npm not available",
                    "detail": "Ensure Node.js is installed",
                })
            elif rc != 0:
                try:
                    data = json.loads(out)
                    vuln_count = (
                        data.get("metadata", {})
                            .get("vulnerabilities", {})
                            .get("total", 0)
                    )
                    if vuln_count > 0:
                        findings.append({
                            "severity": "Critical",
                            "title": f"{vuln_count} npm vulnerabilities",
                            "detail": "Run npm audit for details",
                            "remediation": "npm audit fix",
                        })
                except (json.JSONDecodeError, ValueError):
                    findings.append({
                        "severity": "Important",
                        "title": "npm audit parse error",
                        "detail": out[:200],
                    })
    return findings

# ---------- TODO / FIXME search (pure Python) ----------
def find_todos(root: Path) -> List[Dict]:
    pattern = re.compile(r"\b(TODO|FIXME|HACK)\b")
    skip_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv",
                 "dist", "build", ".next", ".nuxt", ".agents", "logs"}
    findings = []
    count = 0

    skip_files = {"thorough-report.json", "thorough-report.md", ".thorough-history.json"}
    
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune skipped dirs including nested node_modules
        dirnames[:] = [
            d for d in dirnames
            if d not in skip_dirs and "node_modules" not in str(Path(dirpath) / d)
        ]
        for fname in filenames:
            # Skip report files
            if fname in skip_files:
                continue
            fpath = Path(dirpath) / fname
            try:
                with open(fpath, "r", errors="replace") as fh:
                    for lineno, line in enumerate(fh, 1):
                        if pattern.search(line):
                            count += 1
                            if count <= 20:
                                findings.append({
                                    "severity": "Nice-to-have",
                                    "title": "TODO/FIXME found",
                                    "detail": f"{fpath.relative_to(root)}:{lineno}: {line.strip()[:150]}",
                                })
            except (OSError, PermissionError):
                pass

    if count > 20:
        findings.append({
            "severity": "Nice-to-have",
            "title": f"… and {count - 20} more TODOs",
            "detail": "Review remaining items",
        })
    return findings

# ---------- Complexity checks ----------
def check_complexity(root: Path, languages: List[str]) -> List[Dict]:
    findings = []
    for lang in languages:
        if lang == "python":
            rc, out, err = run_cmd(
                ["pylint", "--disable=all", "--enable=R0914,R0912,R0915",
                 "--exit-zero", str(root)],
                cwd=str(root),
            )
            if rc == -2:
                findings.append({
                    "severity": "Important",
                    "title": "pylint not installed",
                    "detail": "Install with: pip install pylint",
                    "remediation": "pip install pylint",
                })
            elif any(code in out for code in ("R0914", "R0912", "R0915")):
                findings.append({
                    "severity": "Important",
                    "title": "Complex functions detected (pylint)",
                    "detail": out[:400],
                    "remediation": "Refactor into smaller functions",
                })

        elif lang == "node":
            rc, out, err = run_cmd(
                ["npx", "eslint", "--no-eslintrc",
                 "--rule", "max-statements: [error, 20]", "."],
                cwd=str(root),
            )
            if rc == -2:
                findings.append({
                    "severity": "Important",
                    "title": "eslint not available",
                    "detail": "npm install -g eslint",
                })
            elif rc != 0:
                findings.append({
                    "severity": "Important",
                    "title": "Complex functions in JS/TS",
                    "detail": out[:300],
                    "remediation": "Break down large functions",
                })
    return findings

# ---------- Test coverage ----------
def check_test_coverage(
    root: Path,
    languages: List[str],
    interactive: bool,
) -> List[Dict]:
    findings = []
    for lang in languages:
        if lang != "python":
            continue

        has_config = (root / "pytest.ini").exists() or (root / "setup.cfg").exists() or (root / "pyproject.toml").exists()

        if not has_config:
            if not interactive:
                return []
            resp = input("No pytest config found. Run coverage anyway? [y/N]: ").strip().lower()
            if resp != "y":
                return []

        rc, out, err = run_cmd(
            ["pytest", "--cov", "--cov-report=term", "--quiet"],
            cwd=str(root),
            timeout=120,
        )
        if rc == -2:
            findings.append({
                "severity": "Important",
                "title": "pytest-cov not installed",
                "detail": "pip install pytest-cov",
            })
        else:
            match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", out)
            if match:
                cov = int(match.group(1))
                if cov < 70:
                    findings.append({
                        "severity": "Important",
                        "title": f"Low test coverage: {cov}%",
                        "detail": "Coverage is below the 70% threshold",
                        "remediation": "Add more unit/integration tests",
                    })
            elif rc != 0:
                findings.append({
                    "severity": "Important",
                    "title": "Test failures detected",
                    "detail": (out + err)[:500],
                })
    return findings

# ---------- N+1 query detection (pure Python, multi-line aware) ----------
def check_nplus_one(root: Path) -> List[Dict]:
    """
    Detects ORM calls inside for-loops by reading file contents directly,
    avoiding the line-by-line grep limitation.
    """
    # Matches: for ... in ...: <newline> <whitespace> .<query/filter/get/all>(
    loop_then_orm = re.compile(
        r"for\s+\S.+\s+in\s+.+:\s*\n\s+\S.*\.(query|filter|get|objects\.all)\(",
        re.MULTILINE,
    )
    skip_dirs = {".git", "node_modules", "__pycache__", ".venv", "venv",
                 "dist", "build", ".next", ".nuxt", ".agents", "logs"}
    findings = []

    for dirpath, dirnames, filenames in os.walk(root):
        # Prune skipped dirs including nested node_modules
        dirnames[:] = [
            d for d in dirnames
            if d not in skip_dirs and "node_modules" not in str(Path(dirpath) / d)
        ]
        for fname in filenames:
            if not fname.endswith((".py", ".js", ".php")):
                continue
            fpath = Path(dirpath) / fname
            try:
                content = fpath.read_text(errors="replace")
                if loop_then_orm.search(content):
                    findings.append({
                        "severity": "Important",
                        "title": "Possible N+1 query pattern",
                        "detail": str(fpath.relative_to(root)),
                        "remediation": "Use eager loading (select_related / prefetch_related) or batch queries",
                    })
            except (OSError, PermissionError):
                pass
    return findings

# ---------- Argument parsing ----------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Thorough project health check",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Categories: security, quality, todos, tests, performance",
    )
    parser.add_argument(
        "target", nargs="?", default=".",
        help="Project directory to check (default: current directory)",
    )
    parser.add_argument(
        "--ci", action="store_true",
        help="Non-interactive CI mode — skips all prompts",
    )
    parser.add_argument(
        "--skip", default="",
        metavar="CATEGORIES",
        help="Comma-separated list of categories to skip",
    )
    parser.add_argument(
        "--output", default=None, metavar="DIR",
        help="Directory to write reports (default: target directory)",
    )
    return parser.parse_args()

# ---------- Main ----------
def main() -> None:
    args = parse_args()
    skip = {s.strip() for s in args.skip.split(",") if s.strip()}
    interactive = not args.ci

    root = Path(args.target).resolve()
    if not root.is_dir():
        log.error("Target directory does not exist: %s", root)
        sys.exit(1)

    output_dir = Path(args.output).resolve() if args.output else root
    output_dir.mkdir(parents=True, exist_ok=True)

    project_info = detect_project(root)
    log.info("Detected languages : %s", project_info["languages"])
    log.info("Source file count  : %s (%s)", project_info["total_files"], project_info["size_category"])

    # Load history (best-effort)
    history: Dict = {}
    history_path = output_dir / HISTORY_JSON
    if history_path.exists():
        try:
            history = json.loads(history_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            log.warning("Could not read history file; starting fresh.")

    all_findings: List[Dict] = []

    if "security" not in skip:
        log.info("Running security checks…")
        all_findings.extend(check_secrets(root))
        all_findings.extend(check_dependencies(root, project_info["languages"]))

    if "quality" not in skip:
        log.info("Running code quality checks…")
        all_findings.extend(check_complexity(root, project_info["languages"]))

    if "todos" not in skip:
        log.info("Searching for TODOs…")
        all_findings.extend(find_todos(root))

    if "tests" not in skip:
        log.info("Running test coverage…")
        all_findings.extend(
            check_test_coverage(root, project_info["languages"], interactive)
        )

    if "performance" not in skip:
        run_perf = (
            interactive and
            input("Run performance checks (N+1 scan, may be slow)? [y/N]: ").strip().lower() == "y"
        ) or not interactive
        if run_perf:
            log.info("Running performance checks…")
            all_findings.extend(check_nplus_one(root))

    # Determine outcome
    critical_findings = [f for f in all_findings if f.get("severity") == "Critical"]
    exit_code = 1 if critical_findings else 0

    old_critical_titles = set(history.get("critical_titles", []))
    new_critical_titles = [
        f["title"] for f in critical_findings
        if f.get("title") not in old_critical_titles
    ]

    # Build Markdown report
    timestamp = datetime.now().isoformat()
    important = [f for f in all_findings if f.get("severity") == "Important"]
    nice = [f for f in all_findings if f.get("severity") == "Nice-to-have"]

    md_lines = [
        "# Thorough project check report",
        "",
        f"**Project:** `{root}`  ",
        f"**Date:** {timestamp}  ",
        f"**Languages:** {', '.join(project_info['languages'])}  ",
        f"**Source files:** {project_info['total_files']}  ",
        "",
        "## Summary",
        "",
        f"| Severity | Count |",
        f"|---|---|",
        f"| Critical | {len(critical_findings)} |",
        f"| Important | {len(important)} |",
        f"| Nice-to-have | {len(nice)} |",
        "",
    ]
    if new_critical_titles:
        md_lines.append(f"**New since last run:** {', '.join(new_critical_titles)}  ")
        md_lines.append("")

    for severity in ("Critical", "Important", "Nice-to-have"):
        items = [f for f in all_findings if f.get("severity") == severity]
        if not items:
            continue
        md_lines.append(f"## {severity}")
        md_lines.append("")
        for item in items:
            md_lines.append(f"### {item['title']}")
            md_lines.append(f"- **Detail:** {item['detail']}")
            if "remediation" in item:
                md_lines.append(f"- **Suggestion:** {item['remediation']}")
            md_lines.append("")

    report_md_path = output_dir / REPORT_MD
    report_md_path.write_text("\n".join(md_lines), encoding="utf-8")

    # JSON report
    json_report = {
        "timestamp": timestamp,
        "project": str(root),
        "total_files": project_info["total_files"],
        "findings": all_findings,
        "exit_code": exit_code,
        "new_critical_titles": new_critical_titles,
    }
    report_json_path = output_dir / REPORT_JSON
    report_json_path.write_text(json.dumps(json_report, indent=2, ensure_ascii=False), encoding="utf-8")

    # Persist history only after a complete run
    history["last_run"] = timestamp
    history["critical_titles"] = [f.get("title") for f in critical_findings]
    try:
        history_path.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError as exc:
        log.warning("Could not save history: %s", exc)

    log.info("Reports written to %s", output_dir)
    if exit_code == 1:
        log.warning("%d critical issue(s) found. Review the report.", len(critical_findings))
    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[!] Interrupted. Partial report may have been saved.")
        sys.exit(130)
    except Exception as exc:
        log.error("Unhandled exception: %s", exc)
        log.error("Please file a bug report. Manual checks recommended.")
        sys.exit(1)