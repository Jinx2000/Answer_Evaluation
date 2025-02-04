import os
import openai
import pandas as pd

openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_key_points_from_text1(text1):
    prompt = f"""
    You are an expert summarizer. You have a 'verified correct answer' (Text 1).
    Extract and summarize only the key points essential for solving the problem. Focus on actionable steps and necessary configurations.
    Ignore minor details, background information, or explanations that do not affect the final outcome. Ensure extracted points are concise and complete.
    - **Format the output as a numbered list**, like this:

    ### **Key Points:**
    1. ...
    2. ...
    3. ...
    
    Text 1:
    {text1}
    """
    response = openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    return response.choices[0].message.content.strip()

def evaluate_generated_answer(text1, text2, key_points):


    prompt = f"""
    <evaluation>
        <instructions>
            You are evaluating **an alternate answer (Text 2)** against a **verified correct answer** (Text 1).
            **Text 1** should always be treated as definitively correct.
            If Text 2 differs but achieves the same result for user, treat it as correct. (e.g. nginx.ingress.kubernetes.io/app-root and rewrite-target)
            Use Key points from text 1 to help. Check if Text 2 covers these key points (or offers a valid alternative).
            
            1. Key Points from Text 1:
            {key_points}

            2. Assign an accuracy score (0-100):
            - 100: Matches Text 1 perfectly.
            - 70-99: Mostly correct, minor omissions.
            - 40-69: Partially correct, missing key details.
            - 0-39: Mostly incorrect or misleading.

            3. Provide reasoning:
            - What Text 2 got right.
            - Any missing/incorrect key points.
            - Any misleading statements.
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
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    return response.choices[0].message.content

# Load CSV file
input_csv = "input_data.csv"
df = pd.read_csv(input_csv)

results = []
for index, row in df.iterrows():
    text1 = str(row["StackOverflow Answer"]).strip()
    text2 = str(row["Previous RAG Answer"]).strip()

    if not text1 or not text2:
        key_points = "N/A"
        explanation = "Similarity Score: N/A\nReasoning: Missing Data"
    else:
        key_points = extract_key_points_from_text1(text1)
        explanation = evaluate_generated_answer(text1, text2, key_points)

    results.append({"ID": row["ID"], "Key Points:": key_points, "LLM Method Result": explanation})
    print(f"Finished ID {row['ID']}")
output_csv = "LLM_keypoint_results.csv"
pd.DataFrame(results).to_csv(output_csv, index=False)

print(f"Comparison completed. Results saved to {output_csv}")
