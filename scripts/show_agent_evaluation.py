from pathlib import Path
import importlib.util
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EVALUATION_FILE = PROJECT_ROOT / "backend" / "agents" / "evaluation.py"

spec = importlib.util.spec_from_file_location("agent_evaluation", EVALUATION_FILE)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Could not load evaluation file: {EVALUATION_FILE}")

agent_evaluation = importlib.util.module_from_spec(spec)
sys.modules["agent_evaluation"] = agent_evaluation
spec.loader.exec_module(agent_evaluation)


if __name__ == "__main__":
    print(agent_evaluation.format_local_evaluation())
