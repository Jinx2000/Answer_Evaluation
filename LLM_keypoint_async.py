import os
import openai
import pandas as pd
import asyncio
from bs4 import BeautifulSoup
from tqdm.asyncio import tqdm_asyncio  # Async progress bar

# Set OpenAI API key

client = openai.AsyncClient(api_key=os.getenv("OPENAI_API_KEY"))

# Semaphore to limit concurrent OpenAI API calls (adjust as needed)
API_CONCURRENCY_LIMIT = 5
semaphore = asyncio.Semaphore(API_CONCURRENCY_LIMIT)

async def extract_key_points_from_text1(text1):
    """ Asynchronously extracts key points from Text 1. """
    prompt = f"""
    You are an expert summarizer and familiar with Cloud-native. Extract key points and relevant code snippets.

    Text 1:
    {text1}
    """

    async with semaphore:  # Limit concurrency
        try:
            response = await client.chat.completions.create(  # ✅ Corrected usage
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error in extract_key_points_from_text1: {e}")
            return "Error extracting key points."

async def evaluate_generated_answer(text1, text2, key_points):
    """ Asynchronously evaluates Text 2 against Text 1 using extracted key points. """
    prompt = f"""
    <evaluation>
        <instructions>
            Compare an alternate answer (Text 2) to a verified correct answer (Text 1).
            Text 1 should always be considered correct.
            Score accuracy (0-100) based on key points and overall similarity.
        </instructions>

        <correct_answer>{text1}</correct_answer>
        <our_answer>{text2}</our_answer>
        <key_points>{key_points}</key_points>

        <response_format>
            <accuracy_score></accuracy_score>
            <reasoning></reasoning>
        </response_format>
    </evaluation>
    """

    async with semaphore:
        try:
            response = await client.chat.completions.create( 
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error in evaluate_generated_answer: {e}")
            return "<accuracy_score>0</accuracy_score>\n<reasoning>Error during evaluation.</reasoning>"

async def process_row(row):
    """ Process a single row asynchronously: extract key points, then evaluate answer. """
    text1 = str(row["StackOverflow Answer"]).strip()
    text2 = str(row["Previous RAG Answer"]).strip()

    if not text1 or not text2:
        return {
            "ID": row["ID"],
            "Key Points": "N/A",
            "LLM Method Result": "Similarity Score: N/A\nReasoning: Missing Data",
            "RAG_Answer": "N/A",
        }
    
    # Step 1: Extract key points
    key_points = await extract_key_points_from_text1(text1)

    # Step 2: Evaluate generated answer using extracted key points
    explanation = await evaluate_generated_answer(text1, text2, key_points)

    # Parse accuracy score
    explanation_soup = BeautifulSoup(explanation, 'html.parser')
    accuracy_score_tag = explanation_soup.find("accuracy_score")
    accuracy_score = int(accuracy_score_tag.contents[0]) if accuracy_score_tag else 0
    rag_answer = "Y" if accuracy_score >= 60 else "N"

    print(f"Finished ID {row['ID']}")
    return {
        "ID": row["ID"],
        "Key Points": key_points,
        "LLM Method Result": explanation,
        "RAG_Answer": rag_answer,
    }

async def process_all_rows(file_path):
    """ Process all rows asynchronously using asyncio. """
    df = pd.read_csv(file_path)

    # Run all rows asynchronously
    tasks = [process_row(row) for _, row in df.iterrows()]
    results = await tqdm_asyncio.gather(*tasks, desc="Processing Rows")

    # Save results
    output_csv = "LLM_keypoint_results.csv"
    pd.DataFrame(results).to_csv(output_csv, index=False)
    print(f"Comparison completed. Results saved to {output_csv}")

if __name__ == "__main__":
    file_path = "input_data.csv"
    asyncio.run(process_all_rows(file_path))
