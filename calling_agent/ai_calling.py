import pandas as pd
import time
from .twilio_caller import make_call
from .webhook_server import sessions
from twilio.base.exceptions import TwilioRestException

def run_calls(file, language="en", webhook_base_url=None):
    if not webhook_base_url:
        raise ValueError("webhook_base_url is required!")

    df = pd.read_excel(file)
    success, skipped = 0, 0

    for _, row in df.iterrows():
        try:
            sid = make_call(row['Phone'], f"{webhook_base_url}/start_call")
            sessions[sid] = {
                "name":     row['Name'],
                "account":  str(row['Account']),
                "amount":   str(row['Amount']),
                "language": language,
                "history":  [],
            }
            print(f"✅ Call initiated for {row['Name']} | SID: {sid}")
            success += 1
            time.sleep(2)

        except TwilioRestException as e:
            if "21219" in str(e):
                print(f"⚠️  Skipped {row['Name']} ({row['Phone']}) — not verified in Twilio trial.")
            else:
                print(f"❌ Failed for {row['Name']}: {e}")
            skipped += 1

    print(f"\n📊 Done — {success} calls made, {skipped} skipped.")