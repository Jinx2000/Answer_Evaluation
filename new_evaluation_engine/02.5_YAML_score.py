import tempfile
import subprocess
import re
import os

def extract_yaml_from_response(text: str) -> str:
    """
    Extracts the first YAML block from the response string.
    Looks for triple backtick (```) enclosed YAML.
    """
    yaml_block = re.findall(r"```(?:yaml)?\n(.*?)```", text, re.DOTALL)
    if yaml_block:
        return yaml_block[0].strip()
    else:
        return ""

def validate_yaml_kube_tools(yaml_str: str, namespace="default"):
    """
    Validates a given YAML string using kubeconform and kubectl dry-run.
    Returns a structured result dictionary.
    """
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.yaml', delete=False) as tmpfile:
        tmpfile.write(yaml_str)
        tmpfile.flush()
        filepath = tmpfile.name

    result = {
        "kubeconform": {"pass": False, "output": ""},
        "dry_run": {"pass": False, "output": ""},
    }

    # Run kubeconform
    try:
        kc_proc = subprocess.run(
            ["kubeconform", "-summary", filepath],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        result["kubeconform"]["pass"] = kc_proc.returncode == 0
        result["kubeconform"]["output"] = kc_proc.stdout + kc_proc.stderr
    except Exception as e:
        result["kubeconform"]["output"] = str(e)

    # Run kubectl dry-run
    try:
        kd_proc = subprocess.run(
            ["kubectl", "apply", "--dry-run=server", "-f", filepath, "-n", namespace],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        result["dry_run"]["pass"] = kd_proc.returncode == 0
        result["dry_run"]["output"] = kd_proc.stdout + kd_proc.stderr
    except Exception as e:
        result["dry_run"]["output"] = str(e)

    os.remove(filepath)
    return result

sample_input = """
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: test-ingress
  namespace: test-layer
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /$1
spec:
  rules:
    - host: mylocalhost.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: test-app
                port:
                  number: 5000
"""