# evaluator.py
import os
import json
import re
from typing import List, Dict, Any

from dotenv import load_dotenv
from openai import OpenAI
import numpy as np

# ── Setup ───────────────────────────────────────────────────────────────────────
load_dotenv()  # loads OPENAI_API_KEY from .env
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY is not set in your .env file!")

client = OpenAI(api_key=api_key)

# Load model names from environment (easy to swap without touching code)
EVAL_MODEL = os.getenv("EVAL_MODEL", "gpt-4.1-mini")
NLI_MODEL  = os.getenv("NLI_MODEL",  "gpt-3.5-turbo")


# ── Few‑Shot for Hypothesis Generation ─────────────────────────────────────────
_FEW_SHOT = [
    {
        "question": "Why does `servicename` no longer work in networking.k8s.io/v1 Ingress?",
        "hypotheses": [
            "In networking.k8s.io/v1, the Ingress `backend` block must use `service.name` and `service.port.number` instead of `serviceName`/`servicePort`",
            "`pathType` is a required field (Exact, Prefix, or ImplementationSpecific) for each HTTP path under `spec.rules`",
            "The `ingressClassName` or default IngressClass must match the controller watching the resource"
        ]
    },
    {
        "question": "How do I expose multiple container ports on a single Kubernetes Service?",
        "hypotheses": [
            "A Service `spec.ports` list can contain multiple entries each with `name`, `port`, and `targetPort`",
            "Each port entry must have a unique `name` and the Service `selector` labels must match the Pod labels for routing",
            "To expose externally, Service `type` must be `NodePort` or `LoadBalancer` so that nodePorts or LB IPs are allocated"
        ]
    },
    {
        "question": "My PersistentVolumeClaim is stuck in Pending state. What must be true?",
        "hypotheses": [
            "The PVC `spec.storageClassName` must reference a StorageClass that exists and supports dynamic provisioning",
            "The PVC `spec.accessModes` must match those offered by available PersistentVolumes",
            "The PVC `spec.resources.requests.storage` must be less than or equal to the capacity of a matching PV"
        ]
    },
    {
        "question": "ConfigMap updates are not taking effect in my pods. What must be checked?",
        "hypotheses": [
            "Pods consume ConfigMaps via `envFrom`, `env`+`configMapKeyRef`, or as a volume under `spec.template.spec.volumes` & `volumeMounts`",
            "ConfigMap changes require Pods to be restarted (or use a sidecar/reloader) unless mounted without `subPath` for auto‑reload",
            "The Deployment/statefulset Pod template must reference the correct ConfigMap name under `spec.template.spec`"
        ]
    },
    {
        "question": "Liveness and readiness probes are failing in my Deployment. What fields must be correct?",
        "hypotheses": [
            "Each probe must specify a valid `httpGet` (with `path` and `port`) or an `exec` command that succeeds inside the container",
            "`initialDelaySeconds`, `periodSeconds`, `failureThreshold`, and `successThreshold` must be tuned to your app’s startup/healthcheck behavior",
            "The probe `port` must match a container port declared under `containers[].ports`, or be given as a literal number"
        ]
    },
    {
        "question": "How do I grant a user admin access via RBAC in Kubernetes?",
        "hypotheses": [
            "A ClusterRole or Role with the desired verbs and resources must exist under `apiVersion: rbac.authorization.k8s.io/v1`",
            "A ClusterRoleBinding or RoleBinding must reference that Role/ClusterRole in `roleRef` and the user in `subjects`",
            "The binding manifest must include `kind: ClusterRoleBinding` (or RoleBinding), `apiVersion: rbac.authorization.k8s.io/v1`, and valid `metadata.name`"
        ]
    },
    {
        "question": "Why are ServiceAccount token secrets not auto-generated in Kubernetes 1.24+?",
        "hypotheses": [
            "The `legacyServiceAccountTokenNoAutoGeneration` feature gate is enabled by default, disabling auto‑creation of token secrets",
            "You must use the TokenRequest API (`kubectl create token <sa-name>` in v1.24+) or manually create a Secret of type `kubernetes.io/service-account-token`",
            "That Secret must live in the same namespace as the ServiceAccount and include an annotation `kubernetes.io/service-account.name: <sa-name>`"
        ]
    },
    {
        "question": "How can I mount a ConfigMap as files inside a Pod?",
        "hypotheses": [
            "The ConfigMap must be declared under `spec.volumes` with `configMap.name` referencing the ConfigMap resource",
            "Each file mount requires a corresponding entry in the container’s `volumeMounts` pointing to the volume name and `mountPath`",
            "You can control individual keys via the `items` field to map specific configMap keys to specific file names"
        ]
    },
    {
        "question": "What is the difference between `hostPath` and `emptyDir` volumes?",
        "hypotheses": [
            "`hostPath` mounts a directory or file from the host node’s filesystem into the Pod",
            "`emptyDir` provisions an ephemeral directory that lives as long as the Pod does and is node-local",
            "`hostPath` can be dangerous for portability and multi‑tenant safety, while `emptyDir` is safe but ephemeral"
        ]
    },
    {
        "question": "How do I limit resource usage for a container in Kubernetes?",
        "hypotheses": [
            "You must set `resources.requests` and/or `resources.limits` under the container spec",
            "`requests` define the guaranteed minimum and `limits` define the maximum allowed CPU/memory",
            "The scheduler uses `requests` to place Pods, and the kube‑let enforces `limits` at runtime"
        ]
    },
    {
        "question": "How can I run a Job once and only once in Kubernetes?",
        "hypotheses": [
            "Use `kind: Job` with `spec.template.spec.restartPolicy: OnFailure` or `Never`",
            "Set `spec.backoffLimit` to control the number of retries upon failure",
            "Once the Job’s `.status.succeeded` equals `.spec.completions`, no further Pods will be created"
        ]
    },
    {
        "question": "What’s the proper way to update a Deployment without downtime?",
        "hypotheses": [
            "Use `spec.strategy.type: RollingUpdate` with sensible `maxSurge` and `maxUnavailable` values",
            "Don’t delete Pods manually—allow the controller to spin up new ones before terminating old ones",
            "Verify readiness probes so that new Pods are only considered ready (and serve traffic) once healthy"
        ]
    }
]


