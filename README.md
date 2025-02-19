# Answer_Evaluation

## Method Introduction

We found that the content of each different post and question is very different.

For example, some posts have very detailed replies, while others only reply with very brief information. This makes it very difficult to directly conduct text comparison for evaluation.

So the first thing we do is extract the key points of text information, which has been achieved through function **save_keypoints()**. We design a prompt to make LLM extract and summarize a key points with description and code snippets for each solution(one answer may containes several solutions).

What's more, for a configuration issue, the most important part of answers is **code snippets**. Thus, we design an another prompt to make LLM to mainly compare the code snippets between the key points from two answers(post answer and RAG answer).

If one of the key point could match any key point in post answer, which means the solution provided by RAG system hit the post answer, so we will give a high similarity score. This prompt has been achieved through function **evaluate_RAG_answer()**.

## Usage

You could only focus on file **LLM_keypoint.py**. Our main functions are all inside. 
- The file **LLM_keypoint_bak.py** store the code of last version.

When you need to generate the new key_points, please call function **save_keypoints()** in **main()**.

Function **save_keypoints()** will generate the key points in file **input_data.csv**.

You can directly evaluation the RAG answers by calling function **evaluate_RAG_answer()** in **main()**.

## Output File Format

The evaluation result will be exported as "LLM_keypoint_results.csv", the rows are "ID", "Key Points", "RAG Key Points", "LLM Method Result", "RAG_Answer".

## Update Log

### 2025.2.18

#### Evaluation Result

The current evaluation accuracy is roughly 97.5% (39/40).

#### LLM_keypoint_bak.py

This new file store the last version code.


### 2025.2.11

#### LLM_simulate_RAG_answer.py

Due to some items in original input_data.csv are irrational, I delete them.

To supplement some items, I choose some posts from [K8_5wQuestion.csv](https://drive.google.com/drive/u/1/folders/1xneNVgMRXSX-rchMlZ7JG4o4musNO3mG) and leverage GPT to generate answers.

#### LLM_keypoint.py

The main changes are:
1. I optimized the key points extraction mechanism. The original key points were a bit too redundant. Actually, one solution should only have one key point. Thus I restrict the number of key points.
2. the generation of key points is a bit abstract, so I provide a example in prompt to guide LLM to generate key points.
3. I have added weights for text matching. Key points content will enjoy a higher rating weight (80%), while the rest of the content will only have a small weight(20%).
4. For configuration issues, a correct configuration code is the most important. Therefore, I will focus the evaluation on the code snippets rather than some simple descriptions.

#### Evaluation Result

The current evaluation accuracy is roughly 91.4% (32/35).

I will also optimize it periodically in the future.
