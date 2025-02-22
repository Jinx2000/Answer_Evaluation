import os
import openai
import pandas as pd
from bs4 import BeautifulSoup

# os.environ["http_proxy"] = "http://localhost:7890"
# os.environ["https_proxy"] = "http://localhost:7890"

openai.api_key = os.getenv("OPENAI_API_KEY")

input_csv = "input_data.csv"

def extract_key_points_from_text1(text1):

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
    {text1}
    """
    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    return response.choices[0].message.content.strip()

def save_keypoints():

    """
    Save key points derived from post answer and RAG answer into the original file "input_data.csv".
    """
    key_points_list_1 = list()
    key_points_list_2 = list()
    df = pd.read_csv(input_csv)

    for index, row in df.iterrows():
        text1 = str(row["StackOverflow Answer"]).strip()
        text2 = str(row["Previous RAG Answer"]).strip()

        if not text1 or not text2:
            key_points_1 = "N/A"
            key_points_2 = "N/A"

        else:
            key_points_1 = extract_key_points_from_text1(text1)
            key_points_2 = extract_key_points_from_text1(text2)

        key_points_list_1.append(key_points_1)
        key_points_list_2.append(key_points_2)
        print(f"Finished ID {row['ID']}")

    df['Key Points'] = key_points_list_1
    df['Key Points_answer'] = key_points_list_2
    df.to_csv(input_csv, index=False)


def evaluate_generated_answer(text1, text2):

    
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

    response = openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    return response.choices[0].message.content


def evaluate_RAG_answer():
    df = pd.read_csv(input_csv)

    results = []
    for index, row in df.iterrows():
        key_points = str(row["Key Points"]).strip()
        key_points_RAG = str(row["Key Points_answer"]).strip()

        if not key_points or not key_points_RAG:
            # key_points = "N/A"
            explanation = "Similarity Score: N/A\nReasoning: Missing Data"
        else:
            # key_points = extract_key_points_from_text1(text1)
            explanation = evaluate_generated_answer(key_points, key_points_RAG)
        
            explanation_soup = BeautifulSoup(explanation, 'html.parser')
            accuracy_score = int(explanation_soup.find("accuracy_score").contents[0])
            if accuracy_score >= 60:
                rag_answer = "Y"
            else:
                rag_answer = "N"


        results.append({"ID": row["ID"], "Key Points:": key_points, "RAG Key Points": key_points_RAG, "LLM Method Result": explanation, "RAG_Answer": rag_answer})
        print(f"Finished ID {row['ID']}")

    output_csv = "LLM_keypoint_results.csv"
    pd.DataFrame(results).to_csv(output_csv, index=False)

    print(f"Comparison completed. Results saved to {output_csv}")

if __name__ == "__main__":
    # save_keypoints()
    evaluate_RAG_answer()