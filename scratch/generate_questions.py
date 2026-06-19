import json
import random
import math

# Seed for reproducibility
random.seed(42)

questions = []

# --- 1. General Knowledge Questions (100) ---
# We will seed the list with high-quality general knowledge questions.
general_templates = [
    {
        "question": "How does an exoplanet transit affect the light curve of a star?",
        "options": [
            "It makes the star look brighter.",
            "It makes the star look dimmer periodically.",
            "It makes the star change color."
        ],
        "correct": 1,
        "feedback": "Correct! When a planet passes in front of its host star, it blocks a tiny fraction of the stellar surface, causing a periodic, temporary drop in measured brightness."
    },
    {
        "question": "What does a deep, 'V-shaped' dip in a light curve usually represent?",
        "options": [
            "A true exoplanet transit.",
            "An Eclipsing Binary star system.",
            "A cosmic ray hit on the sensor."
        ],
        "correct": 1,
        "feedback": "Correct! Eclipsing binary stars often graze or eclipse each other, creating deep, characteristic V-shaped light curves, unlike the flat-bottomed U-shapes of planets."
    },
    {
        "question": "What is the primary purpose of 'detrending' in light curve preprocessing?",
        "options": [
            "To remove slow variations like starspot rotation and isolate short transits.",
            "To artificially increase the size of detected planets.",
            "To add random noise to smooth out the data."
        ],
        "correct": 0,
        "feedback": "Correct! Detrending (using tools like Savitzky-Golay filters) flattens out slow, high-amplitude variations like starspots, making the faint, brief transit events easy to identify."
    },
    {
        "question": "According to Kepler's Third Law, if an exoplanet has a very short orbital period, its orbital distance from the star is:",
        "options": [
            "Very large.",
            "Very small.",
            "Completely unaffected by period."
        ],
        "correct": 1,
        "feedback": "Correct! Kepler's Third Law states that the square of the orbital period is proportional to the cube of the semi-major axis. Thus, short periods mean very close orbits."
    },
    {
        "question": "The depth of a transit signal is proportional to what physical ratio?",
        "options": [
            "Planet mass to star mass.",
            "Planet radius to star radius squared.",
            "Planet distance to star distance."
        ],
        "correct": 1,
        "feedback": "Correct! Transit depth is approximately (Rp/Rs)^2, representing the ratio of the projected area of the planet to that of the star."
    },
    {
        "question": "Why are transit dips often curved/rounded at the bottom instead of flat?",
        "options": [
            "Because the planet is a gas giant.",
            "Due to stellar limb darkening.",
            "Because the star is rotating extremely fast."
        ],
        "correct": 1,
        "feedback": "Correct! The edges of a stellar disk are cooler and appear dimmer than the center (limb darkening), causing a gradual curve as the planet crosses."
    },
    {
        "question": "What is a secondary eclipse in an exoplanet system's light curve?",
        "options": [
            "When the planet passes behind the host star.",
            "When a second planet transits at the same time.",
            "When the star passes behind the planet."
        ],
        "correct": 0,
        "feedback": "Correct! The secondary eclipse occurs when the planet passes behind the star, causing a tiny drop in light as the planet's reflected thermal emission is blocked."
    },
    {
        "question": "The Radial Velocity method detects exoplanets by measuring what physical effect?",
        "options": [
            "The dip in stellar brightness.",
            "The gravitational wobble of the host star via Doppler shifts.",
            "The thermal radiation of the planet."
        ],
        "correct": 1,
        "feedback": "Correct! A planet's gravity pulls on its star, causing the star to orbit around their common center of mass, which produces Doppler shifts in the star's spectrum."
    },
    {
        "question": "When a star moves toward Earth due to a planet's gravity, its spectral lines are:",
        "options": [
            "Redshifted (shifted to longer wavelengths).",
            "Blueshifted (shifted to shorter wavelengths).",
            "Completely extinguished."
        ],
        "correct": 1,
        "feedback": "Correct! Light waves from an approaching source are compressed, shifting them to shorter (bluer) wavelengths."
    },
    {
        "question": "The boundaries of the Habitable Zone (Goldilocks Zone) around a star depend primarily on:",
        "options": [
            "The star's luminosity and temperature.",
            "The planet's magnetic field strength.",
            "The number of moons the planet has."
        ],
        "correct": 0,
        "feedback": "Correct! A star's luminosity determines the amount of energy reaching the planet, defining the distance range where liquid water can exist."
    },
    {
        "question": "What is a 'Hot Jupiter'?",
        "options": [
            "A gas giant orbiting extremely close to its parent star.",
            "A star that looks like Jupiter.",
            "A planet made of molten iron."
        ],
        "correct": 0,
        "feedback": "Correct! Hot Jupiters are gas giants with sizes and masses similar to or greater than Jupiter, but with very short orbital periods (usually under 10 days)."
    },
    {
        "question": "Why is the Savitzky-Golay filter popular for transit detrending?",
        "options": [
            "It fits local low-degree polynomials to preserve sharp transit features.",
            "It converts time-series data into images.",
            "It automatically identifies the orbital period."
        ],
        "correct": 0,
        "feedback": "Correct! The Savitzky-Golay filter fits local polynomials, which removes low-frequency stellar noise while preserving high-frequency edges like the ingress and egress of a transit."
    },
    {
        "question": "The Box Least Squares (BLS) algorithm is optimized for finding:",
        "options": [
            "Sinusoidal radial velocity curves.",
            "Box-like periodic dips in light curves.",
            "Spontaneous stellar flares."
        ],
        "correct": 1,
        "feedback": "Correct! BLS models transits as periodic box-like dips, making it highly effective at scanning light curves for exoplanet transit signatures."
    },
    {
        "question": "The TESS space telescope primary mission observes sectors for how long?",
        "options": [
            "27 days.",
            "365 days.",
            "7 days."
        ],
        "correct": 0,
        "feedback": "Correct! TESS monitors each sky sector for approximately 27.4 days before moving to the next sector."
    },
    {
        "question": "Which instrument capability of the James Webb Space Telescope (JWST) is crucial for analyzing exoplanet atmospheres?",
        "options": [
            "Transit transmission spectroscopy in the infrared.",
            "Radar imaging of surface rocks.",
            "X-ray coronal measurements."
        ],
        "correct": 0,
        "feedback": "Correct! Transmission spectroscopy during transit allows JWST to measure stellar light filtered through a planet's atmosphere to detect molecules like water, CO2, and methane."
    },
    {
        "question": "In the planet name 'Kepler-186f', what does the letter 'f' indicate?",
        "options": [
            "It is the fifth planet discovered in that system.",
            "It is the sixth star in the cluster.",
            "It stands for 'Foreign'."
        ],
        "correct": 0,
        "feedback": "Correct! Exoplanet naming conventions start with 'b' for the first planet discovered in a system, followed by 'c', 'd', 'e', 'f', etc."
    },
    {
        "question": "Why do we compare the depths of odd and even transits in vetting pipelines?",
        "options": [
            "To filter out eclipsing binaries with alternating primary/secondary eclipses.",
            "To measure the eccentricity of the planet's orbit.",
            "To determine the rotation rate of the star."
        ],
        "correct": 0,
        "feedback": "Correct! In eclipsing binaries, the primary and secondary stars have different sizes, producing alternating deep and shallow eclipses. Exoplanets produce identical transit depths."
    },
    {
        "question": "What is a 'Super-Earth'?",
        "options": [
            "A planet with a mass larger than Earth but smaller than Neptune.",
            "A planet identical to Earth in every way.",
            "A giant planet orbiting a black hole."
        ],
        "correct": 0,
        "feedback": "Correct! Super-Earths are planets with masses roughly between 1 and 10 times Earth's mass, which can be either rocky or gaseous."
    },
    {
        "question": "Which of the following is considered a potential atmospheric biosignature?",
        "options": [
            "Simultaneous presence of oxygen and methane out of chemical equilibrium.",
            "High abundance of helium.",
            "Presence of carbon dioxide on a frozen world."
        ],
        "correct": 0,
        "feedback": "Correct! Oxygen and methane react quickly; finding them together implies active biological processes are continuously replenishing them."
    },
    {
        "question": "The distance at which a celestial body, held together only by its own gravity, will disintegrate due to a second body's tidal forces is called the:",
        "options": [
            "Roche Limit.",
            "Kepler Radius.",
            "Lagrange Threshold."
        ],
        "correct": 0,
        "feedback": "Correct! Inside the Roche Limit, tidal forces overcome the gravity holding the smaller body together, ripping it apart."
    },
    {
        "question": "What is a gravitational slingshot (gravity assist)?",
        "options": [
            "Using a planet's gravity to alter the path and speed of a spacecraft.",
            "Using gravity to detect distant black holes.",
            "A method to change a planet's orbit."
        ],
        "correct": 0,
        "feedback": "Correct! Spacecraft fly close to planets to gain momentum and speed without consuming propellant."
    },
    {
        "question": "What is a planet's 'albedo'?",
        "options": [
            "The fraction of incident light reflected by the planet's surface/atmosphere.",
            "The speed of the planet's rotation.",
            "The thickness of the planet's core."
        ],
        "correct": 0,
        "feedback": "Correct! Albedo ranges from 0 (perfect absorber) to 1 (perfect reflector) and is critical for calculating equilibrium temperatures."
    },
    {
        "question": "The Kepler Space Telescope primarily searched for exoplanets using which method?",
        "options": [
            "Transit method.",
            "Radial Velocity method.",
            "Gravitational Microlensing."
        ],
        "correct": 0,
        "feedback": "Correct! Kepler revolutionized exoplanet science by continuously monitoring over 150,000 stars to detect transit dips."
    },
    {
        "question": "Gravitational microlensing detects planets by measuring:",
        "options": [
            "The bending of light from a background star by a foreground star and its planet.",
            "The physical wobble of the star.",
            "The direct thermal emission of the planet."
        ],
        "correct": 0,
        "feedback": "Correct! When a star and its planet pass exactly in front of a background star, their gravity acts as a lens, temporarily magnifying the background star's light."
    },
    {
        "question": "Astrometry detects planets by measuring:",
        "options": [
            "The precise physical positions and motions of a star on the sky.",
            "The brightness fluctuations of the star.",
            "The redshift of spectral lines."
        ],
        "correct": 0,
        "feedback": "Correct! Astrometry tracks the tiny 2D position shifts of a star on the sky as it wobbles due to the gravity of an orbiting planet."
    },
    {
        "question": "Why is direct imaging of exoplanets extremely difficult?",
        "options": [
            "Because planets are much dimmer than their host stars and very close to them.",
            "Because planets do not emit or reflect any light.",
            "Because stars are always moving too fast."
        ],
        "correct": 0,
        "feedback": "Correct! Stars are typically millions to billions of times brighter than their planets, requiring advanced tools like coronagraphs to block the stellar glare."
    },
    {
        "question": "What does a coronagraph do in an astronomical telescope?",
        "options": [
            "It blocks the direct light from a star to reveal faint nearby objects like planets.",
            "It measures the magnetic field of the corona.",
            "It focuses cosmic rays onto a sensor."
        ],
        "correct": 0,
        "feedback": "Correct! A coronagraph acts as an artificial mask to block stellar glare, allowing direct imaging of exoplanetary systems."
    },
    {
        "question": "Proxima Centauri b is famous because it is:",
        "options": [
            "The closest known exoplanet to Earth, orbiting in the habitable zone.",
            "The largest gas giant ever found.",
            "The first exoplanet discovered in another galaxy."
        ],
        "correct": 0,
        "feedback": "Correct! Proxima Centauri b orbits our nearest stellar neighbor, Proxima Centauri, at a distance of 4.2 light-years, inside its habitable zone."
    },
    {
        "question": "What are the primary elements that make up gas giants like Jupiter and Saturn?",
        "options": [
            "Hydrogen and Helium.",
            "Silicon and Iron.",
            "Water and Carbon Dioxide."
        ],
        "correct": 0,
        "feedback": "Correct! Gas giants are composed mostly of hydrogen and helium, similar to the composition of the solar nebula."
    },
    {
        "question": "What happens when an exoplanet is 'tidally locked' to its host star?",
        "options": [
            "One side of the planet permanently faces the star (permanent day).",
            "The planet stops orbiting the star.",
            "The planet's ocean tides freeze solid."
        ],
        "correct": 0,
        "feedback": "Correct! Tidal locking occurs when the planet's rotation period matches its orbital period, resulting in a permanent day side and a permanent night side."
    },
    {
        "question": "Which type of star is the coolest and most common in the Milky Way?",
        "options": [
            "M-Dwarf (Red Dwarf).",
            "G-Dwarf (Yellow Sun-like).",
            "O-Type Star (Blue Giant)."
        ],
        "correct": 0,
        "feedback": "Correct! M-dwarfs are small, cool stars that make up about 70-75% of all stars in the Milky Way."
    },
    {
        "question": "The Earth Similarity Index (ESI) is a measure of:",
        "options": [
            "A planet's physical similarity to Earth (radius, density, temperature).",
            "Whether Earth-like life exists on the planet.",
            "The distance of the planet from Earth."
        ],
        "correct": 0,
        "feedback": "Correct! ESI scales from 0 to 1, comparing a planet's radius, density, escape velocity, and temperature to Earth's parameters."
    },
    {
        "question": "If a planet orbits in a highly eccentric (oval) orbit, its transit duration:",
        "options": [
            "Depends on where the transit occurs along the orbit.",
            "Is always identical to a circular orbit.",
            "Is always zero."
        ],
        "correct": 0,
        "feedback": "Correct! Velocity varies along an eccentric orbit (Kepler's Second Law), so transit duration depends on whether the transit occurs at periastron (fast) or apastron (slow)."
    },
    {
        "question": "Why is Kepler-452b often referred to as 'Earth's Cousin'?",
        "options": [
            "It is a rocky planet orbiting a G-type star with a 385-day orbit.",
            "It has a large active population of scientists.",
            "It was the first planet photographed directly."
        ],
        "correct": 0,
        "feedback": "Correct! Kepler-452b is about 1.6 times Earth's radius and orbits a G-type star very similar to the Sun, with an orbital period of 385 days."
    },
    {
        "question": "What is planetary transit 'ingress'?",
        "options": [
            "The phase where the planet enters the stellar disk.",
            "The phase where the planet leaves the stellar disk.",
            "The midpoint of the transit."
        ],
        "correct": 0,
        "feedback": "Correct! Ingress is the period during which the planet's disk first begins to overlap and fully cross onto the star's disk."
    },
    {
        "question": "What is planetary transit 'egress'?",
        "options": [
            "The phase where the planet leaves the stellar disk.",
            "The phase where the planet enters the stellar disk.",
            "The deepest point of the transit."
        ],
        "correct": 0,
        "feedback": "Correct! Egress is the phase where the planet's disk moves off the stellar disk, returning the light curve back to its out-of-transit level."
    },
    {
        "question": "TESS (Transiting Exoplanet Survey Satellite) focuses primarily on:",
        "options": [
            "Bright, nearby stars to enable follow-up characterization.",
            "Extremely distant galaxies.",
            "Only stars inside the Orion Nebula."
        ],
        "correct": 0,
        "feedback": "Correct! TESS was designed to map the brightest stars in the sky to enable ground-based telescopes and JWST to perform radial velocity and atmospheric measurements."
    },
    {
        "question": "What is 'red noise' (correlated noise) in light curves?",
        "options": [
            "Noise with low-frequency correlations, often caused by stellar activity.",
            "Noise that is only visible when using red filters.",
            "Sensor noise caused by cosmic ray hits."
        ],
        "correct": 0,
        "feedback": "Correct! Red noise refers to time-correlated noise (like starspots or instrument drift) which can easily mimic or obscure transit signals."
    },
    {
        "question": "What is 'white noise' in light curves?",
        "options": [
            "Random, uncorrelated noise from photon counting statistics.",
            "Noise from white dwarf stars.",
            "Interference from visible light leaks."
        ],
        "correct": 0,
        "feedback": "Correct! White noise is independent and identically distributed noise, representing photon shot noise from the telescope sensor."
    },
    {
        "question": "What does phase folding a light curve achieve?",
        "options": [
            "It overlays multiple periodic transits to increase the signal-to-noise ratio.",
            "It physically flattens the light curve.",
            "It removes all out-of-transit data points."
        ],
        "correct": 0,
        "feedback": "Correct! Phase folding maps time-series data to a phase interval [-0.5, 0.5] using the orbital period, wrapping all individual transit events on top of each other."
    },
    {
        "question": "In AstroPulse, what does the 'Consensus Score' represent?",
        "options": [
            "An ensemble average probability combined with signal SNR and fit stability.",
            "The agreement between astronomers on the naming of a planet.",
            "The temperature of the exoplanet's core."
        ],
        "correct": 0,
        "feedback": "Correct! The consensus score aggregates predictions from machine learning models (CNN, RF, XGBoost, etc.) and physical metrics to vet candidate signals."
    },
    {
        "question": "Why do we use 1D Convolutional Neural Networks (CNNs) in exoplanet vetting?",
        "options": [
            "To automatically extract local shape features from phase-folded profiles.",
            "To model long-term stellar cycles spanning years.",
            "To calculate the planetary radius directly."
        ],
        "correct": 0,
        "feedback": "Correct! 1D CNNs are highly effective at detecting local spatial features, allowing them to distinguish U-shaped transits from V-shaped eclipses."
    },
    {
        "question": "What role does an LSTM layer play in a hybrid CNN-LSTM model?",
        "options": [
            "It captures sequential correlations and transition phases like ingress/egress.",
            "It speeds up training times on the CPU.",
            "It predicts the mass of the exoplanet."
        ],
        "correct": 0,
        "feedback": "Correct! LSTMs are Recurrent Neural Networks designed to capture sequence and temporal dependency, enhancing detection for weak transit boundaries."
    },
    {
        "question": "Kepler's First Law states that planetary orbits are:",
        "options": [
            "Ellipses, with the star at one focus.",
            "Perfect circles, with the star at the center.",
            "Parabolas, with the star at the vertex."
        ],
        "correct": 0,
        "feedback": "Correct! Kepler's First Law established that all orbits are elliptical, breaking the classical assumption of perfect circular motion."
    },
    {
        "question": "Kepler's Second Law (equal areas in equal times) implies that a planet moves:",
        "options": [
            "Faster when close to the star, slower when far away.",
            "At a constant speed at all times.",
            "Slower when close to the star, faster when far away."
        ],
        "correct": 0,
        "feedback": "Correct! As a planet approaches periastron (closest point), the gravitational pull increases, causing it to accelerate and sweep out equal areas in equal times."
    },
    {
        "question": "The semi-major axis is a measure of:",
        "options": [
            "The average distance of a planet from its host star.",
            "The radius of the planet's equator.",
            "The rotation speed of the host star."
        ],
        "correct": 0,
        "feedback": "Correct! The semi-major axis is half of the longest diameter of an elliptical orbit, representing the planet's mean distance from its star."
    },
    {
        "question": "An orbital eccentricity (e) of exactly 0 represents:",
        "options": [
            "A perfect circle.",
            "A straight line.",
            "A parabola."
        ],
        "correct": 0,
        "feedback": "Correct! Eccentricity measures the elongation of an orbit. A circle has e=0, ellipses have 0 < e < 1, and parabolas have e=1."
    },
    {
        "question": "The equilibrium temperature of a planet in the habitable zone must allow:",
        "options": [
            "Liquid water to exist on the surface.",
            "Iron to melt into liquid.",
            "Liquid nitrogen to form oceans."
        ],
        "correct": 0,
        "feedback": "Correct! The habitable zone is defined as the range where planetary surface temperatures permit liquid water, a key requirement for life as we know it."
    },
    {
        "question": "Why can a planet's actual temperature be much higher than its calculated equilibrium temperature?",
        "options": [
            "Due to atmospheric greenhouse gas trapping.",
            "Because of tidal heating from its core.",
            "Because the planet is closer than calculated."
        ],
        "correct": 0,
        "feedback": "Correct! Greenhouse gases like carbon dioxide and water vapor trap infrared radiation, raising the surface temperature (as seen on Venus)."
    },
    {
        "question": "Transmission spectroscopy measures exoplanet atmospheres by:",
        "options": [
            "Analyzing starlight filtering through the atmosphere during transit.",
            "Directly photographing the clouds of the planet.",
            "Measuring radio waves emitted by the planet."
        ],
        "correct": 0,
        "feedback": "Correct! As a planet transits, starlight passes through the ring of its atmosphere, leaving absorption lines that reveal atmospheric chemical composition."
    },
    {
        "question": "Emission spectroscopy of exoplanets is typically performed during:",
        "options": [
            "Secondary eclipse (just before or after the planet goes behind the star).",
            "Primary transit.",
            "The planet's winter solstice."
        ],
        "correct": 0,
        "feedback": "Correct! By measuring the spectrum of the system before and during secondary eclipse, scientists can isolate the thermal radiation emitted by the planet's day side."
    },
    {
        "question": "What was the first exoplanet discovered around a Sun-like star?",
        "options": [
            "51 Pegasi b.",
            "Kepler-10b.",
            "HD 189733b."
        ],
        "correct": 0,
        "feedback": "Correct! Discovered in 1995 by Michel Mayor and Didier Queloz (for which they won the Nobel Prize), 51 Pegasi b is a Hot Jupiter orbiting a Sun-like star."
    },
    {
        "question": "The very first exoplanets ever confirmed were found orbiting what type of object?",
        "options": [
            "A pulsar (neutron star).",
            "A red giant.",
            "A white dwarf."
        ],
        "correct": 0,
        "feedback": "Correct! In 1992, Aleksander Wolszczan and Dale Frail discovered three planets orbiting the pulsar PSR B1257+12 by measuring anomalies in pulse timing."
    },
    {
        "question": "Radial velocity measurements are most sensitive to:",
        "options": [
            "Massive planets orbiting close to their stars.",
            "Tiny planets orbiting far from their stars.",
            "Rocky planets orbiting red giants."
        ],
        "correct": 0,
        "feedback": "Correct! Massive planets close to their host stars exert the strongest gravitational pull, causing the largest stellar wobbles."
    },
    {
        "question": "The center of mass of two or more orbiting bodies is called the:",
        "options": [
            "Barycenter.",
            "Apex.",
            "Focus."
        ],
        "correct": 0,
        "feedback": "Correct! Stars and planets orbit around their shared barycenter. For the solar system, the barycenter lies near the surface of the Sun."
    },
    {
        "question": "In AstroPulse, what Python library is used for astronomical coordinates and units?",
        "options": [
            "Astropy.",
            "SciPy.",
            "SymPy."
        ],
        "correct": 0,
        "feedback": "Correct! Astropy is the standard library for astronomy and astrophysics in Python, offering tools for units, coordinates, and FITS files."
    },
    {
        "question": "What is a light-year?",
        "options": [
            "The distance light travels in one Earth year.",
            "The time it takes light to reach the Sun.",
            "The speed of light in a vacuum."
        ],
        "correct": 0,
        "feedback": "Correct! A light-year is a unit of distance, equal to about 9.46 trillion kilometers (5.88 trillion miles)."
    },
    {
        "question": "An Astronomical Unit (AU) is defined as:",
        "options": [
            "The average distance between the Earth and the Sun.",
            "The distance from the Sun to Pluto.",
            "The radius of the Sun."
        ],
        "correct": 0,
        "feedback": "Correct! One AU is approximately 149.6 million kilometers (93 million miles), the mean distance from Earth to the Sun."
    },
    {
        "question": "How does stellar spot modulation affect a light curve?",
        "options": [
            "It creates slow, quasi-periodic waves as the star rotates.",
            "It creates sharp, sudden spikes in brightness.",
            "It removes the transit signature entirely."
        ],
        "correct": 0,
        "feedback": "Correct! As a star rotates, starspots rotate in and out of view, causing gradual, cyclic fluctuations in stellar brightness."
    },
    {
        "question": "What is a stellar flare?",
        "options": [
            "A sudden, high-energy eruption on the star causing a brief spike in brightness.",
            "A slow cooling of the star's surface.",
            "The death of the host star."
        ],
        "correct": 0,
        "feedback": "Correct! Flares are sudden releases of magnetic energy that cause a sharp increase in brightness, which vetting algorithms must filter out as anomalies."
    },
    {
        "question": "Kepler-22b is notable because it was the first Kepler planet confirmed to:",
        "options": [
            "Orbit within the habitable zone of a Sun-like star.",
            "Be composed entirely of water.",
            "Possess an oxygen-rich atmosphere."
        ],
        "correct": 0,
        "feedback": "Correct! Confirmed in 2011, Kepler-22b orbits a G-type star in the habitable zone, with a radius about 2.4 times that of Earth."
    },
    {
        "question": "Approximately how many Earth masses are equal to one Jupiter mass?",
        "options": [
            "318.",
            "10.",
            "1000."
        ],
        "correct": 0,
        "feedback": "Correct! Jupiter is the largest planet in our solar system, with a mass equal to approximately 318 Earth masses."
    },
    {
        "question": "To calculate a planet's density, what two parameters must be known?",
        "options": [
            "Mass and Radius.",
            "Period and Distance.",
            "Temperature and Albedo."
        ],
        "correct": 0,
        "feedback": "Correct! Density is Mass divided by Volume, where volume is calculated from the planet's radius."
    },
    {
        "question": "Which type of planet generally has a higher average density?",
        "options": [
            "Rocky (Terrestrial) planets.",
            "Gas Giant planets.",
            "Ice Giant planets."
        ],
        "correct": 0,
        "feedback": "Correct! Rocky planets are composed of metals and silicate rocks (density ~3-5 g/cm³), while gas giants are mostly hydrogen and helium (density ~0.7-1.3 g/cm³)."
    },
    {
        "question": "What does an impact parameter (b) of 0 mean for a transit?",
        "options": [
            "The planet transits directly across the center of the stellar disk.",
            "The planet grazes the edge of the star.",
            "No transit occurs."
        ],
        "correct": 0,
        "feedback": "Correct! An impact parameter of 0 represents a central transit, maximizing the transit duration."
    },
    {
        "question": "A transit with an impact parameter b ≈ 1.0 is called a:",
        "options": [
            "Grazing transit.",
            "Central transit.",
            "Non-transit."
        ],
        "correct": 0,
        "feedback": "Correct! A grazing transit occurs when the planet only partially overlaps the edge of the star, resulting in a V-shaped curve."
    },
    {
        "question": "Kepler-10b is famous as the first Kepler exoplanet confirmed to be:",
        "options": [
            "Rocky (a rocky Super-Earth).",
            "A gas giant.",
            "A water world."
        ],
        "correct": 0,
        "feedback": "Correct! Kepler-10b was the first rocky exoplanet discovered by Kepler, with a density showing it is composed of rock and iron."
    },
    {
        "question": "The transit depth of Earth transiting the Sun, as seen from a distant star, is about:",
        "options": [
            "100 parts per million (0.01%).",
            "1 percent.",
            "10 percent."
        ],
        "correct": 0,
        "feedback": "Correct! Earth's small radius relative to the Sun results in a tiny transit depth of ~100 ppm, requiring high-precision space photometry to detect."
    },
    {
        "question": "Kepler-16b is famous because it is a 'Tatooine-like' planet, meaning it:",
        "options": [
            "Orbits a binary star system (circumbinary planet).",
            "Is covered in hot desert sand.",
            "Has three suns in its sky."
        ],
        "correct": 0,
        "feedback": "Correct! Kepler-16b was the first confirmed circumbinary planet, orbiting two stars that also orbit each other."
    },
    {
        "question": "A circumbinary planet is a planet that:",
        "options": [
            "Orbits two stars at once.",
            "Orbits a star that orbits a black hole.",
            "Orbits a star in a globular cluster."
        ],
        "correct": 0,
        "feedback": "Correct! Circumbinary planets orbit around a close binary star pair rather than a single host star."
    },
    {
        "question": "If the Savitzky-Golay filter window size is set too small (e.g. 5 points):",
        "options": [
            "It will fit and erase the transit signal itself.",
            "It will do nothing to the light curve.",
            "It will only remove high frequencies."
        ],
        "correct": 0,
        "feedback": "Correct! A window size that is too small behaves like a high-pass filter that can fit and flatten the transit signal, destroying it."
    },
    {
        "question": "How does sigma clipping handle statistical outliers in a dataset?",
        "options": [
            "It removes data points that are a specified number of standard deviations from the mean/median.",
            "It rounds all values to the nearest integer.",
            "It multiplies outliers by ten."
        ],
        "correct": 0,
        "feedback": "Correct! Sigma clipping calculates the median and standard deviation, then filters out extreme deviations (e.g., >3 sigma) to remove cosmic rays or errors."
    },
    {
        "question": "During its primary mission, Kepler pointed at:",
        "options": [
            "One fixed patch of sky in the Cygnus and Lyra constellations.",
            "The entire sky every 27 days.",
            "Only the center of the Milky Way."
        ],
        "correct": 0,
        "feedback": "Correct! Kepler continuously pointed at a single star field in Cygnus-Lyra to monitor the same 150,000 stars for years without interruption."
    },
    {
        "question": "What was the Kepler K2 mission?",
        "options": [
            "A second mission using Kepler's remaining reaction wheels to observe fields along the ecliptic plane.",
            "A mission to find planets in the Andromeda galaxy.",
            "A software update to Kepler's computers."
        ],
        "correct": 0,
        "feedback": "Correct! After two of Kepler's reaction wheels failed, scientists used solar radiation pressure to balance the telescope, initiating the K2 mission to study multiple campaigns."
    },
    {
        "question": "Planetary equilibrium temperature assumes:",
        "options": [
            "The planet absorbs stellar energy and re-radiates it as a blackbody.",
            "The planet has a thick, warming atmosphere.",
            "The planet's interior is cold."
        ],
        "correct": 0,
        "feedback": "Correct! Equilibrium temperature is a theoretical temperature calculated assuming the planet is in thermal equilibrium with its host star, ignoring atmospheric greenhouse effects."
    },
    {
        "question": "The TRAPPIST-1 system is famous for harboring:",
        "options": [
            "Seven Earth-sized planets, three of which are in the habitable zone.",
            "A supermassive planet larger than the star.",
            "A planet with oceans of liquid diamond."
        ],
        "correct": 0,
        "feedback": "Correct! TRAPPIST-1 is an ultra-cool red dwarf star with seven rocky, Earth-sized planets, making it a prime target for habitability studies."
    },
    {
        "question": "The goal of Extreme Precision Radial Velocity (EPRV) instrumentation is to achieve velocity precisions down to:",
        "options": [
            "10 cm/s (enough to detect an Earth-twin).",
            "100 m/s.",
            "1 km/s."
        ],
        "correct": 0,
        "feedback": "Correct! Detecting Earth-twins around Sun-like stars requires measuring stellar reflex velocities of ~9 cm/s, pushing the limits of spectrograph stability."
    },
    {
        "question": "The out-of-transit flux in a light curve represents:",
        "options": [
            "The baseline brightness of the star when no planet is passing in front of it.",
            "The light blocked by the planet.",
            "The thermal radiation of the planet."
        ],
        "correct": 0,
        "feedback": "Correct! The out-of-transit flux serves as the baseline (F0), normalized to 1.0 to measure relative depth drops."
    },
    {
        "question": "Photometric precision is a measure of:",
        "options": [
            "The instrument's ability to measure tiny changes in light brightness.",
            "The telescope's focus accuracy.",
            "The exact coordinates of the star."
        ],
        "correct": 0,
        "feedback": "Correct! High photometric precision is essential for detecting the minute signals of small exoplanets (e.g., 100 ppm transit depths)."
    },
    {
        "question": "In phase folding, the 'epoch' (t0) refers to:",
        "options": [
            "The time of mid-transit.",
            "The date the telescope was launched.",
            "The period of the orbit."
        ],
        "correct": 0,
        "feedback": "Correct! The epoch is the reference time designating a specific mid-transit event, used to align the periodic folds."
    },
    {
        "question": "A vetting false alarm occurs when:",
        "options": [
            "An instrumental artifact or stellar activity is classified as a planet candidate.",
            "A real planet is missed by the pipeline.",
            "A star exploded as a supernova."
        ],
        "correct": 0,
        "feedback": "Correct! False alarms occur when non-planetary signals (noise, flares, starspots) pass vetting filters and are classified as candidates."
    },
    {
        "question": "In the AstroPulse vetting pipeline, XGBoost is particularly useful for:",
        "options": [
            "Minimizing regularized loss on tabular features to classify eclipsing binaries.",
            "Folding time-series data.",
            "Plotting the orbit of the planet."
        ],
        "correct": 0,
        "feedback": "Correct! XGBoost is a powerful gradient boosting framework for tabular datasets, excelling at separating class boundaries using engineered physical features."
    },
    {
        "question": "A Random Forest classifier builds its consensus by:",
        "options": [
            "Averaging the predictions of multiple randomized decision trees.",
            "Convolving 1D filters across the light curve.",
            "Using a single deep neural network layer."
        ],
        "correct": 0,
        "feedback": "Correct! Random Forests aggregate predictions from many independent decision trees, reducing overfitting and providing feature importance rankings."
    },
    {
        "question": "What is a major advantage of LightGBM over standard gradient boosting?",
        "options": [
            "Fast training speed and low memory usage due to leaf-wise tree growth.",
            "It runs directly on raw FITS images.",
            "It requires zero training data."
        ],
        "correct": 0,
        "feedback": "Correct! LightGBM grows trees leaf-wise rather than level-wise, making it exceptionally fast for large vetting searches."
    },
    {
        "question": "The Signal-to-Noise Ratio (SNR) of a transit increases with:",
        "options": [
            "The depth of the transit and the square root of the number of transits observed.",
            "The distance of the star from Earth.",
            "The temperature of the telescope sensor."
        ],
        "correct": 0,
        "feedback": "Correct! Observing more transits allows noise to average out, scaling SNR by the square root of the number of events (N)."
    },
    {
        "question": "The Kepler-90 system is significant because:",
        "options": [
            "It has eight confirmed planets, matching the number of planets in our solar system.",
            "It is the closest system to Earth.",
            "Its planets orbit in retrograde direction."
        ],
        "correct": 0,
        "feedback": "Correct! Kepler-90 was the first exoplanetary system found to contain eight planets, discovered using machine learning on Kepler data."
    },
    {
        "question": "A retrograde orbit is an orbit where the planet:",
        "options": [
            "Orbits in the opposite direction of the star's rotation.",
            "Orbits in the same direction as the star's rotation.",
            "Orbits perpendicular to the stellar equator."
        ],
        "correct": 0,
        "feedback": "Correct! Retrograde planets orbit opposite to their star's rotation, often indicating dynamic migration histories."
    },
    {
        "question": "Planetary migration is the process where:",
        "options": [
            "A planet's orbit changes over time due to interactions with gas, dust, or other planets.",
            "A planet moves from one star to another.",
            "Life migrates across the planetary surface."
        ],
        "correct": 0,
        "feedback": "Correct! Tidal and gravitational interactions in a protoplanetary disk can cause planets to migrate inward or outward from their birthplaces."
    },
    {
        "question": "A protoplanetary disk is:",
        "options": [
            "A rotating disk of gas and dust surrounding a young star, from which planets form.",
            "The flat shape of a galaxy.",
            "A ring of debris orbiting a black hole."
        ],
        "correct": 0,
        "feedback": "Correct! Protoplanetary disks are gas- and dust-rich disks around newly formed stars, providing the raw materials for planet formation."
    },
    {
        "question": "The exoplanet WASP-76b is famous for having what extreme weather condition?",
        "options": [
            "Liquid iron rain on its night side.",
            "Winds of diamond dust.",
            "Oceans of boiling sulfuric acid."
        ],
        "correct": 0,
        "feedback": "Correct! WASP-76b is an ultra-hot Jupiter where temperatures reach 2400°C, vaporizing iron on the day side, which then condenses and rains down as liquid iron on the cooler night side."
    },
    {
        "question": "Kepler-186f is notable because it was the first:",
        "options": [
            "Earth-sized planet discovered in the habitable zone of another star.",
            "Exoplanet with confirmed water vapor.",
            "Planet found around a triple star system."
        ],
        "correct": 0,
        "feedback": "Correct! Confirmed in 2014, Kepler-186f is approximately Earth-sized and orbits inside its red dwarf host star's habitable zone."
    },
    {
        "question": "The CoRoT space telescope was launched by:",
        "options": [
            "The French Space Agency (CNES) and ESA.",
            "NASA.",
            "ISRO."
        ],
        "correct": 0,
        "feedback": "Correct! Launched in 2006, CoRoT was a pioneering space telescope dedicated to exoplanet transit searches and asteroseismology."
    },
    {
        "question": "The European Space Agency's CHEOPS mission is designed to:",
        "options": [
            "Measure the sizes of known exoplanets with high precision.",
            "Search for new exoplanets in distant star clusters.",
            "Directly image Earth-twins."
        ],
        "correct": 0,
        "feedback": "Correct! CHEOPS (Characterising ExOPlanets Satellite) focuses on targeted observations of stars already known to host planets, measuring transit depths with high accuracy."
    },
    {
        "question": "ESA's upcoming PLATO mission will focus on:",
        "options": [
            "Detecting and characterising terrestrial exoplanets orbiting solar-type stars.",
            "Studying black hole accretion disks.",
            "Imaging the surface of Mars."
        ],
        "correct": 0,
        "feedback": "Correct! PLATO (PLAnetary Transits and Oscillations of stars) aims to find Earth-like planets around Sun-like stars and characterize their host stars."
    },
    {
        "question": "ESA's upcoming ARIEL mission is dedicated to:",
        "options": [
            "Performing a chemical survey of exoplanet atmospheres.",
            "Searching for moons around Jupiter.",
            "Mapping the cosmic microwave background."
        ],
        "correct": 0,
        "feedback": "Correct! ARIEL (Atmospheric Remote-sensing Infrared Exoplanet Large-survey) will study what exoplanets are made of, how they form, and how they evolve."
    },
    {
        "question": "Gravitational microlensing is uniquely sensitive to:",
        "options": [
            "Cold planets orbiting far from their host stars, and free-floating 'rogue' planets.",
            "Hot Jupiters orbiting close to red giants.",
            "Rocky planets orbiting white dwarfs."
        ],
        "correct": 0,
        "feedback": "Correct! Because it does not rely on stellar light, microlensing can detect planets at wide separations and even planets ejected from systems (rogues)."
    },
    {
        "question": "What is a 'rogue planet'?",
        "options": [
            "A planet that orbits the galactic center directly, having been ejected from its parent system.",
            "A planet that has a highly irregular orbit.",
            "A planet that orbits a star in a retrograde direction."
        ],
        "correct": 0,
        "feedback": "Correct! Rogue planets are interstellar objects of planetary mass that do not orbit any star, having been flung into interstellar space."
    },
    {
        "question": "What is the approximate average albedo of Earth?",
        "options": [
            "0.30.",
            "0.05.",
            "0.90."
        ],
        "correct": 0,
        "feedback": "Correct! Earth reflects about 30% of incoming sunlight, mostly due to clouds, ice cover, and reflective land surfaces."
    },
    {
        "question": "The radius of Earth is approximately what fraction of Jupiter's radius?",
        "options": [
            "1 / 11.",
            "1 / 2.",
            "1 / 100."
        ],
        "correct": 0,
        "feedback": "Correct! Jupiter is about 11 times the radius of Earth, meaning a Jupiter transit blocks about 121 times more light than an Earth transit."
    },
    {
        "question": "Stellar luminosity is defined as:",
        "options": [
            "The total amount of energy emitted by a star per unit time.",
            "The temperature of the star's surface.",
            "The apparent brightness of the star from Earth."
        ],
        "correct": 0,
        "feedback": "Correct! Luminosity (L) is the intrinsic power output of a star, whereas apparent brightness is how bright it appears depending on distance."
    }
]

