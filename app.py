from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
import requests, os, re, json
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

# ================== DEEP AI ANALYSIS (REAL SCORE) ==================
def deep_ai_analysis(name, results):
    search_summary = "\n".join([
        f"{i+1}. {r['title']} | {r['link']}\n   {r['snippet'][:250]}..."
        for i, r in enumerate(results[:10])
    ])

    prompt = f"""
You are a brutally honest career reputation analyst.
Name: {name}

SEARCH RESULTS:
{search_summary}

Return ONLY valid JSON in this exact format:
{{
  "google_score": <number between 0 and 100>,
  "verdict": "<short, sharp, brutally honest verdict - 2 to 4 lines max>"
}}
Be realistic and critical based on the actual search results.
"""

    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.7
        )
        content = res.choices[0].message.content.strip()

        # Extract JSON
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            score = int(data.get("google_score", 50))
            verdict = data.get("verdict", "Analysis unavailable.")
            return score, verdict
    except Exception as e:
        print("Deep AI Error:", e)

    return 50, "Deep analysis temporarily unavailable."

# ================== MAIN ENDPOINT ==================
@app.post("/analyze")
def analyze(data: Input):
    results = get_google_results(data.name, data.context)
    google_score, ai_verdict = deep_ai_analysis(data.name, results)
    
    domains = [r["link"] for r in results if r.get("link")]

    return {
        "google_score": google_score,
        "layoff_risk": 100 - google_score,
        "ai": ai_verdict,
        "domains": domains
    }

@app.get("/")
def home():
    return "<h1>✅ Backend is Running - Deep AI Active</h1>"

print("🚀 Google Me Score Backend Ready!")
