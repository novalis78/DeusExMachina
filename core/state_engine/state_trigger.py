import json
import os
import subprocess

STATE_FILE = "/var/log/deus-ex-machina/state.json"
BREATH_SCRIPT = "/opt/deus-ex-machina/core/breath/breath.sh"
VIGILANCE_SCRIPT = "/opt/deus-ex-machina/core/vigilance/vigilance.sh"

# Load current state
def load_state():
    if not os.path.exists(STATE_FILE):
        return {"state": "normal"}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

# Trigger script and log output
def trigger(script_path):
    if os.path.exists(script_path):
        subprocess.run(["bash", script_path], check=False)
    else:
        print(f"Script not found: {script_path}")

# Main routine
def main():
    state = load_state()
    current_state = state.get("state", "normal")

    if current_state == "suspicious":
        print("[Trigger] Running breath module")
        trigger(BREATH_SCRIPT)

    elif current_state in ["alert", "critical"]:
        print("[Trigger] Running breath and vigilance modules")
        trigger(BREATH_SCRIPT)
        trigger(VIGILANCE_SCRIPT)

    else:
        print("[Trigger] No action needed in state:", current_state)

if __name__ == "__main__":
    main()

