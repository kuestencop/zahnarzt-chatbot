from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import openai
from datetime import datetime, timedelta

openai.api_key = "DEIN_OPENAI_API_KEY"

app = FastAPI()

# CORS für lokale Tests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Datenbank initialisieren ---
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            reason TEXT,
            date TEXT,
            time TEXT,
            email TEXT,
            phone TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()


@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_input = data["message"]

    system_prompt = """
    Du bist ein digitaler Terminassistent der Zahnarztpraxis „Zahnarztpraxis Dr. Müller“.
    Deine Aufgabe ist es, Patientinnen und Patienten bei der Terminvereinbarung, -verschiebung und -absage zu unterstützen.
    Du darfst einfache Fragen zur Praxis beantworten (z. B. Öffnungszeiten, Adresse, Telefonnummer, Leistungen),
    aber keine medizinischen Diagnosen oder Behandlungen im Detail erklären.

    Wenn du einen Termin vereinbarst, schicke bitte die Informationen in folgendem JSON-Format:
    {"action": "create_appointment", "name": "...", "reason": "...", "date": "YYYY-MM-DD", "time": "HH:MM", "email": "...", "phone": "..."}
    Wenn kein Termin erstellt werden soll, gib nur eine normale Textantwort.
    """

    response = openai.ChatCompletion.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    )

    reply = response["choices"][0]["message"]["content"]

    # Wenn KI JSON enthält → Termin speichern
    if "create_appointment" in reply:
        import json
        try:
            data = json.loads(reply)
            conn = sqlite3.connect("database.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO appointments (name, reason, date, time, email, phone)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (data["name"], data["reason"], data["date"], data["time"], data["email"], data["phone"]))
            conn.commit()
            conn.close()
            return {"reply": f"Der Termin am {data['date']} um {data['time']} wurde für {data['name']} eingetragen."}
        except Exception:
            pass

    return {"reply": reply}


@app.get("/appointments")
def list_appointments():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, reason, date, time FROM appointments ORDER BY date, time")
    rows = cursor.fetchall()
    conn.close()
    return {"appointments": rows}
