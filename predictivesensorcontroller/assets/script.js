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
    
    // Logs table
    const logTableBody = document.querySelector('#logTable tbody');

    // Global state track
    let isSimulationMode = false;
    let pollInterval = null;

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
                logTableBody.innerHTML = '';
                data.logs.forEach(log => {
                    const row = document.createElement('tr');
                    const d = new Date(log.timestamp);
                    const timeStr = `${d.getHours().toString().padStart(2,'0')}:${d.getMinutes().toString().padStart(2,'0')}:${d.getSeconds().toString().padStart(2,'0')}`;
                    
                    row.innerHTML = `
                        <td>${timeStr}</td>
                        <td>${log.calculated_speed > 0 ? log.calculated_speed.toFixed(1) : '-'}</td>
                        <td>${log.target_length}</td>
                        <td class="status-${log.status.split(':')[0]}">${log.status}</td>
                    `;
                    logTableBody.appendChild(row);
                });
            }
        } catch(e) {
            console.error("Failed to fetch logs", e);
        }
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

    // --- Event Listeners ---
    
    simForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        simError.classList.add('hidden');
        const speed = document.getElementById('simSpeed').value;
        
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
