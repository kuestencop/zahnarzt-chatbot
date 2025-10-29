from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import requests

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Zahnarzt-Chatbot online. Nutze /chat für Anfragen."}

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_message = data.get("message", "")

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        return {"error": "OPENROUTER_API_KEY not found in environment variables"}

    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:8000",
        "X-Title": "Zahnarzt Chatbot",
    }

    body = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {"role": "system", "content": "Du bist ein freundlicher Zahnarzt-Chatbot."},
            {"role": "user", "content": user_message},
        ],
    }

    response = requests.post(url, headers=headers, json=body)

    if response.status_code != 200:
        return {"error": f"API Error {response.status_code}", "details": response.text}

    data = response.json()
    reply = data["choices"][0]["message"]["content"]
    return {"reply": reply}
