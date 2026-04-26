from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
import requests, os
from dotenv import load_dotenv
from groq import Groq
from urllib.parse import urlparse

# ✅ Force env load (fix local issues)
load_dotenv(".env", override=True)

app = FastAPI()

SERP_API_KEY = os.getenv("SERPAPI_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(api_key=GROQ_API_KEY)


class Input(BaseModel):
    name: str
    context: str = ""


# ---------------- GOOGLE SEARCH ----------------
def get_google_results(name, context):
    try:
        query = f"{name} {context}".strip()

        res = requests.get(
            "https://serpapi.com/search",
            params={
                "engine": "google",
                "q": query,
                "api_key": SERP_API_KEY
            },
            timeout=10
        )

        data = res.json()

        if "error" in data:
            print("SERP ERROR:", data["error"])
            return []

        results = data.get("organic_results", [])

        # ✅ FIX: deeper search (CRITICAL)
        return [{
            "title": i.get("title", ""),
            "link": i.get("link", "")
        } for i in results[:15]]

    except Exception as e:
        print("SERP EXCEPTION:", e)
        return []


# ---------------- ANALYSIS ----------------
def analyze_results(results):
    links = [r["link"] for r in results]

    # Extract domains
    domains = [urlparse(link).netloc.lower() for link in links]

    # Also check titles + links (stronger detection)
    full_text = " ".join([
        (r["title"] + " " + r["link"]).lower()
        for r in results
    ])

    # ✅ Robust platform detection
    platforms = {
        "LinkedIn": 1 if "linkedin.com" in full_text else 0,
        "GitHub": 1 if "github.com" in full_text else 0,
        "Twitter/X": 1 if ("twitter.com" in full_text or "x.com" in full_text) else 0,
        "Instagram": 1 if "instagram.com" in full_text else 0,
        "YouTube": 1 if "youtube.com" in full_text else 0,
    }

    results_count = len(results)

    # ---------------- GOOGLE SCORE ----------------
    google_score = 0
    google_score += 30 if platforms["LinkedIn"] else 0
    google_score += 15 if platforms["GitHub"] else 0
    google_score += 15 if platforms["Twitter/X"] else 0
    google_score += 10 if platforms["Instagram"] else 0
    google_score += 10 if platforms["YouTube"] else 0
    google_score += min(results_count * 3, 20)

    google_score = min(google_score, 100)

    # ---------------- LAYOFF RISK ----------------
    layoff_risk = 100 - google_score

    if not platforms["LinkedIn"]:
        layoff_risk += 20

    if results_count < 5:
        layoff_risk += 15

    layoff_risk = min(layoff_risk, 100)

    # ---------------- RISKS ----------------
    risks = []

    if not platforms["LinkedIn"]:
        risks.append("No LinkedIn → invisible to recruiters")

    if results_count < 5:
        risks.append("Low Google presence → easily replaceable")

    if not platforms["Twitter/X"] and not platforms["YouTube"]:
        risks.append("No public presence → no industry signal")

    return google_score, layoff_risk, risks, platforms


# ---------------- AI ----------------
def ai_analysis(name, google_score, layoff_risk, risks, platforms):
    prompt = f"""
You are a blunt career risk analyst.

Person: {name}
Google Score: {google_score}/100
Layoff Risk: {layoff_risk}/100
Signals: {platforms}
Risks: {risks}

Write:

1. One-line verdict (direct, slightly harsh)
2. 3 specific reasons
3. 2 ways others are ahead
4. 2 actions to fix

No fluff. No generic advice.
"""

    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200
        )
        return res.choices[0].message.content

    except Exception as e:
        print("GROQ ERROR:", e)
        return "AI temporarily unavailable"


# ---------------- FRONTEND ----------------
@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <html>
    <body style="font-family:Arial; text-align:center;">
        <h1>Layoff Risk Scanner</h1>

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

            document.getElementById("out").innerHTML =
            `<h2>Google Score: ${d.google_score}</h2>
             <h2>Layoff Risk: ${d.layoff_risk}</h2>
             <p>${d.ai}</p>`;
        }
        </script>
    </body>
    </html>
    """


# ---------------- API ----------------
@app.post("/analyze")
def analyze(data: Input):
    results = get_google_results(data.name, data.context)

    google_score, layoff_risk, risks, platforms = analyze_results(results)

    ai = ai_analysis(data.name, google_score, layoff_risk, risks, platforms)

    return {
        "google_score": google_score,
        "layoff_risk": layoff_risk,
        "risks": risks,
        "platforms": platforms,
        "ai": ai
    }
