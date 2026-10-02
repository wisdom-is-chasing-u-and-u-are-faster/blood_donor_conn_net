/**
 * static/js/donors.js — Event Handlers for Proximity Search and Broadcast Dispatcher
 */

function updateRadiusLabel(val) {
    const lbl = document.getElementById('radius-val');
    if (lbl) lbl.innerText = val;
}

async function executeProximitySearch() {
    const radius = parseFloat(document.getElementById('search-radius').value || 15);
    const bloodType = document.getElementById('filter-blood-type').value;

    const payload = {
        latitude: 40.7128,
        longitude: -74.0060,
        radiusMiles: radius,
        bloodTypes: bloodType ? [bloodType] : []
    };

    try {
        const res = await BDCN_API.searchProximityDonors(payload);
        const countBadge = document.getElementById('matched-count-badge');
        if (countBadge) countBadge.innerText = res.matchedDonorsCount;

        const tbody = document.getElementById('donor-tbody');
        if (!tbody || !res.matchedDonors) return;

        let html = '';
        res.matchedDonors.forEach(d => {
            const eligBadge = d.eligibilityStatus === 'ELIGIBLE'
                ? '<span class="badge bg-success">ELIGIBLE</span>'
                : '<span class="badge bg-secondary">DEFERRED (<56d)</span>';

            html += `
                <tr>
                    <td><code>${d.donorId}</code></td>
                    <td><span class="badge bg-danger">${d.bloodType}</span></td>
                    <td>${d.district}</td>
                    <td><strong>${d.distanceMiles} mi</strong></td>
                    <td>${eligBadge}</td>
                    <td><small class="text-muted">${d.lastDonationDate || 'N/A'}</small></td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    } catch (err) {
        console.error('Error executing proximity search:', err);
    }
}

function triggerBroadcastModal() {
    const modal = new bootstrap.Modal(document.getElementById('broadcastModal'));
    modal.show();
}

async function handleBroadcastSubmit(event) {
    event.preventDefault();
    const alertBox = document.getElementById('broadcast-alert');
    alertBox.classList.add('d-none');

    const msg = document.getElementById('broadcast-message').value;

    try {
        const res = await BDCN_API.broadcastAlert({ message: msg });
        alertBox.innerText = `✅ Broadcast Dispatched! Delivered via Push: ${res.deliveredPush}, Fallback SMS: ${res.fallbackSms}`;
        alertBox.classList.remove('d-none');
    } catch (err) {
        alertBox.classList.remove('alert-success');
        alertBox.classList.add('alert-danger');
        alertBox.innerText = 'Failed to broadcast alert: ' + err.message;
        alertBox.classList.remove('d-none');
    }
}
