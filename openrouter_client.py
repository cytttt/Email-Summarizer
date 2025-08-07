import os
import requests
import time
import random
from dotenv import load_dotenv
from utils import parse_openrouter_response, log_warning, log_info

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL = os.getenv("MODEL_NAME")

def summarize_and_classify(email, max_retries=3, base_delay=1):
    """
    Summarize and classify email using OpenRouter API.

    return:
        dict, contains email id, subject, from, and output
    """
    prompt = f"""
Given the following email content, perform 3 tasks:
1. Summarize the email in 1-2 sentences.
2. Classify it into one of: Academic, Career, Notification, Ads, Other.
3. Rate its importance from 1 (low) to 3 (high), with reason.

- If it's related to a verification code, just give it a low score since I've probably already entered it.

Respond in this JSON format:
{{
  "summary": "...",
  "category": "...",
  "importance": 1,
  "reason": "..."
}}

Email content:
---
Subject: {email['subject']}
From: {email['from']}
Body:
{email['body']}
---
"""
    
    for attempt in range(max_retries + 1):
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a helpful email assistant."},
                        {"role": "user", "content": prompt}
                    ]
                }
            )
            
            response_json = response.json()
            
            # Check for rate limiting (429) or other retryable errors
            if response.status_code == 429:
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    log_warning(f"Rate limited (attempt {attempt + 1}/{max_retries + 1}). Retrying in {delay:.1f}s...")
                    time.sleep(delay)
                    continue
                else:
                    raise RuntimeError(f"Rate limit exceeded after {max_retries + 1} attempts")
            
            # Other errors
            if "choices" not in response_json:
                error_msg = response_json.get('error', 'Unknown error')
                raise RuntimeError(f"OpenRouter error: {error_msg}")
            
            # Success
            output = response_json["choices"][0]["message"]["content"]
            if attempt > 0:
                log_info(f"Successfully processed email after {attempt + 1} attempts")
            
            cleaned_output = parse_openrouter_response(output)
            if not cleaned_output:
                raise RuntimeError(f"OpenRouter error: {output}")
            
            return {
                "id": email["id"],
                "subject": email["subject"],
                "from": email["from"],
                "output": cleaned_output
            }
            
        except Exception as e:
            if attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                log_warning(f"Unexpected error (attempt {attempt + 1}/{max_retries + 1}): {str(e)}. Retrying in {delay}s...")
                time.sleep(delay)
                continue
            else:
                raise RuntimeError(f"OpenRouter error after {max_retries + 1} attempts: {str(e)}")
