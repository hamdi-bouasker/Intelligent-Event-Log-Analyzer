### Intelligent-Event-Log-Analyzer
An enterprise-grade, closed-loop automation system for Windows Server environments. This project integrates PowerShell event monitoring with a Python-based AI middleware (powered by Google's Gemini API) to proactively detect system anomalies, triage root causes, and safely execute self-healing remediation workflows.

🚀 #Features
Proactive Anomaly Detection: Utilizes a lightweight PowerShell listener to filter noisy Windows Event Logs, capturing only critical system and application errors in near real-time.

AI-Powered Triage: Integrates with the Gemini 1.5 Pro API using strict JSON schema enforcement to analyze log data and diagnose infrastructure failures without hallucination.

Closed-Loop Self-Healing: Automatically resolves known issues (e.g., service crashes, DNS cache corruption) without human intervention.

Zero-Trust Execution Model: The AI does not have open terminal access. All remediation actions are validated against a strict, hardcoded allowlist of pre-approved PowerShell scripts to ensure absolute security and prevent destructive commands.

Audit-Ready Logging: Maintains comprehensive local logs of all AI decisions, unauthorized command attempts, and successful remediations for SRE review.

🏗️ # Architecture
The system is built on a decoupled, event-driven architecture:

Data Collection (PowerShell): Collect-EventLogs.ps1 runs via Windows Task Scheduler. It queries the System and Application event logs for Level 1 (Critical) and Level 2 (Error) events, sanitizes the data, and writes it to a local JSON queue.

AI Middleware (Python): sre_agent.py acts as a daemon monitoring the queue. When an error is detected, it formats a strict prompt and queries the Gemini API for a diagnosis and a remediation key.

Remediation Engine: The Python script parses the AI's JSON response, validates the requested remediation key against the security Allowlist, and uses subprocess to execute the necessary PowerShell fix.

#🛠️ Prerequisites
OS: Windows Server 2016 or higher (or Windows 10/11 for local testing).

Runtime: Python 3.8+

API Key: A valid Google Gemini API Key.

Permissions: Administrator privileges are required to read Event Logs and execute service-level PowerShell commands.

#⚙️ Installation & Setup
1. Clone the repository:

Bash
```bash
git clone https://github.com/hamdi-bouasker/Intelligent-Event-Log-Analyzer.git
cd sre-auto-healer
```
2. Install dependencies:

Python
```python
pip install -r requirements.txt
```
3. Configure the environment:
Set your Gemini API key as a system environment variable.

PowerShell
```PowerShell
[System.Environment]::SetEnvironmentVariable('GEMINI_API_KEY', 'your_api_key_here', [System.EnvironmentVariableTarget]::Machine)
```
4. Set up the Directory Structure:
Ensure the script paths match your environment. By default, the scripts expect the following structure:

C:\SRE_Agent\queue\ (For the JSON event queue)

C:\SRE_Agent\logs\ (For the agent action logs)

5. Schedule the Event Listener:
Open Windows Task Scheduler and create a new basic task to run Collect-EventLogs.ps1 every 5 minutes with the highest privileges.

#🔒 Security & Compliance Note
This tool is designed with Site Reliability Engineering (SRE) best practices in mind:

No PII Leakage: The PowerShell extraction phase filters out raw event payloads, sending only structured metadata (Event ID, Provider, standard error messages) to the LLM.

Rate Limiting: The queue system prevents overlapping executions and API spam during cascading failure events.

Execution Allowlist: The AI cannot generate arbitrary code. It can only request execution keys mapped to safe, pre-tested commands (e.g., Restart-IIS, Clear-DNS).
