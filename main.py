import threading
import os
from calling_agent.ai_calling import run_calls
from calling_agent.webhook_server import app as flask_app
from reconciliation_agent.reconcile import reconcile
from email_sender import send_email
from database import get_all_results, update_input_file

def start_flask():
    flask_app.run(port=5000, debug=False, use_reloader=False)

def get_ngrok_url():
    import re, urllib.request, json, time
    time.sleep(3)  # Give cloudflared time to start

    # Try ngrok
    try:
        with urllib.request.urlopen("http://localhost:4040/api/tunnels", timeout=2) as r:
            data = json.loads(r.read())
            for t in data["tunnels"]:
                if t["public_url"].startswith("https"):
                    print(f"🌐 Detected ngrok: {t['public_url']}")
                    return t["public_url"]
    except:
        pass

    # Try Cloudflare — scan ports 20241 to 20250
    for port in range(20241, 20251):
        try:
            with urllib.request.urlopen(f"http://localhost:{port}/metrics", timeout=1) as r:
                text = r.read().decode()
                match = re.search(r'https://[a-z0-9\-]+\.trycloudflare\.com', text)
                if match:
                    print(f"🌐 Detected Cloudflare (port {port}): {match.group()}")
                    return match.group()
        except:
            continue

    # Manual fallback
    print("\n" + "="*55)
    print("  📡 Run in a new terminal:")
    print("     cloudflared tunnel --url http://localhost:5000")
    print("  Then copy the https://xxxx.trycloudflare.com URL")
    print("="*55)
    url = input("\nPaste your tunnel URL here: ").strip()
    if not url.startswith("http"):
        url = "https://" + url
    return url

while True:
    print("\n" + "=" * 50)
    print("  AI AGENT SYSTEM")
    print("=" * 50)
    print("1. Run Calling Agent")
    print("2. Run Reconciliation Agent")
    print("3. View Call Results (CSV)")
    print("4. Export input_with_results.xlsx")
    print("5. Exit")
    print("=" * 50)

    choice = input("Enter choice: ").strip()

    if choice == "1":
        print("\nSelect Language for calls:")
        print("  en       → English")
        print("  hi       → Hindi")
        print("  hinglish → Hinglish (Hindi + English mix)")
        print("  ta       → Tamil")
        print("  te       → Telugu")

        language = input("Enter language code [default: en]: ").strip() or "en"

        print("\n🚀 Starting Flask webhook server...")
        flask_thread = threading.Thread(target=start_flask, daemon=True)
        flask_thread.start()

        import time; time.sleep(1)

        webhook_url = get_ngrok_url()
        run_calls("data/input.xlsx", language=language, webhook_base_url=webhook_url)

        input("\n⏳ Calls running... Press Enter when done.\n")

    elif choice == "2":
        to_email = input("Send report to email [leave blank for .env EMAIL]: ").strip() or None
        reconcile("data/base.xlsx", "data/compare.xlsx")
        send_email(to_email)

    elif choice == "3":
        df = get_all_results()
        if df.empty:
            print("⚠️  No call results yet.")
        else:
            print(f"\n📋 Call Results ({len(df)} records):")
            print(df[["id", "name", "account", "status", "next_payment_date", "called_at"]].to_string(index=False))

    elif choice == "4":
        update_input_file("data/input.xlsx")

    elif choice == "5":
        print("Goodbye!")
        break
    else:
        print("Invalid choice.")