# Add general templates to final list
for q in general_templates:
    questions.append(q)

# --- 2. Kepler's Third Law (300 questions) ---
catalog_names = ["TOI", "Kepler", "LTT", "GJ", "HIP", "HD", "WASP", "HAT-P", "K2", "NGTS"]
for i in range(300):
    m_star = round(random.uniform(0.1, 2.0), 2)
    period = round(random.uniform(0.5, 365.0), 1)
    planet_letter = random.choice(["b", "c", "d", "e", "f"])
    planet_name = f"{random.choice(catalog_names)}-{random.randint(100, 2999)}{planet_letter}"
    
    # Calculate semi-major axis: a = (M_* * (P/365.25)^2)^(1/3)
    p_yr = period / 365.25
    a_au = (m_star * (p_yr ** 2)) ** (1.0 / 3.0)
    correct_val = round(a_au, 3)
    
    # Generate distractors
    options = [correct_val]
    while len(options) < 3:
        factor = random.choice([0.4, 0.7, 1.3, 1.6, 2.0])
        distractor = round(correct_val * factor, 3)
        if distractor != correct_val and distractor > 0.001 and distractor not in options:
            options.append(distractor)
    
    random.shuffle(options)
    correct_idx = options.index(correct_val)
    
    question_text = f"Using Kepler's Third Law, if the exoplanet {planet_name} orbits a star of mass {m_star} M_sun with a period of {period} days, what is its approximate orbital distance (semi-major axis)?"
    feedback = f"Correct! By Kepler's Third Law simplified for solar units, a = (M_* * P_yr^2)^(1/3). Substituting M_* = {m_star} and P = {period} days ({round(p_yr, 4)} years) yields approximately {correct_val} AU."
    
    # Format options with units
    options_str = [f"{opt} AU" for opt in options]
    
    questions.append({
        "question": question_text,
        "options": options_str,
        "correct": correct_idx,
        "feedback": feedback
    })

