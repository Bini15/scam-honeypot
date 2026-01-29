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

def analyze_scam(message):
    msg = message.lower()

    red_flags = []
    risk = 0
    scam_type = "Unknown"

    # Keyword detection
    if any(x in msg for x in ["otp", "one time password", "pin"]):
        risk += 40
        red_flags.append("Asking for OTP / PIN")
        scam_type = "OTP Scam"

    if any(x in msg for x in ["kyc", "verify", "account blocked", "suspend"]):
        risk += 30
        red_flags.append("Fake KYC / Account Block Threat")
        scam_type = "Bank KYC Scam"

    if any(x in msg for x in ["upi", "refund", "collect request"]):
        risk += 30
        red_flags.append("UPI Refund Scam")
        scam_type = "UPI Scam"

    if any(x in msg for x in ["job", "offer", "work from home"]):
        risk += 20
        red_flags.append("Fake Job Offer")
        scam_type = "Job Scam"

    if any(x in msg for x in ["lottery", "won", "prize"]):
        risk += 20
        red_flags.append("Lottery / Prize Scam")
        scam_type = "Lottery Scam"

    if any(x in msg for x in ["click", "link", "http", "bit.ly"]):
        risk += 20
        red_flags.append("Suspicious Link")

    # Cap risk at 100
    risk = min(risk, 100)

    if risk == 0:
        scam_type = "No Scam Detected"

    return {
        "risk_score": risk,
        "scam_type": scam_type,
        "red_flags": red_flags
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
    "analysis": analysis
}



@app.post("/reset")
def reset_conversation(session_id: str = "default"):
    conversation_store[session_id] = [SYSTEM_PROMPT.copy()]
    return {"status": "reset done", "session_id": session_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)