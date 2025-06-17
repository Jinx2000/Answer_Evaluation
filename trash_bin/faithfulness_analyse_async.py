import pandas as pd
import openai
import os
import asyncio
from tqdm.asyncio import tqdm_asyncio
from openai import AsyncOpenAI
import re

os.environ["http_proxy"] = "http://localhost:7890"
os.environ["https_proxy"] = "http://localhost:7890"

# 配置参数
MODEL_NAME = "gpt-4o-mini"  # 修正为有效模型名称
INPUT_CSV = "./dev_data/test_verification_results_v3.csv"
OUTPUT_CSV = "./dev_data/test_verification_results_v3_analyse2.csv"
TEXT1_COL = "gpt_Refined_Response"
TEXT2_COL = "gpt_Merged_Contexts"
CONCURRENCY_LIMIT = 5  # 并发请求限制
DELAY_SECONDS = 1

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 系统角色设定
K8S_EXPERT_ROLE = """
I will give you two text named "Answer" and "Context".
You need to determine whether the content of the "Answer" has drawn on or referenced the content of the "Context".
Return the "Yes" or "No" and give a simple explaination.
"""

# 系统角色设定
K8S_EXPERT_ROLE = """
I will give you two text named "Answer" and "Context". "Answer" is a List that contains several sentences.
You need to determine whether each sentence in the 'Answer' references or draws on the content of the 'Context'.
Return the number of sentences that can and cannot be derived from the "Context" content.
For example:
    If "Answer" contains 8 sentences. and 5 of them derived from the "Context", you should return "[5,3]"
"""

# 系统角色设定
K8S_EXPERT_ROLE = """
I will give you two text named "Answer" and "Context".
You need to determine whether 'Answer' can be derived from the 'Context'.

"""

def split_string(input_str):
    # 首先提取所有被```包裹的内容
    code_blocks = re.findall(r'```(.*?)```', input_str, re.DOTALL)
    
    # 移除所有```包裹的内容，以便后续处理
    remaining_text = re.sub(r'```.*?```', '', input_str, flags=re.DOTALL)

    # 移除###开头的行和其他Markdown非纯文本内容
    remaining_text = re.sub(r'^#+.*$', '', remaining_text, flags=re.MULTILINE)
    
    # 按句子分割剩余文本
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', remaining_text.strip())
    
    # 合并结果：首先是代码块，然后是句子
    result = []
    for block in code_blocks:
        # 去除代码块可能的前后空白和语言标识符
        clean_block = block.strip()
        if '\n' in clean_block:
            # 如果有换行，第一个是语言标识符
            lang, *content = clean_block.split('\n', 1)
            result.append('\n'.join(content).strip())
        else:
            result.append(clean_block)
    
    # 添加句子，过滤掉空字符串
    result.extend(sentence for sentence in sentences if sentence.strip())
    
    return result




async def analyze_k8s_similarity(answer:list, context):
    """K8s专业相似度分析函数"""
    user_prompt = f"""
    "Answer": {answer},
    "Context": {context}
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
            analysis = await analyze_k8s_similarity(split_string(row[TEXT1_COL]), row[TEXT2_COL])
            await asyncio.sleep(DELAY_SECONDS)  # 控制请求频率
            return row.name, analysis
        except Exception as e:
            print(f"Error processing row {row.name}: {str(e)}")
            return row.name, f"Error: {str(e)}"

async def analyze_faithfulness():
    """异步处理CSV文件的主函数"""
    df = pd.read_csv(INPUT_CSV)
    df = df.head(30)  # 处理前30条
    
    if "Faithfulness_Analysis" not in df.columns:
        df["Faithfulness_Analysis"] = None

    # 创建信号量控制并发
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    
    # 准备任务列表
    tasks = []
    for _, row in df.iterrows():
        if pd.isnull(row["Faithfulness_Analysis"]):
            tasks.append(process_row(row, semaphore))
    
    # 使用tqdm显示进度
    results = await tqdm_asyncio.gather(*tasks, desc="Processing rows")
    
    # 更新结果到DataFrame
    for index, analysis in results:
        df.at[index, "Faithfulness_Analysis"] = analysis
    
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Analysis complete. Results saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    asyncio.run(analyze_faithfulness())
