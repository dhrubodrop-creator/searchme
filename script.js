const BACKEND_URL = "https://searchme-cv72.onrender.com/analyze";
let globalData = null;

document.getElementById('checkBtn').addEventListener('click', checkScore);

async function checkScore() {
    const name = document.getElementById('nameInput').value.trim();
    const context = document.getElementById('profInput').value.trim();
    if(!name) return;

    document.getElementById('loading').classList.add('active');

    try {
        const response = await fetch(BACKEND_URL, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ name, context })
        });

        globalData = await response.json();
        
        // This is the important part: we use exactly what the API says
        console.log("Real Score from API:", globalData.google_score); 

        document.getElementById('loading').classList.remove('active');
        displayResults(name);
    } catch (err) {
        alert("API Error");
        document.getElementById('loading').classList.remove('active');
    }
}

function displayResults(name) {
    document.getElementById('hero').style.display = 'none';
    document.getElementById('results').classList.add('visible');
    
    // 1. Set the Name
    document.getElementById('scoreName').innerText = name.toUpperCase();
    
    // 2. FORCE THE ANIMATION TO USE THE REAL SCORE (42)
    const realScore = parseInt(globalData.google_score);
    animateScore(realScore);
    
    // 3. SET THE VERDICT TEXT
    document.getElementById('insightText').innerText = `"${globalData.ai}"`;
}

function animateScore(target) {
    const el = document.getElementById('scoreNum');
    const ring = document.getElementById('ringFill');
    const circumference = 439.82;
    let cur = 0;
    
    // Clear any old intervals
    if (window.scoreInterval) clearInterval(window.scoreInterval);

    window.scoreInterval = setInterval(() => {
        if(cur >= target) {
            clearInterval(window.scoreInterval);
            // Final UI check
            const label = document.getElementById('scoreLabel');
            if(target > 70) label.innerText = "Strong Presence";
            else if(target > 40) label.innerText = "Average Presence";
            else label.innerText = "Weak Presence";
        }
        el.innerText = cur;
        ring.style.strokeDashoffset = circumference - (circumference * cur / 100);
        cur++;
    }, 20);
}
