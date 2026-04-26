from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
import requests, os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

app = FastAPI()

SERP_API_KEY = os.getenv("SERPAPI_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)

class Input(BaseModel):
    name: str
    context: str = ""

def get_google_results(name, context):
    query = f"{name} {context}".strip()
    url = "https://serpapi.com/search"
    params = {"engine": "google", "q": query, "api_key": SERP_API_KEY}
    data = requests.get(url, params=params).json()

    return [{
        "title": i.get("title",""),
        "link": i.get("link","")
    } for i in data.get("organic_results", [])[:6]]

def analyze_results(results, context):
    links = [r["link"] for r in results]
    domains = " ".join(links)

    platforms = {
        "LinkedIn": 20 if "linkedin.com" in domains else 0,
        "GitHub": 15 if "github.com" in domains else 0,
        "Twitter/X": 10 if ("twitter.com" in domains or "x.com" in domains) else 0,
        "Instagram": 10 if "instagram.com" in domains else 0,
        "YouTube": 10 if "youtube.com" in domains else 0,
    }

    score = sum(platforms.values())
    score = min(score, 100)

    risks = []
    if platforms["LinkedIn"] == 0:
        risks.append("No LinkedIn → low professional trust")

    if score < 40:
        verdict = "Invisible online"
    elif score < 60:
        verdict = "Weak presence"
    elif score < 80:
        verdict = "Average presence"
    else:
        verdict = "Strong presence"

    return score, risks, verdict, platforms

def ai_analysis(name, score, risks, platforms):
    prompt = f"""
You are a professional career branding analyst.

Analyze this person's online presence based on data below.

Name: {name}
Score: {score}/100
Platforms: {platforms}
Risks: {risks}

Respond ONLY with:
1. What impression this creates
2. Why it is weak or strong
3. 2 specific improvements

Keep it professional, direct, and safe.
Do NOT mention anything about illegal activity or refusal.
"""

    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"AI ERROR: {str(e)}"

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <body style="font-family:Arial; text-align:center;">
        <h1>Google Reputation Scanner</h1>

        <input id="name" placeholder="Name"><br><br>
        <input id="context" placeholder="Profession"><br><br>
        <button onclick="run()">Analyze</button>

        <div id="out"></div>

        <script>
        async function run(){
            let res = await fetch("/analyze", {
                method:"POST",
                headers:{"Content-Type":"application/json"},
                body: JSON.stringify({
                    name:document.getElementById("name").value,
                    context:document.getElementById("context").value
                })
            });

            let d = await res.json();

            let platformHTML = Object.entries(d.platforms)
                .map(([k,v]) => `<li>${k}: ${v}</li>`).join("");

            document.getElementById("out").innerHTML =
            `<h2>${d.score}/100</h2>
             <p>${d.verdict}</p>
             <ul>${platformHTML}</ul>
             <p>${d.ai}</p>`;
        }
        </script>
    </body>
    </html>
    """

@app.post("/analyze")
def analyze(data: Input):
    results = get_google_results(data.name, data.context)
    score, risks, verdict, platforms = analyze_results(results, data.context)
    ai = ai_analysis(data.name, score, risks, platforms)

    return {
        "score": score,
        "verdict": verdict,
        "risks": risks,
        "platforms": platforms,
        "ai": ai
    }
