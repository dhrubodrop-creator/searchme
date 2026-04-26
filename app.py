from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
import requests, os
from dotenv import load_dotenv
from groq import Groq

# Load env safely
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
            timeout=8
        )

        data = res.json()

        if "error" in data:
            print("SERP ERROR:", data["error"])
            return []

        results = data.get("organic_results", [])

        return [{
            "title": i.get("title", ""),
            "link": i.get("link", ""),
            "snippet": i.get("snippet", "")
        } for i in results[:12]]

    except Exception as e:
        print("SERP FAIL:", e)
        return []


# ---------------- ANALYSIS ----------------
def analyze_results(results):
    full_text = " ".join([
        (r["title"] + " " + r["link"] + " " + r.get("snippet", "")).lower()
        for r in results
    ])

    platforms = {
        "LinkedIn": int("linkedin.com" in full_text),
        "GitHub": int("github.com" in full_text),
        "Twitter/X": int("twitter.com" in full_text or "x.com" in full_text),
        "Instagram": int("instagram.com" in full_text),
        "YouTube": int("youtube.com" in full_text),
    }

    results_count = len(results)

    # authority signals
    authority = any(x in full_text for x in [
        "wikipedia.org", "forbes", "bloomberg", "techcrunch", "cnn", "bbc"
    ])

    # ---------------- GOOGLE SCORE ----------------
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

    # ---------------- LAYOFF RISK ----------------
    layoff_risk = 100 - google_score

    if not platforms["LinkedIn"]:
        layoff_risk += 15

    if results_count < 4:
        layoff_risk += 10

    if not authority:
        layoff_risk += 10

    layoff_risk = min(layoff_risk, 100)

    # ---------------- RISKS ----------------
    risks = []

    if not platforms["LinkedIn"]:
        risks.append("No LinkedIn → low professional visibility")

    if results_count < 4:
        risks.append("Low Google presence → weak discoverability")

    if not authority:
        risks.append("No authority mentions → low credibility")

    if not platforms["Twitter/X"] and not platforms["YouTube"]:
        risks.append("No public presence → weak industry signal")

    return google_score, layoff_risk, risks, platforms


# ---------------- AI ----------------
def ai_analysis(name, google_score, layoff_risk, risks, platforms, results):
    prompt = f"""
You are a brutally honest digital reputation and career risk analyst.

PERSON:
{name}

GOOGLE SCORE:
{google_score}/100

LAYOFF RISK:
{layoff_risk}/100

PLATFORM SIGNALS:
{platforms}

DETECTED RISKS:
{risks}

SEARCH DATA:
{results}

--------------------------------

OUTPUT:

1. VERDICT (1 line, sharp)

2. WHAT THIS SIGNALS (3 bullets)

3. WHERE THEY FALL BEHIND (2 bullets)

4. HIDDEN RISK (1 insight)

5. FIX (2 actions only)

STYLE:
- direct
- slightly harsh
- no fluff
"""

    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=180
        )
        return res.choices[0].message.content

    except Exception as e:
        print("AI ERROR:", e)
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

    ai = ai_analysis(
        data.name,
        google_score,
        layoff_risk,
        risks,
        platforms,
        results
    )

    return {
        "google_score": google_score,
        "layoff_risk": layoff_risk,
        "risks": risks,
        "platforms": platforms,
        "ai": ai
    }
