import os
import openai
import numpy as np
from scipy.spatial.distance import cosine

# Load API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")  # Ensure this is set in your system

# Function to get embeddings from OpenAI API (Updated for v1.0+)
def get_embedding(text):
    """Fetches embedding for a given text using OpenAI API."""
    response = openai.embeddings.create(
        model="text-embedding-ada-002",
        input=[text]
    )
    return response.data[0].embedding  # Extract the embedding vector

# Function to compute cosine similarity between two embeddings
def cosine_similarity(text1, text2):
    """Computes cosine similarity between two texts using their embeddings."""
    emb1 = get_embedding(text1)
    emb2 = get_embedding(text2)
    similarity = 1 - cosine(emb1, emb2)  # Cosine similarity formula
    return similarity

# Threshold-based classification
def classify_answer(similarity_score, high_threshold=0.9, low_threshold=0.7):
    """
    Classifies the similarity score into:
    - "Correct" if above high_threshold
    - "Incorrect" if below low_threshold
    - "Borderline" if in between
    """
    if similarity_score >= high_threshold:
        return "Correct"
    elif similarity_score < low_threshold:
        return "Incorrect"
    else:
        return "Borderline (Needs LLM Evaluation)"

# Example texts to compare
text1 = """
"It's possible to achieve what you want, however you will need to use Nginx Ingress to do that, as you will need to use specific annotation - nginx.ingress.kubernetes.io/upstream-vhost.

It was well described in this Github issue based on storage.googleapis.com.

apiVersion: v1
kind: Service
metadata:
  name: google-storage-buckets
spec:
  type: ExternalName
  externalName: storage.googleapis.com
---
apiVersion: extensions/v1beta1
kind: Ingress
metadata:
  name: proxy-assets-ingress
  annotations:
    kubernetes.io/ingress.class: nginx-ingress
    nginx.ingress.kubernetes.io/rewrite-target: /[BUCKET_NAME]/[BUILD_SHA]
    nginx.ingress.kubernetes.io/backend-protocol: ""HTTPS""
    nginx.ingress.kubernetes.io/upstream-vhost: ""storage.googleapis.com""
spec:
  rules:
  - host: abc.company.com
    http:
      paths:
      - path: /your/path
        backend:
          serviceName: google-storage-buckets
          servicePort: 443
Depends on your needs, if you would use it on non https you would need to change servicePort to 80 and remove annotation nginx.ingress.kubernetes.io/backend-protocol: ""HTTPS"".

For additional details, you can check other similar Stackoverflow question.

Please remember to not use - in spec.rules.host and spec.rules.http in the same manifest. You should use - only with http, if you don't have host in your configuration."
"""

text2 = """
"Based on the context provided, it seems like you are trying to achieve URL forwarding or redirection using Kubernetes Ingress. Here is the response to address the query:

```yaml
# Define the ExternalName Service to forward traffic to google.com
apiVersion: v1
kind: Service
metadata:
  name: test-srv
spec:
  type: ExternalName
  externalName: google.com

---
# Configure the Ingress to handle requests for abc.company.com/google and redirect to google.com
apiVersion: networking.k8s.io/v1beta1
kind: Ingress
metadata:
  name: test-ingress
spec:
  rules:
  - host: abc.company.com
    http:
      paths:
      - path: /google
        pathType: ImplementationSpecific
        backend:
          service:
            name: test-srv
            port:
              number: 80
```"
"""

# Run similarity comparison
similarity_score = cosine_similarity(text1, text2)
classification = classify_answer(similarity_score)

# Print results
print(f"Similarity Score: {similarity_score:.4f}")
print(f"Classification: {classification}")
