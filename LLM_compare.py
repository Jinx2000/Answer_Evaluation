import os
import openai

# Load API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# Function to get similarity reasoning from GPT-4 Turbo
def get_similarity_reasoning(text1, text2):
    """Asks GPT-4 Turbo to analyze similarity and provide reasoning."""
    prompt = f"""
    Compare the following two texts and determine how similar they are.
    Provide a similarity score from 0 to 100, where:
    - 100 means nearly identical
    - 70-99 means highly similar but with minor differences
    - 40-69 means somewhat similar but with key differences
    - 0-39 means mostly different

    Then, explain why they are similar or different. Highlight key points of overlap and differences.

    Text 1:
    {text1}

    Text 2:
    {text2}

    Response format:
    Similarity Score: [0-100]
    Reasoning: [Detailed explanation]
    """

    response = openai.chat.completions.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

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

# Get similarity reasoning from GPT-4 Turbo
explanation = get_similarity_reasoning(text1, text2)

# Output results
print(explanation)
