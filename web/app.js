document.addEventListener("DOMContentLoaded", () => {
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
let planetDepth = 0.0106;

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
    if (!isPlaying) return; // pause logic

    simTime += 0.05; // increment time
    
    // 1. Calculate semi-major axis & physical transit parameters
    const orbitalPeriodYears = orbitalPeriod / 365.25;
    const a = Math.pow(starMass * Math.pow(orbitalPeriodYears, 2), 1/3); // AU
    const planetRadiusSun = planetRadius * 0.103;
    planetDepth = Math.pow(planetRadiusSun / starRadius, 2);
    
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

const quizBank = [
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
    },
    {
        question: "According to Kepler's Third Law, if an exoplanet has a very short orbital period, its orbital distance from the star is:",
        options: [
            "Very large.",
            "Very small.",
            "Completely unaffected by period."
        ],
        correct: 1,
        feedback: "Correct! Kepler's Third Law states that the square of the orbital period is proportional to the cube of the semi-major axis. Thus, short periods mean very close orbits."
    },
    {
        question: "The depth of a transit signal is proportional to what physical ratio?",
        options: [
            "Planet mass to star mass.",
            "Planet radius to star radius squared.",
            "Planet distance to star distance."
        ],
        correct: 1,
        feedback: "Correct! Transit depth is approximately (Rp/Rs)^2, representing the ratio of the projected area of the planet to that of the star."
    },
    {
        question: "Why are transit dips often curved/rounded at the bottom instead of flat?",
        options: [
            "Because the planet is a gas giant.",
            "Due to stellar limb darkening.",
            "Because the star is rotating extremely fast."
        ],
        correct: 1,
        feedback: "Correct! The edges of a stellar disk are cooler and appear dimmer than the center (limb darkening), causing a gradual curve as the planet crosses."
    },
    {
        question: "What is a secondary eclipse in an exoplanet system's light curve?",
        options: [
            "When the planet passes behind the host star.",
            "When a second planet transits at the same time.",
            "When the star passes behind the planet."
        ],
        correct: 0,
        feedback: "Correct! The secondary eclipse occurs when the planet passes behind the star, causing a tiny drop in light as the planet's reflected thermal emission is blocked."
    },
    {
        question: "The Radial Velocity method detects exoplanets by measuring what physical effect?",
        options: [
            "The dip in stellar brightness.",
            "The gravitational wobble of the host star via Doppler shifts.",
            "The thermal radiation of the planet."
        ],
        correct: 1,
        feedback: "Correct! A planet's gravity pulls on its star, causing the star to orbit around their common center of mass, which produces Doppler shifts in the star's spectrum."
    },
    {
        question: "When a star moves toward Earth due to a planet's gravity, its spectral lines are:",
        options: [
            "Redshifted (shifted to longer wavelengths).",
            "Blueshifted (shifted to shorter wavelengths).",
            "Completely extinguished."
        ],
        correct: 1,
        feedback: "Correct! Light waves from an approaching source are compressed, shifting them to shorter (bluer) wavelengths."
    },
    {
        question: "The boundaries of the Habitable Zone (Goldilocks Zone) around a star depend primarily on:",
        options: [
            "The star's luminosity and temperature.",
            "The planet's magnetic field strength.",
            "The number of moons the planet has."
        ],
        correct: 0,
        feedback: "Correct! A star's luminosity determines the amount of energy reaching the planet, defining the distance range where liquid water can exist."
    },
    {
        question: "What is a 'Hot Jupiter'?",
        options: [
            "A gas giant orbiting extremely close to its parent star.",
            "A star that looks like Jupiter.",
            "A planet made of molten iron."
        ],
        correct: 0,
        feedback: "Correct! Hot Jupiters are gas giants with masses similar to or greater than Jupiter, but with very short orbital periods (usually under 10 days)."
    },
    {
        question: "Why is the Savitzky-Golay filter popular for transit detrending?",
        options: [
            "It fits local low-degree polynomials to preserve sharp transit features.",
            "It converts time-series data into images.",
            "It automatically identifies the orbital period."
        ],
        correct: 0,
        feedback: "Correct! The Savitzky-Golay filter fits local polynomials, which removes low-frequency stellar noise while preserving high-frequency edges like the ingress and egress of a transit."
    },
    {
        question: "The Box Least Squares (BLS) algorithm is optimized for finding:",
        options: [
            "Sinusoidal radial velocity curves.",
            "Box-like periodic dips in light curves.",
            "Spontaneous stellar flares."
        ],
        correct: 1,
        feedback: "Correct! BLS models transits as periodic box-like dips, making it highly effective at scanning light curves for exoplanet transit signatures."
    },
    {
        question: "The TESS space telescope primary mission observes sectors for how long?",
        options: [
            "27 days.",
            "365 days.",
            "7 days."
        ],
        correct: 0,
        feedback: "Correct! TESS monitors each sky sector for approximately 27.4 days before moving to the next sector."
    },
    {
        question: "Which instrument capability of the James Webb Space Telescope (JWST) is crucial for analyzing exoplanet atmospheres?",
        options: [
            "Transit transmission spectroscopy in the infrared.",
            "Radar imaging of surface rocks.",
            "X-ray coronal measurements."
        ],
        correct: 0,
        feedback: "Correct! Transmission spectroscopy during transit allows JWST to measure stellar light filtered through a planet's atmosphere to detect molecules like water, CO2, and methane."
    },
    {
        question: "In the planet name 'Kepler-186f', what does the letter 'f' indicate?",
        options: [
            "It is the fifth planet discovered in that system.",
            "It is the sixth star in the cluster.",
            "It stands for 'Foreign'."
        ],
        correct: 0,
        feedback: "Correct! Exoplanet naming conventions start with 'b' for the first planet discovered in a system, followed by 'c', 'd', 'e', 'f', etc."
    },
    {
        question: "Why do we compare the depths of odd and even transits in vetting pipelines?",
        options: [
            "To filter out eclipsing binaries with alternating primary/secondary eclipses.",
            "To measure the eccentricity of the planet's orbit.",
            "To determine the rotation rate of the star."
        ],
        correct: 0,
        feedback: "Correct! In eclipsing binaries, the primary and secondary stars have different sizes, producing alternating deep and shallow eclipses. Exoplanets produce identical transit depths."
    },
    {
        question: "What is a 'Super-Earth'?",
        options: [
            "A planet with a mass larger than Earth but smaller than Neptune.",
            "A planet identical to Earth in every way.",
            "A giant planet orbiting a black hole."
        ],
        correct: 0,
        feedback: "Correct! Super-Earths are planets with masses roughly between 1 and 10 times Earth's mass, which can be either rocky or gaseous."
    },
    {
        question: "Which of the following is considered a potential atmospheric biosignature?",
        options: [
            "Simultaneous presence of oxygen and methane out of chemical equilibrium.",
            "High abundance of helium.",
            "Presence of carbon dioxide on a frozen world."
        ],
        correct: 0,
        feedback: "Correct! Oxygen and methane react quickly; finding them together implies active biological processes are continuously replenishing them."
    },
    {
        question: "The distance at which a celestial body, held together only by its own gravity, will disintegrate due to a second body's tidal forces is called the:",
        options: [
            "Roche Limit.",
            "Kepler Radius.",
            "Lagrange Threshold."
        ],
        correct: 0,
        feedback: "Correct! Inside the Roche Limit, tidal forces overcome the gravity holding the smaller body together, ripping it apart."
    },
    {
        question: "What is a gravitational slingshot (gravity assist)?",
        options: [
            "Using a planet's gravity to alter the path and speed of a spacecraft.",
            "Using gravity to detect distant black holes.",
            "A method to change a planet's orbit."
        ],
        correct: 0,
        feedback: "Correct! Spacecraft fly close to planets to gain momentum and speed without consuming propellant."
    },
    {
        question: "What is a planet's 'albedo'?",
        options: [
            "The fraction of incident light reflected by the planet's surface/atmosphere.",
            "The speed of the planet's rotation.",
            "The thickness of the planet's core."
        ],
        correct: 0,
        feedback: "Correct! Albedo ranges from 0 (perfect absorber) to 1 (perfect reflector) and is critical for calculating equilibrium temperatures."
    },
    {
        question: "The Kepler Space Telescope primarily searched for exoplanets using which method?",
        options: [
            "Transit method.",
            "Radial Velocity method.",
            "Gravitational Microlensing."
        ],
        correct: 0,
        feedback: "Correct! Kepler revolutionized exoplanet science by continuously monitoring over 150,000 stars to detect transit dips."
    },
    {
        question: "Gravitational microlensing detects planets by measuring:",
        options: [
            "The bending of light from a background star by a foreground star and its planet.",
            "The physical wobble of the star.",
            "The direct thermal emission of the planet."
        ],
        correct: 0,
        feedback: "Correct! When a star and its planet pass exactly in front of a background star, their gravity acts as a lens, temporarily magnifying the background star's light."
    },
    {
        question: "Astrometry detects planets by measuring:",
        options: [
            "The precise physical positions and motions of a star on the sky.",
            "The brightness fluctuations of the star.",
            "The redshift of spectral lines."
        ],
        correct: 0,
        feedback: "Correct! Astrometry tracks the tiny 2D position shifts of a star on the sky as it wobbles due to the gravity of an orbiting planet."
    },
    {
        question: "Why is direct imaging of exoplanets extremely difficult?",
        options: [
            "Because planets are much dimmer than their host stars and very close to them.",
            "Because planets do not emit or reflect any light.",
            "Because stars are always moving too fast."
        ],
        correct: 0,
        feedback: "Correct! Stars are typically millions to billions of times brighter than their planets, requiring advanced tools like coronagraphs to block the stellar glare."
    },
    {
        question: "What does a coronagraph do in an astronomical telescope?",
        options: [
            "It blocks the direct light from a star to reveal faint nearby objects like planets.",
            "It measures the magnetic field of the corona.",
            "It focuses cosmic rays onto a sensor."
        ],
        correct: 0,
        feedback: "Correct! A coronagraph acts as an artificial mask to block stellar glare, allowing direct imaging of exoplanetary systems."
    },
    {
        question: "Proxima Centauri b is famous because it is:",
        options: [
            "The closest known exoplanet to Earth, orbiting in the habitable zone.",
            "The largest gas giant ever found.",
            "The first exoplanet discovered in another galaxy."
        ],
        correct: 0,
        feedback: "Correct! Proxima Centauri b orbits our nearest stellar neighbor, Proxima Centauri, at a distance of 4.2 light-years, inside its habitable zone."
    },
    {
        question: "What are the primary elements that make up gas giants like Jupiter and Saturn?",
        options: [
            "Hydrogen and Helium.",
            "Silicon and Iron.",
            "Water and Carbon Dioxide."
        ],
        correct: 0,
        feedback: "Correct! Gas giants are composed mostly of hydrogen and helium, similar to the composition of the solar nebula."
    },
    {
        question: "What happens when an exoplanet is 'tidally locked' to its host star?",
        options: [
            "One side of the planet permanently faces the star (permanent day).",
            "The planet stops orbiting the star.",
            "The planet's ocean tides freeze solid."
        ],
        correct: 0,
        feedback: "Correct! Tidal locking occurs when the planet's rotation period matches its orbital period, resulting in a permanent day side and a permanent night side."
    },
    {
        question: "Which type of star is the coolest and most common in the Milky Way?",
        options: [
            "M-Dwarf (Red Dwarf).",
            "G-Dwarf (Yellow Sun-like).",
            "O-Type Star (Blue Giant)."
        ],
        correct: 0,
        feedback: "Correct! M-dwarfs are small, cool stars that make up about 70-75% of all stars in the Milky Way."
    },
    {
        question: "The Earth Similarity Index (ESI) is a measure of:",
        options: [
            "A planet's physical similarity to Earth (radius, density, temperature).",
            "Whether Earth-like life exists on the planet.",
            "The distance of the planet from Earth."
        ],
        correct: 0,
        feedback: "Correct! ESI scales from 0 to 1, comparing a planet's radius, density, escape velocity, and temperature to Earth's parameters."
    },
    {
        question: "If a planet orbits in a highly eccentric (oval) orbit, its transit duration:",
        options: [
            "Depends on where the transit occurs along the orbit.",
            "Is always identical to a circular orbit.",
            "Is always zero."
        ],
        correct: 0,
        feedback: "Correct! Velocity varies along an eccentric orbit (Kepler's Second Law), so transit duration depends on whether the transit occurs at periastron (fast) or apastron (slow)."
    },
    {
        question: "Why is Kepler-452b often referred to as 'Earth's Cousin'?",
        options: [
            "It is a rocky planet orbiting a G-type star with a 385-day orbit.",
            "It has a large active population of scientists.",
            "It was the first planet photographed directly."
        ],
        correct: 0,
        feedback: "Correct! Kepler-452b is about 1.6 times Earth's radius and orbits a G-type star very similar to the Sun, with an orbital period of 385 days."
    },
    {
        question: "What is planetary transit 'ingress'?",
        options: [
            "The phase where the planet enters the stellar disk.",
            "The phase where the planet leaves the stellar disk.",
            "The midpoint of the transit."
        ],
        correct: 0,
        feedback: "Correct! Ingress is the period during which the planet's disk first begins to overlap and fully cross onto the star's disk."
    },
    {
        question: "What is planetary transit 'egress'?",
        options: [
            "The phase where the planet leaves the stellar disk.",
            "The phase where the planet enters the stellar disk.",
            "The deepest point of the transit."
        ],
        correct: 0,
        feedback: "Correct! Egress is the phase where the planet's disk moves off the stellar disk, returning the light curve back to its out-of-transit level."
    },
    {
        question: "TESS (Transiting Exoplanet Survey Satellite) focuses primarily on:",
        options: [
            "Bright, nearby stars to enable follow-up characterization.",
            "Extremely distant galaxies.",
            "Only stars inside the Orion Nebula."
        ],
        correct: 0,
        feedback: "Correct! TESS was designed to map the brightest stars in the sky to enable ground-based telescopes and JWST to perform radial velocity and atmospheric measurements."
    },
    {
        question: "What is 'red noise' (correlated noise) in light curves?",
        options: [
            "Noise with low-frequency correlations, often caused by stellar activity.",
            "Noise that is only visible when using red filters.",
            "Sensor noise caused by cosmic ray hits."
        ],
        correct: 0,
        feedback: "Correct! Red noise refers to time-correlated noise (like starspots or instrument drift) which can easily mimic or obscure transit signals."
    },
    {
        question: "What is 'white noise' in light curves?",
        options: [
            "Random, uncorrelated noise from photon counting statistics.",
            "Noise from white dwarf stars.",
            "Interference from visible light leaks."
        ],
        correct: 0,
        feedback: "Correct! White noise is independent and identically distributed noise, representing photon shot noise from the telescope sensor."
    },
    {
        question: "What does phase folding a light curve achieve?",
        options: [
            "It overlays multiple periodic transits to increase the signal-to-noise ratio.",
            "It physically flattens the light curve.",
            "It removes all out-of-transit data points."
        ],
        correct: 0,
        feedback: "Correct! Phase folding maps time-series data to a phase interval [-0.5, 0.5] using the orbital period, wrapping all individual transit events on top of each other."
    },
    {
        question: "In AstroPulse, what does the 'Consensus Score' represent?",
        options: [
            "An ensemble average probability combined with signal SNR and fit stability.",
            "The agreement between astronomers on the naming of a planet.",
            "The temperature of the exoplanet's core."
        ],
        correct: 0,
        feedback: "Correct! The consensus score aggregates predictions from machine learning models (CNN, RF, XGBoost, etc.) and physical metrics to vet candidate signals."
    },
    {
        question: "Why do we use 1D Convolutional Neural Networks (CNNs) in exoplanet vetting?",
        options: [
            "To automatically extract local shape features from phase-folded profiles.",
            "To model long-term stellar cycles spanning years.",
            "To calculate the planetary radius directly."
        ],
        correct: 0,
        feedback: "Correct! 1D CNNs are highly effective at detecting local spatial features, allowing them to distinguish U-shaped transits from V-shaped eclipses."
    },
    {
        question: "What role does an LSTM layer play in a hybrid CNN-LSTM model?",
        options: [
            "It captures sequential correlations and transition phases like ingress/egress.",
            "It speeds up training times on the CPU.",
            "It predicts the mass of the exoplanet."
        ],
        correct: 0,
        feedback: "Correct! LSTMs are Recurrent Neural Networks designed to capture sequence and temporal dependency, enhancing detection for weak transit boundaries."
    },
    {
        question: "Kepler's First Law states that planetary orbits are:",
        options: [
            "Ellipses, with the star at one focus.",
            "Perfect circles, with the star at the center.",
            "Parabolas, with the star at the vertex."
        ],
        correct: 0,
        feedback: "Correct! Kepler's First Law established that all orbits are elliptical, breaking the classical assumption of perfect circular motion."
    },
    {
        question: "Kepler's Second Law (equal areas in equal times) implies that a planet moves:",
        options: [
            "Faster when close to the star, slower when far away.",
            "At a constant speed at all times.",
            "Slower when close to the star, faster when far away."
        ],
        correct: 0,
        feedback: "Correct! As a planet approaches periastron (closest point), the gravitational pull increases, causing it to accelerate and sweep out equal areas in equal times."
    },
    {
        question: "The semi-major axis is a measure of:",
        options: [
            "The average distance of a planet from its host star.",
            "The radius of the planet's equator.",
            "The rotation speed of the host star."
        ],
        correct: 0,
        feedback: "Correct! The semi-major axis is half of the longest diameter of an elliptical orbit, representing the planet's mean distance from its star."
    },
    {
        question: "An orbital eccentricity (e) of exactly 0 represents:",
        options: [
            "A perfect circle.",
            "A straight line.",
            "A parabola."
        ],
        correct: 0,
        feedback: "Correct! Eccentricity measures the elongation of an orbit. A circle has e=0, ellipses have 0 < e < 1, and parabolas have e=1."
    },
    {
        question: "The equilibrium temperature of a planet in the habitable zone must allow:",
        options: [
            "Liquid water to exist on the surface.",
            "Iron to melt into liquid.",
            "Liquid nitrogen to form oceans."
        ],
        correct: 0,
        feedback: "Correct! The habitable zone is defined as the range where planetary surface temperatures permit liquid water, a key requirement for life as we know it."
    },
    {
        question: "Why can a planet's actual temperature be much higher than its calculated equilibrium temperature?",
        options: [
            "Due to atmospheric greenhouse gas trapping.",
            "Because of tidal heating from its core.",
            "Because the planet is closer than calculated."
        ],
        correct: 0,
        feedback: "Correct! Greenhouse gases like carbon dioxide and water vapor trap infrared radiation, raising the surface temperature (as seen on Venus)."
    },
    {
        question: "Transmission spectroscopy measures exoplanet atmospheres by:",
        options: [
            "Analyzing starlight filtering through the atmosphere during transit.",
            "Directly photographing the clouds of the planet.",
            "Measuring radio waves emitted by the planet."
        ],
        correct: 0,
        feedback: "Correct! As a planet transits, starlight passes through the ring of its atmosphere, leaving absorption lines that reveal atmospheric chemical composition."
    },
    {
        question: "Emission spectroscopy of exoplanets is typically performed during:",
        options: [
            "Secondary eclipse (just before or after the planet goes behind the star).",
            "Primary transit.",
            "The planet's winter solstice."
        ],
        correct: 0,
        feedback: "Correct! By measuring the spectrum of the system before and during secondary eclipse, scientists can isolate the thermal radiation emitted by the planet's day side."
    },
    {
        question: "What was the first exoplanet discovered around a Sun-like star?",
        options: [
            "51 Pegasi b.",
            "Kepler-10b.",
            "HD 189733b."
        ],
        correct: 0,
        feedback: "Correct! Discovered in 1995 by Michel Mayor and Didier Queloz (for which they won the Nobel Prize), 51 Pegasi b is a Hot Jupiter orbiting a Sun-like star."
    },
    {
        question: "The very first exoplanets ever confirmed were found orbiting what type of object?",
        options: [
            "A pulsar (neutron star).",
            "A red giant.",
            "A white dwarf."
        ],
        correct: 0,
        feedback: "Correct! In 1992, Aleksander Wolszczan and Dale Frail discovered three planets orbiting the pulsar PSR B1257+12 by measuring anomalies in pulse timing."
    },
    {
        question: "Radial velocity measurements are most sensitive to:",
        options: [
            "Massive planets orbiting close to their stars.",
            "Tiny planets orbiting far from their stars.",
            "Rocky planets orbiting red giants."
        ],
        correct: 0,
        feedback: "Correct! Massive planets close to their host stars exert the strongest gravitational pull, causing the largest stellar wobbles."
    },
    {
        question: "The center of mass of two or more orbiting bodies is called the:",
        options: [
            "Barycenter.",
            "Apex.",
            "Focus."
        ],
        correct: 0,
        feedback: "Correct! Stars and planets orbit around their shared barycenter. For the solar system, the barycenter lies near the surface of the Sun."
    },
    {
        question: "In AstroPulse, what Python library is used for astronomical coordinates and units?",
        options: [
            "Astropy.",
            "SciPy.",
            "SymPy."
        ],
        correct: 0,
        feedback: "Correct! Astropy is the standard library for astronomy and astrophysics in Python, offering tools for units, coordinates, and FITS files."
    },
    {
        question: "What is a light-year?",
        options: [
            "The distance light travels in one Earth year.",
            "The time it takes light to reach the Sun.",
            "The speed of light in a vacuum."
        ],
        correct: 0,
        feedback: "Correct! A light-year is a unit of distance, equal to about 9.46 trillion kilometers (5.88 trillion miles)."
    },
    {
        question: "An Astronomical Unit (AU) is defined as:",
        options: [
            "The average distance between the Earth and the Sun.",
            "The distance from the Sun to Pluto.",
            "The radius of the Sun."
        ],
        correct: 0,
        feedback: "Correct! One AU is approximately 149.6 million kilometers (93 million miles), the mean distance from Earth to the Sun."
    },
    {
        question: "How does stellar spot modulation affect a light curve?",
        options: [
            "It creates slow, quasi-periodic waves as the star rotates.",
            "It creates sharp, sudden spikes in brightness.",
            "It removes the transit signature entirely."
        ],
        correct: 0,
        feedback: "Correct! As a star rotates, starspots rotate in and out of view, causing gradual, cyclic fluctuations in stellar brightness."
    },
    {
        question: "What is a stellar flare?",
        options: [
            "A sudden, high-energy eruption on the star causing a brief spike in brightness.",
            "A slow cooling of the star's surface.",
            "The death of the host star."
        ],
        correct: 0,
        feedback: "Correct! Flares are sudden releases of magnetic energy that cause a sharp increase in brightness, which vetting algorithms must filter out as anomalies."
    },
    {
        question: "Kepler-22b is notable because it was the first Kepler planet confirmed to:",
        options: [
            "Orbit within the habitable zone of a Sun-like star.",
            "Be composed entirely of water.",
            "Possess an oxygen-rich atmosphere."
        ],
        correct: 0,
        feedback: "Correct! Confirmed in 2011, Kepler-22b orbits a G-type star in the habitable zone, with a radius about 2.4 times that of Earth."
    },
    {
        question: "Approximately how many Earth masses are equal to one Jupiter mass?",
        options: [
            "318.",
            "10.",
            "1000."
        ],
        correct: 0,
        feedback: "Correct! Jupiter is the largest planet in our solar system, with a mass equal to approximately 318 Earth masses."
    },
    {
        question: "To calculate a planet's density, what two parameters must be known?",
        options: [
            "Mass and Radius.",
            "Period and Distance.",
            "Temperature and Albedo."
        ],
        correct: 0,
        feedback: "Correct! Density is Mass divided by Volume, where volume is calculated from the planet's radius."
    },
    {
        question: "Which type of planet generally has a higher average density?",
        options: [
            "Rocky (Terrestrial) planets.",
            "Gas Giant planets.",
            "Ice Giant planets."
        ],
        correct: 0,
        feedback: "Correct! Rocky planets are composed of metals and silicate rocks (density ~3-5 g/cm³), while gas giants are mostly hydrogen and helium (density ~0.7-1.3 g/cm³)."
    },
    {
        question: "What does an impact parameter (b) of 0 mean for a transit?",
        options: [
            "The planet transits directly across the center of the stellar disk.",
            "The planet grazes the edge of the star.",
            "No transit occurs."
        ],
        correct: 0,
        feedback: "Correct! An impact parameter of 0 represents a central transit, maximizing the transit duration."
    },
    {
        question: "A transit with an impact parameter b ≈ 1.0 is called a:",
        options: [
            "Grazing transit.",
            "Central transit.",
            "Non-transit."
        ],
        correct: 0,
        feedback: "Correct! A grazing transit occurs when the planet only partially overlaps the edge of the star, resulting in a V-shaped curve."
    },
    {
        question: "Kepler-10b is famous as the first Kepler exoplanet confirmed to be:",
        options: [
            "Rocky (a rocky Super-Earth).",
            "A gas giant.",
            "A water world."
        ],
        correct: 0,
        feedback: "Correct! Kepler-10b was the first rocky exoplanet discovered by Kepler, with a density showing it is composed of rock and iron."
    },
    {
        question: "The transit depth of Earth transiting the Sun, as seen from a distant star, is about:",
        options: [
            "100 parts per million (0.01%).",
            "1 percent.",
            "10 percent."
        ],
        correct: 0,
        feedback: "Correct! Earth's small radius relative to the Sun results in a tiny transit depth of ~100 ppm, requiring high-precision space photometry to detect."
    },
    {
        question: "Kepler-16b is famous because it is a 'Tatooine-like' planet, meaning it:",
        options: [
            "Orbits a binary star system (circumbinary planet).",
            "Is covered in hot desert sand.",
            "Has three suns in its sky."
        ],
        correct: 0,
        feedback: "Correct! Kepler-16b was the first confirmed circumbinary planet, orbiting two stars that also orbit each other."
    },
    {
        question: "A circumbinary planet is a planet that:",
        options: [
            "Orbits two stars at once.",
            "Orbits a star that orbits a black hole.",
            "Orbits a star in a globular cluster."
        ],
        correct: 0,
        feedback: "Correct! Circumbinary planets orbit around a close binary star pair rather than a single host star."
    },
    {
        question: "If the Savitzky-Golay filter window size is set too small (e.g. 5 points):",
        options: [
            "It will fit and erase the transit signal itself.",
            "It will do nothing to the light curve.",
            "It will only remove high frequencies."
        ],
        correct: 0,
        feedback: "Correct! A window size that is too small behaves like a high-pass filter that can fit and flatten the transit signal, destroying it."
    },
    {
        question: "How does sigma clipping handle statistical outliers in a dataset?",
        options: [
            "It removes data points that are a specified number of standard deviations from the mean/median.",
            "It rounds all values to the nearest integer.",
            "It multiplies outliers by ten."
        ],
        correct: 0,
        feedback: "Correct! Sigma clipping calculates the median and standard deviation, then filters out extreme deviations (e.g., >3 sigma) to remove cosmic rays or errors."
    },
    {
        question: "During its primary mission, Kepler pointed at:",
        options: [
            "One fixed patch of sky in the Cygnus and Lyra constellations.",
            "The entire sky every 27 days.",
            "Only the center of the Milky Way."
        ],
        correct: 0,
        feedback: "Correct! Kepler continuously pointed at a single star field in Cygnus-Lyra to monitor the same 150,000 stars for years without interruption."
    },
    {
        question: "What was the Kepler K2 mission?",
        options: [
            "A second mission using Kepler's remaining reaction wheels to observe fields along the ecliptic plane.",
            "A mission to find planets in the Andromeda galaxy.",
            "A software update to Kepler's computers."
        ],
        correct: 0,
        feedback: "Correct! After two of Kepler's reaction wheels failed, scientists used solar radiation pressure to balance the telescope, initiating the K2 mission to study multiple campaigns."
    },
    {
        question: "Planetary equilibrium temperature assumes:",
        options: [
            "The planet absorbs stellar energy and re-radiates it as a blackbody.",
            "The planet has a thick, warming atmosphere.",
            "The planet's interior is cold."
        ],
        correct: 0,
        feedback: "Correct! Equilibrium temperature is a theoretical temperature calculated assuming the planet is in thermal equilibrium with its host star, ignoring atmospheric greenhouse effects."
    },
    {
        question: "The TRAPPIST-1 system is famous for harboring:",
        options: [
            "Seven Earth-sized planets, three of which are in the habitable zone.",
            "A supermassive planet larger than the star.",
            "A planet with oceans of liquid diamond."
        ],
        correct: 0,
        feedback: "Correct! TRAPPIST-1 is an ultra-cool red dwarf star with seven rocky, Earth-sized planets, making it a prime target for habitability studies."
    },
    {
        question: "The goal of Extreme Precision Radial Velocity (EPRV) instrumentation is to achieve velocity precisions down to:",
        options: [
            "10 cm/s (enough to detect an Earth-twin).",
            "100 m/s.",
            "1 km/s."
        ],
        correct: 0,
        feedback: "Correct! Detecting Earth-twins around Sun-like stars requires measuring stellar reflex velocities of ~9 cm/s, pushing the limits of spectrograph stability."
    },
    {
        question: "The out-of-transit flux in a light curve represents:",
        options: [
            "The baseline brightness of the star when no planet is passing in front of it.",
            "The light blocked by the planet.",
            "The thermal radiation of the planet."
        ],
        correct: 0,
        feedback: "Correct! The out-of-transit flux serves as the baseline (F0), normalized to 1.0 to measure relative depth drops."
    },
    {
        question: "Photometric precision is a measure of:",
        options: [
            "The instrument's ability to measure tiny changes in light brightness.",
            "The telescope's focus accuracy.",
            "The exact coordinates of the star."
        ],
        correct: 0,
        feedback: "Correct! High photometric precision is essential for detecting the minute signals of small exoplanets (e.g., 100 ppm transit depths)."
    },
    {
        question: "In phase folding, the 'epoch' (t0) refers to:",
        options: [
            "The time of mid-transit.",
            "The date the telescope was launched.",
            "The period of the orbit."
        ],
        correct: 0,
        feedback: "Correct! The epoch is the reference time designating a specific mid-transit event, used to align the periodic folds."
    },
    {
        question: "A vetting false alarm occurs when:",
        options: [
            "An instrumental artifact or stellar activity is classified as a planet candidate.",
            "A real planet is missed by the pipeline.",
            "A star exploded as a supernova."
        ],
        correct: 0,
        feedback: "Correct! False alarms occur when non-planetary signals (noise, flares, starspots) pass vetting filters and are classified as candidates."
    },
    {
        question: "In the AstroPulse vetting pipeline, XGBoost is particularly useful for:",
        options: [
            "Minimizing regularized loss on tabular features to classify eclipsing binaries.",
            "Folding time-series data.",
            "Plotting the orbit of the planet."
        ],
        correct: 0,
        feedback: "Correct! XGBoost is a powerful gradient boosting framework for tabular datasets, excelling at separating class boundaries using engineered physical features."
    },
    {
        question: "A Random Forest classifier builds its consensus by:",
        options: [
            "Averaging the predictions of multiple randomized decision trees.",
            "Convolving 1D filters across the light curve.",
            "Using a single deep neural network layer."
        ],
        correct: 0,
        feedback: "Correct! Random Forests aggregate predictions from many independent decision trees, reducing overfitting and providing feature importance rankings."
    },
    {
        question: "What is a major advantage of LightGBM over standard gradient boosting?",
        options: [
            "Fast training speed and low memory usage due to leaf-wise tree growth.",
            "It runs directly on raw FITS images.",
            "It requires zero training data."
        ],
        correct: 0,
        feedback: "Correct! LightGBM grows trees leaf-wise rather than level-wise, making it exceptionally fast for large vetting searches."
    },
    {
        question: "The Signal-to-Noise Ratio (SNR) of a transit increases with:",
        options: [
            "The depth of the transit and the square root of the number of transits observed.",
            "The distance of the star from Earth.",
            "The temperature of the telescope sensor."
        ],
        correct: 0,
        feedback: "Correct! Observing more transits allows noise to average out, scaling SNR by the square root of the number of events (N)."
    },
    {
        question: "The Kepler-90 system is significant because:",
        options: [
            "It has eight confirmed planets, matching the number of planets in our solar system.",
            "It is the closest system to Earth.",
            "Its planets orbit in retrograde direction."
        ],
        correct: 0,
        feedback: "Correct! Kepler-90 was the first exoplanetary system found to contain eight planets, discovered using machine learning on Kepler data."
    },
    {
        question: "A retrograde orbit is an orbit where the planet:",
        options: [
            "Orbits in the opposite direction of the star's rotation.",
            "Orbits in the same direction as the star's rotation.",
            "Orbits perpendicular to the stellar equator."
        ],
        correct: 0,
        feedback: "Correct! Retrograde planets orbit opposite to their star's rotation, often indicating dynamic migration histories."
    },
    {
        question: "Planetary migration is the process where:",
        options: [
            "A planet's orbit changes over time due to interactions with gas, dust, or other planets.",
            "A planet moves from one star to another.",
            "Life migrates across the planetary surface."
        ],
        correct: 0,
        feedback: "Correct! Tidal and gravitational interactions in a protoplanetary disk can cause planets to migrate inward or outward from their birthplaces."
    },
    {
        question: "A protoplanetary disk is:",
        options: [
            "A rotating disk of gas and dust surrounding a young star, from which planets form.",
            "The flat shape of a galaxy.",
            "A ring of debris orbiting a black hole."
        ],
        correct: 0,
        feedback: "Correct! Protoplanetary disks are gas- and dust-rich disks around newly formed stars, providing the raw materials for planet formation."
    },
    {
        question: "The exoplanet WASP-76b is famous for having what extreme weather condition?",
        options: [
            "Liquid iron rain on its night side.",
            "Winds of diamond dust.",
            "Oceans of boiling sulfuric acid."
        ],
        correct: 0,
        feedback: "Correct! WASP-76b is an ultra-hot Jupiter where temperatures reach 2400°C, vaporizing iron on the day side, which then condenses and rains down as liquid iron on the cooler night side."
    },
    {
        question: "Kepler-186f is notable because it was the first:",
        options: [
            "Earth-sized planet discovered in the habitable zone of another star.",
            "Exoplanet with confirmed water vapor.",
            "Planet found around a triple star system."
        ],
        correct: 0,
        feedback: "Correct! Confirmed in 2014, Kepler-186f is approximately Earth-sized and orbits inside its red dwarf host star's habitable zone."
    },
    {
        question: "The CoRoT space telescope was launched by:",
        options: [
            "The French Space Agency (CNES) and ESA.",
            "NASA.",
            "ISRO."
        ],
        correct: 0,
        feedback: "Correct! Launched in 2006, CoRoT was a pioneering space telescope dedicated to exoplanet transit searches and asteroseismology."
    },
    {
        question: "The European Space Agency's CHEOPS mission is designed to:",
        options: [
            "Measure the sizes of known exoplanets with high precision.",
            "Search for new exoplanets in distant star clusters.",
            "Directly image Earth-twins."
        ],
        correct: 0,
        feedback: "Correct! CHEOPS (Characterising ExOPlanets Satellite) focuses on targeted observations of stars already known to host planets, measuring transit depths with high accuracy."
    },
    {
        question: "ESA's upcoming PLATO mission will focus on:",
        options: [
            "Detecting and characterising terrestrial exoplanets orbiting solar-type stars.",
            "Studying black hole accretion disks.",
            "Imaging the surface of Mars."
        ],
        correct: 0,
        feedback: "Correct! PLATO (PLAnetary Transits and Oscillations of stars) aims to find Earth-like planets around Sun-like stars and characterize their host stars."
    },
    {
        question: "ESA's upcoming ARIEL mission is dedicated to:",
        options: [
            "Performing a chemical survey of exoplanet atmospheres.",
            "Searching for moons around Jupiter.",
            "Mapping the cosmic microwave background."
        ],
        correct: 0,
        feedback: "Correct! ARIEL (Atmospheric Remote-sensing Infrared Exoplanet Large-survey) will study what exoplanets are made of, how they form, and how they evolve."
    },
    {
        question: "Gravitational microlensing is uniquely sensitive to:",
        options: [
            "Cold planets orbiting far from their host stars, and free-floating 'rogue' planets.",
            "Hot Jupiters orbiting close to red giants.",
            "Rocky planets orbiting white dwarfs."
        ],
        correct: 0,
        feedback: "Correct! Because it does not rely on stellar light, microlensing can detect planets at wide separations and even planets ejected from systems (rogues)."
    },
    {
        question: "What is a 'rogue planet'?",
        options: [
            "A planet that orbits the galactic center directly, having been ejected from its parent system.",
            "A planet that has a highly irregular orbit.",
            "A planet that orbits a star in a retrograde direction."
        ],
        correct: 0,
        feedback: "Correct! Rogue planets are interstellar objects of planetary mass that do not orbit any star, having been flung into interstellar space."
    },
    {
        question: "What is the approximate average albedo of Earth?",
        options: [
            "0.30.",
            "0.05.",
            "0.90."
        ],
        correct: 0,
        feedback: "Correct! Earth reflects about 30% of incoming sunlight, mostly due to clouds, ice cover, and reflective land surfaces."
    },
    {
        question: "The radius of Earth is approximately what fraction of Jupiter's radius?",
        options: [
            "1 / 11.",
            "1 / 2.",
            "1 / 100."
        ],
        correct: 0,
        feedback: "Correct! Jupiter is about 11 times the radius of Earth, meaning a Jupiter transit blocks about 121 times more light than an Earth transit."
    },
    {
        question: "Stellar luminosity is defined as:",
        options: [
            "The total amount of energy emitted by a star per unit time.",
            "The temperature of the star's surface.",
            "The apparent brightness of the star from Earth."
        ],
        correct: 0,
        feedback: "Correct! Luminosity (L) is the intrinsic power output of a star, whereas apparent brightness is how bright it appears depending on distance."
    }
];

let quizData = [];
let currentQuestionIdx = 0;
let quizScore = 0;
let selectedOptionIdx = -1;
let quizState = "question"; // "question", "answered"

const QUESTIONS_PER_QUIZ = 5;
const POINTS_PER_CORRECT = 10;
const POINT_SYMBOL = "✦";

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

function initQuiz() {
    // Shuffle the quizBank and select the first QUESTIONS_PER_QUIZ questions
    const shuffled = [...quizBank].sort(() => 0.5 - Math.random());
    quizData = shuffled.slice(0, QUESTIONS_PER_QUIZ);
    currentQuestionIdx = 0;
    quizScore = 0;
}

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
    qProgress.textContent = `Question ${currentQuestionIdx + 1} of ${QUESTIONS_PER_QUIZ} | Score: ${POINT_SYMBOL} ${quizScore}`;
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
            quizScore += POINTS_PER_CORRECT;
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
        
        // Update button text and show live points
        qProgress.textContent = `Question ${currentQuestionIdx + 1} of ${QUESTIONS_PER_QUIZ} | Score: ${POINT_SYMBOL} ${quizScore}`;
        
        if (currentQuestionIdx < QUESTIONS_PER_QUIZ - 1) {
            btnQuizNext.textContent = "Next Question";
        } else {
            btnQuizNext.textContent = "See Results";
        }
    } else {
        // Go to next question or complete
        if (currentQuestionIdx < QUESTIONS_PER_QUIZ - 1) {
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
    
    quizScoreSpan.innerHTML = `<span style="color: var(--accent-cyan); font-weight: bold;">${POINT_SYMBOL} ${quizScore}</span> / ${QUESTIONS_PER_QUIZ * POINTS_PER_CORRECT} Points`;
    
    let rank = "Novice Stargazer 🌙";
    if (quizScore === 50) {
        rank = `AstroPulse Master Astrophysicist 🚀 ${POINT_SYMBOL}`;
    } else if (quizScore === 40) {
        rank = "Solar System Vetting Specialist 🔭";
    } else if (quizScore === 30) {
        rank = "Stellar Observer 🌌";
    } else if (quizScore === 20) {
        rank = "Junior Space Observer ☄️";
    } else if (quizScore === 10) {
        rank = "Novice Stargazer 🌙";
    } else {
        rank = "Cosmic Cadet 🛰️";
    }
    
    quizRankSpan.textContent = `Rank: ${rank}`;
}

btnQuizRestart.addEventListener("click", () => {
    initQuiz();
    quizQuestionBox.classList.remove("hidden");
    quizResultBox.classList.add("hidden");
    loadQuestion();
});

// Initialize Quiz
if (quizQuestionBox) {
    initQuiz();
    loadQuestion();
}

    // --- SCROLL REVEAL TIMELINE NODES ---
    if (typeof IntersectionObserver !== "undefined") {
        const revealObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add("visible");
                    revealObserver.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.15,
            rootMargin: "0px 0px -50px 0px"
        });
        
        document.querySelectorAll(".reveal").forEach(el => {
            revealObserver.observe(el);
        });
    } else {
        // Fallback: instantly reveal pipeline nodes if observer API is blocked or unsupported
        document.querySelectorAll(".reveal").forEach(el => {
            el.classList.add("visible");
        });
    }
});

