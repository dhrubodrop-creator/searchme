from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
import requests, os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

app = FastAPI()

# ENV
SERP_API_KEY = os.getenv("SERPAPI_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

print("SERP:", "OK" if SERP_API_KEY else "MISSING")
print("GROQ:", "OK" if GROQ_API_KEY else "MISSING")

client = Groq(api_key=GROQ_API_KEY)


class Input(BaseModel):
    name: str
    context: str = ""


# ---------------- GOOGLE SEARCH ----------------
def get_google_results(name, context):
    try:
        query = f"{name} {context}".strip()
        url = "https://serpapi.com/search"
        params = {
            "engine": "google",
            "q": query,
            "api_key": SERP_API_KEY
        }

        res = requests.get(url, params=params, timeout=10)
        data = res.json()

        # 🔴 DEBUG (see in Render logs)
        print("SERP RAW:", data)

        # Handle API errors
        if "error" in data:
            print("SERP ERROR:", data["error"])
            return []

        results = data.get("organic_results", [])

        return [{
            "title": i.get("title", ""),
            "link": i.get("link", "")
        } for i in results[:6]]

    except Exception as e:
        print("SERP EXCEPTION:", e)
        return []


# ---------------- ANALYSIS ----------------
def analyze_results(results):
    links = [r["link"] for r in results]
    domains = " ".join(links)

    platforms = {
        "LinkedIn": 1 if "linkedin.com" in domains else 0,
        "GitHub": 1 if "github.com" in domains else 0,
        "Twitter/X": 1 if ("twitter.com" in domains or "x.com" in domains) else 0,
        "Instagram": 1 if "instagram.com" in domains else 0,
        "YouTube": 1 if "youtube.com" in domains else 0,
    }

    results_count = len(results)

    # GOOGLE SCORE
    google_score = 0
    google_score += 30 if platforms["LinkedIn"] else 0
    google_score += 15 if platforms["GitHub"] else 0
    google_score += 10 if platforms["Twitter/X"] else 0
    google_score += 10 if platforms["Instagram"] else 0
    google_score += 10 if platforms["YouTube"] else 0
    google_score += min(results_count * 5, 25)

    google_score = min(google_score, 100)

    # LAYOFF RISK
    layoff_risk = 100 - google_score

    if not platforms["LinkedIn"]:
        layoff_risk += 15

    if results_count < 3:
        layoff_risk += 10

    layoff_risk = min(layoff_risk, 100)

    risks = []
    if not platforms["LinkedIn"]:
        risks.append("No LinkedIn presence")
    if results_count < 3:
        risks.append("Low Google visibility")

    return google_score, layoff_risk, risks, platforms


# ---------------- AI ----------------
def ai_analysis(name, google_score, layoff_risk, risks, platforms):
    prompt = f"""
You are a blunt career risk analyst.

Name: {name}
Google Score: {google_score}
Layoff Risk: {layoff_risk}
Signals: {platforms}
Risks: {risks}

Output:

1. One-line verdict
2. 3 reasons they are at risk
3. 2 ways others are ahead
4. 2 actions to reduce risk

Tone:
- direct
- slightly uncomfortable
- no fluff
"""

    try:
        res = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
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
