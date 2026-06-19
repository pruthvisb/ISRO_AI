// Elements
const canvas = document.getElementById("sim-canvas");
const ctx = canvas.getContext("2d");

const slideSize = document.getElementById("planet-size");
const slidePeriod = document.getElementById("orbit-period");
const slideVar = document.getElementById("stellar-var");
const slideNoise = document.getElementById("noise-level");

const valSize = document.getElementById("val-size");
const valPeriod = document.getElementById("val-period");
const valVar = document.getElementById("val-var");
const valNoise = document.getElementById("val-noise");

const btnDetrend = document.getElementById("btn-toggle-detrend");
const btnFold = document.getElementById("btn-toggle-fold");

// State variables
let planetDepth = parseFloat(slideSize.value) / 100; // e.g. 0.01 for 1%
let orbitalPeriod = parseFloat(slidePeriod.value); // days
let spotActivity = parseInt(slideVar.value); // 0, 1, 2, 3
let noiseLevel = parseInt(slideNoise.value); // 0, 1, 2, 3
let detrendOn = true;
let foldOn = false;

// Physics and Simulation variables
let simTime = 0;
const points = []; // Array of {time, rawFlux, trend, detrendedFlux, phase}
const maxPoints = 400; // max length of moving light curve

// Resize canvas to match display size
function resizeCanvas() {
    canvas.width = canvas.parentElement.clientWidth;
    canvas.height = canvas.parentElement.clientHeight || 400;
}
resizeCanvas();
window.addEventListener("resize", resizeCanvas);

// Update sliders label values
slideSize.addEventListener("input", (e) => {
    valSize.textContent = `${e.target.value}%`;
    planetDepth = parseFloat(e.target.value) / 100;
});
slidePeriod.addEventListener("input", (e) => {
    valPeriod.textContent = `${e.target.value} d`;
    orbitalPeriod = parseFloat(e.target.value);
});
slideVar.addEventListener("input", (e) => {
    const labels = ["None", "Low", "Medium", "High"];
    valVar.textContent = labels[e.target.value];
    spotActivity = parseInt(e.target.value);
});
slideNoise.addEventListener("input", (e) => {
    const labels = ["None", "Low", "Medium", "High"];
    valNoise.textContent = labels[e.target.value];
    noiseLevel = parseInt(e.target.value);
});

// Toggle Buttons
btnDetrend.addEventListener("click", () => {
    detrendOn = !detrendOn;
    btnDetrend.classList.toggle("active", detrendOn);
    btnDetrend.textContent = `Detrending: ${detrendOn ? "ON" : "OFF"}`;
});
btnFold.addEventListener("click", () => {
    foldOn = !foldOn;
    btnFold.classList.toggle("active", foldOn);
    btnFold.textContent = foldOn ? "Plot: Folded Phase" : "Plot: Time-series";
});

// Helper: Box-Muller transform for Gaussian Noise
function randn() {
    let u = 0, v = 0;
    while(u === 0) u = Math.random();
    while(v === 0) v = Math.random();
    return Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
}

