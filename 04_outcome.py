import matplotlib.pyplot as plt
import numpy as np
import os, json

def get_file_names(directory):
    # 获取目录下的所有文件和文件夹
    all_items = os.listdir(directory)
    # 过滤出文件（排除文件夹）
    file_names = [item for item in all_items if os.path.isfile(os.path.join(directory, item))]
    return file_names


# 该函数用于计算 baseline 的 accuracy 数值
def cal_gpt_indicator():
    print("=============== Here are GPT scores ============")
    output_filename = "gpt_scores.json"

    accuracy = list()

    with open(output_filename, "r", encoding='utf-8') as f:
        eval_results = json.load(f)


    for result in eval_results:
        accuracy.append(result["answer_correctness"])


    accuracy_mean = np.mean(accuracy)
    accuracy_var = np.var(accuracy)

    print(f"accuracy mean is {accuracy_mean}, variance is {accuracy_var}")


# 该函数用于统计某一 RAG 版本各个 Metric 在 0-1 不同区间的分布情况
def plt_data(arrays):

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
    plt.title('Distribution of Numbers in Different Intervals')
    plt.legend(["faithfulness", "answer_relevancy", "context_precision", "context_recall", "accuracy"])
    plt.show()


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
    plt_data([faithfulness, answer_relevancy, context_precision, context_recall, accuracy])
    
    return [faithfulness_mean, answer_relevancy_mean, context_precision_mean, context_recall_mean, accuracy_mean]

def plt_compare_scores():
    directory_path = './score_data'
    file_names = get_file_names(directory_path)


    # scores 记录各个版本的 五个指标 的数据
    scores = list()
    for file in file_names:
        scores.append(cal_rag_score(directory_path + "/" + file))


    # 打印出这些数据，以方便利用
    print(scores)

    scores = np.array(scores)

    # Metric 名称
    metrics = ['faithfulness_mean', 'answer_relevancy_mean', 'context_precision_mean', 'context_recall_mean', 'accuracy_mean']

    # RAG 版本标记
    versions = list()
    for i in range(len(scores)):
        versions.append(f'Version {i+1}')


    # 设置柱状图的宽度
    bar_width = 0.15

    # 设置x轴的位置
    x = np.arange(len(metrics))

    plt.figure(figsize=(12, 6))

    # 绘制每个版本的柱状图
    for i in range(len(versions)):
        plt.bar(x + i * bar_width, scores[i], width=bar_width, label=versions[i])
        
    plt.xticks(x + bar_width * 2, metrics)  # 将x轴刻度居中
    plt.xlabel('Metrics')
    plt.ylabel('Scores')
    plt.title('Comparison of RAG System Versions by Metrics')
    plt.legend()
    plt.show()

plt_compare_scores()
# cal_gpt_indicator()