# --- 3. Transit Depth Questions (300 questions) ---
for i in range(300):
    r_planet = round(random.uniform(0.5, 1.8), 2)  # In Jupiter radii
    r_star = round(random.uniform(0.1, 2.5), 2)    # In Solar radii
    planet_letter = random.choice(["b", "c", "d", "e"])
    planet_name = f"{random.choice(catalog_names)}-{random.randint(100, 2999)}{planet_letter}"
    
    # Ratio Rp / Rs in Jupiter-to-solar units
    # R_jup / R_sun = 0.10049
    ratio_pct = (r_planet * 0.10049 / r_star) ** 2 * 100
    
    # Convert to percentage or parts per million (ppm)
    is_ppm = ratio_pct < 0.1
    if is_ppm:
        correct_val = round(ratio_pct * 10000, 1) # In ppm
        unit = "ppm"
    else:
        correct_val = round(ratio_pct, 3) # In %
        unit = "%"
        
    options = [correct_val]
    while len(options) < 3:
        factor = random.choice([0.1, 0.5, 2.0, 5.0, 10.0])
        distractor = round(correct_val * factor, 1 if is_ppm else 3)
        if distractor != correct_val and distractor > 0 and distractor not in options:
            options.append(distractor)
            
    random.shuffle(options)
    correct_idx = options.index(correct_val)
    
    question_text = f"If exoplanet {planet_name} has a radius of {r_planet} R_Jupiter and transits a host star with a radius of {r_star} R_Sun, what is the expected transit depth (brightness drop)?"
    feedback = f"Correct! The transit depth is given by delta = (R_p / R_*)^2. Given R_p = {r_planet} R_J (where 1 R_J approx 0.1005 R_Sun) and R_* = {r_star} R_Sun, the calculated depth is {correct_val} {unit}."
    
    options_str = [f"{opt} {unit}" for opt in options]
    
    questions.append({
        "question": question_text,
        "options": options_str,
        "correct": correct_idx,
        "feedback": feedback
    })

