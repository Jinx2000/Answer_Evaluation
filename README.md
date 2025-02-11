# Answer_Evaluation
 
# Update Log

## LLM_simulate_RAG_answer.py

Due to some items in original input_data.csv are irrational, I delete them.

To supplement some items, I choose some posts from [K8_5wQuestion.csv](https://drive.google.com/drive/u/1/folders/1xneNVgMRXSX-rchMlZ7JG4o4musNO3mG) and leverage GPT to generate answers.

## LLM_keypoint_backup.py

The main changes are:
1. I optimized the key points extraction mechanism. The original key points were a bit too redundant. Actually, one solution should only have one key point. Thus I restrict the number of key points.
2. the generation of key points is a bit abstract, so I provide a example in prompt to guide LLM to generate key points.
3. I have added weights for text matching. Key points content will enjoy a higher rating weight (80%), while the rest of the content will only have a small weight(20%).
4. For configuration issues, a correct configuration code is the most important. Therefore, I will focus the evaluation on the code snippets rather than some simple descriptions.

## Output File Format

The evaluation result will be exported as "LLM_keypoint_results.csv", the rows are "ID", "Key Point", "LLM Method Result", "RAG_Answer"

## Evaluation Result

The current evaluation accuracy is roughly 91.4% (32/35).

I will also optimize it periodically in the future