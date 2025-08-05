# Email Summarizer
## Structures
```
email-summarizer/
├── README.md
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── .gitignore
├── agent.py
├── gmail_client.py
├── openrouter_client.py
├── notify_discord.py
└── utils.py
```

## Testing Notes

This repo supports two modes:

- **Full mode**: uses real Gmail API (requires token.json, credentials.json)
- **Mock mode**: uses dummy email + fake LLM for easy review
    - ```python agent.py --mock```

All logic in `agent.py` is tested identically in both modes.
