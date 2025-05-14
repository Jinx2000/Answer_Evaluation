# evaluator.py

import json
import os

from . import extract_yaml_from_response, validate_yaml_kube_tools
from .  import validate_cli_command
from . import evaluate_explanation_entry  # from the drop‑in solution

def evaluate_entry(entry: dict) -> dict:
    """
    Takes one `entry` dict (with keys question, generated_response, etc.)
    and returns that dict augmented with evaluation fields.
    """
    category = entry.get("output_category", "Explanation")
    response = entry.get("generated_response", "")

    # 1) YAML gating
    if category == "YAML":
        yaml_text = extract_yaml_from_response(response)
        yaml_res  = validate_yaml_kube_tools(yaml_text)
        entry.update(yaml_res)
        # If dry‑run fails, skip deeper evaluation:
        if not yaml_res["dry_run"]["pass"]:
            entry["auto_pass"] = False
            return entry

    # 2) CLI gating
    elif category == "CLI":
        cli_res = validate_cli_command(response)
        entry.update(cli_res)
        # If syntax fails, skip deeper evaluation:
        if not cli_res.get("cli_syntax_pass", False):
            entry["auto_pass"] = False
            return entry

    # 3) Explanation (and Mixed) — run your assertion+NLI checker
    #    You could also merge RAGAS here if desired
    #    Make sure `entry` already contains `assertions: [...]`
    entry = evaluate_explanation_entry(entry)

    return entry


def evaluate_all(input_path: str, output_path: str):
    # Load your pre‑processed JSON (with assertions & output_category)
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Run each entry through the evaluator
    results = []
    for entry in data:
        evaluated = evaluate_entry(entry)
        results.append(evaluated)

    # Write out augmented results
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"✅ Wrote {len(results)} evaluated entries to {output_path}")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--input",  "-i", required=True, help="Processed JSON input path")
    p.add_argument("--output", "-o", required=True, help="Where to save evaluated JSON")
    args = p.parse_args()
    evaluate_all(args.input, args.output)
