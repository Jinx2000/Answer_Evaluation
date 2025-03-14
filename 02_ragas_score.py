# Remember ```pip install ragas```
import json, os, csv
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall, answer_correctness
from datasets import Dataset
from ragas import evaluate
import faulthandler
faulthandler.enable()

API_KEY= "API"

os.environ["http_proxy"] = "http://localhost:7890"
os.environ["https_proxy"] = "http://localhost:7890"
os.environ["OPENAI_API_KEY"] = API_KEY


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

# 我已经include baseline as test_0.csv ... 然后所有baseline没办法完成的metric会变成0.0
# gpt_answer_file = "test.csv"
# gpt_answer_score_file = "gpt_scores.json"

# def score_baseline():

#     gpt_answers = list()
#     questions = list()
#     reference_answers = list()
#     contexts = list()

#     with open(gpt_answer_file, "r", encoding="utf-8") as csvfile:
#         reader = csv.DictReader(csvfile)
#         cnt = 0
#         for row in reader:
#             if cnt == 100:
#                 break
#             gpt_answers.append(row["gpt_Generated_Response"])
#             questions.append(row["Question Body"])
#             reference_answers.append(row["Answer Body"])
#             contexts.append([])

#             cnt += 1

#     dataset = Dataset.from_dict({
#         "question": questions,
#         "answer": gpt_answers,
#         "ground_truth": reference_answers,
#         "contexts": contexts
#     })

#     #RAGAS requires column map:
#     column_map = {
#         "question": "question",
#         "response": "answer",  # mapping our column "generated_response" to what RAGAS expects as "response"
#         "retrieved_contexts": "contexts",
#         "reference": "ground_truth"
#     }


#     scores = evaluate(dataset=dataset, metrics=[answer_correctness], column_map=column_map)

#     # Convert scores to a dictionary format
#     scored_data = []
#     for i in range(len(gpt_answers)):
#         entry = {
#             "question": questions[i],
#             "retrieved_contexts": "",
#             "generated_response": gpt_answers[i],
#             "reference_answer": reference_answers[i],
#             "answer_correctness": scores["answer_correctness"][i]
#         }
#         scored_data.append(entry)

#     # Save scores to JSON
#     with open(gpt_answer_score_file, "w", encoding="utf-8") as jsonfile:
#         json.dump(scored_data, jsonfile, indent=4, ensure_ascii=False)

#     print(f"RAGAS scoring completed. Output saved to {gpt_answer_score_file}")


if __name__ == "__main__":
    # score_baseline()
    # score_rag("test_3processed_data.json", "test_3_ragas_scores.json")
    # score_rag("test_4processed_data.json", "test_4_ragas_scores.json")
    # score_rag("test_5processed_data.json", "test_5_ragas_scores.json")
    # score_rag("test_5processed_data.json", "test_5_ragas_scores.json")
    # score_rag("test_6processed_data.json", "test_6_ragas_scores.json")
    # score_rag("test_7processed_data.json", "test_7_ragas_scores.json")
    # Baseline 评分
    score_rag("test_0processed_data.json", "test_0_ragas_scores.json")