# ── Utilities ──────────────────────────────────────────────────────────────────
def _safe_json_load(s: str) -> Any:
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return None

# ── Hypothesis Generation ──────────────────────────────────────────────────────
from typing import List, Any
import re

def generate_hypotheses(question: str, n: int = 5) -> List[str]:
    system = {
        "role": "system",
        "content": (
            f"You are a Kubernetes expert and strict JSON generator. "
            f"Return *only* a JSON array of exactly {n} strings. "
            "Each string must be at least six words long, start with “The answer should ensure” "
            "or “The answer should mention”, and capture one indispensable truth. "
            "Do NOT include bullets, markdown, or any extra text."
        )
    }

    # 2) Few‑shot examples updated to illustrate indispensable truths
    few_shot = {
        "role": "user",
        "content": (
            "Example 1:\n"
            "Q: Why does `servicename` no longer work in networking.k8s.io/v1 Ingress?\n"
            "A: [\n"
            '  "The answer should ensure the backend uses `service.name` and `service.port.number` instead of the old fields.",\n'
            '  "The answer should mention that `pathType` is now REQUIRED for every HTTP path."\n'
            "]\n\n"
            "Example 2:\n"
            "Q: How can I share files between two containers in the same Pod?\n"
            "A: [\n"
            '  "The answer should ensure you define a single `emptyDir` (or other) volume in the Pod spec.",\n'
            '  "The answer should mention mounting that same volume into both containers."\n'
            "]\n\n"
            f"Now you for Q: {question}\n"
            "A:"
        )
    }

    # 2) Call the model
    resp = client.chat.completions.create(
        model=EVAL_MODEL,
        messages=[system, few_shot],
        temperature=0.0,
        max_tokens=256,
    )
    content = resp.choices[0].message.content.strip()

    # 1) Strict JSON parse and count check
    arr = _safe_json_load(content)
    if not isinstance(arr, list) or len(arr) != n:
        # dump content to logs here
        raise ValueError(f"Expected {n} items, got {len(arr)}: {content!r}")

    # 2) Filter by prefix regex
    PREFIX_RE = re.compile(r'^The answer should (?:ensure|mention)', re.IGNORECASE)
    def valid(h): return len(h.split()) >= 6 and bool(PREFIX_RE.match(h))
    hyps = [h.strip() for h in arr if isinstance(h, str) and valid(h)]

    # 3) If somehow fewer, pad only with valid raw lines
    raw_lines = [ln.strip(" -•`[]") for ln in content.splitlines() if ln.strip()]
    for ln in raw_lines:
        if valid(ln) and ln not in hyps:
            hyps.append(ln)
        if len(hyps) == n:
            break

    # 4) Final pad with blank strings if still too few
    hyps += [""] * (n - len(hyps))
    return hyps[:n]









