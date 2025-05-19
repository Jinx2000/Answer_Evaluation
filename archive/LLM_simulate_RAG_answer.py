import os
import openai
import pandas as pd

os.environ["http_proxy"] = "http://localhost:7890"
os.environ["https_proxy"] = "http://localhost:7890"


text = f"""
I have a MySQL pod running in my cluster. I need to temporarily pause the pod from working without deleting it, something similar to docker where the docker stop container-id cmd will stop the container not delete the container.

Are there any commands available in kubernetes to pause/stop a pod?

"""

prompt = f"""
You are a expert in Cloud-native. I'll give you a Questions(Text), please solve the problem with specific code and give the reasons.
You answer should be concise clear, focusing only on the problem.
Text:
{text}
"""

response = openai.chat.completions.create(
    model="gpt-4-turbo",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.0
)

print(response.choices[0].message.content)