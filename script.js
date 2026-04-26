const BACKEND_URL = "https://searchme-cv72.onrender.com/analyze";
let globalData = null;

// Event Listeners
document.getElementById('checkBtn').addEventListener('click', checkScore);
document.getElementById('payBtn').addEventListener('click', handlePayment);
document.getElementById('ipaidBtn').addEventListener('click', unlockReport);
document.getElementById('downloadBtn').addEventListener('click', downloadPDF);

async function checkScore() {
    const name = document.getElementById('nameInput').value.trim();
    const context = document.getElementById('profInput').value.trim();
    if(!name) { alert("Please enter your name."); return; }

    document.getElementById('loading').classList.add('active');

    try {
        const response = await fetch(BACKEND_URL, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ name, context })
        });

        globalData = await response.json();
        console.log("✅ DATA RECEIVED:", globalData);

        document.getElementById('loading').classList.remove('active');
        displayResults(name);
    } catch (err) {
        console.error("Fetch Error:", err);
        alert("Server is waking up. Try again in 10 seconds.");
        document.getElementById('loading').classList.remove('active');
    }
}

function displayResults(name) {
    document.getElementById('hero').style.display = 'none';
    document.getElementById('results').classList.add('visible');
    document.getElementById('scoreName').innerText = name.toUpperCase();
    
    // Core Score mapping
    animateScore(globalData.google_score || 50);
    
    // AI Verdict
    document.getElementById('insightText').innerText = `"${globalData.ai || 'No analysis available.'}"`;
    
    // Platform detection based on your real domains
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
            const brutal = document.getElementById('scoreBrutal');
            if(target > 70) { label.innerText = "Strong Presence"; brutal.innerText = "You own your name."; }
            else if(target > 40) { label.innerText = "Average Presence"; brutal.innerText = "You are findable but quiet."; }
            else { label.innerText = "Weak Presence"; brutal.innerText = "You are a digital ghost."; }
        }
        el.innerText = cur;
        ring.style.strokeDashoffset = circumference - (circumference * cur / 100);
        cur++;
    }, 15);
}

function renderPlatforms(links) {
    const grid = document.getElementById('platformGrid');
    grid.innerHTML = '';
    
    const sites = {
        'linkedin.com': 'LinkedIn',
        'github.io': 'GitHub',
        'soundcloud.com': 'SoundCloud',
        'instagram.com': 'Instagram',
        'zaubacorp.com': 'Business/DIN'
    };

    Object.keys(sites).forEach(domain => {
        const found = links.some(l => l.toLowerCase().includes(domain));
        const card = document.createElement('div');
        card.className = 'platform-card';
        card.innerHTML = `
            <div class="p-info">
                <div class="p-name">${sites[domain]}</div>
                <div class="p-status ${found ? 'present' : 'missing'}">${found ? '● Present' : '○ Missing'}</div>
            </div>
        `;
        grid.appendChild(card);
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

function downloadPDF() {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    const name = document.getElementById('nameInput').value;
    doc.setFontSize(22); doc.text(`Reputation Audit: ${name}`, 20, 20);
    doc.setFontSize(16); doc.text(`Score: ${globalData.google_score}/100`, 20, 30);
    doc.setFontSize(12); doc.text("AI Analysis:", 20, 45);
    doc.text(doc.splitTextToSize(globalData.ai, 170), 20, 55);
    doc.save(`SearchMe_Report.pdf`);
}    document.getElementById('results').classList.add('visible');
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
