import matplotlib.pyplot as plt
import numpy as np
import os, json, re

def get_file_names(directory):
    # 获取目录下的所有文件和文件夹
    all_items = os.listdir(directory)
    # 过滤出文件（排除文件夹）
    file_names = [item for item in all_items if os.path.isfile(os.path.join(directory, item))]
    return file_names

# 该函数用于统计某一 RAG 版本各个 Metric 在 0-1 不同区间的分布情况
def plt_data(arrays, filename):

    # 提取 `test_n` 作为标识
    base_name = os.path.basename(filename)  # 获取文件名部分（去掉路径）
    test_name = base_name.split("_ragas_scores")[0]  # 提取 `test_5` 这种格式

    # 定义区间
    bins = [0, 0.2, 0.4, 0.6, 0.8, 1]

    # 统计每个数组在区间内的个数
    hist_data = [np.histogram(array, bins=bins)[0] for array in arrays]

    # 区间标签
    bin_labels = ['0-0.2', '0.2-0.4', '0.4-0.6', '0.6-0.8', '0.8-1']

    # 设置柱状图的宽度
    bar_width = 0.15

    # 设置x轴的位置
    x = np.arange(len(bin_labels))

    # 创建图形
    plt.figure(figsize=(12, 6))

    # 绘制每个数组的柱状图
    for i in range(len(arrays)):
        bars = plt.bar(x + i * bar_width, hist_data[i], width=bar_width, label=f'Array {i+1}')
        
        # 在每个柱状图上方标注具体数字
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2, height, f'{int(height)}',
                    ha='center', va='bottom', fontsize=9)

    plt.xticks(x + bar_width * 2, bin_labels)
    plt.xlabel('Intervals')
    plt.ylabel('Count')
    plt.title(f'Distribution of Numbers - {test_name}') # 标题包含 test 名字
    plt.legend(["faithfulness", "answer_relevancy", "context_precision", "context_recall", "accuracy"])

    # 确保输出目录存在
    output_dir = "./graphs"
    os.makedirs(output_dir, exist_ok=True)
    # 生成独立的文件名
    output_path = os.path.join(output_dir, f"number_distribution_{test_name}.png")
    # 保存图片
    plt.savefig(output_path, dpi=300, bbox_inches='tight')

    #plt.show()


# 该函数用于统计某个 RAG 版本的 Metric 分数
def cal_rag_score(filename):

    # 五个 Metric
    faithfulness = list()
    answer_relevancy = list()
    context_precision = list()
    context_recall = list()
    accuracy = list()

    with open(filename, "r", encoding='utf-8') as f:
        eval_results = json.load(f)


    for result in eval_results:
        try:
            faithfulness.append(result["faithfulness"])
            answer_relevancy.append(result["answer_relevancy"])
            context_precision.append(result["context_precision"])
            context_recall.append(result["context_recall"])
            accuracy.append(result["answer_correctness"])
        except:
            accuracy.append(result["answer_correctness"])

    faithfulness_mean = np.mean(faithfulness)
    faithfulness_var = np.var(faithfulness)

    answer_relevancy_mean = np.mean(answer_relevancy)
    answer_relevancy_var = np.var(answer_relevancy)

    context_precision_mean = np.mean(context_precision)
    context_precision_var = np.var(context_precision)

    context_recall_mean = np.mean(context_recall)
    context_recall_var = np.var(context_recall)

    accuracy_mean = np.mean(accuracy)
    accuracy_var = np.var(accuracy)
    plt_data([faithfulness, answer_relevancy, context_precision, context_recall, accuracy], filename)
    
    return [faithfulness_mean, answer_relevancy_mean, context_precision_mean, context_recall_mean, accuracy_mean]

def plt_compare_scores():
    directory_path = './score_data'
    file_names = get_file_names(directory_path)


    # scores 记录各个版本的 五个指标 的数据
    scores = list()
    for file in file_names:
        scores.append(cal_rag_score(directory_path + "/" + file))

    # 提取所有 test 版本号
    test_numbers = []
    for file in file_names:
        match = re.search(r'test_(\d+)_ragas_scores', file)  # 提取 `test_X`
        if match:
            test_numbers.append(int(match.group(1)))

    # 如果 test_numbers 为空，则退出
    if not test_numbers:
        print("No valid test versions found in filenames!")
        return        
    
    # 计算 test 版本范围
    min_test = min(test_numbers)
    max_test = max(test_numbers)
    test_range = f"{min_test}to{max_test}"  # 形成 "1to5" 形式

    # 打印出这些数据，以方便利用
    print(scores)

    scores = np.array(scores)

    # Metric 名称
    metrics = ['faithfulness_mean', 'answer_relevancy_mean', 'context_precision_mean', 'context_recall_mean', 'accuracy_mean']

    # 生成 RAG 版本标记（从 test_ 提取版本号）
    versions = [f'Test {num}' for num in test_numbers]


    # 设置柱状图的宽度
    bar_width = 0.15

    # 设置x轴的位置
    x = np.arange(len(metrics))

    plt.figure(figsize=(12, 6))

    # 绘制每个版本的柱状图
    for i in range(len(versions)):
        bars = plt.bar(x + i * bar_width, scores[i], width=bar_width, label=versions[i])

        # 在每个柱子顶部标注具体数值
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width() / 2, height, f'{height:.2f}',
                     ha='center', va='bottom', fontsize=9, color='black')
        
    plt.xticks(x + bar_width * 2, metrics)  # 将x轴刻度居中
    plt.xlabel('Metrics')
    plt.ylabel('Scores')
    plt.title(f'Comparison of RAG System Versions (Test {min_test} to {max_test})')
    plt.legend()
    # save the graph 
    # 确保 `./graphs` 目录存在
    output_dir = "./graphs"
    os.makedirs(output_dir, exist_ok=True)

    # 生成动态命名的文件
    output_path = os.path.join(output_dir, f"rag_comparison_by_metrics_{test_range}.png")

    plt.savefig(output_path, dpi=300, bbox_inches='tight')

    plt.show()

plt_compare_scores()
# cal_gpt_indicator()