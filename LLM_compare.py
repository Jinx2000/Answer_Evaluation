import os
import openai
import pandas as pd

# Load API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# Function to get similarity reasoning from GPT-4 Turbo
def evaluate_generated_answer(text1, text2):
    """Evaluates the model-generated answer (Text 2) against the correct StackOverflow answer (Text 1),
    providing an accuracy score and reasoning for mistakes."""
    
    prompt = f"""
    <evaluation>
        <instructions>
            You are evaluating **our answer (Text 2)** against a **verified correct answer** from StackOverflow (Text 1).
            - **Correct Answer (Text 1)** is a StackOverflow response that accurately addresses a given problem.
            - **Our Answer (Text 2)** is the response we provided to the same problem.

            Your task:
            1. Compare **our answer (Text 2)** to **the correct answer (Text 1)** and evaluate **how accurately it replicates the correct information**.
            2. Identify **any errors, missing details, or misleading statements** in our answer.
            3. Assign an **accuracy score from 0 to 100**:
            - 100: Matches Text 1 perfectly in correctness and clarity.
            - 70-99: Mostly correct but has minor omissions or differences.
            - 40-69: Partially correct but missing key technical details.
            - 0-39: Mostly incorrect or misleading.
            4. Provide **reasoning** explaining:
            - What our answer got right.
            - What is incorrect or missing compared to the correct answer.
            - Any misleading or unclear parts.

            **Text 1 should always be treated as correct. Our answer (Text 2) should be evaluated solely on how well it aligns with Text 1.**
        </instructions>
        <correct_answer>{text1}</correct_answer>
        <our_answer>{text2}</our_answer>
        <response_format>
            <accuracy_score></accuracy_score>
            <reasoning></reasoning>
        </response_format>
    </evaluation>
    """

    response = openai.chat.completions.create(
        model="gpt-4-turbo",  # Use "gpt-3.5-turbo" if needed
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content


# Load CSV file
input_csv = "input_data.csv"  # Replace with your actual file
df = pd.read_csv(input_csv)

# Ensure required columns exist
if "StackOverflow Answer" not in df.columns or "Previous RAG Answer" not in df.columns:
    raise ValueError("CSV must contain 'StackOverflow Answer' and 'Previous RAG Answer' columns")

# Process each row
results = []
for index, row in df.iterrows():
    text1 = str(row["StackOverflow Answer"]).strip()  # Convert to string and remove whitespace
    text2 = str(row["Previous RAG Answer"]).strip()

    if not text1 or not text2:
        explanation = "Similarity Score: N/A\nReasoning: Missing Data"
    else:
        explanation = evaluate_generated_answer(text1, text2)

    results.append({"ID": row["ID"], "LLM Method Result": explanation})

# Save results to CSV
output_csv = "LLM_comparison_results.csv"
output_df = pd.DataFrame(results)
output_df.to_csv(output_csv, index=False)

print(f"Comparison completed. Results saved to {output_csv}")
