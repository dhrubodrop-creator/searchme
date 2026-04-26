const BACKEND_URL = "https://searchme-cv72.onrender.com/analyze";
let globalData = null;

// Event Listeners
document.getElementById('checkBtn').addEventListener('click', checkScore);
document.getElementById('payBtn').addEventListener('click', handlePayment);
document.getElementById('ipaidBtn').addEventListener('click', unlockReport);

async function checkScore() {
    const name = document.getElementById('nameInput').value.trim();
    const context = document.getElementById('profInput').value.trim();
    if(!name) { alert("Enter your name!"); return; }

    document.getElementById('loading').classList.add('active');

    try {
        const response = await fetch(BACKEND_URL, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ name, context })
        });

        globalData = await response.json();
        console.log("Data Received:", globalData);

        document.getElementById('loading').classList.remove('active');
        displayResults(name);
    } catch (err) {
        console.error(err);
        alert("Backend Offline. Check Render logs.");
        document.getElementById('loading').classList.remove('active');
    }
}

function displayResults(name) {
    document.getElementById('hero').style.display = 'none';
    document.getElementById('results').classList.add('visible');
    document.getElementById('scoreName').innerText = name.toUpperCase();
    
    // Animate Score from backend 'google_score'
    animateScore(globalData.google_score);
    
    // AI Verdict from backend 'ai'
    document.getElementById('insightText').innerText = `"${globalData.ai}"`;
    
    // Platform detection
    renderPlatforms(globalData.domains || []);
}

function animateScore(target) {
    const el = document.getElementById('scoreNum');
    const ring = document.getElementById('ringFill');
    const circumference = 439.82;
    let cur = 0;
    const interval = setInterval(() => {
        if(cur >= target) {
            clearInterval(interval);
            const label = document.getElementById('scoreLabel');
            if(target > 70) label.innerText = "Strong Presence";
            else if(target > 40) label.innerText = "Average Presence";
            else label.innerText = "Weak Presence";
        }
        el.innerText = cur;
        ring.style.strokeDashoffset = circumference - (circumference * cur / 100);
        cur++;
    }, 15);
}

function renderPlatforms(links) {
    const grid = document.getElementById('platformGrid');
    grid.innerHTML = '';
    const sites = {'linkedin.com': 'LinkedIn', 'github.com': 'GitHub', 'twitter.com': 'Twitter/X', 'instagram.com': 'Instagram'};
    Object.keys(sites).forEach(domain => {
        const found = links.some(l => l.toLowerCase().includes(domain));
        grid.innerHTML += `<div class="platform-card"><div class="p-info"><div class="p-name">${sites[domain]}</div><div class="p-status ${found ? 'present' : 'missing'}">${found ? '● Present' : '○ Missing'}</div></div></div>`;
    });
}

function handlePayment() {
    window.open('https://rzp.io/rzp/PUNs9XqO', '_blank');
    document.getElementById('ipaidBtn').classList.add('show');
}

function unlockReport() {
    document.getElementById('lockedSection').style.display = 'none';
    document.getElementById('premiumReport').classList.add('revealed');
    document.getElementById('rptName').innerText = document.getElementById('nameInput').value;
    document.getElementById('rptScoreDisplay').innerText = globalData.google_score;
    document.getElementById('diagText').innerText = globalData.ai;
    const bar = document.getElementById('diagBar');
    bar.style.width = globalData.google_score + '%';
    bar.style.backgroundColor = globalData.google_score < 40 ? '#e63946' : '#2a9d8f';
}
