import pandas as pd
import openai
import os
import asyncio
from tqdm.asyncio import tqdm_asyncio
from openai import AsyncOpenAI

os.environ["http_proxy"] = "http://localhost:7890"
os.environ["https_proxy"] = "http://localhost:7890"

# 配置参数
MODEL_NAME = "gpt-4o-mini"  # 修正为有效模型名称
INPUT_CSV = "./dev_data/test_verification_results_v4.csv"
OUTPUT_CSV = "./dev_data/test_results_v4_analyse_correct.csv"
TEXT1_COL = "Answer Body"
TEXT2_COL = "gpt_Refined_Response"
CONCURRENCY_LIMIT = 5  # 并发请求限制
DELAY_SECONDS = 1

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 系统角色设定
K8S_EXPERT_ROLE = """
You are a expert in Kubernetes field. Now I will give you two texts, both of which are answers to a certain question.
One of them is a "reference answer", which should be considered correct; The other is "rag answer", which we answer ourselves.
You need to judge whether the "rag answer" can be considered correct or incorrect and indicate where it is correct or incorrect. Please give me a specific conclusion, correct or incorrect.
Rag answer does not necessarily have to be completely identical to the reference answer to be correct. 
The reference answer will elaborate on which key points are the most important, and as long as some parts of these critical points are consistent, the rag answer can be deemed correct.
"""

async def analyze_k8s_similarity(reference, rag_answer):
    """K8s专业相似度分析函数"""
    user_prompt = f"""
    "reference answer": {reference},
    "rag answers": {rag_answer}
    """
    
    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": K8S_EXPERT_ROLE},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0,
            max_tokens=4090,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"API call error: {str(e)}")
        return f"Analyse Error: {str(e)}"

async def process_row(row, semaphore):
    """处理单行数据的协程"""
    async with semaphore:
        try:
            analysis = await analyze_k8s_similarity(row[TEXT1_COL], row[TEXT2_COL])
            await asyncio.sleep(DELAY_SECONDS)  # 控制请求频率
            return row.name, analysis
        except Exception as e:
            print(f"Error processing row {row.name}: {str(e)}")
            return row.name, f"Error: {str(e)}"

async def analyze_faithfulness():
    """异步处理CSV文件的主函数"""
    df = pd.read_csv(INPUT_CSV)
    df = df.head(30)  # 处理前30条
    
    if "Correct_Analysis" not in df.columns:
        df["Correct_Analysis"] = None

    # 创建信号量控制并发
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    
    # 准备任务列表
    tasks = []
    for _, row in df.iterrows():
        if pd.isnull(row["Correct_Analysis"]):
            tasks.append(process_row(row, semaphore))
    
    # 使用tqdm显示进度
    results = await tqdm_asyncio.gather(*tasks, desc="Processing rows")
    
    # 更新结果到DataFrame
    for index, analysis in results:
        df.at[index, "Correct_Analysis"] = analysis
    
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Analysis complete. Results saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    asyncio.run(analyze_faithfulness())