// Main physics step
function updateSimulation() {
    simTime += 0.05; // increment time
    
    // 1. Calculate transit dip (trapezoidal)
    const transitCenter = orbitalPeriod / 2;
    // phase goes from 0 to orbitalPeriod
    const currentPhase = (simTime) % orbitalPeriod;
    const duration = 0.5; // transit duration in days
    
    let transitSignal = 0;
    const timeToTransit = Math.abs(currentPhase - transitCenter);
    
    if (timeToTransit < duration / 2) {
        const ingress = duration * 0.15;
        const flatLimit = duration / 2 - ingress;
        if (timeToTransit <= flatLimit) {
            transitSignal = -planetDepth;
        } else {
            // linear ingress/egress
            const slope = (duration / 2 - timeToTransit) / ingress;
            transitSignal = -planetDepth * slope;
        }
    }
    
    // 2. Calculate Stellar Spot Variability (sinusoidal rotation)
    let spotSignal = 0;
    if (spotActivity > 0) {
        const spotAmp = spotActivity * 0.006; // amp scaling
        const rotPeriod = orbitalPeriod * 2.5; // star rotates slower than orbit
        spotSignal = spotAmp * Math.sin(2 * Math.PI * simTime / rotPeriod) + 
                     (spotAmp * 0.2) * Math.sin(4 * Math.PI * simTime / rotPeriod); // harmonic
    }
    
    // 3. Generate Noise
    let noise = 0;
    if (noiseLevel > 0) {
        const noiseStd = noiseLevel * 0.0015;
        noise = randn() * noiseStd;
    }
    
    // 4. Combine signals
    const rawFlux = 1.0 + transitSignal + spotSignal + noise;
    
    // 5. Store point
    const point = {
        time: simTime,
        rawFlux: rawFlux,
        trend: 1.0, // will compute rolling average
        detrendedFlux: rawFlux,
        phase: (currentPhase / orbitalPeriod) - 0.5 // phase from -0.5 to 0.5
    };
    
    points.push(point);
    if (points.length > maxPoints) {
        points.shift();
    }
    
    // 6. Compute Detrending (rolling boxcar average)
    if (points.length > 50) {
        const windowSize = 100;
        for (let i = 0; i < points.length; i++) {
            let sum = 0;
            let count = 0;
            const start = Math.max(0, i - windowSize / 2);
            const end = Math.min(points.length, i + windowSize / 2);
            for (let j = start; j < end; j++) {
                sum += points[j].rawFlux;
                count++;
            }
            points[i].trend = sum / count;
            points[i].detrendedFlux = points[i].rawFlux / points[i].trend;
        }
    }
}

