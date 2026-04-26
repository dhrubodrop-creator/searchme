from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
import requests, os
from dotenv import load_dotenv
from groq import Groq

load_dotenv(".env", override=True)

app = FastAPI(title="Google Me Score")

SERP_API_KEY = os.getenv("SERPAPI_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

class Input(BaseModel):
    name: str
    context: str = ""

# ================== GOOGLE SEARCH ==================
def get_google_results(name: str, context: str):
    try:
        query = f"{name} {context}".strip()
        res = requests.get(
            "https://serpapi.com/search",
            params={"engine": "google", "q": query, "api_key": SERP_API_KEY, "num": 15},
            timeout=15
        )
        data = res.json()
        if "error" in data:
            print("SERP ERROR:", data["error"])
            return []
        results = data.get("organic_results", [])
        return [{
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "snippet": item.get("snippet", "")
        } for item in results[:12]]
    except Exception as e:
        print("SERP FAIL:", e)
        return []

# ================== DEEP AI ANALYSIS ==================
def deep_ai_analysis(name, results):
    search_summary = "\n".join([
        f"{i+1}. {r['title']} | {r['link']}\n   {r['snippet'][:200]}..."
        for i, r in enumerate(results[:10])
    ])

    prompt = f"""
You are an expert digital reputation analyst.
Analyze the search results for {name} deeply.

SEARCH RESULTS:
{search_summary}

TASK:
1. Evaluate the overall online reputation and visibility.
2. Identify key strengths and weaknesses.
3. Check for professional signals (LinkedIn activity, content, authority mentions, etc.).
4. Give a realistic Google Presence Score (0-100) with reasoning.
5. Write a brutally honest short verdict (2-4 lines).

Be very detailed and critical.
"""

    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.7
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        print("Deep AI Error:", e)
        return "Deep analysis temporarily unavailable."

# ================== MAIN ENDPOINT ==================
@app.post("/analyze")
def analyze(data: Input):
    results = get_google_results(data.name, data.context)
    
    # Deep AI research on all results
    ai = deep_ai_analysis(data.name, results)

    # Basic score (kept for compatibility)
    google_score = 55
    layoff_risk = 60
    domains = [r["link"] for r in results if r.get("link")]

    return {
        "google_score": google_score,
        "layoff_risk": layoff_risk,
        "ai": ai,
        "domains": domains
    }

@app.get("/", response_class=HTMLResponse)
def home():
    return "<h1>✅ Backend Running - Deep AI Analysis Active</h1>"

print("🚀 Google Me Score Backend with Deep AI Ready!")
