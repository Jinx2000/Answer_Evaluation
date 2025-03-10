# Remember ```pip install ragas```

import json, os
import sys
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall, answer_correctness
from datasets import Dataset
import faulthandler
faulthandler.enable()

API_KEY= "Put your api key here"

os.environ["http_proxy"] = "http://localhost:7890"
os.environ["https_proxy"] = "http://localhost:7890"
os.environ["OPENAI_API_KEY"] = API_KEY

# Input JSON file from previous step
json_filename = "processed_data.json"
# Output JSON file
output_filename = "ragas_scores.json"

# Load processed JSON data
with open(json_filename, "r", encoding="utf-8") as jsonfile:
    data = json.load(jsonfile)

# Determine evaluation mode
use_reference = not (len(sys.argv) > 1 and sys.argv[1].lower() == "evaluateragonly")

# Extract required fields for evaluation
questions = [item["question"] for item in data]
retrieved_contexts = [item["retrieved_contexts"] for item in data]  # Already an array of strings
generated_responses = [item["generated_response"] for item in data]
gpt_response = [item["gpt_Generated_Response_withoutRAG"] for item in data]

if use_reference:
    reference_answers = [item["reference_answer"] if item["reference_answer"] else "" for item in data]
    print("Running RAGAS with reference answers...")
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
        llm="gpt-4o-mini"
    )

else:
    print("Running RAGAS without reference answers...")
    metrics = [faithfulness, answer_relevancy, context_precision, context_recall]  # No `answer_correctness`
    scores = evaluate(
        questions=questions,
        generated_responses=generated_responses,
        retrieved_contexts=retrieved_contexts,
        reference_answers=None,
        metrics=metrics,
        llm="gpt-4o-mini"
    )


# Convert scores to a dictionary format
scored_data = []
for i in range(len(data)):
    entry = {
        "question": data[i]["question"],
        "retrieved_contexts": data[i]["retrieved_contexts"],
        "generated_response": data[i]["generated_response"],
        "reference_answer": data[i]["reference_answer"],
        "faithfulness": scores["faithfulness"][i],
        "context_precision": scores["context_precision"][i],
        "context_recall": scores["context_recall"][i],
        "answer_relevancy": scores["answer_relevancy"][i],
    }
    if use_reference:
        entry["answer_correctness"] = scores["answer_correctness"][i]
    
    scored_data.append(entry)

# Save scores to JSON
with open(output_filename, "w", encoding="utf-8") as jsonfile:
    json.dump(scored_data, jsonfile, indent=4, ensure_ascii=False)

print(f"RAGAS scoring completed. Output saved to {output_filename}")

def compare_baseline():

    gpt_answers = [gpt_answer for gpt_answer in gpt_answers]
    reference_answers = [item["reference_answer"] if item["reference_answer"] else "" for item in data]

    # Fill it with None.
    contexts = [[] for _ in gpt_answers]  # 空上下文列表

    dataset = Dataset.from_dict({
        "question": questions,
        "answer": gpt_answers,
        "ground_truth": reference_answers,
        "contexts": contexts  # 即使无上下文也需保留字段
    })

    result = evaluate(dataset, metrics=[answer_correctness])
    print(result)