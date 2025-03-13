# Remember ```pip install ragas```
import json, os, csv
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

def score_rag():
    # Load processed JSON data
    with open(json_filename, "r", encoding="utf-8") as jsonfile:
        data = json.load(jsonfile)

    # Extract required fields for evaluation
    questions = [item["question"] for item in data]
    retrieved_contexts = [item["retrieved_contexts"] for item in data]  # Already an array of strings
    generated_responses = [item["generated_response"] for item in data]
    gpt_response = [item["gpt_Generated_Response_withoutRAG"] for item in data]

    # if use_reference:
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
            "answer_correctness": scores["answer_correctness"][i]
        }
        scored_data.append(entry)

    # Save scores to JSON
    with open(output_filename, "w", encoding="utf-8") as jsonfile:
        json.dump(scored_data, jsonfile, indent=4, ensure_ascii=False)

    print(f"RAGAS scoring completed. Output saved to {output_filename}")


gpt_answer_file = "test.csv"
gpt_answer_score_file = "gpt_scores.json"

def score_baseline():

    with open(gpt_answer_file, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

    questions = [row["Question Body"] for row in reader]
    gpt_answers = [row["gpt_Generated_Response"] for row in reader]
    reference_answers = [row["gpt_Generated_Response"] if row["gpt_Generated_Response"] else "" for row in reader]

    # Fill it with None.
    contexts = [[] for _ in gpt_answers] 

    dataset = Dataset.from_dict({
        "question": questions,
        "answer": gpt_answers,
        "ground_truth": reference_answers,
        "contexts": contexts
    })

    print(questions)

    return

    scores = evaluate(dataset, metrics=[answer_correctness], llm="gpt-4o-mini")

    # Convert scores to a dictionary format
    scored_data = []
    for i in range(len(scores)):
        entry = {
            "question": questions[i],
            "retrieved_contexts": "",
            "generated_response": gpt_answers[i],
            "reference_answer": reference_answers[i],
            "answer_correctness": scores["answer_correctness"][i]
        }
        scored_data.append(entry)

    # Save scores to JSON
    with open(gpt_answer_score_file, "w", encoding="utf-8") as jsonfile:
        json.dump(scored_data, jsonfile, indent=4, ensure_ascii=False)

    print(f"RAGAS scoring completed. Output saved to {gpt_answer_score_file}")

if __name__ == "__main__":
    score_baseline()
    # score_rag()