import json
import os
from datetime import datetime, timedelta

STATE_FILE = "/var/log/deus-ex-machina/state.json"
HEARTBEAT_FILE = "/var/log/deus-ex-machina/heartbeat.json"

DEFAULT_STATE = {
    "state": "normal",
    "last_transition": datetime.now().isoformat(),
    "ttl_seconds": 600
}

TRANSITIONS = {
    "normal": {
        "thresholds": {"cpu_load": 1.0, "open_ports": 100},
        "next": "suspicious",
        "previous": None
    },
    "suspicious": {
        "thresholds": {"cpu_load": 2.0, "open_ports": 150},
        "next": "alert",
        "previous": "normal"
    },
    "alert": {
        "thresholds": {"cpu_load": 4.0, "open_ports": 200},
        "next": "critical",
        "previous": "suspicious"
    },
    "critical": {
        "thresholds": {},
        "next": "critical",
        "previous": "alert"
    }
}

def load_state():
    if not os.path.exists(STATE_FILE):
        return DEFAULT_STATE
    with open(STATE_FILE, 'r') as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def should_escalate(current_metrics, state):
    current_state = state["state"]
    thresholds = TRANSITIONS[current_state]["thresholds"]
    for key, value in thresholds.items():
        try:
            if float(current_metrics.get(key, 0)) > value:
                return True
        except (ValueError, TypeError):
            continue
    return False

def should_decay(state):
    last = datetime.fromisoformat(state["last_transition"])
    return datetime.now() > last + timedelta(seconds=state["ttl_seconds"])

def transition_state(current_metrics):
    state = load_state()
    current_state = state["state"]

    if should_escalate(current_metrics, state):
        next_state = TRANSITIONS[current_state]["next"]
        if next_state != current_state:
            print(f"Escalating to {next_state}")
            state["state"] = next_state
            state["last_transition"] = datetime.now().isoformat()
            save_state(state)
            return state

    elif should_decay(state):
        previous_state = TRANSITIONS[current_state].get("previous")
        if previous_state and previous_state != current_state:
            print(f"Decaying to {previous_state}")
            state["state"] = previous_state
            state["last_transition"] = datetime.now().isoformat()
            save_state(state)
            return state

    # No change
    save_state(state)
    return state

def main():
    if not os.path.exists(HEARTBEAT_FILE):
        print("Heartbeat file not found.")
        return

    with open(HEARTBEAT_FILE) as f:
        metrics = json.load(f)

    # Convert types if needed
    try:
        metrics["cpu_load"] = float(metrics.get("cpu_load", 0))
        metrics["open_ports"] = int(metrics.get("open_ports", 0))
    except Exception as e:
        print(f"Error parsing metrics: {e}")

    updated_state = transition_state(metrics)
    print("Current state:", updated_state["state"])

if __name__ == "__main__":
    main()
