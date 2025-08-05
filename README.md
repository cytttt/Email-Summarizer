# Email Summarizer
## Structures
```
email-summarizer/
├── README.md
├── requirements.txt
├── Dockerfile
├── deploy.sh
├── .dockerignore
├── .gitignore
├── agent.py
├── gmail_client.py
├── openrouter_client.py
├── notify_discord.py
└── utils.py

├── authorize_gmail.py  # Get token by credentials
```

## Testing Notes

This repo supports two modes:

- **Full mode**: uses real Gmail API (requires token.json, credentials.json), OpenRouter API
- **Mock mode**: uses dummy email + fake LLM for easy review

```
// install requirements
pip install -r requirements.txt

// Tests locally with gmail, openrouter API
python agent.py --local

// Tests with mock input
python agent.py --mock
```

All logic in `agent.py` is tested identically in both modes.
