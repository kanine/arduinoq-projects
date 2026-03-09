// Predictive Factory Sensor Controller - Frontend JS
document.addEventListener('DOMContentLoaded', () => {
    
    // DOM Elements
    const statusText = document.getElementById('statusText');
    const simBadge = document.getElementById('simBadge');
    
    // Nodes
    const nodeA = document.getElementById('nodeA');
    const nodeB = document.getElementById('nodeB');
    const nodeC = document.getElementById('nodeC');
    const nodeCutter = document.getElementById('nodeCutter');
    
    // Labels
    const lblDistCA = document.getElementById('lblDistCA');
    const lblDistAB = document.getElementById('lblDistAB');
    const lblDistBC = document.getElementById('lblDistBC');
    const lblTargetLength = document.getElementById('lblTargetLength');
    
    // Metrics
    const metricSpeed = document.getElementById('metricSpeed');
    const metricCutTime = document.getElementById('metricCutTime');
    
    // Forms
    const simForm = document.getElementById('simForm');
    const configForm = document.getElementById('configForm');
    const btnSimulate = document.getElementById('btnSimulate');
    const simError = document.getElementById('simError');
    const cfgFeedback = document.getElementById('cfgFeedback');
    
    // Config Inputs
    const cfgTarget = document.getElementById('cfgTarget');
    const cfgCA = document.getElementById('cfgCA');
    const cfgAB = document.getElementById('cfgAB');
    const cfgBC = document.getElementById('cfgBC');
    const cfgSimMode = document.getElementById('cfgSimMode');
    const cfgValMode = document.getElementById('cfgValMode');
    
    // Progress Bar
    const progressSection = document.getElementById('progressSection');
    const progTargetVal = document.getElementById('progTargetVal');
    const progFill = document.getElementById('progFill');
    const progActiveValue = document.getElementById('progActiveValue');
    
    // Logs table
    const logTableBody = document.querySelector('#logTable tbody');

    // Global state track
    let isSimulationMode = false;
    let pollInterval = null;
    let audioCtx = null;
    let audioEnabled = false;
    let prevSensorState = { A: false, B: false, C: false, relay: false };
    
    // Progress track
    let simStartTime = 0;
    let currentSpeed = 0;
    let currentTarget = 300;
    let simActive = false;
    let animationFrameId = null;

    // --- initialization ---
    async function init() {
        await loadConfig();
        await updateStatus();
        await updateLogs();
        
        // Start polling (fast during sim, slow otherwise)
        pollInterval = setInterval(pollState, 100);
        setInterval(updateLogs, 5000); // Poll logs every 5s
    }

    async function updateStatus() {
        await pollState();
    }

    // --- API Calls ---
    async function loadConfig() {
        try {
            const res = await fetch('/config');
            const data = await res.json();
            if (data.ok && data.config) {
                applyConfigToUI(data.config);
            }
        } catch (e) {
            console.error("Failed to load config", e);
        }
    }

    async function pollState() {
        try {
            const res = await fetch('/status');
            const data = await res.json();
            
            // Update UI
            updateDashboard(data);
            
        } catch (e) {
            statusText.textContent = "Disconnected";
            statusText.style.color = "var(--danger-red)";
        }
    }

    async function updateLogs() {
        try {
            const res = await fetch('/logs');
            const data = await res.json();
            
            if (data.ok && data.logs) {
                // Update standard logs table (full history limit)
                logTableBody.innerHTML = '';
                
                // Update Timestamp History table (last 3 only)
                const tsTableBody = document.querySelector('#tsTable tbody');
                if (tsTableBody) tsTableBody.innerHTML = '';
                
                data.logs.forEach((log, index) => {
                    const d = new Date(log.timestamp);
                    const timeStr = `${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}:${d.getSeconds().toString().padStart(2,'0')}`;
                    
                    // Standard logs row
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${timeStr}</td>
                        <td>${log.calculated_speed > 0 ? log.calculated_speed.toFixed(1) : '-'}</td>
                        <td>${log.target_length}</td>
                        <td class="status-${log.status.split(':')[0]}">${log.status}</td>
                    `;
                    logTableBody.appendChild(row);
                    
                    // Detailed Timestamp History row (latest 3)
                    if (index < 3 && tsTableBody) {
                        const tsRow = document.createElement('tr');
                        // Calculate differential from start
                        const tsA = (log.sensorA_time || 0).toFixed(2);
                        const tsB = (log.sensorB_time || 0).toFixed(2);
                        const tsC = (log.sensorC_time || 0).toFixed(2);
                        const tsCut = (log.actual_cut_time || 0).toFixed(2);
                        
                        tsRow.innerHTML = `
                            <td>${timeStr}</td>
                            <td>${tsA}s</td>
                            <td>${tsB}s</td>
                            <td>${tsC}s</td>
                            <td style="color:var(--danger-red)">${tsCut}s</td>
                        `;
                        tsTableBody.appendChild(tsRow);
                    }
                });
            }
        } catch(e) {
            console.error("Failed to fetch logs", e);
        }
    }

    // --- Audio Cues ---
    function initAudio() {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
    }

    function playTone(freq, type = 'sine', duration = 100) {
        if (!audioEnabled || !audioCtx) return;
        
        const oscillator = audioCtx.createOscillator();
        const gainNode = audioCtx.createGain();
        
        oscillator.type = type;
        oscillator.frequency.value = freq;
        
        gainNode.gain.setValueAtTime(0.1, audioCtx.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + (duration / 1000));
        
        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);
        
        oscillator.start();
        oscillator.stop(audioCtx.currentTime + (duration / 1000));
    }

    // --- UI Updaters ---

    function applyConfigToUI(config) {
        // populate form
        cfgTarget.value = config.target_length;
        cfgCA.value = config.distance_cut_to_A;
        cfgAB.value = config.distance_AB;
        cfgBC.value = config.distance_BC;
        cfgSimMode.checked = config.simulation_mode;
        cfgValMode.checked = config.validation_enabled;
        
        // update track labels
        lblDistCA.textContent = `${config.distance_cut_to_A} mm`;
        lblDistAB.textContent = `${config.distance_AB} mm`;
        lblDistBC.textContent = `${config.distance_BC} mm`;
        lblTargetLength.textContent = `Target: ${config.target_length} mm`;
        progTargetVal.textContent = config.target_length;
        
        // enable/disable sim button
        isSimulationMode = config.simulation_mode;
        btnSimulate.disabled = !isSimulationMode;
        if(isSimulationMode) {
            simBadge.classList.remove('hidden');
        } else {
            simBadge.classList.add('hidden');
        }
    }

    function updateDashboard(state) {
        statusText.textContent = state.status.toUpperCase();
        if(state.status.startsWith('error')) {
            statusText.style.color = "var(--danger-red)";
        } else if (state.status === "simulating" || state.status === "running") {
            statusText.style.color = "var(--success-green)";
        } else {
            statusText.style.color = "var(--accent-blue)";
        }

        // Metrics
        metricSpeed.textContent = state.speed_mm_per_s > 0 ? state.speed_mm_per_s.toFixed(1) : "0";
        metricCutTime.textContent = state.next_cut_ms || "0";
        
        // Edge Detection for Audio Cues & UI Triggers
        if (state.sensorA && !prevSensorState.A) playTone(880, 'sine', 150);     // A5
        if (state.sensorB && !prevSensorState.B) playTone(987.77, 'sine', 150);  // B5
        if (state.sensorC && !prevSensorState.C) playTone(1046.50, 'sine', 150); // C6
        if (state.relay_active && !prevSensorState.relay) {
            playTone(440, 'square', 300); // A4, harsher buzz
            // Fetch the newly written logs immediately on cut
            setTimeout(updateLogs, 50); 
        }
        
        prevSensorState.A = state.sensorA;
        prevSensorState.B = state.sensorB;
        prevSensorState.C = state.sensorC;
        prevSensorState.relay = state.relay_active;
        
        // Nodes
        toggleNode(nodeA, state.sensorA);
        toggleNode(nodeB, state.sensorB);
        toggleNode(nodeC, state.sensorC);
        toggleNode(nodeCutter, state.relay_active);
    }

    function toggleNode(el, active) {
        if (active) {
            el.classList.add('active');
        } else {
            el.classList.remove('active');
        }
    }

    // --- Progress Bar ---
    function progressLoop() {
        if (!simActive) return;
        
        const elapsedSecs = (Date.now() - simStartTime) / 1000;
        const currentLen = Math.min(elapsedSecs * currentSpeed, currentTarget);
        
        const percent = (currentLen / currentTarget) * 100;
        progFill.style.width = `${percent}%`;
        progActiveValue.textContent = currentLen.toFixed(1);
        
        if (currentLen < currentTarget) {
            animationFrameId = requestAnimationFrame(progressLoop);
        } else {
            simActive = false;
        }
    }

    // --- Event Listeners ---
    
    // UI Local Config
    const cfgAudioCues = document.getElementById('cfgAudioCues');
    if (cfgAudioCues) {
        cfgAudioCues.addEventListener('change', (e) => {
            audioEnabled = e.target.checked;
            if (audioEnabled) initAudio();
        });
    }
    
    // User interaction required to unlock audio context in browsers
    document.body.addEventListener('click', initAudio, { once: true });
    
    simForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        initAudio(); // ensure audio is awake
        simError.classList.add('hidden');
        const speed = document.getElementById('simSpeed').value;
        const target = document.getElementById('cfgTarget').value;
        
        // Start progress immediately for smoothness
        simStartTime = Date.now();
        currentSpeed = parseFloat(speed);
        currentTarget = parseInt(target);
        simActive = true;
        
        progressSection.classList.remove('hidden');
        progTargetVal.textContent = currentTarget;
        progFill.style.width = '0%';
        progActiveValue.textContent = '0.0';
        
        if (animationFrameId) cancelAnimationFrame(animationFrameId);
        progressLoop();
        
        try {
            const res = await fetch('/simulate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ simulated_speed_mm_per_s: speed })
            });
            const data = await res.json();
            
            if (data.error) {
                simError.textContent = data.error;
                simError.classList.remove('hidden');
            } else {
                // Immediately poll to show starting state
                pollState();
            }
        } catch(e) {
            simError.textContent = "Network error starting simulation";
            simError.classList.remove('hidden');
        }
    });

    configForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const config = {
            target_length: parseInt(cfgTarget.value),
            distance_cut_to_A: parseInt(cfgCA.value),
            distance_AB: parseInt(cfgAB.value),
            distance_BC: parseInt(cfgBC.value),
            simulation_mode: cfgSimMode.checked,
            validation_enabled: cfgValMode.checked
        };
        
        try {
            const res = await fetch('/config', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(config)
            });
            const data = await res.json();
            
            if(data.ok && data.config) {
                applyConfigToUI(data.config);
                cfgFeedback.classList.remove('hidden');
                setTimeout(() => cfgFeedback.classList.add('hidden'), 2000);
            }
        } catch (e) {
            console.error("Config save error", e);
        }
    });

    // Run
    init();
});
