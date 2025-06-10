import os
import json
import pandas as pd

# Configuration 
EVALUATED_PATH = "evaluated/test_verification_results_v1_evaluated.json"
OUTPUT_SUMMARY_CSV = "./graphs/evaluation_summary.csv"

# Load and normalize 
with open(EVALUATED_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

df = pd.json_normalize(data)

# Ensure 'pass' is boolean and 'coverage_percent' numeric
df['pass'] = df['pass'].astype(bool)
df['coverage_percent'] = pd.to_numeric(df['coverage_percent'], errors='coerce')

# Build summary 
summary = []
for category, group in df.groupby('output_category'):
    total = len(group)
    pass_rate = group['pass'].mean() * 100               # percent of entries that passed
    avg_coverage = group['coverage_percent'].mean()      # average coverage %
    avg_missing = group['missing'].apply(len).mean()     # avg number of missing keys

    summary.append({
        'Category':         category,
        'Total':            total,
        'Pass Rate (%)':    round(pass_rate, 1),
        'Avg Coverage (%)': round(avg_coverage, 1),
        'Avg Missing Keys': round(avg_missing, 1)
    })

summary_df = pd.DataFrame(summary)

#  Output 
print("\n=== Evaluation Summary ===")
print(summary_df.to_markdown(index=False))

# Save to CSV
os.makedirs(os.path.dirname(OUTPUT_SUMMARY_CSV), exist_ok=True)
summary_df.to_csv(OUTPUT_SUMMARY_CSV, index=False)
print(f"\nSummary CSV saved to {OUTPUT_SUMMARY_CSV}")
