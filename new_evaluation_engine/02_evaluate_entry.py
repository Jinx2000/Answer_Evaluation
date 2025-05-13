from . import validate_cli_command 
from . import extract_yaml_from_response
from . import validate_yaml_kube_tools
from . import run_ragas_scores
def evaluate_entry(entry):
    category = entry.get("output_category")
    response = entry.get("generated_response")

    if category == "YAML":
        yaml_text = extract_yaml_from_response(response)
        return validate_yaml_kube_tools(yaml_text)

    elif category == "CLI":
        return validate_cli_command(response)

    elif category == "Explanation":
        return run_ragas_scores(entry)  # or custom text classifier

    else:
        return {"note": "unscored or unknown format"}