# --- 4. Equilibrium Temperature (300 questions) ---
for i in range(300):
    t_star = random.choice([3000, 3500, 4000, 4500, 5000, 5500, 5800, 6000, 6500]) # Star Temp K
    r_star = round(random.uniform(0.1, 2.0), 2)
    albedo = random.choice([0.1, 0.2, 0.3, 0.4, 0.5])
    distance = round(random.uniform(0.02, 3.0), 2)
    planet_letter = random.choice(["b", "c", "d", "e"])
    planet_name = f"{random.choice(catalog_names)}-{random.randint(100, 2999)}{planet_letter}"
    
    # Formula: T_eq = T_* * (1 - A)^0.25 * sqrt(R_* / (430 * a))
    try:
        t_eq = t_star * ((1.0 - albedo) ** 0.25) * math.sqrt(r_star / (430.0 * distance))
        correct_val = int(round(t_eq))
    except Exception:
        correct_val = 250 # fallback
        
    options = [correct_val]
    while len(options) < 3:
        offset = random.choice([-200, -100, -50, 50, 100, 200, 300])
        distractor = correct_val + offset
        if distractor != correct_val and distractor > 0 and distractor not in options:
            options.append(distractor)
            
    random.shuffle(options)
    correct_idx = options.index(correct_val)
    
    question_text = f"If exoplanet {planet_name} orbits at a distance of {distance} AU from a star of temperature {t_star} K and radius {r_star} R_Sun, assuming a bond albedo of {albedo}, what is its theoretical equilibrium temperature?"
    feedback = f"Correct! Using the planetary equilibrium temperature equation T_eq = T_* * (1 - A)^0.25 * sqrt(R_* / (430 * a)), the calculation yields approximately {correct_val} K."
    
    options_str = [f"{opt} K" for opt in options]
    
    questions.append({
        "question": question_text,
        "options": options_str,
        "correct": correct_idx,
        "feedback": feedback
    })

# Crop to exactly 1000 if needed (it should be exactly 1000: 100 + 300 + 300 + 300 = 1000)
questions = questions[:1000]

print(f"Generated {len(questions)} questions successfully.")

# Write to questions.json
with open("d:/trial/web/questions.json", "w") as f:
    json.dump(questions, f, indent=4)
