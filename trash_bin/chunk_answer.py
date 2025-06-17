import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["http_proxy"] = "http://localhost:7890"
os.environ["https_proxy"] = "http://localhost:7890"

import nltk
from sentence_transformers import SentenceTransformer
import torch
import re

# 下载nltk的punkt分词模型（首次运行需要下载，之后就无需再执行了）
# if nltk.download('punkt_tab') == True:
#     print("Download success!")

# else:
#     print("Download Failed...")


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





def semantic_chunking(text, threshold=0.7):
    """
    将文本按语义分割成相关句子组
    
    参数：
    text (str): 输入文本
    threshold (float): 相邻句子相似度阈值（0-1）
    
    返回：
    list: 分组后的句子列表
    """
    # 初步分句
    sentences = nltk.sent_tokenize(text)
    if len(sentences) <= 1:
        return sentences


    print("初次分句结果：\n", sentences)
    # 加载句子嵌入模型（首次运行会自动下载）

    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # 生成句子嵌入
    embeddings = model.encode(sentences, convert_to_tensor=True)
    
    # 初始化分块
    chunks = []
    current_chunk = [sentences[0]]
    
    # 计算余弦相似度
    cos = torch.nn.CosineSimilarity(dim=0)
    
    # 遍历相邻句子
    for i in range(1, len(sentences)):
        # 计算相似度
        similarity = cos(embeddings[i-1], embeddings[i]).item()
        
        if similarity >= threshold:
            # 合并到当前块
            current_chunk.append(sentences[i])
        else:
            # 创建新块
            chunks.append(" ".join(current_chunk))
            current_chunk = [sentences[i]]
    
    # 添加最后一个块
    chunks.append(" ".join(current_chunk))
    
    return chunks

# 示例用法
if __name__ == "__main__":
    sample_text = """The sun was shining brightly. Birds were singing in the trees. 
    John decided to go for a walk. He put on his favorite hat. The temperature outside 
    was quite cold. He grabbed his coat before leaving. A cat crossed his path suddenly. 
    It had beautiful striped fur. John smiled and continued walking."""
    
    sample_text = """
    ```yaml\nkind: configmap\napiVersion: v1\nmetadata:\n  name: nginx-configuration\n  namespace: ingress-nginx\n  labels:\n    app: ingress-nginx\ndata:\n  proxy-connect-timeout: \"15\"\n  proxy-read-timeout: \"600\"\n  proxy-send-timeout: \"600\"\n  proxy-body-size: \"8m\"\n  hsts-include-subdomains: \"false\"\n  body-size: \"64m\"  # This should be adjusted based on your application's needs\n  server-name-hash-bucket-size: \"256\"\n  client-max-body-size: \"8m\"  # Ensure this matches the desired limit\n```\n\n### Explanation:\n- The `client-max-body-size` is set to `8m`, which matches the `proxy-body-size`. This alignment helps prevent HTTP 413 errors when the request body exceeds the specified limit.\n\n### Validation:\n- After applying this ConfigMap, ensure that the Nginx Ingress Controller is restarted to apply the new configuration. This step is crucial for the changes to take effect.
    """

    # chunks = semantic_chunking(sample_text, threshold=0.3)
    
    # for i, chunk in enumerate(chunks, 1):
    #     print(f"Chunk {i}:")
    #     print(chunk)
    #     print("-" * 50)

    result = split_string(sample_text)
    i = 1
    for res in result:
        print(i, ":\n", res)
        i += 1