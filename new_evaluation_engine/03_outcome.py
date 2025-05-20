import os, json
import numpy as np
import pandas as pd

# Load evaluated data
with open('evaluated/test_verification_results_v1_evaluated.json','r') as f:
    data = json.load(f)

# Normalize to DataFrame
df = pd.json_normalize(data)

# Compute average confidence per entry
def avg_conf(eval_list):
    if not isinstance(eval_list, list) or len(eval_list) == 0:
        return np.nan
    return np.mean([item.get("confidence", 0.0) for item in eval_list])

df['avg_confidence'] = df['hypotheses_evaluations'].apply(avg_conf)

# Generate summary table
summary = []
for category, group in df.groupby('output_category'):
    total = len(group)
    correctness_series = group['is_correct'].astype(float)
    summary.append({
        'Category':          category,
        'Total':             total,
        'Correctness Rate':  correctness_series.mean(),
        'Avg Confidence':    group['avg_confidence'].mean()
    })

summary_df = pd.DataFrame(summary)
print("\n=== Evaluation Summary ===")
print(summary_df.to_markdown(index=False))

# Export summary to CSV if you want
summary_df.to_csv("./graphs/evaluation_summary.csv", index=False)
