# Remember ```pip install ragas```
import json, os, csv
from datasets import Dataset
from ragas import evaluate
import faulthandler
faulthandler.enable()

# API_KEY= "API"

os.environ["http_proxy"] = "http://localhost:7890"
os.environ["https_proxy"] = "http://localhost:7890"
# os.environ["OPENAI_API_KEY"] = API_KEY
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")


def accuracy_score_byLLM():
    pass

def score_rag(json_filename, output_filename):
    # Load processed JSON data
    with open(json_filename, "r", encoding="utf-8") as jsonfile:
        data = json.load(jsonfile)

    # 判断是否是 Baseline（如果所有 retrieved_contexts 都是 []，则为 Baseline）
    is_baseline = all(not item["retrieved_contexts"] for item in data)

    # Extract required fields for evaluation
    questions = [item["question"] for item in data]
    retrieved_contexts = [item["retrieved_contexts"] for item in data]  # Already an array of strings
    generated_responses = [item["generated_response"] for item in data]
    reference_answers = [item["reference_answer"] if item["reference_answer"] else "" for item in data]

    # 选择要计算的 Metrics
    if is_baseline:
        print(f"Detected Baseline (No retrieved_contexts): Running only Answer Relevancy & Answer Correctness for {json_filename}")
        metrics = [answer_relevancy, answer_correctness]  # Baseline 只跑这两个
    else:
        print(f"Running full RAGAS evaluation for {json_filename}")
        metrics = [faithfulness, answer_relevancy, context_precision, context_recall, answer_correctness]


    # RAGAS requires dataset:
    dataset = Dataset.from_dict({
        "question": questions,
        "generated_response": generated_responses,
        "retrieved_contexts": retrieved_contexts,
        "reference_answer": reference_answers
    })

    #RAGAS requires column map:
    column_map = {
        "question": "question",
        "response": "generated_response",  # mapping our column "generated_response" to what RAGAS expects as "response"
        "retrieved_contexts": "retrieved_contexts",
        "reference": "reference_answer"
    }

    # Actual evaluation:
    scores = evaluate(
        dataset=dataset,
        metrics=metrics,
        column_map=column_map,
    )


    # Convert scores to a dictionary format
    scored_data = []
    for i in range(len(data)):
        entry = {
            "question": data[i]["question"],
            "retrieved_contexts": data[i]["retrieved_contexts"],
            "generated_response": data[i]["generated_response"],
            "reference_answer": data[i]["reference_answer"],
            "faithfulness": scores["faithfulness"][i] if not is_baseline else 0.0, # 如果是baseline直接输出0.0
            "context_precision": scores["context_precision"][i] if not is_baseline else 0.0,
            "context_recall": scores["context_recall"][i] if not is_baseline else 0.0,
            "answer_relevancy": scores["answer_relevancy"][i],
            "answer_correctness": scores["answer_correctness"][i]
        }
        scored_data.append(entry)

    # Save scores to JSON
    with open(output_filename, "w", encoding="utf-8") as jsonfile:
        json.dump(scored_data, jsonfile, indent=4, ensure_ascii=False)

    print(f"RAGAS scoring completed. Output saved to {output_filename}")


if __name__ == "__main__":

    score_rag("test_131processed_data.json", "test_131_ragas_scores.json")
