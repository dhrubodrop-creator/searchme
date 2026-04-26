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
            params={
                "engine": "google",
                "q": query,
                "api_key": SERP_API_KEY,
                "num": 15
            },
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
        } for item in results[:15]]
    except Exception as e:
        print("SERP FAIL:", e)
        return []

# ================== ANALYSIS ==================
def analyze_results(results):
    full_text = " ".join([
        (r["title"] + " " + r["link"] + " " + r.get("snippet", "")).lower()
        for r in results
    ])
    
    domains = [r["link"].lower() for r in results if r.get("link")]

    platforms = {
        "LinkedIn": int(any("linkedin.com" in d for d in domains)),
        "GitHub": int(any("github.com" in d for d in domains)),
        "Twitter/X": int(any("twitter.com" in d or "x.com" in d for d in domains)),
        "Instagram": int(any("instagram.com" in d for d in domains)),
        "YouTube": int(any("youtube.com" in d for d in domains)),
    }

    results_count = len(results)
    authority = any(x in full_text for x in ["wikipedia.org", "forbes", "bloomberg", "techcrunch", "cnn", "bbc", "nytimes.com"])

    # Google Score
    google_score = 0
    google_score += 30 if platforms["LinkedIn"] else 0
    google_score += 15 if platforms["GitHub"] else 0
    google_score += 15 if platforms["Twitter/X"] else 0
    google_score += 10 if platforms["Instagram"] else 0
    google_score += 10 if platforms["YouTube"] else 0
    google_score += min(results_count * 3, 20)
    if authority:
        google_score += 10
    google_score = min(google_score, 100)

    # Layoff Risk
    layoff_risk = 100 - google_score
    if not platforms["LinkedIn"]:
        layoff_risk += 15
    if results_count < 4:
        layoff_risk += 10
    if not authority:
        layoff_risk += 10
    layoff_risk = min(layoff_risk, 100)

    return google_score, layoff_risk, domains, platforms

# ================== AI ANALYSIS ==================
def ai_analysis(name, google_score, layoff_risk, platforms, results):
    prompt = f"""
You are a brutally honest career reputation analyst.

Name: {name}
Google Score: {google_score}/100
Layoff Risk: {layoff_risk}/100
Platforms: {platforms}
Search Results: {len(results)} results found.

Give short, sharp, honest verdict (2-4 lines max).
"""
    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",   # ← As you wanted
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.7
        )
        return res.choices[0].message.content.strip()
    except Exception as e:
        print("AI Error:", e)
        return "AI analysis temporarily unavailable."

# ================== MAIN ENDPOINT ==================
@app.post("/analyze")
def analyze(data: Input):
    results = get_google_results(data.name, data.context)
    google_score, layoff_risk, domains, platforms = analyze_results(results)
    ai = ai_analysis(data.name, google_score, layoff_risk, platforms, results)

    return {
        "google_score": google_score,
        "layoff_risk": layoff_risk,
        "ai": ai,
        "domains": domains,
        "platforms": platforms
    }

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <h1 style="text-align:center;margin-top:100px;font-family:Arial;">
        ✅ Backend is Running Successfully<br><br>
        <small>POST to <code>/analyze</code> with {"name": "Your Name"}</small>
    </h1>
    """

print("🚀 Google Me Score Backend Ready!")
