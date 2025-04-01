# Deus Ex Machina

> A self-aware, token-efficient AI agent designed to maintain, monitor, and protect a Linux server through intelligent observation cycles: heartbeat, breath, and vigilance.

## Vision

**Deus Ex Machina** is a lightweight, modular, and optionally AI-augmented system that brings mindfulness to machine maintenance. Inspired by the biological rhythms of life and consciousness, this system ensures the continuous well-being of a Linux server without excessive resource use. It makes decisions based on priority, context, and a limited budget (token or compute/time-based).

## Core Principles

- **Minimal Impact**: Every operation should justify its resource cost.
- **Situational Awareness**: The agent should always know the current system state with high confidence.
- **Event Responsiveness**: Escalate awareness depth only when conditions change.
- **Modularity**: Each module can run independently or cooperatively.
- **Auditability**: Every decision and state transition is logged and explainable.

---

## Layers of Awareness

### 1. Heartbeat (every 30s to 2 min)
- Liveness checks: CPU, RAM, disk usage, essential process health
- Port scans, interface status, system load average
- Deltas stored locally and optionally reported externally

### 2. Breath (every 10–30 min)
- Hashes of config files and binaries
- File size/permissions in key paths (e.g., /etc, /usr/bin, /home)
- Systemd status, cron jobs, new services
- Resource trend analysis

### 3. Vigilance (event-triggered or hourly)
- Deep file diffing via Merkle tree
- Anomaly detection in auth logs and system events
- Suspicious network traffic, unexpected listeners
- Optional AI summarization and response planning

---

## State Machine

| State        | Description                                  | Action Scope           |
|--------------|----------------------------------------------|------------------------|
| Normal       | All systems operating within tolerance       | Heartbeat only        |
| Suspicious   | Minor anomalies detected                     | Heartbeat + Breath     |
| Alert        | Clear deviation or risk                      | Trigger Vigilance      |
| Critical     | Confirmed compromise or failure              | Dump logs + Harden     |

Each state has a TTL (time to live) and a decay or escalation path based on persistent anomalies or resolution.

---

## Technical Stack

### Languages & Tools
- Bash, Python
- sha256sum, diff, rsync, eBPF, inotify, auditd
- TUI: fzf, glow, gum, htop, ncdu
- AI: Optional integration with OpenAI, local models, or summarizers

### Optional Integrations
- Prometheus + Grafana
- Matrix or Signal alert bots
- Docker / systemd packaging

---

## Project Tree and Module Work Plan

```
/ (repo root)
├── README.md
├── LICENSE
├── docs/
│   └── design.md
├── core/
│   ├── heartbeat/
│   │   ├── heartbeat.sh
│   │   └── heartbeat_test.sh
│   ├── breath/
│   │   ├── file_hashing.py
│   │   └── service_check.sh
│   ├── vigilance/
│   │   ├── merkle_tree.py
│   │   ├── log_analyzer.py
│   │   └── vigilance.sh
│   ├── state_engine/
│   │   ├── state.json
│   │   └── transition.py
├── utils/
│   ├── diffing.py
│   ├── notifier.sh
│   └── telemetry.sh
├── config/
│   └── paths.yaml
└── scripts/
    ├── install.sh
    └── run_all.sh
```

---

## Initial Work Packages (Phase 1)

### [1] Heartbeat Module
- [ ] CPU/RAM/Disk monitor (bash)
- [ ] Process liveness (bash)
- [ ] Network interface status
- [ ] Delta diffing & simple JSON output

### [2] Breath Module
- [ ] Hash known config files
- [ ] Diff systemd service state
- [ ] New cronjobs / user scripts detection

### [3] Vigilance Module
- [ ] Merkle tree implementation
- [ ] Auth log anomaly patterns
- [ ] Traffic pattern detector (optional eBPF)

### [4] State Engine
- [ ] Define state logic in `transition.py`
- [ ] JSON-based current state + TTL tracker
- [ ] Trigger scope execution based on state

### [5] Utility & Output
- [ ] Logging system with minimal format
- [ ] Alert notification via shell/email/api
- [ ] Optional AI summary endpoint

---

## Contributing

All contributions are welcome—code, ideas, design, performance suggestions. This project will live and breathe through its community. PRs should include test coverage and follow the modular separation of duties.

To join the project:
1. Fork the repo
2. Clone and explore
3. Look for open issues or create one
4. Submit a PR with detailed rationale

---

## License
MIT

## Acknowledgments
- Unix philosophy
- Biological metaphors
- Systems that whisper before they scream

