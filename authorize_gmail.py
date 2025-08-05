from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os
import pickle
from utils import log_info

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def main():
    creds = None

    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)

    with open('token.json', 'w') as token_file:
        token_file.write(creds.to_json())

    log_info("Token created successfully!")

if __name__ == '__main__':
    main()
