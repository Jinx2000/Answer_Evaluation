import csv
import json

# Input CSV file
csv_filename = "input_data.csv"
# Output JSON file
json_filename = "processed_data.json"

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
            "gpt_response": row["gpt_Generated_Response_withoutRAG"]
        }
        
        data.append(entry)

# Save to JSON file
with open(json_filename, "w", encoding="utf-8") as jsonfile:
    json.dump(data, jsonfile, indent=4, ensure_ascii=False)

print(f"01 Data processing completed. Output saved to {json_filename}")
