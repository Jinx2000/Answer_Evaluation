import shlex

def validate_cli_command(command: str):
    try:
        shlex.split(command)
        return {"cli_syntax_pass": True}
    except Exception as e:
        return {"cli_syntax_pass": False, "error": str(e)}
