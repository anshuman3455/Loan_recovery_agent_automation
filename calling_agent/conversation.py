import os
import time
from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Free tier model priority — tries each if previous is quota-exhausted
MODELS = [
    "gemini-1.5-flash-8b",   # most generous free quota
    "gemini-1.5-flash",
    "gemini-2.0-flash-lite",
]

LANGUAGE_PROMPTS = {
    "en":       "Respond in English.",
    "hi":       "हिंदी में जवाब दें।",
    "hinglish": "Respond in Hinglish (mix of Hindi and English, like casual Indian conversation).",
    "ta":       "தமிழில் பதில் சொல்லுங்கள்.",
    "te":       "తెలుగులో సమాధానం చెప్పండి.",
}

def generate_response(user_input, context, language="en", conversation_history=None):
    lang_instruction = LANGUAGE_PROMPTS.get(language, LANGUAGE_PROMPTS["en"])

    history_text = ""
    if conversation_history:
        history_text = "\n".join([
            f"{m['role'].title()}: {m['text']}"
            for m in conversation_history[-6:]
        ])

    prompt = f"""You are a polite, professional payment recovery agent.

Customer Details:
{context}

Conversation so far:
{history_text}

Customer just said: "{user_input}"

Instructions:
- {lang_instruction}
- Be empathetic and polite, never aggressive
- Goal: Either get payment confirmation OR get a specific next payment date
- Keep responses SHORT (2-3 sentences max) for phone conversation
- If customer says goodbye/thank you, give a closing statement

Respond with ONLY the spoken text.
On a new line at the end add one of: STATUS:ONGOING or STATUS:PAYMENT_PROMISED or STATUS:DATE_GIVEN:[date] or STATUS:END"""

    last_error = None
    for model in MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt
            )
            return response.text
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                print(f"⚠️  {model} quota exhausted, trying next model...")
                last_error = e
                time.sleep(2)
                continue
            else:
                raise e

    # All models exhausted — return a polite fallback so call doesn't crash
    print(f"❌ All models quota exhausted: {last_error}")
    return "I understand. Let me note your details and our team will follow up shortly. Thank you for your time. Goodbye!\nSTATUS:END"