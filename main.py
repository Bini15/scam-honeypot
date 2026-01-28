from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import FastAPI
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv

# =========================
# Setup
# =========================

load_dotenv()

HF_TOKEN = os.getenv("HF_TOKEN")

if not HF_TOKEN:
    raise RuntimeError("HF_TOKEN not found in .env file")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_ui():
    return FileResponse("static/index.html")

# ==============================
# Scam Analyzer
# ==============================

def analyze_scam(text: str):
    text = text.lower()

    flags = []
    risk = 0

    keywords = {
        "otp": 30,
        "one time password": 30,
        "pin": 30,
        "atm": 25,
        "card number": 25,
        "account will be blocked": 20,
        "account will be frozen": 20,
        "urgent": 15,
        "immediately": 15,
        "verify": 10,
        "bank": 5
    }

    for k, score in keywords.items():
        if k in text:
            flags.append(k)
            risk += score

    if risk > 100:
        risk = 100

    if risk >= 70:
        scam_type = "Financial Fraud / Phishing"
    elif risk >= 40:
        scam_type = "Suspicious"
    else:
        scam_type = "Low Risk"

    return {
        "risk_score": risk,
        "scam_type": scam_type,
        "red_flags": flags
    }


# =========================
# In-memory conversation store
# =========================

conversation_store = {}

SYSTEM_PROMPT = {
    "role": "system",
    "content": "You are a human pretending to be a bank customer. Reply naturally, cautiously, and do not reveal sensitive information easily."
}

# =========================
# Request Models
# =========================

class MessageIn(BaseModel):
    message: str
    session_id: str | None = "default"

# =========================
# HuggingFace AI Call
# =========================

def ai_agent_reply(history: list) -> str:
    url = "https://router.huggingface.co/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {HF_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "HuggingFaceH4/zephyr-7b-beta:featherless-ai",
        "messages": history,
        "temperature": 0.7,
        "max_tokens": 300
    }

    response = requests.post(url, headers=headers, json=payload)

    print("HF STATUS:", response.status_code)
    print("HF RAW RESPONSE:", response.text)

    if response.status_code != 200:
        return f"HuggingFace API error: {response.text}"

    data = response.json()

    if "choices" not in data:
        return f"Unexpected HF response: {data}"

    return data["choices"][0]["message"]["content"]

# =========================
# Routes
# =========================

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/webhook")
def webhook(data: MessageIn):
    session_id = data.session_id
    user_msg = data.message
    analysis = analyze_scam(user_msg)
    risk = analysis["risk_score"]


    if session_id not in conversation_store:
        conversation_store[session_id] = [SYSTEM_PROMPT.copy()]

    # Add user message
    conversation_store[session_id].append({
        "role": "user",
        "content": user_msg
    })

    # Get AI reply
    if risk >= 60:
        reply = "⚠️ WARNING: This is almost certainly a scam. Do NOT share any OTP, PIN, or card details. Please disconnect the call immediately and contact your bank using the official number."
    elif risk >= 30:
        reply = ai_agent_reply(conversation_store[session_id])
        reply = "⚠️ Be cautious. This looks suspicious.\n\n" + reply
    else:
        reply = ai_agent_reply(conversation_store[session_id])

    # Add AI reply to history
    conversation_store[session_id].append({
        "role": "assistant",
        "content": reply
    })



    return {
        "reply": reply,
        "analysis": analysis,
        "history": conversation_store[session_id]
    }


@app.post("/reset")
def reset_conversation(session_id: str = "default"):
    conversation_store[session_id] = [SYSTEM_PROMPT.copy()]
    return {"status": "reset done", "session_id": session_id}

