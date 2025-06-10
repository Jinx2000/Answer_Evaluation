#!/usr/bin/env python3
import os
import re
import json
import textwrap
from typing import Any, Dict, List, Optional, Set

import yaml

# ── Configuration ───────────────────────────────────────────────────────────────
PASS_THRESHOLD = {
    'yaml': 80.0,         # require 80% of fields (and no value mismatches)
    'cli': 80.0,          # require 80% of flags
    'explanation': 50.0   # require 50% of key names
}
SAMPLE_SIZE: Optional[int] = None  # set to 10 to test only first 10 entries

# Keys to ignore when comparing YAML fields
IGNORE_KEYS = {
    'metadata.creationTimestamp',
    'metadata.resourceVersion',
    'metadata.uid'
}

# Optional synonyms for explanation matching
SYNONYMS = {
    'svc': ['service'],
    'ingressclass': ['ingressClassName', 'ingressClass'],
    'pv': ['persistentVolume', 'persistentvolumeclaim'],
    # add more as needed
}


def extract_fields_and_values(
    obj: Any, base: str = '', paths: Dict[str, Any] = None
) -> Dict[str, Any]:
    if paths is None:
        paths = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            prefix = f'{base}.{k}' if base else k
            extract_fields_and_values(v, prefix, paths)
    elif isinstance(obj, list):
        for item in obj:
            prefix = f'{base}[*]'
            extract_fields_and_values(item, prefix, paths)
    else:
        if isinstance(obj, (str, int, float, bool)):
            paths[base] = obj
    return paths


def load_yaml_fields(yaml_text: str) -> Dict[str, Any]:
    # Strip fences and dedent
    yaml_text = re.sub(r'^```(?:yaml)?\s*|```\s*$', '', yaml_text.strip(), flags=re.MULTILINE)
    yaml_text = textwrap.dedent(yaml_text).strip()
    try:
        docs = yaml.safe_load_all(yaml_text)
        fields: Dict[str, Any] = {}
        for doc in docs:
            if doc is not None:
                fields.update(extract_fields_and_values(doc))
        return fields
    except yaml.YAMLError:
        # Fallback: only top-level keys
        keys = re.findall(r'^[ \t]*([A-Za-z0-9_-]+):', yaml_text, re.MULTILINE)
        return {k: None for k in set(keys)}


def extract_cli_flags(text: str) -> Set[str]:
    return set(re.findall(r'--[A-Za-z0-9\-]+(?:=[^\s]+)?', text))


def evaluate_entry(entry: Dict[str, Any]) -> Dict[str, Any]:
    reference = entry.get('reference_answer', '') or ''
    generated = entry.get('generated_response', '') or ''
    category = entry.get('output_category', 'explanation').lower()

    # 1) Build reference field map
    m_ref = re.search(r'```(?:yaml)?\s*\n(.*?)```', reference, re.DOTALL)
    ref_yaml = m_ref.group(1) if m_ref else reference
    ref_map = load_yaml_fields(ref_yaml)

    # Prune unwanted and deeply nested keys
    ref_keys = {
        k for k in ref_map.keys()
        if k not in IGNORE_KEYS and k.count('.') <= 2
    }

    result = {
        'coverage_percent': 0.0,
        'missing': [],
        'value_errors': [],
        'pass': False
    }

    if ref_keys:
        matched: Set[str]
        missing: List[str]
        value_errors: List[Dict[str, Any]] = []

        if category == 'yaml':
            # YAML branch
            m_gen = re.search(r'```(?:yaml)?\s*\n(.*?)```', generated, re.DOTALL)
            gen_yaml = m_gen.group(1) if m_gen else generated
            gen_map = load_yaml_fields(gen_yaml)

            # Prune gen_keys similarly
            gen_keys = {
                k for k in gen_map.keys()
                if k not in IGNORE_KEYS and k.count('.') <= 2
            }

            matched = ref_keys & gen_keys
            missing = sorted(ref_keys - gen_keys)

            for k in matched:
                if ref_map.get(k) != gen_map.get(k):
                    value_errors.append({
                        'key': k,
                        'expected': ref_map.get(k),
                        'got': gen_map.get(k)
                    })

        elif category == 'cli':
            # CLI branch
            ref_flags = extract_cli_flags(reference)
            gen_flags = extract_cli_flags(generated)

            if not ref_flags:
                # fallback to explanation
                category = 'explanation'
            else:
                matched = ref_flags & gen_flags
                missing = sorted(ref_flags - gen_flags)
                value_errors = []

        if category == 'explanation':
            # Explanation branch
            ref_names = {k.split('.')[-1] for k in ref_keys}
            matched = set()
            for name in ref_names:
                # check name or synonyms
                patterns = [name] + SYNONYMS.get(name.lower(), [])
                for pat in patterns:
                    if re.search(rf'\b{re.escape(pat)}\b', generated, re.IGNORECASE):
                        matched.add(name)
                        break
            missing = sorted(ref_names - matched)
            value_errors = []

        # Compute coverage and pass/fail
        coverage = 100.0 * len(matched) / len(ref_keys)
        threshold = PASS_THRESHOLD.get(category, PASS_THRESHOLD['explanation'])
        passed = coverage >= threshold
        # In YAML, require no value_errors
        if category == 'yaml' and value_errors:
            passed = False

        result.update({
            'coverage_percent': round(coverage, 1),
            'missing': missing,
            'value_errors': value_errors,
            'pass': passed
        })

    entry.update(result)
    return entry


def evaluate_all(input_path: str, output_path: str, debug_path: Optional[str] = None):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if SAMPLE_SIZE:
        data = data[:SAMPLE_SIZE]

    evaluated = []
    debug = []
    for ent in data:
        out = evaluate_entry(ent)
        evaluated.append(out)
        if not out['pass']:
            debug.append({
                'question': out.get('question'),
                'coverage_percent': out['coverage_percent'],
                'missing': out['missing'],
                'value_errors': out['value_errors']
            })

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(evaluated, f, indent=2)
    print(f"Evaluation results saved to {output_path}")

    if debug_path:
        os.makedirs(os.path.dirname(debug_path), exist_ok=True)
        with open(debug_path, 'w', encoding='utf-8') as f:
            json.dump(debug, f, indent=2)
        print(f"Debug output saved to {debug_path}")


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description='Field-based Kubernetes evaluator')
    p.add_argument('--input',  '-i', required=True, help='JSON input path')
    p.add_argument('--output', '-o', required=True, help='JSON evaluated output path')
    p.add_argument('--debug',  '-d', required=False, help='JSON debug output path')
    args = p.parse_args()
    evaluate_all(args.input, args.output, args.debug)
