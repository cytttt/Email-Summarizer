import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

import json
import re

def clean_email_text(text):
    # Remove unicode zero-width characters and invisible characters
    text = re.sub(r"[\u200b\u200c\u200d\u2060\u034f\u00ad]", "", text)

    # Remove extra newlines
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove multiple spaces
    text = re.sub(r"[ \u00a0\u2003]{5,}", " ", text)

    # Remove extra newlines
    text = re.sub(r"(?m)^\s+$", "", text)

    # Remove leading and trailing whitespace
    return text.strip()

# Catch ```json ... ``` block
def parse_openrouter_response(text):
    
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        cleaned = match.group(1)
    else:
        cleaned = text.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print("[Parser] JSON parsing failed:", e)
        print("[Parser] Raw content:\n", cleaned)
        return None

# Configure logging based on environment
handlers = [logging.StreamHandler()]  # Always log to console

# Only add file handler if not in Cloud Run
if not os.environ.get('K_SERVICE'):
    handlers.append(RotatingFileHandler(
        'email_agent.log', 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=0
    ))


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=handlers
)

logger = logging.getLogger(__name__)

def log_error(message):
    logger.error(message)

def log_info(message):
    logger.info(message)

def log_debug(message):
    logger.debug(message)

def log_warning(message):
    logger.warning(message)
