import os
import json
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

# 1. INITIALIZATION
load_dotenv(".env", override=True)
app = FastAPI(title="Google Me Score - Production")

# CORS setup for flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Keys from Environment Variables
SERP_API_KEY = os.getenv("SERPAPI_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("CRITICAL ERROR: GROQ_API_KEY is missing!")

client = Groq(api_key=GROQ_API_KEY)

# Data Schema for Input
class SearchInput(BaseModel):
    name: str
    context: str = ""

# 2. CORE LOGIC: GOOGLE SEARCH (SERPAPI)
def fetch_google_data(name, context):
    try:
        search_query = f"{name} {context}".strip()
        params = {
            "engine": "google",
            "q": search_query,
            "api_key": SERP_API_KEY,
            "num": 10
        }
        response = requests.get("https://serpapi.com/search", params=params, timeout=10)
        data = response.json()
        
        results = data.get("organic_results", [])
        return [{
            "link": item.get("link", ""),
            "snippet": item.get("snippet", "")
        } for item in results]
    except Exception as e:
        print(f"SerpApi Error: {e}")
        return []

# 3. CORE LOGIC: AI AUDITOR (DEVIL'S ADVOCATE)
def audit_reputation(name, search_results):
    if not search_results:
        return 22, "You are a digital ghost. There is zero trail of your professional existence. This is a massive trust red flag."

    # Format findings for the AI
    formatted_results = "\n".join([f"- {r['snippet']} ({r['link']})" for r in search_results])
    
    system_prompt = (
        "You are a brutal, high-stakes Digital Reputation Auditor. "
        "Do not sugarcoat. Be a devil's advocate. "
        "Fight with the results provided to find gaps, inconsistencies, or risks. "
        "If they are successful, find why they might still be a risk. "
        "Output MUST be JSON."
    )
    
    user_prompt = (
        f"Name: {name}\n"
        f"Found Data:\n{formatted_results}\n\n"
        "Return JSON with exactly two keys:\n"
        "1. 'score': Integer (0-100)\n"
        "2. 'verdict': A short, brutally honest analysis (max 3 sentences).\n"
    )

    try:
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        ai_response = json.loads(completion.choices[0].message.content)
        return ai_response.get("score", 45), ai_response.get("verdict", "Inconclusive results.")
    except Exception as e:
        print(f"AI Error: {e}")
        return 45, "Reputation analysis encountered a technical glitch."

# 4. API ENDPOINTS
@app.post("/analyze")
async def handle_analyze(data: SearchInput):
    # Get Google Data
    results = fetch_google_data(data.name, data.context)
    
    # Get AI Audit
    score, verdict = audit_reputation(data.name, results)
    
    return {
        "google_score": score,
        "ai": verdict,
        "domains": [r["link"] for r in results]
    }

# 5. UI SERVING (ROOT ROUTE)
@app.get("/")
async def serve_home():
    # This serves your 500+ line index.html from the root folder
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"error": "index.html not found. Please ensure it is in the root directory."}

# Health check for Render
@app.get("/health")
async def health():
    return {"status": "online"}
