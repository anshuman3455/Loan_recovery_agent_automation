"""
Flask webhook server that Twilio calls to handle real-time conversation.
Run this with ngrok to get a public URL for Twilio.
"""
import os
import json
from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from .conversation import generate_response
from database import save_call_result

app = Flask(__name__)

# In-memory session store (use Redis in production)
sessions = {}

LANGUAGE_VOICES = {
    "en": ("en-US", "Polly.Joanna"),
    "hi": ("hi-IN", "Polly.Aditi"),
    "hinglish": ("hi-IN", "Polly.Aditi"),
    "ta": ("ta-IN", "Polly.Raveena"),
    "te": ("en-IN", "Polly.Raveena"),
}

def twiml_say(text, language="en"):
    """Helper to create TwiML with proper language voice."""
    lang_code, voice = LANGUAGE_VOICES.get(language, LANGUAGE_VOICES["en"])
    vr = VoiceResponse()
    gather = Gather(
        input="speech",
        action="/respond",
        method="POST",
        language=lang_code,
        speech_timeout="auto",
        timeout=5
    )
    gather.say(text, voice=voice)
    vr.append(gather)
    # Fallback if no speech detected
    vr.redirect("/no_response")
    return str(vr)

@app.route("/start_call", methods=["POST"])
def start_call():
    """Initial webhook when call connects."""
    call_sid = request.form.get("CallSid")
    
    # Get session data passed when call was initiated
    session = sessions.get(call_sid, {})
    name = session.get("name", "Customer")
    amount = session.get("amount", "")
    language = session.get("language", "en")
    
    # Initialize conversation history
    sessions[call_sid]["history"] = []
    
    # Opening message by language
    openings = {
        "en": f"Hello {name}, this is a call from our accounts team. You have a pending amount of {amount} rupees. How are you doing today?",
        "hi": f"नमस्ते {name} जी, मैं अकाउंट्स टीम से बोल रहा हूँ। आपका {amount} रुपये का भुगतान बाकी है। आप कैसे हैं?",
        "hinglish": f"Hello {name} ji, main accounts team se bol raha hoon. Aapka {amount} rupees pending hai. Kaise hain aap?",
    }
    opening = openings.get(language, openings["en"])
    sessions[call_sid]["history"].append({"role": "agent", "text": opening})
    
    return Response(twiml_say(opening, language), mimetype="text/xml")


@app.route("/respond", methods=["POST"])
def respond():
    """Called by Twilio each time customer speaks."""
    call_sid = request.form.get("CallSid")
    speech_result = request.form.get("SpeechResult", "").strip()
    
    session = sessions.get(call_sid, {})
    language = session.get("language", "en")
    history = session.get("history", [])
    
    if not speech_result:
        return Response(twiml_say("Sorry, I didn't catch that. Could you repeat?", language), mimetype="text/xml")
    
    # Add customer speech to history
    history.append({"role": "customer", "text": speech_result})
    
    # Build context string
    context = f"""Name: {session.get('name')}
Account: {session.get('account')}
Pending Amount: {session.get('amount')}"""
    
    # Get AI response
    ai_reply = generate_response(speech_result, context, language, history)
    
    # Parse status from reply
    status = "ONGOING"
    spoken_text = ai_reply
    
    if "STATUS:" in ai_reply:
        parts = ai_reply.rsplit("STATUS:", 1)
        spoken_text = parts[0].strip()
        status_part = parts[1].strip()
        
        if "PAYMENT_PROMISED" in status_part:
            status = "PAYMENT_PROMISED"
        elif "DATE_GIVEN:" in status_part:
            date_str = status_part.replace("DATE_GIVEN:", "").strip()
            status = f"DATE_GIVEN:{date_str}"
        elif "END" in status_part:
            status = "END"
    
    history.append({"role": "agent", "text": spoken_text})
    sessions[call_sid]["history"] = history
    
    # Save to DB if we have a resolution
    if status != "ONGOING":
        next_date = status.replace("DATE_GIVEN:", "") if "DATE_GIVEN" in status else None
        save_call_result(
            account=session.get("account"),
            name=session.get("name"),
            status=status,
            next_payment_date=next_date,
            conversation=json.dumps(history)
        )
    
    # End call gracefully
    if status == "END" or status == "PAYMENT_PROMISED":
        vr = VoiceResponse()
        lang_code, voice = LANGUAGE_VOICES.get(language, LANGUAGE_VOICES["en"])
        vr.say(spoken_text, voice=voice)
        vr.hangup()
        return Response(str(vr), mimetype="text/xml")
    
    return Response(twiml_say(spoken_text, language), mimetype="text/xml")


@app.route("/no_response", methods=["POST"])
def no_response():
    call_sid = request.form.get("CallSid")
    session = sessions.get(call_sid, {})
    language = session.get("language", "en")
    msgs = {
        "en": "I didn't hear anything. Please call us back at your convenience. Goodbye!",
        "hi": "कोई आवाज़ नहीं आई। कृपया हमें वापस कॉल करें। धन्यवाद!",
        "hinglish": "Koi awaaz nahi aayi. Please hume callback karein. Thank you!",
    }
    vr = VoiceResponse()
    _, voice = LANGUAGE_VOICES.get(language, LANGUAGE_VOICES["en"])
    vr.say(msgs.get(language, msgs["en"]), voice=voice)
    vr.hangup()
    return Response(str(vr), mimetype="text/xml")