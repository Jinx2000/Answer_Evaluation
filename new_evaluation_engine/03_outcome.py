import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from ace_tools import display_dataframe_to_user

# Load evaluated data
input_path = 'evaluated/newKD_test_evaluated.json'
with open(input_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Normalize to DataFrame
df = pd.json_normalize(data)

# Display summary DataFrame
summary = []
for category, group in df.groupby('output_category'):
    total = len(group)
    yaml_pass_rate = group.get('dry_run.pass', pd.Series([])).sum() / total if 'dry_run.pass' in group else np.nan
    cli_pass_rate  = group.get('cli_syntax_pass', pd.Series([])).sum() / total if 'cli_syntax_pass' in group else np.nan
    expl_pass_rate = group.get('auto_pass', pd.Series([])).sum() / total if 'auto_pass' in group else np.nan

    summary.append({
        'Category': category,
        'Total': total,
        'YAML Pass Rate': yaml_pass_rate,
        'CLI Pass Rate': cli_pass_rate,
        'Explanation Auto-Pass Rate': expl_pass_rate,
        'Mean Fact Coverage': group.get('fact_coverage', pd.Series([])).mean(),
        'Mean Entailment Coverage': group.get('entailment_coverage', pd.Series([])).mean(),
        'Mean Accuracy Score': group.get('accuracy_score', pd.Series([])).mean(),
    })

summary_df = pd.DataFrame(summary)
display_dataframe_to_user("Evaluation Summary", summary_df)

# Distribution plots for explanation metrics
metrics = ['fact_coverage', 'entailment_coverage', 'accuracy_score']
bins = [0, 0.2, 0.4, 0.6, 0.8, 1]
bin_labels = ['0-0.2', '0.2-0.4', '0.4-0.6', '0.6-0.8', '0.8-1']

plt.figure(figsize=(10, 6))
x = np.arange(len(bin_labels))
bar_width = 0.25

for i, metric in enumerate(metrics):
    if metric in df:
        data_arr = df[metric].fillna(0).to_numpy()
        counts, _ = np.histogram(data_arr, bins=bins)
        bars = plt.bar(x + i * bar_width, counts, width=bar_width, label=metric)
        for bar in bars:
            plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                     int(bar.get_height()), ha='center', va='bottom', fontsize=8)

plt.xticks(x + bar_width, bin_labels)
plt.xlabel('Metric Value Intervals')
plt.ylabel('Count')
plt.title('Distribution of Explanation Metrics')
plt.legend()
os.makedirs('./graphs', exist_ok=True)
plt.savefig('./graphs/explanation_metric_distribution.png', dpi=300, bbox_inches='tight')

# Comparison of mean metrics per category
mean_metrics = df.groupby('output_category')[metrics].mean()

plt.figure(figsize=(10, 6))
categories = mean_metrics.index.tolist()
x = np.arange(len(categories))
bar_width = 0.2

for i, metric in enumerate(metrics):
    vals = mean_metrics[metric].to_numpy()
    bars = plt.bar(x + i * bar_width, vals, width=bar_width, label=metric)
    for bar in bars:
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height(),
                 f"{bar.get_height():.2f}", ha='center', va='bottom', fontsize=8)

plt.xticks(x + bar_width, categories)
plt.xlabel('Output Category')
plt.ylabel('Mean Metric Value')
plt.title('Mean Explanation Metrics by Category')
plt.legend()
plt.savefig('./graphs/explanation_metrics_by_category.png', dpi=300, bbox_inches='tight')
