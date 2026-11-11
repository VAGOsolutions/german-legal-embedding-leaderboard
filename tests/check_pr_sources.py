"""Check for pull requests from forks (runs in .github/workflows/validate-results.yml, not via pytest).

External pull requests may only add or change submissions: every changed file under results/ must carry
`"source": "submission"` before (if it existed) and after. Otherwise a PR could label its file as a VAGO
measurement ("vago") or MTEB score ("mteb") to bypass the submission checks in tests/test_results.py, or modify
existing entries. Deleting files is not allowed either.

Usage: python tests/check_pr_sources.py <base-ref>   (e.g. origin/main)
"""
import json
import subprocess
import sys


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def source_at(ref: str, path: str):
    try:
        return json.loads(git("show", f"{ref}:{path}")).get("source")
    except subprocess.CalledProcessError:
        return None  # file does not exist at this ref


def main(base: str) -> int:
    errors = []
    diff = git("diff", "--name-status", f"{base}...HEAD", "--", "results/")
    for line in diff.splitlines():
        parts = line.split("\t")
        status, path = parts[0], parts[-1]
        if not path.endswith(".json"):
            continue
        if status.startswith("D"):
            errors.append(f"{path}: deleting files is not allowed in external pull requests")
            continue
        before = source_at(base, parts[1] if status.startswith("R") else path)
        after = source_at("HEAD", path)
        if after != "submission":
            errors.append(f"{path}: source = {after!r}, only 'submission' is allowed")
        if before not in (None, "submission"):
            errors.append(f"{path}: existing entry (source = {before!r}) must not be changed")
    for e in errors:
        print("✗", e)
    print("OK" if not errors else f"{len(errors)} violation(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "origin/main"))
