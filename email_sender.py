import os, smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

def send_email(to_email=None):
    msg = EmailMessage()
    msg['Subject'] = "Reconciliation Report — Differences & Base Data"
    msg['From'] = os.getenv("EMAIL")
    msg['To'] = to_email or os.getenv("EMAIL")
    msg.set_content("Please find attached:\n1. differences_with_comments.xlsx — All mismatches with suggested actions\n2. base_data.xlsx — Original base file")

    # Attach differences file
    with open("output/differences_with_comments.xlsx", "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="octet-stream",
                           filename="differences_with_comments.xlsx")

    # Attach base data file
    with open("output/base_data.xlsx", "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="octet-stream",
                           filename="base_data.xlsx")

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(os.getenv("EMAIL"), os.getenv("EMAIL_PASSWORD"))
        smtp.send_message(msg)
    
    print(" Email sent with both attachments!")