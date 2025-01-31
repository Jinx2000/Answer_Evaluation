import os
import openai
import pandas as pd
import numpy as np
from scipy.spatial.distance import cosine

# Load API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# Function to get embeddings from OpenAI API
def get_embedding(text):
    """Fetches embedding for a given text using OpenAI API."""
    response = openai.embeddings.create(
        model="text-embedding-ada-002",
        input=[text]
    )
    return response.data[0].embedding

# Function to compute cosine similarity
def cosine_similarity(text1, text2):
    """Computes cosine similarity between two texts."""
    emb1 = get_embedding(text1)
    emb2 = get_embedding(text2)
    similarity = 1 - cosine(emb1, emb2)  # Cosine similarity formula
    return similarity

# Function to classify similarity score
def classify_answer(similarity_score, high_threshold=0.9, low_threshold=0.7):
    """
    Classifies the similarity score:
    - "Correct" if above high_threshold
    - "Incorrect" if below low_threshold
    - "Borderline (Needs LLM Evaluation)" if in between
    """
    if similarity_score >= high_threshold:
        return "Correct"
    elif similarity_score < low_threshold:
        return "Incorrect"
    else:
        return "Borderline (Needs LLM Evaluation)"

# Load CSV file
input_csv = "input_data.csv"  # Replace with your actual filename
df = pd.read_csv(input_csv)

# Ensure required columns exist
if "StackOverflow Answer" not in df.columns or "Previous RAG Answer" not in df.columns:
    raise ValueError("CSV must contain 'StackOverflow Answer' and 'Previous RAG Answer' columns")

# Process each row
results = []
for index, row in df.iterrows():
    text1 = str(row["StackOverflow Answer"])  # Convert to string in case of NaN values
    text2 = str(row["Previous RAG Answer"])
    
    if not text1.strip() or not text2.strip():
        similarity_score = "N/A"
        classification = "Missing Data"
    else:
        similarity_score = cosine_similarity(text1, text2)
        classification = classify_answer(similarity_score)
    
    result_text = f"Similarity Score: {similarity_score:.4f}\nClassification: {classification}"
    results.append({"ID": row["ID"], "Embedding Method Result": result_text})

# Save results to CSV
output_csv = "embedding_comparison_results.csv"
output_df = pd.DataFrame(results)
output_df.to_csv(output_csv, index=False)

print(f"Comparison completed. Results saved to {output_csv}")
