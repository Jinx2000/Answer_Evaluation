import json, os, re, subprocess, shlex
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
    answer_correctness,
)

# Optional proxy and API key setup (comment out if not needed)
os.environ["http_proxy"] = "http://localhost:7890"
os.environ["https_proxy"] = "http://localhost:7890"
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


def run_subprocess(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return result.returncode, result.stdout, result.stderr


def evaluate_yaml(yaml_str: str, tmp_namespace="default"):
    import tempfile

    with tempfile.NamedTemporaryFile(mode='w+', suffix='.yaml', delete=False) as f:
        f.write(yaml_str)
        f.flush()
        filepath = f.name

        schema_code, _, schema_err = run_subprocess(["kubeconform", "-summary", filepath])
        schema_pass = schema_code == 0

        score_code, score_out, _ = run_subprocess(["kube-score", "score", filepath])
        has_critical = "CRITICAL" in score_out
        score_pass = not has_critical

        dryrun_code, _, dryrun_err = run_subprocess(
            ["kubectl", "apply", "--dry-run=server", "-f", filepath, "-n", tmp_namespace]
        )
        dryrun_pass = dryrun_code == 0

    return {
        "SchemaValidation": {"Pass": schema_pass, "Error": schema_err if not schema_pass else None},
        "KubeScore": {"Pass": score_pass, "Summary": score_out if not score_pass else None},
        "DryRun": {"Pass": dryrun_pass, "Error": dryrun_err if not dryrun_pass else None},
    }


def is_cli_valid(cli_str: str) -> bool:
    try:
        shlex.split(cli_str)
        return True
    except Exception:
        return False


def run_ragas(data, is_baseline):
    dataset = Dataset.from_dict({
        "question": [d["question"] for d in data],
        "generated_response": [d["generated_response"] for d in data],
        "retrieved_contexts": [d["retrieved_contexts"] for d in data],
        "reference_answer": [d["reference_answer"] or "" for d in data],
    })

    metrics = [answer_relevancy, answer_correctness] if is_baseline else [
        faithfulness, answer_relevancy, context_precision, context_recall, answer_correctness
    ]

    column_map = {
        "question": "question",
        "response": "generated_response",
        "retrieved_contexts": "retrieved_contexts",
        "reference": "reference_answer"
    }

    return evaluate(dataset=dataset, metrics=metrics, column_map=column_map)


def evaluate_all(json_filename, output_filename):
    with open(json_filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    # RAGAS will only be applied to Explanation and CLI
    ragas_input = [d for d in data if d["output_category"] in {"Explanation", "CLI"}]
    is_baseline = all(not d["retrieved_contexts"] for d in ragas_input)
    ragas_scores = run_ragas(ragas_input, is_baseline)

    # Track index so we apply RAGAS results only to those examples
    ragas_index = 0
    final_data = []

    for item in data:
        category = item["output_category"]
        result = dict(item)  # copy original

        if category == "YAML":
            result.update(evaluate_yaml(item["generated_response"]))

        elif category == "CLI":
            result["CLI_Syntax_Valid"] = is_cli_valid(item["generated_response"])
            # RAGAS optional here
            if ragas_index < len(ragas_input):
                result.update({
                    "faithfulness": ragas_scores["faithfulness"][ragas_index] if not is_baseline else 0.0,
                    "context_precision": ragas_scores["context_precision"][ragas_index] if not is_baseline else 0.0,
                    "context_recall": ragas_scores["context_recall"][ragas_index] if not is_baseline else 0.0,
                    "answer_relevancy": ragas_scores["answer_relevancy"][ragas_index],
                    "answer_correctness": ragas_scores["answer_correctness"][ragas_index],
                })
                ragas_index += 1

        elif category == "Explanation":
            result.update({
                "faithfulness": ragas_scores["faithfulness"][ragas_index] if not is_baseline else 0.0,
                "context_precision": ragas_scores["context_precision"][ragas_index] if not is_baseline else 0.0,
                "context_recall": ragas_scores["context_recall"][ragas_index] if not is_baseline else 0.0,
                "answer_relevancy": ragas_scores["answer_relevancy"][ragas_index],
                "answer_correctness": ragas_scores["answer_correctness"][ragas_index],
            })
            ragas_index += 1

        final_data.append(result)

    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(final_data, f, indent=4, ensure_ascii=False)

    print(f"✅ Evaluation complete. Output written to: {output_filename}")


if __name__ == "__main__":
    input_file = "newKD_testprocessed_data.json"
    output_file = "newKD_test_evaluated.json"
    evaluate_all(input_file, output_file)
