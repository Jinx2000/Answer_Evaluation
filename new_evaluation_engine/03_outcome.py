import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Load evaluated data
input_path = 'evaluated/test_verification_results_v1_evaluated.json'
with open(input_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Normalize to DataFrame
df = pd.json_normalize(data)

# Compute average confidence per entry
def avg_conf(eval_list):
    if not isinstance(eval_list, list) or len(eval_list) == 0:
        return np.nan
    return np.mean([item.get("confidence", 0.0) for item in eval_list])

df['avg_confidence'] = df.get('hypotheses_evaluations', []).apply(avg_conf)

# Generate summary table
summary = []
for category, group in df.groupby('output_category'):
    total = len(group)
    summary.append({
        'Category': category,
        'Total': total,
        'Correctness Rate (avg)': group.get('correctness_rate', pd.Series([])).mean(),
        'Avg Confidence': group.get('avg_confidence', pd.Series([])).mean()
    })

summary_df = pd.DataFrame(summary)
print("\n=== Evaluation Summary ===")
print(summary_df.to_markdown(index=False))

# Optionally export summary to CSV
summary_df.to_csv("./graphs/evaluation_summary.csv", index=False)

# You can now generate plots or export other stats as needed
