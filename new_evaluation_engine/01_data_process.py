import csv
import json
import os, re

def get_file_names(directory):
    # 获取目录下的所有文件和文件夹
    all_items = os.listdir(directory)
    # 过滤出文件（排除文件夹）
    file_names = [item for item in all_items if os.path.isfile(os.path.join(directory, item))]
    return file_names

def categorize_response(response: str) -> str:
    if re.search(r"(?m)^```(?:yaml)?\s*\n", response) or (
       "apiVersion:" in response and "kind:" in response):
        return "YAML"

    # Detect CLI commands next
    if re.search(r"\b(kubectl|helm|docker)\b", response):
        return "CLI"

    # Otherwise it’s free-text
    return "Explanation"

# def categorize_response(response: str) -> str:
#     # 1) Find fenced blocks
#     fences = re.findall(r"```(?:yaml)?\n(.*?)```", response, flags=re.DOTALL)
#     if fences:
#         # Count code vs. text in the first fence
#         code_lines = sum(1 for line in fences[0].splitlines() if ":" in line)
#         total_lines = len(fences[0].splitlines())
#         if code_lines / max(total_lines,1) > 0.5:
#             return "YAML"
#         else:
#             return "YAML"

#     # 2) Fallback to multi‑line key:value detection
#     kv_lines = re.findall(r"^[ \t]*[A-Za-z0-9_-]+:\s+.*$", response, flags=re.MULTILINE)
#     if len(kv_lines) >= 3:
#         return "YAML"

#     # 3) CLI detection
#     if (
#         re.search(r"(?m)^(?:\$|>)\s*\S+", response) or
#         re.search(r"\b(?:kubectl|helm|docker|git|aws|oc)\s+\S+", response) or
#         re.search(r"\s&&\s|\s\|\s", response)
#     ):
#         return "CLI"

#     # 4) Everything else
#     return "Explanation"



def data_process(csv_filename):
    # Input CSV file
    # csv_filename = "input_data.csv"

    # This will output it into a new directory, what we're doing right now is way too convoluted 
    output_dir = "./processed_data"
    os.makedirs(output_dir, exist_ok=True)
    json_filename = os.path.join(output_dir, csv_filename.split("/")[-1].replace(".csv", "_processed.json"))
    csv_filename = "./dev_data/" + csv_filename

    print(f"Processing: {csv_filename}")

    # 判断是否为 Baseline（test_0.csv）
    is_baseline = re.search(r'test_0\.csv$', csv_filename) is not None  # 如果文件名是 `test_0.csv`，则是 Baseline

    # Read CSV and convert to JSON format
    data = []

    with open(csv_filename, "r", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            # Process the question by combining title and body
            question_title = row["Question Title"].strip()
            question_body = row["Question Body"].strip()
            
            if question_body:
                question = f"{question_title} - {question_body}"
            else:
                question = question_title  # Use title only if body is empty

            # Ensure retrieved contexts are formatted as an array of strings
            if is_baseline:
                retrieved_contexts = []  # Baseline（test_0）没有 retrieved_contexts
            else: 
                retrieved_contexts = [
                    row["gpt_Top_1_Context"].strip(),
                    row["gpt_Top_2_Context"].strip(),
                    row["gpt_Top_3_Context"].strip()
                ]
                # Filter out empty contexts (in case some are missing)
                retrieved_contexts = [context for context in retrieved_contexts if context]

            # Construct the JSON entry
            generated_response = row["gpt_Refined_Response"].strip()
            reference_answer = row["Answer Body"].strip() if row["Answer Body"].strip() else None
            entry = {
                "question": question,
                "retrieved_contexts": retrieved_contexts,  # Now correctly formatted as a list
                "generated_response": generated_response,
                "reference_answer": reference_answer,  # Set to None if empty
                "output_category": categorize_response(generated_response),
            }
            
            data.append(entry)


    # Save to JSON file
    with open(json_filename, "w", encoding="utf-8") as jsonfile:
        json.dump(data, jsonfile, indent=4, ensure_ascii=False)

    print(f"01 Data processing completed. Output saved to {json_filename}")


if __name__ == "__main__":
    directory_path = './dev_data'  # 替换为你的目标目录路径
    file_names = get_file_names(directory_path)
    print(file_names)
    
    # 只处理 test_13.csv
    test_14_file = "test_verification_results_v1.csv"
    
    if test_14_file in file_names:
        print(f"Processing only {test_14_file}...")
        data_process(test_14_file)
        
    # for file in file_names:
    #     data_process(file)
