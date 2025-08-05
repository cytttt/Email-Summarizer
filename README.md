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

## Testing

```
// install requirements
pip install -r requirements.txt
```
This repo supports two modes:
- **Mock mode**: uses dummy email + fake LLM for easy review
    ```
    // Tests with mock input
    python agent.py --mock
    ```

- **Full mode**: uses real Gmail API (requires token.json, credentials.json), OpenRouter API
    - https://developers.google.com/workspace/gmail/api/auth/web-server 
    ```
    // Generate token.json from credentials.json
    python authorize_gmail.py

    // Tests locally with gmail, openrouter API
    python agent.py --local
    ```

All logic in `agent.py` is tested identically in both modes.