# ── Hypothesis Evaluation via NLI ───────────────────────────────────────────────
def evaluate_hypothesis_nli(premise: str, hypothesis: str) -> Dict[str, Any]:
    messages = [
        {
            "role": "system",
            "content": (
                "You are a strict Kubernetes fact‑checker. "
                "Given a piece of text and a single claim, decide if the text fully supports the claim. "
                "Respond ONLY with JSON in this exact format: "
                '{"entailment":"Yes" or "No","confidence":<float between 0 and 1>}.'
            )
        },
        {
            "role": "user",
            "content": f"""
            Example 1:
            Premise:
            \"\"\"
            Pods consume ConfigMaps via envFrom and volumes.
            \"\"\"
            Claim:
            \"Pods automatically reload when a ConfigMap changes.\"
            Response: {{"entailment":"No","confidence":0.90}}

            Example 2:
            Premise:
            \"\"\"
            The Ingress spec.rules[].http.pathType must be Exact, Prefix, or ImplementationSpecific.
            \"\"\"
            Claim:
            \"`pathType` is a required field.\"
            Response: {{"entailment":"Yes","confidence":0.95}}

            Now evaluate the following:

            Premise:
            \"\"\"
            {premise}
            \"\"\"

            Claim:
            \"{hypothesis}\"

            Is the claim fully supported by the premise? Reply only with the JSON.
            """
        }
    ]

    resp = client.chat.completions.create(
        model=NLI_MODEL,
        messages=messages,
        temperature=0.0,
        max_tokens=50,
    )
    out = resp.choices[0].message.content.strip()
    data = _safe_json_load(out) or {}
    ent = str(data.get("entailment", "No")).lower().startswith("y")
    conf = float(data.get("confidence", 0.0))
    return {"entailment": ent, "confidence": conf}


def evaluate_hypotheses(answer: str, hypotheses: List[str]) -> List[Dict[str, Any]]:
    return [
        {
            "hypothesis": h,
            **evaluate_hypothesis_nli(answer, h)
        }
        for h in hypotheses
    ]

def evaluate_entry(entry: dict) -> dict:
    q, a = entry["question"], entry["generated_response"]

    # Step 1: Generate hypotheses
    hyps = generate_hypotheses(q, n=3)

    # Step 2: Filter out non-lexical hypotheses
    filtered = [h for h in hyps if _overlaps(q, h) and len(h.split()) > 4]
    if not filtered:
        entry.update({
            "hypotheses": hyps,
            "hypotheses_evaluations": [],
            "fallback_used": True,
            "is_correct": False,
            "confidence_score": 0.0
        })
        return entry

    hyps = filtered

    # Step 3: Evaluate each hypothesis via NLI
    hyp_evals = evaluate_hypotheses(a, hyps)
    passed = sum(e["entailment"] for e in hyp_evals)

    # Step 4: Dynamic threshold: majority of evaluated hypotheses must pass
    needed = max(1, len(hyp_evals) // 2 + 1)
    is_correct = passed >= needed

    # Step 5: Blended confidence (only count passing ones)
    pass_confs = [e["confidence"] for e in hyp_evals if e["entailment"]]
    conf_score = round(float(np.mean(pass_confs)), 3) if pass_confs else 0.0

    # Step 6: Update entry
    entry.update({
        "hypotheses": hyps,
        "hypotheses_evaluations": hyp_evals,
        "fallback_used": False,
        "is_correct": is_correct,
        "confidence_score": conf_score
    })

    return entry







import json
import os

def evaluate_all(input_path: str, output_path: str, debug_path: str = None):
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    out = []
    debug_cases = []

    for idx, ent in enumerate(data[:150], 1):
        print(f"[{idx}/{len(data)}] {ent['question'][:50]}...")
        result = evaluate_entry(ent)
        out.append(result)

        # Collect any “unlikely” cases for debugging:
        if not result["is_correct"] or result["confidence_score"] < 0.5:
            debug_cases.append({
                "question": ent["question"],
                "answer":   ent["generated_response"],
                "is_correct": result["is_correct"],
                "confidence_score": result["confidence_score"],
                "hypotheses": result["hypotheses"],
                "hypotheses_evaluations": result["hypotheses_evaluations"],
            })

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(out)} entries to {output_path}")

    # Dump debug cases if path given
    if debug_path:
        os.makedirs(os.path.dirname(debug_path), exist_ok=True)
        with open(debug_path, "w", encoding="utf-8") as f:
            json.dump(debug_cases, f, indent=2, ensure_ascii=False)
        print(f" Wrote {len(debug_cases)} debug cases to {debug_path}")



# ── Utilities ──────────────────────────────────────────────────────────────────
def _safe_json_load(s: str) -> Any:
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        return None

def _overlaps(question: str, hypothesis: str) -> bool:
    """
    Quick token‐overlap filter so we only fall back when none of the generated
    hypotheses even share a single word with the question.
    """
    q_tokens = set(re.findall(r"[A-Za-z0-9_]+", question.lower()))
    h_tokens = set(re.findall(r"[A-Za-z0-9_]+", hypothesis.lower()))
    return bool(q_tokens & h_tokens)

# ── CLI Hook ───────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Strict NLI‑based evaluator")
    p.add_argument("--input",  "-i", required=True, help="Processed JSON input")
    p.add_argument("--output", "-o", required=True, help="Evaluated JSON output")
    p.add_argument("--debug", required=False, help="Path to debug output (e.g. misclassified entries)")
    args = p.parse_args()
    evaluate_all(args.input, args.output, args.debug)
