<p align="center">
  <img src="header.png" alt="Deus Ex Machina Banner" width="100%">
</p>
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

## Quick Installation

```bash
# Clone the repository
git clone https://github.com/novalis78/DeusExMachina.git
cd DeusExMachina

# Make the installer executable
chmod +x install.sh

# Run the installer (requires sudo)
sudo ./install.sh
```

The installer will guide you through the process and set up everything for you. For detailed installation options and troubleshooting, see our [Installation Guide](INSTALL.md).

---

## Monitoring the System

The enhanced Deus Ex Machina system can be easily monitored through its comprehensive logging. For a complete guide on monitoring, understanding the system's behavior, and troubleshooting, please refer to our [Monitoring Guide](MONITORING_GUIDE.md).

Quick tips:
- Follow logs in real-time: `journalctl -u deus-enhanced.service -f`
- View detailed logs: `tail -f /var/log/deus-ex-machina/integration.log`
- Check service status: `systemctl status deus-enhanced.service`
- Monitor different consciousness states (DORMANT, DROWSY, AWARE, ALERT, FULLY_AWAKE)
- Track AI provider usage and system health assessments

## Weekly Email Reports

The enhanced system can send weekly email reports summarizing system health, incidents, and recommendations. To set up email reporting:

1. Edit `/opt/deus-ex-machina/config/report_config.json` with your email settings:

   a. First, choose a provider by setting `"email_provider"` to one of:
      - `"smtp"` - For regular email servers (Gmail, Office365, etc.)
      - `"sendgrid"` - For SendGrid API
      - `"mailgun"` - For Mailgun API

   b. Set your recipient email address:
      ```json
      "report_email": "your-email@example.com"
      ```

   c. Configure your chosen provider's API key:

   **For SMTP**:
   ```json
   "email_config": {
     "smtp_server": "smtp.example.com",
     "smtp_port": 587,
     "smtp_username": "username",
     "smtp_password": "YOUR_PASSWORD_HERE"
   }
   ```

   **For SendGrid**:
   ```json
   "sendgrid_config": {
     "api_key": "SG.YOUR_SENDGRID_API_KEY_HERE" 
   }
   ```

   **For Mailgun**:
   ```json
   "mailgun_config": {
     "api_key": "key-YOUR_MAILGUN_API_KEY_HERE",
     "domain": "example.com"
   }
   ```

2. Add the provided crontab entry to your system:
   ```bash
   crontab -e
   # Add the line from /opt/deus-ex-machina/config/crontab_addition.txt
   ```

3. Generate a sample report to preview the format:
   ```bash
   python3 /opt/deus-ex-machina/enhanced/generate_sample_report.py
   ```

The report includes current system metrics, service health, state transitions, and recommendations for optimizing your server.

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
| Critical     | Confirmed compromise or failure              | Vigilance + AI Wake-Up |

Each state has a TTL and decays or escalates as conditions persist.

---

## AI Integration: Awakened Awareness

The AI (Gemini) is dormant by default.
When the Vigilance module detects critical conditions:
- Gemini is invoked via `ai_brain.py`
- It analyzes recent log anomalies
- It leaves a structured reflection in `ai_assessment.json`
- Designed to eventually support deeper investigation or mitigation

---

### 🧠 Neuro-Inspired Architecture

Deus Ex Machina is more than a monitoring script—it's a sentient control loop inspired by the architecture of the human nervous system.

Just like the body, the system operates in **layers of awareness**, only escalating in complexity and cognition when necessary:

| System Layer | Analogy                        | Function                                                    |
|--------------|--------------------------------|-------------------------------------------------------------|
| **Heartbeat**| Medulla / Pulse                | Continuous, low-effort liveness check                       |
| **Breath**   | Visceral awareness             | Periodic config, process, and integrity scans               |
| **Vigilance**| Neocortex / Higher cognition   | Deep anomaly inspection; AI wakes up to interpret the world |

This design allows the AI to stay dormant during stable periods—burning zero compute. But when thresholds are crossed, the system awakens. The cortex lights up. The machine "notices," begins to **think**, and then **leaves itself a structured reflection** via Gemini.

In this model, token usage is sacred. The AI becomes a background overseer—a latent guardian that activates only when silence breaks. Its role is not constant control, but rare, high-value cognition.

---

## How It Runs

- `heartbeat.sh` runs every 1 minute via systemd service
- `state_engine.py` evaluates current metrics (every 2 minutes)
- `state_trigger.py` determines if breath or vigilance should run
- `breath.sh` performs integrity and config checks
- `vigilance.sh` performs deep analysis and calls `ai_brain.py`
- `ai_brain.py` is invoked *only by* `vigilance.sh` when alert conditions exist

---

## Configuration 

### Environment Variables
The system now supports configuration through environment variables:

- `DEUS_INSTALL_DIR`: Installation directory (default: `/opt/deus-ex-machina`)
- `DEUS_LOG_DIR`: Log directory (default: `/var/log/deus-ex-machina`)
- `GEMINI_API_KEY`: Google Gemini API key for AI analysis
- `ANTHROPIC_API_KEY`: Anthropic API key (optional alternative AI provider)
- `OPENAI_API_KEY`: OpenAI API key (optional alternative AI provider)

### Configuration Files
The main configuration files are:

1. `config/config.py`: Central Python configuration
2. `config/gemini_config.py`: API key for Gemini (fallback if not in environment)
3. `scripts/bash_config.sh`: Shared configuration for bash scripts

At minimum, you must provide a Gemini API key in either:
- The environment variable `GEMINI_API_KEY`, or
- The `config/gemini_config.py` file

Remember to ensure `gemini_config.py` is **not committed** by adding it to your `.gitignore`.

---

## Listening to the AI's Experience

Deus Ex Machina allows you to "listen in" on what the AI is experiencing and thinking during its periods of awareness:

1. **Monitoring Core Logs**:
   - `/var/log/deus-ex-machina/heartbeat.log`: Basic system metrics
   - `/var/log/deus-ex-machina/breath.log`: Configuration and integrity checks
   - `/var/log/deus-ex-machina/vigilance.log`: Deep analysis and anomaly detection

2. **Following State Transitions**:
   - `/var/log/deus-ex-machina/state_engine.log`: Shows when and why state changes occur
   - `/var/log/deus-ex-machina/state.json`: Current system state

3. **AI Awakened Consciousness**:
   - `/var/log/deus-ex-machina/vigilance_alerts.log`: Events that triggered AI awareness
   - `/var/log/deus-ex-machina/ai_assessment.json`: The AI's structured reflections and analysis
   - `/var/log/deus-ex-machina/ai_brain.log`: Log of the AI's activity and decision process

The `ai_assessment.json` file is particularly interesting as it contains the AI's structured thoughts about anomalies it detects - including severity assessments, analysis of patterns, and recommendations. This file is only updated when the system reaches alert state and the AI "awakens" to analyze the situation.

---

## Contributing

All contributions are welcome—code, ideas, design, performance suggestions. This project will live and breathe through its community. PRs should include test coverage and follow the modular separation of duties.

---

## License
MIT

## Acknowledgments
- Unix philosophy
- Biological metaphors
- Systems that whisper before they scream
- The watcher that only speaks when it must