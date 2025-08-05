import os
import requests
from utils import log_info, log_warning, log_error
from dotenv import load_dotenv

load_dotenv()
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

def notify_discord(summary_list):
    """
    Send email summaries to Discord.
        Separate summaries into multiple messages if they exceed 2000 characters.
    """
    if not DISCORD_WEBHOOK_URL:
        log_warning("[Discord] No webhook URL found.")
        return

    if not summary_list:
        log_info("[Discord] No summary to send.")
        return

    log_info(f"[Discord] Sending {len(summary_list)} summaries.")
    
    # Split summaries into multiple messages to respect Discord's 2000 char limit
    messages = []
    current_message = ["**Email Summary**\n"]
    current_length = len("**Email Summary**\n")
    
    for i, summary in enumerate(summary_list, 1):
        email = summary["subject"]
        sender = summary["from"]
        output = summary["output"] if isinstance(summary["output"], dict) else {}
        category = output.get("category", "N/A")
        importance = output.get("importance", "?")
        abstract = output.get("summary", "(No summary)")

        # Format single summary
        summary_lines = [
            f"**{i}. [{category}] {importance * ':star:'}**",
            f"Subject: {email}",
            f"Sender: `{sender}`",
            f"> {abstract}",
            ""
        ]
        summary_text = "\n".join(summary_lines)
        summary_length = len(summary_text)
        
        # Check if adding this summary would exceed the limit
        if current_length + summary_length > 1950:
            # Save current message and start a new one
            if len(current_message) > 1:  # Only save if there's content beyond header
                messages.append("\n".join(current_message))
            
            # Start new message
            current_message = ["**Email Summary (continued)**\n"]
            current_length = len("**Email Summary (continued)**\n")
        
        # Add summary to current message
        current_message.extend(summary_lines)
        current_length += summary_length
    
    # Add the last message if it has content
    if len(current_message) > 1:
        messages.append("\n".join(current_message))
    
    # Send all messages
    total_messages = len(messages)
    successful_sends = 0
    
    for msg_index, message in enumerate(messages, 1):
        payload = {"content": message}
        
        try:
            resp = requests.post(DISCORD_WEBHOOK_URL, json=payload)
            if resp.status_code == 204:
                successful_sends += 1
                log_info(f"[Discord] Message {msg_index}/{total_messages} sent successfully.")
            else:
                log_error(f"[Discord] Message {msg_index}/{total_messages} failed ({resp.status_code}): {resp.text}")
        except Exception as e:
            log_error(f"[Discord] Error sending message {msg_index}/{total_messages}: {e}")
    
    log_info(f"[Discord] Completed: {successful_sends}/{total_messages} messages sent successfully.")