// Rendering function
function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw layout divisions: Upper 35% is visual sky, Lower 65% is Plot
    const skyHeight = canvas.height * 0.35;
    const plotY = skyHeight + 10;
    const plotHeight = canvas.height - plotY - 40;
    
    // --- DRAW SKY (TRANSIT VISUALIZATION) ---
    ctx.fillStyle = "#030712";
    ctx.fillRect(0, 0, canvas.width, skyHeight);
    
    // Draw Star
    const starX = canvas.width / 2;
    const starY = skyHeight / 2;
    const starRadius = skyHeight * 0.38;
    
    // Stellar limb darkening gradient
    const grad = ctx.createRadialGradient(starX, starY, starRadius * 0.1, starX, starY, starRadius);
    grad.addColorStop(0, "#fef08a"); // core
    grad.addColorStop(0.7, "#f59e0b"); // outer
    grad.addColorStop(1, "#b45309"); // limb
    
    ctx.beginPath();
    ctx.arc(starX, starY, starRadius, 0, 2 * Math.PI);
    ctx.fillStyle = grad;
    ctx.shadowBlur = 30;
    ctx.shadowColor = "#f59e0b";
    ctx.fill();
    ctx.shadowBlur = 0; // reset
    
    // Draw Starspots visually
    if (spotActivity > 0) {
        ctx.fillStyle = "rgba(74, 42, 10, 0.65)";
        // spot positions shift slowly
        const spotX1 = starX - starRadius * 0.4 + (Math.sin(simTime * 0.1) * starRadius * 0.3);
        const spotY1 = starY - starRadius * 0.2;
        ctx.beginPath();
        ctx.arc(spotX1, spotY1, starRadius * 0.12, 0, 2*Math.PI);
        ctx.fill();
        
        const spotX2 = starX + starRadius * 0.3 + (Math.sin(simTime * 0.1 + 1) * starRadius * 0.3);
        const spotY2 = starY + starRadius * 0.2;
        ctx.beginPath();
        ctx.arc(spotX2, spotY2, starRadius * 0.15, 0, 2*Math.PI);
        ctx.fill();
    }
    
    // Draw Planet orbiting
    // Phase goes from -0.5 to 0.5
    const currentPhase = ((simTime) % orbitalPeriod) / orbitalPeriod - 0.5;
    const planetX = starX + currentPhase * (starRadius * 4.5); // span wider than star
    const planetY = starY;
    const planetRadius = starRadius * Math.sqrt(planetDepth); // radius scales with sqrt of depth!
    
    ctx.beginPath();
    ctx.arc(planetX, planetY, planetRadius, 0, 2 * Math.PI);
    ctx.fillStyle = "#0b0f19";
    ctx.strokeStyle = "rgba(96, 165, 250, 0.4)";
    ctx.lineWidth = 1.5;
    ctx.fill();
    ctx.stroke();
    
    // Boundary line
    ctx.strokeStyle = "rgba(255,255,255,0.08)";
    ctx.beginPath();
    ctx.moveTo(0, skyHeight);
    ctx.lineTo(canvas.width, skyHeight);
    ctx.stroke();
    
    // --- DRAW PLOT AXES ---
    const plotX = 70;
    const plotWidth = canvas.width - plotX - 30;
    
    ctx.strokeStyle = "#1e293b";
    ctx.lineWidth = 1;
    ctx.strokeRect(plotX, plotY, plotWidth, plotHeight);
    
    // Gridlines & Labels (Y Axis)
    ctx.fillStyle = "#9fa6b2";
    ctx.font = "10px Inter";
    ctx.textAlign = "right";
    
    const yTicks = [0.97, 0.99, 1.0, 1.01, 1.03];
    yTicks.forEach(val => {
        // Map flux values to Y coordinates
        // Let's center around 1.0, span from 0.96 to 1.04
        const y = plotY + plotHeight/2 - (val - 1.0) * (plotHeight / 0.08);
        if (y >= plotY && y <= plotY + plotHeight) {
            ctx.strokeStyle = "rgba(30, 41, 59, 0.4)";
            ctx.beginPath();
            ctx.moveTo(plotX, y);
            ctx.lineTo(plotX + plotWidth, y);
            ctx.stroke();
            ctx.fillText(val.toFixed(2), plotX - 10, y + 3);
        }
    });
    
    // --- PLOT DATA POINTS ---
    if (points.length > 1) {
        ctx.lineWidth = 2;
        ctx.lineJoin = "round";
        
        if (foldOn) {
            // FOLDED PLOT
            ctx.fillStyle = "#9fa6b2";
            ctx.textAlign = "center";
            ctx.fillText("Phase (Folded Orbit)", plotX + plotWidth/2, plotY + plotHeight + 30);
            
            // Draw phase points
            // Sort points by phase visually or just scatter plot them
            points.forEach(p => {
                const px = plotX + (p.phase + 0.5) * plotWidth; // map phase [-0.5, 0.5] to width
                const fluxVal = detrendOn ? p.detrendedFlux : p.rawFlux;
                const py = plotY + plotHeight/2 - (fluxVal - 1.0) * (plotHeight / 0.08);
                
                if (py >= plotY && py <= plotY + plotHeight) {
                    ctx.beginPath();
                    ctx.arc(px, py, 2.5, 0, 2*Math.PI);
                    ctx.fillStyle = detrendOn ? "#06b6d4" : "#ef4444"; // Cyan if detrended, red otherwise
                    ctx.fill();
                }
            });
        } else {
            // TIME-SERIES PLOT
            ctx.fillStyle = "#9fa6b2";
            ctx.textAlign = "center";
            ctx.fillText("Time (Arbitrary days)", plotX + plotWidth/2, plotY + plotHeight + 30);
            
            const minTime = points[0].time;
            const maxTime = points[points.length - 1].time;
            const timeSpan = maxTime - minTime || 1;
            
            // Draw raw data points
            points.forEach(p => {
                const px = plotX + ((p.time - minTime) / timeSpan) * plotWidth;
                const py = plotY + plotHeight/2 - (p.rawFlux - 1.0) * (plotHeight / 0.08);
                
                if (py >= plotY && py <= plotY + plotHeight) {
                    ctx.beginPath();
                    ctx.arc(px, py, 1.5, 0, 2 * Math.PI);
                    ctx.fillStyle = detrendOn ? "rgba(239, 68, 68, 0.3)" : "#ef4444"; // dimmed if detrended
                    ctx.fill();
                }
            });
            
            // Draw stellar trend line (Savitzky-Golay / Moving Average) in gold
            if (detrendOn) {
                ctx.strokeStyle = "#ecc94b";
                ctx.lineWidth = 2;
                ctx.beginPath();
                points.forEach((p, idx) => {
                    const px = plotX + ((p.time - minTime) / timeSpan) * plotWidth;
                    const py = plotY + plotHeight/2 - (p.trend - 1.0) * (plotHeight / 0.08);
                    if (idx === 0) ctx.moveTo(px, py);
                    else ctx.lineTo(px, py);
                });
                ctx.stroke();
                
                // Draw cleaned flat curve in Cyan
                ctx.strokeStyle = "#06b6d4";
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                points.forEach((p, idx) => {
                    const px = plotX + ((p.time - minTime) / timeSpan) * plotWidth;
                    const py = plotY + plotHeight/2 - (p.detrendedFlux - 1.0) * (plotHeight / 0.08);
                    if (idx === 0) ctx.moveTo(px, py);
                    else ctx.lineTo(px, py);
                });
                ctx.stroke();
            }
        }
    }
}

