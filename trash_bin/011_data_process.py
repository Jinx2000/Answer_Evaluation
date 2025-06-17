import csv
import json
import os, re

def get_file_names(directory):
    # 获取目录下的所有文件和文件夹
    all_items = os.listdir(directory)
    # 过滤出文件（排除文件夹）
    file_names = [item for item in all_items if os.path.isfile(os.path.join(directory, item))]
    return file_names


def split_string(input_str):
    # 首先提取所有被```包裹的内容
    code_blocks = re.findall(r'```(.*?)```', input_str, re.DOTALL)
    
    # 移除所有```包裹的内容，以便后续处理
    remaining_text = re.sub(r'```.*?```', '', input_str, flags=re.DOTALL)
    
    # 移除###开头的行和其他Markdown非纯文本内容
    remaining_text = re.sub(r'^#+.*$', '', remaining_text, flags=re.MULTILINE)
    
    # 按句子分割剩余文本
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', remaining_text.strip())
    
    # 合并结果：首先是代码块，然后是句子
    result = []
    for block in code_blocks:
        # 去除代码块可能的前后空白和语言标识符
        clean_block = block.strip()
        if '\n' in clean_block:
            # 如果有换行，第一个是语言标识符
            lang, *content = clean_block.split('\n', 1)
            result.append(['\n'.join(content).strip()])
        else:
            result.append([clean_block])
    
    # 添加句子，过滤掉空字符串
    result.extend([sentence] for sentence in sentences if sentence.strip())
    
    return result

def data_process(csv_filename):
    # Input CSV file
    # csv_filename = "input_data.csv"

    # Output JSON file
    json_filename = csv_filename.split(".")[0] + "processed_data.json"
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
            entry = {
                "question": question,
                "retrieved_contexts": retrieved_contexts,  # Now correctly formatted as a list
                "generated_response": split_string(row["gpt_Refined_Response"].strip()),
                "reference_answer": split_string(row["Answer Body"].strip()) if row["Answer Body"].strip() else None,  # Set to None if empty
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
    test_13_file = "test_verification_results_v1.csv"
    
    if test_13_file in file_names:
        print(f"Processing only {test_13_file}...")
        data_process(test_13_file)
        
    # for file in file_names:
    #     data_process(file)
