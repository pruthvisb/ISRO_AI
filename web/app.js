// Elements
const canvas = document.getElementById("sim-canvas");
const ctx = canvas.getContext("2d");

const selectStarType = document.getElementById("star-type");
const valStarType = document.getElementById("val-star-type");
const slideSize = document.getElementById("planet-size");
const slidePeriod = document.getElementById("orbit-period");
const slideImpact = document.getElementById("orbit-impact");
const slideVar = document.getElementById("stellar-var");
const slideNoise = document.getElementById("noise-level");

const valSize = document.getElementById("val-size");
const valPeriod = document.getElementById("val-period");
const valImpact = document.getElementById("val-impact");
const valVar = document.getElementById("val-var");
const valNoise = document.getElementById("val-noise");

const btnPlay = document.getElementById("btn-toggle-play");
const btnDetrend = document.getElementById("btn-toggle-detrend");
const btnFold = document.getElementById("btn-toggle-fold");

// Metrics DOM elements
const metricStarParams = document.getElementById("metric-star-params");
const metricStarTemp = document.getElementById("metric-star-temp");
const metricAxis = document.getElementById("metric-axis");
const metricDepth = document.getElementById("metric-depth");
const metricTemp = document.getElementById("metric-temp");
const metricStatus = document.getElementById("metric-status");

// Live equations elements
const liveEqDepth = document.getElementById("live-eq-depth");
const liveEqAxis = document.getElementById("live-eq-axis");
const liveEqTemp = document.getElementById("live-eq-temp");

// State variables
let starType = "G";
let starRadius = 1.0; // Solar Radii R_sun
let starMass = 1.0; // Solar Masses M_sun
let starTemp = 5778; // Kelvin
let planetRadius = 1.0; // Jupiter Radii (R_J)
let orbitalPeriod = 4.5; // days
let impactParameter = 0.0; // b (0 to 0.95)
let spotActivity = 2; // 0, 1, 2, 3
let noiseLevel = 1; // 0, 1, 2, 3
let detrendOn = true;
let foldOn = false;
let isPlaying = true;

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

// Update values from sliders and select
selectStarType.addEventListener("change", (e) => {
    starType = e.target.value;
    if (starType === "M") {
        starRadius = 0.3;
        starMass = 0.3;
        starTemp = 3000;
        valStarType.textContent = "M-Dwarf (Red Dwarf)";
    } else if (starType === "G") {
        starRadius = 1.0;
        starMass = 1.0;
        starTemp = 5778;
        valStarType.textContent = "G-Dwarf (Yellow Dwarf)";
    } else if (starType === "F") {
        starRadius = 1.4;
        starMass = 1.3;
        starTemp = 7000;
        valStarType.textContent = "F-Star (Yellow-White)";
    }
    updateMetrics();
});

slideSize.addEventListener("input", (e) => {
    planetRadius = parseFloat(e.target.value);
    valSize.textContent = `${planetRadius.toFixed(1)} R_J`;
    updateMetrics();
});

slidePeriod.addEventListener("input", (e) => {
    orbitalPeriod = parseFloat(e.target.value);
    valPeriod.textContent = `${orbitalPeriod.toFixed(1)} d`;
    updateMetrics();
});