// Animation loop
function loop() {
    updateSimulation();
    draw();
    requestAnimationFrame(loop);
}

// Start loop
loop();

// --- INTERACTIVE BEGINNER QUIZ LOGIC ---

const quizData = [
    {
        question: "How does an exoplanet transit affect the light curve of a star?",
        options: [
            "It makes the star look brighter.",
            "It makes the star look dimmer periodically.",
            "It makes the star change color."
        ],
        correct: 1,
        feedback: "Correct! When a planet passes in front of its host star, it blocks a tiny fraction of the stellar surface, causing a periodic, temporary drop in measured brightness."
    },
    {
        question: "What does a deep, 'V-shaped' dip in a light curve usually represent?",
        options: [
            "A true exoplanet transit.",
            "An Eclipsing Binary star system.",
            "A cosmic ray hit on the sensor."
        ],
        correct: 1,
        feedback: "Correct! Eclipsing binary stars often graze or eclipse each other, creating deep, characteristic V-shaped light curves, unlike the flat-bottomed U-shapes of planets."
    },
    {
        question: "What is the primary purpose of 'detrending' in light curve preprocessing?",
        options: [
            "To remove slow variations like starspot rotation and isolate short transits.",
            "To artificially increase the size of detected planets.",
            "To add random noise to smooth out the data."
        ],
        correct: 0,
        feedback: "Correct! Detrending (using tools like Savitzky-Golay filters) flattens out slow, high-amplitude variations like starspots, making the faint, brief transit events easy to identify."
    }
];

let currentQuestionIdx = 0;
let quizScore = 0;
let selectedOptionIdx = -1;
let quizState = "question"; // "question", "answered"

// DOM Elements
const qProgress = document.getElementById("quiz-progress");
const qText = document.getElementById("quiz-question-text");
const qOptionsContainer = document.getElementById("quiz-options");
const qFeedback = document.getElementById("quiz-feedback");
const qFeedbackText = document.getElementById("quiz-feedback-text");
const btnQuizNext = document.getElementById("btn-quiz-next");
const quizQuestionBox = document.getElementById("quiz-question-box");
const quizResultBox = document.getElementById("quiz-result-box");
const quizScoreSpan = document.getElementById("quiz-score");
const quizRankSpan = document.getElementById("quiz-rank-desc");
const btnQuizRestart = document.getElementById("btn-quiz-restart");

