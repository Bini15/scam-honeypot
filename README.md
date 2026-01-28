Scam Honeypot – AI-Powered Fraud Detection System

An AI-powered system that detects scam attempts in real-time, analyzes risk level, and safely responds to scammers while protecting users from fraud.

Features

- ✅ Real-time scam detection
- ✅ Risk scoring engine
- ✅ Red-flag keyword analysis
- ✅ AI-powered safe response generation
- ✅ Conversation memory (multi-turn chat)
- ✅ Web-based chat interface
- ✅ Secure API backend (FastAPI)
- ✅ HuggingFace LLM integration

How It Works

1. User enters a suspicious message
2. System analyzes it using:
   - Keyword risk scoring
   - Pattern detection
   - AI reasoning
3. If risk is high → Shows WARNING
4. If medium → Shows CAUTION + AI advice
5. If low → Normal AI guidance
6. Conversation history is preserved

Tech Stack

- Backend: FastAPI (Python)
- Frontend: HTML, CSS, JavaScript
- AI: HuggingFace Inference API
- Security: Environment variables, secret-safe deployment

API Endpoints

- `POST /webhook` → Main chat endpoint
- `POST /reset` → Reset conversation session
- `GET /` → Health check

How to Run Locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload
