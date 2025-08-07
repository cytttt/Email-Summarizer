# Reflection Questions

## 1. Problem framing: Why this problem? What does success look like?
- As a graduate student and developer, I receive a lot of automated and notification-based emails daily: ranging from academic updates, job alerts, to marketing content. Important emails are often buried under low-priority ones, causing missed opportunities.
- This project aims to automate the email-checking process: summarizing each email, classifying it by topic, and prioritizing it. 
- Success means that I can review the entire day’s emails through a concise Discord message in less than a minute, with no need to open Gmail at all unless something is marked as important.

## 2. What libraries/APIs/frameworks did you choose and why?
- Gmail API: I use Gmail as my primary email platform. It supports convenient query options such as `newer_than:6h` and `is:unread`, which make it easy to filter relevant emails.
- OpenRouter + GLM-4.5-Air: This free-tier model is easy to use, integrates well with the OpenAI libraries, and provides reliable outputs.
- Google Cloud Run:
    - Cloud Scheduler: Used to trigger the service on a cron-like schedule.
    - Google Cloud Storage: Stores the refreshed Gmail API token. This setup allows for higher email-fetching frequency without requiring repeated manual token refresh, improving scalability.
- Docker: Used for packaging the application. It ensures compatibility and reproducibility when deploying to Cloud Run.
- Discord Webhook: I use Discord as my main messaging app. It provides a simple way to receive and write summarized results in to text channel.
- Flask: Chosen for its simplicity. I use it to create the HTTP endpoint that receives requests from Cloud Scheduler.
- BeautifulSoup4: Used for conversion of HTML-based email bodies into clean text suitable for both LLM processing and human readability.

## 3. Describe your prompt-engineering and output evaluation approach.
```python
"""
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
```

- Prompts are designed to enforce structured JSON output.
- The JSON response is typically wrapped in Markdown code blocks.
- I found the LLM results to be generally reasonable.
- I added a guideline specifically for verification codes, since language models tend to classify verification emails as urgent or important. However, in practice, I’ve likely already entered the code by the time I check the email: on iPhone, where the keyboard auto-fills verification codes without needing to open the message.

## 4. How does your agent determine when its task is complete?

- Workflow:
    1. Fetch recent emails from Gmail (within the past 6 hours).
    2. For each email, run LLM summarization and classification.
    3. Store results in memory.
    4. Once all emails are processed, send a Discord summary message and terminate.

1. If there are no unread emails in the past 6 hours, the agent will still execute the rest of the functions (LLM parsing and Discord messaging). However, since there is no input, those steps will simply be skipped, and the program will terminate normally.
2. If an email uses up all 3 attempts to retrieve an LLM result, it will be skipped.
3. Given Discord's message length limit of 2000 characters, we do not break a single email's summary into multiple messages. The program stops after all email summaries are processed and sent.



## 5. What failure modes did you consider and mitigate?
- Rate limiting from OpenRouter:
    - Since we are using the free-tier model, OpenRouter enforces a rate limit. This is not noticeable unless we hit the API limit.
    - For each email, we allow at most 3 attempts to call the LLM API.
- Missing `choices` field from the LLM API response:
    - If the `choices` field is missing, we log an error message and count it as a failed attempt for that email.
- Unparsable replies from the LLM:
    - We use regex-based extraction combined with `json.loads()` to parse LLM output, which is typically wrapped in a Markdown code block.
- Gmail API token expiration:
    - If the token has expired, it is automatically refreshed and the updated token is saved to a GCS bucket.
- HTML noise in the email body:
    - We use BeautifulSoup to extract text content and apply regex cleaning to remove invisible characters, redundant spaces, and unnecessary newlines.
    - Image links are skipped.
    - After cleaning, the email body becomes more readable for both the LLM and human reviewers. It also helps reduce unnecessary token usage for the LLM.

## 6. If given another week, what would you improve?
- Gmail step improvements:
    - Integrate a lightweight local language model or heuristic-based filter to pre-classify spam-like emails or verification code messages. This would reduce unnecessary LLM calls and improve precision in prioritization.
- Preprocessing enhancements:
    - Handle long email threads more intelligently by detecting and avoiding redundant summarization of previously seen content, especially in repeated newsletters or notification digests.
- LLM step extensions:
    - Explore using a multimodal model capable of parsing embedded images or image-based content (e.g., flyers or diagrams), which are currently ignored due to single-modality limitations.

- Alternative project idea:
    - Build a chatbot that lives in any chat platform (e.g., Discord, Slack) and replies with clever, context-aware puns or jokes. It could reference shared inside jokes or running gags, making group conversations more engaging and personalized.
    - Event-based on any messages.
    - A few agents generate puns and they vote for the best.
    - According to my experiments, I cannot make it really funny in 3-4 days, so I give up. QQ