slideImpact.addEventListener("input", (e) => {
    impactParameter = parseFloat(e.target.value);
    valImpact.textContent = impactParameter === 0 ? "0.00 (Center)" : impactParameter.toFixed(2);
    updateMetrics();
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
btnPlay.addEventListener("click", () => {
    isPlaying = !isPlaying;
    btnPlay.classList.toggle("active", isPlaying);
    btnPlay.innerHTML = isPlaying ? '<i class="fa-solid fa-pause"></i> Active' : '<i class="fa-solid fa-play"></i> Paused';
});

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

// Function to calculate and render physical metrics
function updateMetrics() {
    const orbitalPeriodYears = orbitalPeriod / 365.25;
    const a = Math.pow(starMass * Math.pow(orbitalPeriodYears, 2), 1/3); // AU
    
    const planetRadiusSun = planetRadius * 0.103;
    const depthFraction = Math.pow(planetRadiusSun / starRadius, 2);
    const depthPercent = depthFraction * 100;
    const depthPpm = depthFraction * 1000000;
    
    // Equilibrium Temp Teq = 0.0441 * T_* * sqrt(R_*/a)
    const teq = 0.0441 * starTemp * Math.sqrt(starRadius / a);
    const teqCelsius = teq - 273.15;
    
    metricStarParams.textContent = `${starRadius.toFixed(2)} R☉ / ${starMass.toFixed(2)} M☉`;
    metricStarTemp.textContent = `${starTemp.toLocaleString()} K`;
    metricAxis.textContent = `${a.toFixed(4)} AU`;
    
    const canTransit = impactParameter < (1.0 + planetRadiusSun / starRadius);
    if (canTransit) {
        metricDepth.textContent = `${depthPercent.toFixed(3)}% (${Math.round(depthPpm).toLocaleString()} ppm)`;
    } else {
        metricDepth.textContent = `0.00% (No Transit, b too high)`;
    }
    
    metricTemp.textContent = `${Math.round(teq)} K (${Math.round(teqCelsius)}°C)`;
    
    // Habitability status
    metricStatus.className = "metric-value status-badge";
    if (teq > 310) {
        metricStatus.textContent = "Too Hot (Scorch)";
        metricStatus.classList.add("hot");
    } else if (teq >= 190 && teq <= 310) {
        metricStatus.textContent = "Habitable Zone";
        metricStatus.classList.add("habitable");
    } else {
        metricStatus.textContent = "Too Cold (Frozen)";
        metricStatus.classList.add("cold");
    }
    
    // Live mathematical formula updates
    if (liveEqDepth) {
        liveEqDepth.textContent = `Live: ${canTransit ? depthPercent.toFixed(3) : "0.00"}%`;
    }
    if (liveEqAxis) {
        liveEqAxis.textContent = `Live: ${a.toFixed(4)} AU`;
    }
    if (liveEqTemp) {
        liveEqTemp.textContent = `Live: ${Math.round(teq)} K`;
    }
}

// Initial metrics calculation
updateMetrics();

// Main physics step
function updateSimulation() {
    simTime += 0.05; // increment time
    
// Main physics step
function updateSimulation() {
    if (!isPlaying) return; // pause logic

    simTime += 0.05; // increment time
    
    // 1. Calculate semi-major axis & physical transit parameters
    const orbitalPeriodYears = orbitalPeriod / 365.25;
    const a = Math.pow(starMass * Math.pow(orbitalPeriodYears, 2), 1/3); // AU
    const planetRadiusSun = planetRadius * 0.103;
    const planetDepth = Math.pow(planetRadiusSun / starRadius, 2);
    
    // Keplerian transit duration with inclination (impact parameter b)
    // Scale duration by 2.0 for visual clarity in simulation plot
    const durationBaseline = (orbitalPeriod / Math.PI) * (starRadius * 0.00465 / a);
    const durationFactor = Math.max(0, 1 - Math.pow(impactParameter, 2));
    const duration = 2.0 * durationBaseline * Math.sqrt(durationFactor);
    
    // 2. Calculate transit dip (trapezoidal)
    const transitCenter = orbitalPeriod / 2;
    const currentPhase = (simTime) % orbitalPeriod;
    
    let transitSignal = 0;
    const timeToTransit = Math.abs(currentPhase - transitCenter);
    const canTransit = impactParameter < (1.0 + planetRadiusSun / starRadius);
    
    if (canTransit && duration > 0 && timeToTransit < duration / 2) {
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
    
    // 3. Calculate Stellar Spot Variability (sinusoidal rotation)
    // M-dwarfs are highly active, F-stars are slightly more stable
    let spotSignal = 0;
    if (spotActivity > 0) {
        const activityMultiplier = starType === "M" ? 2.2 : (starType === "F" ? 0.6 : 1.0);
        const spotAmp = spotActivity * 0.006 * activityMultiplier; // amp scaling
        const rotPeriod = orbitalPeriod * 2.5; // star rotates slower than orbit
        spotSignal = spotAmp * Math.sin(2 * Math.PI * simTime / rotPeriod) + 
                     (spotAmp * 0.2) * Math.sin(4 * Math.PI * simTime / rotPeriod); // harmonic
    }
    
    // 4. Generate Noise
    let noise = 0;
    if (noiseLevel > 0) {
        const noiseMultiplier = starType === "M" ? 1.5 : 1.0;
        const noiseStd = noiseLevel * 0.0015 * noiseMultiplier;
        noise = randn() * noiseStd;
    }
    
    // 5. Combine signals
    const rawFlux = 1.0 + transitSignal + spotSignal + noise;
    
    // 6. Store point
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
    
    // 7. Compute Detrending (rolling boxcar average)
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

// Clear historical points to prevent mixing physical presets
function clearSimulationData() {
    points.length = 0;
}

// Hook data clearing to physical change listeners
selectStarType.addEventListener("change", clearSimulationData);
slideSize.addEventListener("input", clearSimulationData);
slidePeriod.addEventListener("input", clearSimulationData);
slideImpact.addEventListener("input", clearSimulationData);

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
    
    // Visual radius scales slightly with star class
    let starRadiusScale = 1.0;
    if (starType === "M") starRadiusScale = 0.6;
    else if (starType === "F") starRadiusScale = 1.3;
    const drawStarRadius = skyHeight * 0.3 * starRadiusScale;
    
    // Stellar limb darkening gradient
    const grad = ctx.createRadialGradient(starX, starY, drawStarRadius * 0.1, starX, starY, drawStarRadius);
    if (starType === "M") {
        grad.addColorStop(0, "#fecaca"); // core
        grad.addColorStop(0.6, "#ef4444"); // outer
        grad.addColorStop(1, "#7f1d1d"); // limb
        ctx.shadowColor = "#ef4444";
    } else if (starType === "F") {
        grad.addColorStop(0, "#ffffff"); // core
        grad.addColorStop(0.6, "#e0f2fe"); // outer
        grad.addColorStop(1, "#38bdf8"); // limb
        ctx.shadowColor = "#0ea5e9";
    } else {
        grad.addColorStop(0, "#fef08a"); // core
        grad.addColorStop(0.7, "#f59e0b"); // outer
        grad.addColorStop(1, "#b45309"); // limb
        ctx.shadowColor = "#f59e0b";
    }
    
    ctx.beginPath();
    ctx.arc(starX, starY, drawStarRadius, 0, 2 * Math.PI);
    ctx.fillStyle = grad;
    ctx.shadowBlur = 30;
    ctx.fill();
    ctx.shadowBlur = 0; // reset
    
    // Draw Starspots visually
    if (spotActivity > 0) {
        ctx.fillStyle = starType === "M" ? "rgba(100, 10, 10, 0.75)" : "rgba(74, 42, 10, 0.65)";
        // spot positions shift slowly
        const spotX1 = starX - drawStarRadius * 0.4 + (Math.sin(simTime * 0.1) * drawStarRadius * 0.3);
        const spotY1 = starY - drawStarRadius * 0.2;
        ctx.beginPath();
        ctx.arc(spotX1, spotY1, drawStarRadius * 0.12, 0, 2*Math.PI);
        ctx.fill();
        
        const spotX2 = starX + drawStarRadius * 0.3 + (Math.sin(simTime * 0.1 + 1) * drawStarRadius * 0.3);
        const spotY2 = starY + drawStarRadius * 0.2;
        ctx.beginPath();
        ctx.arc(spotX2, spotY2, drawStarRadius * 0.15, 0, 2*Math.PI);
        ctx.fill();
    }
    
    // Draw Orbit Chord Path
    ctx.strokeStyle = "rgba(96, 165, 250, 0.12)";
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(starX - drawStarRadius * 2.25, starY + impactParameter * drawStarRadius);
    ctx.lineTo(starX + drawStarRadius * 2.25, starY + impactParameter * drawStarRadius);
    ctx.stroke();
    ctx.setLineDash([]); // reset
    
    // Draw Planet orbiting
    // Phase goes from 0 to orbitalPeriod
    const currentPhase = (simTime) % orbitalPeriod;
    const currentPhaseRatio = currentPhase / orbitalPeriod - 0.5; // -0.5 to 0.5
    const planetX = starX + currentPhaseRatio * (drawStarRadius * 4.5); // span wider than star
    const planetY = starY + impactParameter * drawStarRadius;
    
    const planetRadiusSun = planetRadius * 0.103;
    const drawPlanetRadius = Math.max(3, drawStarRadius * (planetRadiusSun / starRadius));
    
    // Determine if planet is behind the star (occulted)
    const isBehind = (currentPhaseRatio < -0.25 || currentPhaseRatio > 0.25);
    const isOverlapping = Math.hypot(planetX - starX, planetY - starY) < drawStarRadius;
    
    if (isBehind && isOverlapping) {
        // Draw occulted planet (translucent)
        ctx.save();
        ctx.globalAlpha = 0.15;
        ctx.beginPath();
        ctx.arc(planetX, planetY, drawPlanetRadius, 0, 2 * Math.PI);
        ctx.fillStyle = "#0b0f19";
        ctx.fill();
        ctx.restore();
    } else {
        // Draw normal planet in front of or outside the star
        ctx.beginPath();
        ctx.arc(planetX, planetY, drawPlanetRadius, 0, 2 * Math.PI);
        ctx.fillStyle = "#0b0f19";
        ctx.strokeStyle = "rgba(96, 165, 250, 0.6)";
        ctx.lineWidth = 1.5;
        ctx.fill();
        ctx.stroke();
    }
    
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
    
    // Set Y scale centered around 1.0. Let's make it responsive to transit depth
    const maxDip = Math.max(0.02, planetDepth * 1.5);
    const yTicks = [1.0 - maxDip, 1.0 - maxDip * 0.5, 1.0, 1.0 + maxDip * 0.5];
    
    yTicks.forEach(val => {
        const y = plotY + plotHeight/2 - (val - 1.0) * (plotHeight / (maxDip * 2.2));
        if (y >= plotY && y <= plotY + plotHeight) {
            ctx.strokeStyle = "rgba(30, 41, 59, 0.4)";
            ctx.beginPath();
            ctx.moveTo(plotX, y);
            ctx.lineTo(plotX + plotWidth, y);
            ctx.stroke();
            ctx.fillText(val.toFixed(3), plotX - 10, y + 3);
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
            
            points.forEach(p => {
                const px = plotX + (p.phase + 0.5) * plotWidth; // map phase [-0.5, 0.5] to width
                const fluxVal = detrendOn ? p.detrendedFlux : p.rawFlux;
                const py = plotY + plotHeight/2 - (fluxVal - 1.0) * (plotHeight / (maxDip * 2.2));
                
                if (py >= plotY && py <= plotY + plotHeight) {
                    ctx.beginPath();
                    ctx.arc(px, py, 2.5, 0, 2*Math.PI);
                    ctx.fillStyle = detrendOn ? "#06b6d4" : "#ef4444";
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
                const py = plotY + plotHeight/2 - (p.rawFlux - 1.0) * (plotHeight / (maxDip * 2.2));
                
                if (py >= plotY && py <= plotY + plotHeight) {
                    ctx.beginPath();
                    ctx.arc(px, py, 1.5, 0, 2 * Math.PI);
                    ctx.fillStyle = detrendOn ? "rgba(239, 68, 68, 0.3)" : "#ef4444";
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
                    const py = plotY + plotHeight/2 - (p.trend - 1.0) * (plotHeight / (maxDip * 2.2));
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
                    const py = plotY + plotHeight/2 - (p.detrendedFlux - 1.0) * (plotHeight / (maxDip * 2.2));
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

// --- SCROLL REVEAL TIMELINE NODES ---
const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add("visible");
            revealObserver.unobserve(entry.target); // stop observing once visible
        }
    });
}, {
    threshold: 0.15,
    rootMargin: "0px 0px -50px 0px"
});

document.querySelectorAll(".reveal").forEach(el => {
    revealObserver.observe(el);
});

