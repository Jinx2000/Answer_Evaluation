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
