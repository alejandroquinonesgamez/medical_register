async function fetchJson(url) {
    const response = await fetch(url, { credentials: 'same-origin' });
    if (!response.ok) {
        throw new Error(`Error ${response.status}`);
    }
    return response.json();
}

function formatJson(data) {
    return JSON.stringify(data, null, 2);
}

async function refreshSupervisor() {
    const now = new Date().toLocaleTimeString();
    const lastUpdate = document.getElementById('supervisor-last-update');
    const requestsEl = document.getElementById('supervisor-requests');
    const dbEl = document.getElementById('supervisor-db');

    try {
        const requests = await fetchJson('/api/supervisor/requests');
        requestsEl.textContent = formatJson(requests.requests || []);
        lastUpdate.textContent = now;
    } catch (error) {
        requestsEl.textContent = `Error cargando tráfico: ${error.message}`;
    }

    try {
        const dbSnapshot = await fetchJson('/api/supervisor/db');
        dbEl.textContent = formatJson(dbSnapshot);
    } catch (error) {
        dbEl.textContent = `Error cargando DB: ${error.message}`;
    }
}

refreshSupervisor();
setInterval(refreshSupervisor, 2000);
