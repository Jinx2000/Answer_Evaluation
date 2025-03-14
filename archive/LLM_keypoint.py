import os
import openai
import pandas as pd
import asyncio
import time
from bs4 import BeautifulSoup

# os.environ["http_proxy"] = "http://localhost:7890"
# os.environ["https_proxy"] = "http://localhost:7890"

openai.api_key = os.getenv("OPENAI_API_KEY")

input_csv = "input_data.csv"
# save keypoints in seperated files
keypoints_stack_csv = "keypoints_stack.csv"
keypoints_RAG_csv = "keypoints_RAG.csv"

#async to imporve speed:
async def extract_key_points_from_text(text):

    prompt = f"""
    You are an expert summarizer and familiar with Cloud-native. You will recieve a 'verified correct answer' (Text 1)which is a solution for some problems.
    The "Text 1" contains a description of solution and specific codes snippets. The description is usually a normal sentence, while the code consists of a series of words. Please try to distinguish them.
    Text 1 may provide multiple solutions. For each solution, you need to extract and summarize a key point. Each key point must include the most important and concise overview, and be accompanied by relevant code snippets at the end.
    While extracting key points, focus on actionable steps and necessary configurations. Ignore minor details, background information, or explanations that do not affect the final outcome. Ensure extracted points are concise and complete.
    - **Format the output as a numbered list**, like this:

    ### **Key Points:**
    1. ...
    2. ...

    For example:
        <Text 1>
        Create an Ingress rule with a app-root annotation:

        apiVersion: extensions/v1beta1
        kind: Ingress
        metadata:
        annotations:
            nginx.ingress.kubernetes.io/app-root: /app1
        name: approot
        namespace: default
        ...

        or can you create an Ingress rule with a rewrite annotation:

        apiVersion: extensions/v1beta1
        kind: Ingress
        metadata:
        annotations:
            nginx.ingress.kubernetes.io/rewrite-target: /$2
        name: rewrite
        namespace: default
        spec:
        rules:
        - host: rewrite.bar.com
            http:
            paths:
            - backend:
                serviceName: http-svc
                servicePort: 80
                path: /something(/|$)(.*)
        In this ingress definition, any characters captured by (.*) will be assigned to the placeholder $2, which is then used as a parameter in the rewrite-target annotation
        </Text 1>

        According to the description from Text 1, there are two solutions to solve the problem. So we have two key points.
        The first solution is creating a app-root annotation and the code snippet is "nginx.ingress.kubernetes.io/app-root: /app1".
        The second solution is creating a rewrite annotation and the code snippet is "nginx.ingress.kubernetes.io/rewrite-target: /$2".
        Thus the key points are:
        1. app-root filed in annotation, ```nginx.ingress.kubernetes.io/app-root: /app1```.
        2. rewrite filed in annotation, ```nginx.ingress.kubernetes.io/rewrite-target: /$2```.

    Text 1:
    {text}
    """

    for attempt in range(3):  # Retry up to 3 times
        try:
            response = await asyncio.to_thread(
                openai.chat.completions.create,  # Runs the blocking function in a thread
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            return response.choices[0].message.content.strip()  # Successful response
        except openai.RateLimitError:
            print(f"Rate limit error, retrying ({attempt+1}/3)...")
            time.sleep(2 ** attempt)  # Uses time.sleep() instead of async sleep
        except openai.OpenAIError as e:
            print(f"OpenAI API Error: {e}")
            return "API Error"

    return "API Error: Max retries exceeded."


# Check if we can reuse keypoints_stack.csv
def can_use_existing_keypoints(margin=10):
    if os.path.exists(keypoints_stack_csv):
        df_input = pd.read_csv(input_csv)
        df_stack = pd.read_csv(keypoints_stack_csv)

        # Check if the row count is within margin
        return abs(len(df_input) - len(df_stack)) <= margin
    return False

# Save key points extracted from CSV
async def save_keypoints():
    df = pd.read_csv(input_csv)
    
    key_points_list_1 = []
    key_points_list_2 = []

    if can_use_existing_keypoints(margin=10):
        print("Reusing existing keypoints_stack.csv")
        df_stack = pd.read_csv(keypoints_stack_csv)
        key_points_list_1 = df_stack["Key Points"].tolist()
    else:
        print("Extracting new key points for stack answers...")
        key_points_list_1 = await asyncio.gather(*[extract_key_points_from_text(str(row["Answer Body"]).strip()) for _, row in df.iterrows()])
        pd.DataFrame({"Key Points": key_points_list_1}).to_csv(keypoints_stack_csv, index=False)
    
    print("Extracting new key points for RAG answers...")
    key_points_list_2 = await asyncio.gather(*[extract_key_points_from_text(str(row["gpt_Generated_Response"]).strip()) for _, row in df.iterrows()])
    
    pd.DataFrame({"Key Points": key_points_list_2}).to_csv(keypoints_RAG_csv, index=False)
    print("Key point extraction completed.")


async def evaluate_generated_answer(text1, text2):
    prompt = f"""
    <evaluation>
        <instructions>
            You are an expert in Cloud-native. You are evaluating **an alternate answer (Text 2)** against a **verified correct answer** (Text 1).
            **Text 1** should always be treated as definitively correct.
            Each Text contains serveral key points. And each key points consists of a description and specific codes snippets. The description is usually a normal sentence, while the code consists of a series of words. Please try to distinguish them.
            You need to compare the key points in two texts. And score them according to the following rules. The scoring range is from 0 to 100.
            Rule 1: If any key point in Text 2 is similar to the key point in Text 1, give it a score of at least 60. On this basis, the more similar the two Text are, the higher the score.
            Rule 2: You should focus on code snippets comparison rather than description comparison. For the code snippet comparison part, as long as there are some key words that are the same between the two key points, we consider the key points to be similar.
            Rule 2: The final score is the sum of the scores for each key point(with a maximum of 100 points). You should give the final score in label <accuracy_score> below.

            2. Provide reasoning:
            - Show how many points the Text 2 receive in each of the two parts.
            - What Text 2 got right.
            - Any dissimilar key points.
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

    for attempt in range(3):  # Retry up to 3 times
        try:
            response = await asyncio.to_thread(
                openai.chat.completions.create,  # Runs the blocking function in a thread
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            return response.choices[0].message.content.strip()  # Successfully returns async result
        except openai.RateLimitError:
            print(f"⚠️ Rate limit error, retrying ({attempt+1}/3)...")
            await asyncio.sleep(2 ** attempt)  # Uses proper async wait
        except openai.OpenAIError as e:
            print(f"❌ OpenAI API Error: {e}")
            return "API Error"

    return "API Error: Max retries exceeded."


# Evaluate RAG results
async def evaluate_RAG_answer():
    df = pd.read_csv(input_csv)
    df_stack = pd.read_csv(keypoints_stack_csv)
    df_RAG = pd.read_csv(keypoints_RAG_csv)

    results = []
    
    tasks = []
    for index, row in df.iterrows():
        key_points_stack = str(df_stack["Key Points"][index]).strip()
        key_points_RAG = str(df_RAG["Key Points"][index]).strip()
        
        if not key_points_stack or not key_points_RAG:
            explanation = "Similarity Score: N/A\nReasoning: Missing Data"
            final_score = "N/A"
        else:
            tasks.append(evaluate_generated_answer(key_points_stack, key_points_RAG))

    explanations = await asyncio.gather(*tasks)

    for index, explanation in enumerate(explanations):
        explanation_soup = BeautifulSoup(explanation, 'html.parser')
        try:
            accuracy_score = int(explanation_soup.find("accuracy_score").contents[0])
            final_score = "Y" if accuracy_score >= 60 else "N"
        except:
            accuracy_score = "N/A"
            final_score = "N/A"

        results.append({
            "ID": df["Answer ID"][index],
            "Key Points": df_stack["Key Points"][index],
            "Answer": df["gpt_Generated_Response"][index],
            "RAG Key Points": df_RAG["Key Points"][index],
            "LLM Method Result": explanation,
            "Score": final_score
        })

    output_csv = "LLM_keypoint_results.csv"
    pd.DataFrame(results).to_csv(output_csv, index=False)
    print(f"Comparison completed. Results saved to {output_csv}")

# Run async functions
if __name__ == "__main__":
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(save_keypoints())
    loop.run_until_complete(evaluate_RAG_answer())