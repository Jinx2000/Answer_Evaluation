import json
import asyncio
from ragas import SingleTurnSample
from ragas.metrics import (
    NonLLMStringSimilarity,
    BleuScore,
    RougeScore,
)

# Input JSON file from previous step
json_filename = "processed_data.json"
# Output JSON file
output_filename = "ragas_noLLM_scores.json"

# Load processed JSON data
with open(json_filename, "r", encoding="utf-8") as jsonfile:
    data = json.load(jsonfile)

# Initialize metrics
string_similarity_metric = NonLLMStringSimilarity()
bleu_metric = BleuScore()
rouge_metric = RougeScore()

async def evaluate_sample(item):
    """ Runs non-LLM text similarity metrics for a single sample. """
    response_sample = SingleTurnSample(
        response=item["generated_response"],
        reference=item["reference_answer"]
    )

    # parallel
    (
        string_similarity, 
        bleu_score, 
        rouge_score
    ) = await asyncio.gather(
        string_similarity_metric.single_turn_ascore(response_sample),
        bleu_metric.single_turn_ascore(response_sample),
        rouge_metric.single_turn_ascore(response_sample),
    )

    return {
        "question": item["question"],
        "retrieved_contexts": item["retrieved_contexts"],
        "generated_response": item["generated_response"],
        "reference_answer": item.get("reference_answer", ""),
        "nonllm_string_similarity": string_similarity,
        "bleu_score": bleu_score,
        "rouge_score": rouge_score,
    }

async def evaluate_samples():
    """ Runs all non-LLM text similarity evaluations asynchronously. """
    tasks = [evaluate_sample(item) for item in data]
    scored_data = await asyncio.gather(*tasks)

    # Save the scores to a JSON file
    with open(output_filename, "w", encoding="utf-8") as jsonfile:
        json.dump(scored_data, jsonfile, indent=4, ensure_ascii=False)

    print(f"Non-LLM text similarity evaluation completed. Output saved to {output_filename}")


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
loop.run_until_complete(evaluate_samples())
