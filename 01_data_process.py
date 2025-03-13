import csv
import json
import os

def get_file_names(directory):
    # 获取目录下的所有文件和文件夹
    all_items = os.listdir(directory)
    # 过滤出文件（排除文件夹）
    file_names = [item for item in all_items if os.path.isfile(os.path.join(directory, item))]
    return file_names



def data_process(csv_filename):
    # Input CSV file
    # csv_filename = "input_data.csv"

    # Output JSON file
    json_filename = csv_filename.split(".")[0] + "processed_data.json"
    csv_filename = "./dev_data/" + csv_filename

    print(csv_filename)

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
            retrieved_contexts = [
                row["gpt_Top_1_Context"].strip(),
                row["gpt_Top_2_Context"].strip(),
                row["gpt_Top_3_Context"].strip()
            ]
            # Filter out empty contexts (in case some are missing)
            retrieved_contexts = [context for context in retrieved_contexts if context]

            # Construct the JSON entry
            entry = {
                "question": question,
                "retrieved_contexts": retrieved_contexts,  # Now correctly formatted as a list
                "generated_response": row["gpt_Generated_Response"].strip(),
                "reference_answer": row["Answer Body"].strip() if row["Answer Body"].strip() else None,  # Set to None if empty
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
    
    for file in file_names:
        data_process(file)