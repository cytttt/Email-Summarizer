import os
import time
import sys
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from flask import Flask, request, jsonify

from gmail_client import fetch_recent_emails
from notify_discord import notify_discord
from openrouter_client import summarize_and_classify
from utils import log_error, log_info

USE_MOCK = "--mock" in sys.argv
USE_LOCAL = "--local" in sys.argv
# Load environment variables
load_dotenv()

# Create Flask app for Cloud Run
app = Flask(__name__)
INTERVAL = int(os.getenv("INTERVAL_IN_HOUR", 6))

def run_agent():
    log_info("[Agent] Starting mail summarizer agent...")

    try:
        if USE_MOCK:
            from mocks import fetch_mock_emails, fake_llm_response
            emails = fetch_mock_emails()
            for email in emails:
                log_info(f"[Agent] Processing: {email['subject']}")
                result = fake_llm_response(email)
                log_info(f"[Agent] Reason: {result['output']['reason']}")
        else:
            from gmail_client import fetch_recent_emails
            from openrouter_client import summarize_and_classify
            
            emails = fetch_recent_emails(INTERVAL, local_mode=USE_LOCAL)

            log_info(f"[Agent] Fetched {len(emails)} emails")

            results = []
            # for email in [emails[1]]:
            for email in emails:
                try:
                    log_info(f"[Agent] Processing: {email['subject']}")
                    result = summarize_and_classify(email)
                    log_info(f"[Agent] Reason: {result['output']['reason']}")
                    results.append(result)
                except Exception as e:
                    log_error(f"Failed to process email {email.get('id')}: {e}")

            # Output to discord
            notify_discord(results)

    except Exception as e:
        log_error(f"[Agent] Fatal error: {e}")

    log_info("[Agent] Done.")

@app.route('/', methods=['GET', 'POST'])
def handle_request():
    """Handle HTTP requests from Cloud Scheduler or manual triggers"""
    try:
        log_info("[CloudRun] Received HTTP request")
        run_agent()
        return jsonify({"status": "success", "message": "Email processing completed"}), 200
    except Exception as e:
        log_error(f"[CloudRun] Error processing request: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Cloud Run"""
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    # Check if running in Cloud Run environment
    port = int(os.environ.get('PORT', 8080))
    if os.environ.get('K_SERVICE'):
        # Running in Cloud Run
        log_info(f"[CloudRun] Starting server on port {port}")
        app.run(host='0.0.0.0', port=port)
    else:
        # Running locally
        run_agent()
