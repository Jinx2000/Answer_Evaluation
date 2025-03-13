# Answer_Evaluation

## Usage

### Run Key Point Extraction
```bash
python LLM_keypoint.py
```

## Output File Format

- The evaluation results are now exported as `LLM_keypoint_results.csv`.
- The output file contains the following columns:
  - **`ID`** – The unique identifier of the answer (Answer ID).
  - **`Key Points`** – Extracted key points from the correct answers.
  - **`Answer`** – The LLM-generated response.
  - **`RAG Key Points`** – Extracted key points from the LLM-generated response.
  - **`LLM Method Result`** – Evaluation result based on key point similarity.
  - **`Score`** – Final evaluation score. (Y/N)

## Update Log

### 2025.3.13

---

1. Intergrated baseline as test_0, now 01, 02, 04.py can all run test_0 without specifically asked for baseline. 
   - (Note: Baseline's test0processed_data.json has "retrieved_contexts": [], which means it cannot run **faithfulness**, **context precision**, and **context recall** metrics in RAGAS. I've set them to 0.0 at this point, but maybe not the best solution (set them to N/A or something in the future).)

2. Fixed the graph a bit, now 04.py will save the graphs in /graphs, naming each test's number distribution correctly as `number_distribution_test_n.png`, and the overall comparison to `rag_comparison_by_metrics_0toN.png`. Should be easier to archieve. 

---

### 2025.3.10

#### RAGAS_NOLLM_SCORES Metrics Explanation

##### Example Output:
```
{
    "nonllm_string_similarity": 0.2547,
    "bleu_score": 0.1238,
    "rouge_score": 0.1618
}
```

Each metric is explained in detail below:

---

1. Non-LLM String Similarity (0.2547)  
   - Definition: Measures how similar the `RAG-generated answer (LLM response)` is to the `reference answer (Stack Overflow answer)` using traditional string similarity methods such as Levenshtein distance, Jaro similarity, or Hamming distance.  
   - 0.25 Score Meaning: The generated answer shares some similarities with the reference answer but has significant differences, indicating possible wording changes or missing details.

---

2. BLEU Score (0.1238)  
   - Definition: Measures the **n-gram precision** of the `RAG-generated answer (LLM response)` compared to the `reference answer (Stack Overflow answer)`, penalizing overly short responses. BLEU is commonly used for machine translation and text generation evaluation.  
   - 0.12 Score Meaning: The generated answer has low overlap in word sequences with the reference answer, suggesting potential paraphrasing, missing key phrases, or incorrect information.

---

3. ROUGE Score (0.1618)  
   - Definition: Measures the **word overlap** between the `RAG-generated answer (LLM response)` and the `reference answer (Stack Overflow answer)`. It considers recall, precision, and F1-score, making it useful for summarization evaluation.  
   - 0.16 Score Meaning: The generated answer contains some words from the reference answer but lacks substantial overlap, indicating missing key details or different phrasing.

---

**Noted that these three metrics are non-LLM.**

**Even though RAGAS provided a non-LLM version for `Context Precision` and `Context Recall`, they cannot be computed using our current input data. More detail in the design doc of the evaluation system.**

---

### 2025.3.4 (2)

#### RAGAS_SCORES Metrics Explaination

##### Example
```
{
    "faithfulness": 0.0,
    "context_precision": 0.5833,
    "context_recall": 0.25,
    "answer_relevancy": 0.8229,
    "answer_correctness": 0.6787
}
```

Each metric is explained in detail below:

---

1. Faithfulness (0.0)
   - Definition: Measures if the `RAG-generated answer (LLM response)` is supported by the `retrieved context (RAG documents)`.
   - 0.0 Score Meaning: The generated answer is not grounded in the retrieved documents—it may contain hallucinated or incorrect information.

---

2. Context Precision (0.5833)
   - Definition: Measures how many of the `retrieved documents (RAG context)` are actually relevant to the `user input(Stack Overflow question)`.
   - 0.58 Score Meaning: Some retrieved documents were useful, but many were irrelevant, affecting response accuracy.

---

3. Context Recall (0.25)
   - Definition: Measures how much of the `reference answer (Stack Overflow answer)` was found in the `retrieved context (RAG documents)`.
   - 0.25 Score Meaning: most of the necessary information was missing, making it difficult for the LLM to generate a complete answer.

---

4. Answer Relevancy (0.8229)
   - Definition: Measures how well the `RAG-generated answer (LLM response)` aligns with the `user input(Stack Overflow question)`.
   - 0.82 Score Meaning: The LLM’s answer mostly addresses the question, but some details might be missing.

---

5. Answer Correctness (0.6787)
   - Definition: Measures how factually correct the `RAG-generated answer (LLM response)` is compared to the `reference answer (Stack Overflow answer)`.
   - 0.68 Score Meaning: The answer is partially correct but contains errors or missing details.

---

**Noted that for now we're using the LLM method.**

**We're considering using non-LLM method and test on it next week.**

### 2025.3.4

#### RAGAS Format Introduction

Generation Metrics:

- Faithfulness
    
  Measure how factually consistent a **RAG Answer** is with the **retrieved context**(top 3 chunks). Ranges from 0 to 1, higher scores indicating better consistency and less Illustration.

- Answer Relevancy

  Measure how relevant a **RAG Answer** is to the **user input**(Query). Higher scores indicate better alignment with the user input, while lower scores are given if the response is incomplete or includes redundant information.

Retrieval Metrics:

- Context Precision

  Measure the proportion of relevant chunks in the **retrieved contexts**. It is calculated as the mean of the precision@k for each chunk in the context. Precision@k is the ratio of the number of relevant chunks at rank k to the total number of chunks at rank k.

- Context Recall

  Measure how many of the relevant documents (or pieces of information) were successfully retrieved. Or measure whether each point in **Ground Truth** is included in the **retrieved contexts**.

### 2025.2.22

#### 1. Repository Structure Changes
- Added `/archive/` to store previous versions of scripts.
- Added `/dev_data/` to store data used for improving the evaluation tool.
- Updated `.gitignore`.

#### 2. Parallel Processing for OpenAI Requests
- `save_keypoints()` now runs OpenAI API calls asynchronously using `asyncio.to_thread()`.
- This ensures true parallel execution, improving processing speed.
- Implemented automatic retry with exponential backoff for OpenAI rate limits.
- 9x-10x speedup.

#### 3. Key Point Extraction Optimization
- Key points from the two texts are now stored in separate CSV files:
  - `keypoints_stack.csv` for the correct answers.
  - `keypoints_RAG.csv` for the LLM-generated responses.
- This allows reusing previously extracted key points from `keypoints_stack.csv`, reducing API calls and improving speed.

#### 4. Input Data Processing Improvement
- Standardized the way `input_data.csv` is read.
- This aligns with the format of data from the RAG system, making comparisons more consistent.

---

### 2025.2.18

#### Evaluation Result

The current evaluation accuracy is roughly 94.3% (33/35).

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

I will also optimize it periodically in the future
