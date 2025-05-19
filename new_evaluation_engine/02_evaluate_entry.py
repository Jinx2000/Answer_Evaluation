# evaluator.py
import os
import json
import re
from typing import List, Dict, Any

from dotenv import load_dotenv
from openai import OpenAI

# ── Setup ────────────────────────────────────────────────────────────────────────
load_dotenv()  # loads OPENAI_API_KEY from .env
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY is not set in your .env file!")

client = OpenAI(api_key=api_key)

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
def generate_hypotheses(question: str, n: int = 5) -> List[str]:
    # Build few‑shot block
    shots = [f"Q: {ex['question']}\nA: {json.dumps(ex['hypotheses'])}"
             for ex in _FEW_SHOT]
    few_shot_block = "\n\n".join(shots)

    prompt = f"""
You are a Kubernetes expert.  For each user question below, list the top {n}
specific facts or API‑level statements that a *correct* answer *must* cover.
Include version numbers when relevant (e.g. “Since v1.24…”).  Output **only**
a JSON array of strings.

{few_shot_block}

Q: {question}
A:
"""
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=256,
    )
    content = resp.choices[0].message.content.strip()
    arr = _safe_json_load(content)

    if isinstance(arr, list) and all(isinstance(x, str) for x in arr):
        return arr[:n]
    # fallback
    lines = [l.strip(" -•123.") for l in content.splitlines() if l.strip()]
    return lines[:n]

# ── Hypothesis Evaluation via NLI ───────────────────────────────────────────────
def evaluate_hypothesis_nli(premise: str, hypothesis: str) -> Dict[str, Any]:
    prompt = f"""
You are a Kubernetes expert.

Premise:
\"\"\"
{premise}
\"\"\"

Hypothesis:
\"{hypothesis}\"

Question: Does the premise *entail* the hypothesis?
Reply *only* with JSON, no extra text:

{{"entailment": "Yes" or "No", "confidence": <float between 0 and 1>}}
"""
    resp = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=20,
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

    # 1) Generate hypotheses
    hyps = generate_hypotheses(q, n=3)

    # 1a) Fallback: if none of the hypotheses share any tokens with the question,
    # mark as incorrect immediately
    filtered = [h for h in hyps if _overlaps(q, h)]
    if not filtered:
        entry["hypotheses"] = hyps
        entry["hypotheses_evaluations"] = []
        entry["fallback_used"] = True
        entry["is_correct"] = False
        entry["confidence_score"] = 0.0
        return entry
    hyps = filtered

    # 2) Evaluate each hypothesis via NLI
    hyp_evals = evaluate_hypotheses(a, hyps)

    # 3) Meta‑check: does the answer fully address the question?
    meta_hyp = "The provided answer correctly and completely answers the user's question."
    meta_ev = evaluate_hypothesis_nli(a, meta_hyp)
    meta_pass = meta_ev["entailment"] and meta_ev["confidence"] >= 0.7

    # 4) k‑of‑n coverage: require at least 2 of 3 hypotheses to pass
    passed = sum(e["entailment"] for e in hyp_evals)
    cov_pass = (passed >= 2)

    # 5) Final correctness flag
    entry["is_correct"] = bool(meta_pass and cov_pass)
    entry["fallback_used"] = False

    # 6) Blended confidence score (50% meta, 50% hypothesis average)
    meta_w = 0.5
    hyp_w = 0.5 / len(hyp_evals)
    blended = meta_w * meta_ev["confidence"] + sum(e["confidence"] * hyp_w for e in hyp_evals)
    entry["confidence_score"] = round(blended, 3)

    # 7) Keep diagnostics
    entry["hypotheses"] = hyps
    entry["hypotheses_evaluations"] = hyp_evals

    return entry


def evaluate_all(input_path: str, output_path: str):
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    out = []
    for idx, ent in enumerate(data, 1):
        print(f"[{idx}/{len(data)}] {ent['question'][:50]}...")
        out.append(evaluate_entry(ent))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"✅ Wrote {len(out)} entries to {output_path}")


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
    args = p.parse_args()
    evaluate_all(args.input, args.output)
