def fetch_mock_emails():
    return [
        {
            "id": "001",
            "subject": "NTU Course Schedule Update",
            "from": "registrar@ntu.edu.tw",
            "body": "Dear student, your class schedule for Fall 2025 is now available..."
        },
        {
            "id": "002",
            "subject": "50% off on your Uber Eats order!",
            "from": "uber@marketing.com",
            "body": "Get 50% off your next order before Aug 10..."
        }
    ]

def fake_llm_response(email):
    return {
        "id": email["id"],
        "subject": email["subject"],
        "from": email["from"],
        "output": {
            "summary": "This is a mock summary of the email.",
            "category": "Academic" if "NTU" in email["subject"] else "Ads",
            "importance": 2,
            "reason": "Academic info is important." if "NTU" in email["subject"] else "Just a coupon for you!"
        }
    }
