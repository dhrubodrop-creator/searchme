from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import requests, os, re, json
from dotenv import load_dotenv
from groq import Groq

load_dotenv(".env", override=True)

app = FastAPI(title="Google Me Score")

# Fixes the connection between browser and Render
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SERP_API_KEY = os.getenv("SERPAPI_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

class Input(BaseModel):
    name: str
    context: str = ""

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
            return []
        results = data.get("organic_results", [])
        return [{
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "snippet": item.get("snippet", "")
        } for item in results[:12]]
    except Exception as e:
        return []

def deep_ai_analysis(name, results):
    if not results:
        return 20, "No digital footprint found. You are invisible to Google."

    search_summary = "\n".join([
        f"{i+1}. {r['title']} | {r['link']}\n   {r['snippet'][:250]}..."
        for i, r in enumerate(results[:10])
    ])

    prompt = f"Name: {name}\nResults:\n{search_summary}\n\nReturn ONLY JSON: {{\"google_score\": <0-100>, \"verdict\": \"<brutal honesty>\"}}"

    try:
        res = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"}
        )
        data = json.loads(res.choices[0].message.content)
        return int(data.get("google_score", 50)), data.get("verdict", "No verdict.")
    except:
        return 50, "AI Analysis failed."

@app.post("/analyze")
async def analyze(data: Input):
    results = get_google_results(data.name, data.context)
    score, verdict = deep_ai_analysis(data.name, results)
    domains = [r["link"] for r in results if r.get("link")]
    return {
        "google_score": score,
        "ai": verdict,
        "domains": domains
    }

@app.get("/")
def home():
    return {"status": "online"}
