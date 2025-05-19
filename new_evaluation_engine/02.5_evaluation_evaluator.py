# explanation_evaluator.py

import os
import re
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
import json
from typing import List

# ── Configuration ────────────────────────────────────────────────────────────────

# Point to your OpenAI key however you like

# Weights for blending rule vs. NLI signals
W_RULE = 0.4
W_NLI  = 0.6


# ── Rule‑Based Assertion Coverage ───────────────────────────────────────────────

def assertion_coverage(prediction: str, facts: List[str]) -> float:
    """
    Fraction of `facts` whose exact lowercase substring appears in prediction.
    """
    pred_low = prediction.lower()
    hits = sum(1 for fact in facts if fact.lower() in pred_low)
    return hits / len(facts) if facts else 0.0


# ── NLI‑Based Entailment Coverage ────────────────────────────────────────────────

def entailment_score(prediction: str, assertion: str) -> float:
    """
    Returns 1.0 if the LLM judges that `prediction` entails `assertion`, else 0.0.
    """
    prompt = f"""
You are a Kubernetes expert.  

Premise (model’s answer):
\"\"\"
{prediction}
\"\"\"

Hypothesis (assertion):
\"{assertion}\"

Question: Does the premise *entail* the hypothesis?
Reply with exactly “Yes.” or “No.” (without extra commentary).
"""
    resp = client.chat.completions.create(model="gpt-4",
    messages=[{"role":"user", "content": prompt}],
    temperature=0.0,
    max_tokens=3)
    reply = resp.choices[0].message.content.strip().lower()
    return 1.0 if reply.startswith("yes") else 0.0

def entailment_coverage(prediction: str, facts: List[str]) -> float:
    """
    Average entailment_score over all assertions.
    """
    if not facts:
        return 0.0
    scores = [entailment_score(prediction, f) for f in facts]
    return sum(scores) / len(scores)


# ── Combined Explanation Accuracy ───────────────────────────────────────────────

def explanation_accuracy(prediction: str, facts: List[str],
                         w_rule: float = W_RULE, w_nli: float = W_NLI) -> float:
    """
    Weighted blend of rule-based coverage and NLI entailment.
    """
    rule_cov = assertion_coverage(prediction, facts)
    nli_cov  = entailment_coverage(prediction, facts)
    return w_rule * rule_cov + w_nli * nli_cov


# ── Entry Evaluator ──────────────────────────────────────────────────────────────

def evaluate_explanation_entry(entry: dict) -> dict:
    """
    Mutates the entry dict with:
      - fact_coverage
      - entailment_coverage
      - accuracy_score
      - auto_pass (bool)
    """
    pred  = entry.get("generated_response", "")
    facts = entry.get("assertions", [])

    fc = assertion_coverage(pred, facts)
    ec = entailment_coverage(pred, facts)
    acc = explanation_accuracy(pred, facts)

    entry["fact_coverage"]      = round(fc,  3)
    entry["entailment_coverage"]= round(ec,  3)
    entry["accuracy_score"]     = round(acc, 3)
    entry["auto_pass"]          = acc >= 0.75

    return entry


# ── Example Batch Runner ────────────────────────────────────────────────────────

def evaluate_batch(input_json: str, output_json: str):
    """
    Loads a list of entries from `input_json`, runs evaluate_explanation_entry
    on each, and writes out the augmented list to `output_json`.
    """
    with open(input_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    for entry in data:
        # only evaluate explanations (you can guard by entry["output_category"])
        entry = evaluate_explanation_entry(entry)

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"→ Wrote evaluated entries to {output_json}")


# ── CLI Hook ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Evaluate explanation entries")
    p.add_argument("--input",  "-i", required=True, help="Processed JSON with assertions")
    p.add_argument("--output", "-o", required=True, help="Where to write evaluated JSON")
    args = p.parse_args()
    evaluate_batch(args.input, args.output)
