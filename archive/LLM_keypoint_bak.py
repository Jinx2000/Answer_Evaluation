import os
import openai
import pandas as pd
from bs4 import BeautifulSoup

os.environ["http_proxy"] = "http://localhost:7890"
os.environ["https_proxy"] = "http://localhost:7890"


input_csv = "input_data.csv"

def save_keypoints():

    key_points_list = list()
    df = pd.read_csv(input_csv)

    for index, row in df.iterrows():
        text1 = str(row["StackOverflow Answer"]).strip()
        text2 = str(row["Previous RAG Answer"]).strip()

        if not text1 or not text2:
            key_points = "N/A"
            # explanation = "Similarity Score: N/A\nReasoning: Missing Data"
        else:
            key_points = extract_key_points_from_text1(text1)
            # explanation = evaluate_generated_answer(text1, text2, key_points)
            # explanation_soup = BeautifulSoup(explanation, 'html.parser')
            # accuracy_score = int(explanation_soup.find("accuracy_score").contents[0])
            # if accuracy_score >= 60:
            #     rag_answer = "Y"
            # else:
            #     rag_answer = "N"

        key_points_list.append(key_points)
        print(f"Finished ID {row['ID']}")

    df['Key Points'] = key_points_list
    df.to_csv(input_csv, index=False)

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

def evaluate_generated_answer(text1, text2, key_points):


    prompt = f"""
    <evaluation>
        <instructions>
            You are an expert in Cloud-native. You are evaluating **an alternate answer (Text 2)** against a **verified correct answer** (Text 1).
            **Text 1** should always be treated as definitively correct.
            Text contains a description of solution and specific codes snippets. The description is usually a normal sentence, while the code consists of a series of words. Please try to distinguish them.
            Please assign an accuracy score (0 to 100 points) for Text 2 according to rules below.
            Use Key points from Text 1 to help. Check if Text 2 covers these key points. 
            Rule 1: The evaluation is divided into two parts, one is the key point evaluation(0 to 80 points), and the other is the general text evaluation(0 to 20 points).
            Rule 2: In key point evaluation(0 to 80 points). Only focus on the code part, as long as the code snippets in the text have two or more words that are the same as the code in any key point, we can give it a score of 80. If not, give it a score not exceeding 20.
            Rule 3: In general text evaluation(0 to 20 points), for other content unrelated to key points, the more similar the Text 2 is to Text 1, the higher the score.
            The final score is the sum of the scores from two parts. You should give the final score in label <accuracy_score> below.
            
            1. Key Points from Text 1:
            {key_points}

            2. Provide reasoning:
            - Show how many points the Text 2 receive in each of the two parts.
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
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )
    return response.choices[0].message.content


# Load CSV file

def evaluate_RAG_answer():


    df = pd.read_csv(input_csv)

    results = []
    for index, row in df.iterrows():
        text1 = str(row["StackOverflow Answer"]).strip()
        text2 = str(row["Previous RAG Answer"]).strip()
        key_points = str(row["Key Points"]).strip()

        if not text1 or not text2:
            # key_points = "N/A"
            explanation = "Similarity Score: N/A\nReasoning: Missing Data"
        else:
            # key_points = extract_key_points_from_text1(text1)
            explanation = evaluate_generated_answer(text1, text2, key_points)

            explanation_soup = BeautifulSoup(explanation, 'html.parser')
            accuracy_score = int(explanation_soup.find("accuracy_score").contents[0])
            if accuracy_score >= 60:
                rag_answer = "Y"
            else:
                rag_answer = "N"


        results.append({"ID": row["ID"], "Key Points:": key_points, "LLM Method Result": explanation, "RAG_Answer": rag_answer})
        print(f"Finished ID {row['ID']}")

    output_csv = "LLM_keypoint_results.csv"
    pd.DataFrame(results).to_csv(output_csv, index=False)

    print(f"Comparison completed. Results saved to {output_csv}")

if __name__ == "__main__":
    # save_keypoints()
    evaluate_RAG_answer()