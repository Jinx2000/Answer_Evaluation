import shlex
import subprocess

def validate_cli_command(command: str):
    result = {
        "cli_syntax_pass": False,
        "dry_run_pass": None,
        "syntax_error": None,
        "dry_run_error": None
    }
    # 1) Syntax check
    try:
        parts = shlex.split(command)
        result["cli_syntax_pass"] = True
    except Exception as e:
        result["syntax_error"] = str(e)
        return result

    # 2) If it's a kubectl apply, do a server‐side dry‑run
    if parts[0] == "kubectl" and "apply" in parts:
        # Insert or override --dry-run=server
        # Build the dry-run command
        dry_parts = []
        skip_next = False
        for i, p in enumerate(parts):
            if skip_next:
                skip_next = False
                continue
            # Drop any existing --dry-run or dry-run flags
            if p.startswith("--dry-run"):
                continue
            # If -o yaml or similar, you might drop or keep it
            dry_parts.append(p)
        # Ensure server dry‑run
        dry_parts.append("--dry-run=server")

        try:
            proc = subprocess.run(
                dry_parts,
                capture_output=True,
                text=True,
                check=False  # we want to inspect returncode
            )
            if proc.returncode == 0:
                result["dry_run_pass"] = True
            else:
                result["dry_run_pass"] = False
                result["dry_run_error"] = proc.stderr or proc.stdout
        except Exception as e:
            result["dry_run_pass"] = False
            result["dry_run_error"] = str(e)

    return result
