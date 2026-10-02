/**
 * static/js/inventory.js — Event Handlers for Blood Inventory & FEFO Console
 */

async function handleUnitCheckIn(event) {
    event.preventDefault();
    const alertBox = document.getElementById('checkin-alert');
    alertBox.classList.add('d-none');

    const payload = {
        dinBarcode: document.getElementById('checkin-din').value,
        facilityId: document.getElementById('checkin-facility').value,
        bloodType: document.getElementById('checkin-blood-type').value,
        componentType: document.getElementById('checkin-component').value,
        volumeMl: parseInt(document.getElementById('checkin-volume').value, 10),
        expiresAt: new Date(Date.now() + 42 * 24 * 60 * 60 * 1000).toISOString()
    };

    try {
        await BDCN_API.registerBloodUnit(payload);
        window.location.reload();
    } catch (err) {
        alertBox.innerText = 'Check-in failed: ' + err.message;
        alertBox.classList.remove('d-none');
    }
}

async function loadInventoryTable() {
    try {
        const data = await BDCN_API.getInventorySummary();
        const tbody = document.getElementById('inventory-tbody');
        if (!tbody || !data.units) return;

        let html = '';
        data.units.forEach(u => {
            const statusBadge = u.status === 'AVAILABLE'
                ? '<span class="badge bg-success">AVAILABLE</span>'
                : (u.status === 'RESERVED' ? '<span class="badge bg-warning text-dark">RESERVED</span>' : `<span class="badge bg-secondary">${u.status}</span>`);

            html += `
                <tr>
                    <td><code>${u.unitId}</code></td>
                    <td><strong>${u.dinBarcode}</strong></td>
                    <td><span class="badge bg-danger">${u.bloodType}</span></td>
                    <td><small class="text-muted">${u.componentType}</small></td>
                    <td>${u.volumeMl} mL</td>
                    <td>${statusBadge}</td>
                    <td><small class="text-muted">${u.expiresAt}</small></td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    } catch (err) {
        console.error('Error refreshing inventory:', err);
    }
}
