import os
from dotenv import load_dotenv
from twilio.rest import Client

load_dotenv()
client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))

def make_call(to_number, webhook_url):
    """Make a call that connects to our Flask webhook for real conversation."""
    call = client.calls.create(
        url=webhook_url,          # Twilio will POST to this URL
        to=to_number,
        from_=os.getenv("TWILIO_PHONE_NUMBER"),
        method="POST"
    )
    return call.sid