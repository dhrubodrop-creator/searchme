import os
import json
import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

# 1. SETUP & CONFIG
load_dotenv(".env", override=True)
app = FastAPI(title="Google Me Score - Production")

# CORS remains enabled for safety, though relative paths will bypass it
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Keys from Render Environment Variables
SERP_API_KEY = os.getenv("SERPAPI_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

class SearchInput(BaseModel):
    name: str
    context: str = ""

# 2. CORE LOGIC: GOOGLE SEARCH
def fetch_serp_results(name, context):
    try:
        query = f"{name} {context}".strip()
        # Using SerpApi for clean, structured data
        params = {
            "engine": "google",
            "q": query,
            "api_key": SERP_API_KEY,
            "num": 10
        }
        response = requests.get("https://serpapi.com/search", params=params, timeout=10)
        data = response.json()
        
        if "organic_results" not in data:
            return []
            
        return [{
            "link": item.get("link", ""),
            "snippet": item.get("snippet", "")
        } for item in data["organic_results"]]
    except Exception as e:
        print(f"SERP Error: {e}")
        return []

# 3. CORE LOGIC: AI ANALYSIS (DEVIL'S ADVOCATE MODE)
def analyze_with_ai(name, results):
    if not results:
        return 20, "You are a digital ghost. No meaningful footprint detected."

    footprint = "\n".join([f"- {r['snippet']} ({r['link']})" for r in results])
    
    # Master Prompt with Devil's Advocate / Brutal Honesty update
    system_prompt = (
        "You are a brutal Digital Reputation Auditor and Devil's Advocate. "
        "Do not sugarcoat. Fight with the results to find inconsistencies. "
        "Your goal is to give the harshest, most realistic first impression a high-stakes recruiter would have."
    )
    
    user_prompt = (
        f"Name: {name}\n"
        f"Search Results:\n{footprint}\n\n"
        "Analyze the results above. Return ONLY a JSON object with two keys:\n"
        "1. 'google_score': An integer (0-100) based on visibility, authority, and consistency.\n"
        "2. 'verdict': A short, brutally honest paragraph analyzing their reputation.\n"
        "Format: {\"google_score\": 45, \"verdict\": \"...\"}"
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
        data = json.loads(completion.choices[0].message.content)
        return data.get("google_score", 50), data.get("verdict", "Analysis inconclusive.")
    except Exception as e:
        print(f"AI Error: {e}")
        return 50, "AI Analysis encountered a glitch."

# 4. ENDPOINTS
@app.post("/analyze")
async def handle_analyze(data: SearchInput):
    results = fetch_serp_results(data.name, data.context)
    score, verdict = analyze_with_ai(data.name, results)
    
    return {
        "google_score": score,
        "ai": verdict,
        "domains": [r["link"] for r in results]
    }

# 5. FRONTEND SERVING (The All-In-One Fix)
@app.get("/")
async def serve_frontend():
    # This serves your index.html directly from the root folder
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return {"error": "index.html not found in root directory"}

# For health checks
@app.get("/health")
async def health():
    return {"status": "online"}