function loadQuestion() {
    const currentQ = quizData[currentQuestionIdx];
    
    // Reset state
    selectedOptionIdx = -1;
    quizState = "question";
    btnQuizNext.textContent = "Submit Answer";
    btnQuizNext.disabled = true;
    qFeedback.classList.add("hidden");
    qFeedback.classList.remove("correct", "wrong");
    
    // Update progress and text
    qProgress.textContent = `Question ${currentQuestionIdx + 1} of ${quizData.length}`;
    qText.textContent = currentQ.question;
    
    // Render options
    qOptionsContainer.innerHTML = "";
    currentQ.options.forEach((opt, idx) => {
        const btn = document.createElement("button");
        btn.className = "quiz-opt-btn";
        btn.textContent = opt;
        btn.setAttribute("data-idx", idx);
        
        btn.addEventListener("click", () => {
            if (quizState !== "question") return; // disable clicks once answered
            
            // Toggle selection styling
            document.querySelectorAll(".quiz-opt-btn").forEach(b => b.classList.remove("selected"));
            btn.classList.add("selected");
            
            selectedOptionIdx = idx;
            btnQuizNext.disabled = false;
        });
        
        qOptionsContainer.appendChild(btn);
    });
}

btnQuizNext.addEventListener("click", () => {
    const currentQ = quizData[currentQuestionIdx];
    
    if (quizState === "question") {
        // Evaluate answer
        quizState = "answered";
        btnQuizNext.disabled = false;
        
        const optionButtons = document.querySelectorAll(".quiz-opt-btn");
        
        if (selectedOptionIdx === currentQ.correct) {
            quizScore++;
            qFeedbackText.textContent = currentQ.feedback;
            qFeedback.className = "quiz-feedback-box correct";
            // Highlight selected as correct
            optionButtons[selectedOptionIdx].className = "quiz-opt-btn correct-choice";
        } else {
            qFeedbackText.textContent = `Incorrect. The correct answer was: "${currentQ.options[currentQ.correct]}". \n\n${currentQ.feedback}`;
            qFeedback.className = "quiz-feedback-box wrong";
            // Highlight selected as wrong, and correct option as correct
            optionButtons[selectedOptionIdx].className = "quiz-opt-btn wrong-choice";
            optionButtons[currentQ.correct].className = "quiz-opt-btn correct-choice";
        }
        
        qFeedback.classList.remove("hidden");
        
        // Update button text
        if (currentQuestionIdx < quizData.length - 1) {
            btnQuizNext.textContent = "Next Question";
        } else {
            btnQuizNext.textContent = "See Results";
        }
    } else {
        // Go to next question or complete
        if (currentQuestionIdx < quizData.length - 1) {
            currentQuestionIdx++;
            loadQuestion();
        } else {
            showResults();
        }
    }
});

function showResults() {
    quizQuestionBox.classList.add("hidden");
    quizResultBox.classList.remove("hidden");
    
    quizScoreSpan.textContent = `${quizScore} / ${quizData.length}`;
    
    let rank = "Novice Stargazer";
    if (quizScore === 3) {
        rank = "Antigravity Astrophysicist 🚀";
    } else if (quizScore === 2) {
        rank = "Solar System Vetting Specialist 🔭";
    } else if (quizScore === 1) {
        rank = "Junior Space Observer 🌌";
    }
    
    quizRankSpan.textContent = `Rank: ${rank}`;
}

btnQuizRestart.addEventListener("click", () => {
    currentQuestionIdx = 0;
    quizScore = 0;
    quizQuestionBox.classList.remove("hidden");
    quizResultBox.classList.add("hidden");
    loadQuestion();
});

// Initialize Quiz
if (quizQuestionBox) {
    loadQuestion();
}

