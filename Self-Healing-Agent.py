import json
import os
import subprocess
import time
import logging
import google.generativeai as genai

# ==========================================
# CONFIGURATION & SECURITY
# ==========================================
QUEUE_FILE = r"C:\SRE_Agent\queue\event_queue.json"
LOG_FILE = r"C:\SRE_Agent\logs\agent_action.log"
API_KEY = os.environ.get("GEMINI_API_KEY")

# STRICT ALLOWLIST: The AI is ONLY allowed to execute these specific commands.
# This prevents the AI from hallucinating destructive commands like 'Remove-Item'
ALLOWLIST = {
    "Restart-Spooler": "Restart-Service -Name Spooler -Force",
    "Restart-IIS": "iisreset",
    "Clear-DNS": "Clear-DnsClientCache",
    "Restart-WinUpdate": "Restart-Service -Name wuauserv -Force"
}

# Setup Logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s"
)

# ==========================================
# AI INITIALIZATION
# ==========================================
def initialize_ai():
    if not API_KEY:
        raise ValueError("GEMINI_API_KEY environment variable is missing.")
    
    genai.configure(api_key=API_KEY)
    
    # Define the required JSON schema for the AI's response
    schema = {
        "type": "object",
        "properties": {
            "diagnosis": {"type": "string"},
            "action_required": {"type": "boolean"},
            "remediation_key": {"type": "string", "description": f"Must be one of: {list(ALLOWLIST.keys())} or 'None'"}
        },
        "required": ["diagnosis", "action_required", "remediation_key"]
    }
    
    # Initialize the model with structured output enforced
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        generation_config={
            "temperature": 0.1, # Low temperature for analytical consistency
            "response_mime_type": "application/json",
            "response_schema": schema
        },
        system_instruction=(
            "You are an elite Site Reliability Engineer (SRE) AI system. "
            "Analyze the provided Windows Event logs. Identify the root cause of the crash or error. "
            "If the issue is known and can be fixed with one of the provided remediation keys, set action_required to true. "
            "Do not hallucinate commands. Only use the provided remediation keys."
        )
    )
    return model

# ==========================================
# EXECUTION ENGINE
# ==========================================
def execute_remediation(remediation_key):
    if remediation_key not in ALLOWLIST:
        logging.warning(f"Security Block: AI attempted to run unauthorized command key: {remediation_key}")
        return False
    
    command = ALLOWLIST[remediation_key]
    logging.info(f"Executing self-healing command: {command}")
    
    try:
        # Execute the PowerShell command safely
        result = subprocess.run(
            ["powershell.exe", "-Command", command],
            capture_output=True,
            text=True,
            check=True
        )
        logging.info(f"Command successful. Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Command failed. Error: {e.stderr.strip()}")
        return False

# ==========================================
# MAIN LOOP
# ==========================================
def process_queue():
    if not os.path.exists(QUEUE_FILE):
        return

    logging.info("New event log detected. Initiating AI analysis...")
    
    with open(QUEUE_FILE, "r", encoding="utf-8") as file:
        try:
            event_data = json.load(file)
        except json.JSONDecodeError:
            logging.error("Failed to parse JSON queue file.")
            os.remove(QUEUE_FILE)
            return

    # Convert the log data to a string for the prompt
    log_payload = json.dumps(event_data, indent=2)
    prompt = f"Analyze these recent Windows Event Logs:\n{log_payload}\nAvailable Remediation Keys: {list(ALLOWLIST.keys())}"

    try:
        model = initialize_ai()
        response = model.generate_content(prompt)
        
        # Parse the guaranteed JSON response
        ai_decision = json.loads(response.text)
        
        logging.info(f"AI Diagnosis: {ai_decision.get('diagnosis')}")
        
        if ai_decision.get("action_required") and ai_decision.get("remediation_key") != "None":
            logging.info(f"AI requested self-healing action: {ai_decision.get('remediation_key')}")
            execute_remediation(ai_decision.get("remediation_key"))
        else:
            logging.info("No automated action required by AI.")

    except Exception as e:
        logging.error(f"AI API request failed: {e}")
    finally:
        # Clean up the queue file after processing to prevent duplicate runs
        os.remove(QUEUE_FILE)
        logging.info("Queue cleared. Awaiting next event cycle.")

if __name__ == "__main__":
    process_queue()