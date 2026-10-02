/**
 * static/js/dispatch.js — Dynamic Event Handling for Trauma Dispatch Console
 */

async function handleCodeRedSubmit(event) {
    event.preventDefault();
    const alertBox = document.getElementById('modal-alert-box');
    alertBox.classList.add('d-none');

    const submitBtn = document.getElementById('btn-submit-order');
    submitBtn.disabled = true;
    submitBtn.innerText = 'Reserving Inventory & Routing...';

    const payload = {
        requestingHospitalId: document.getElementById('form-facility-id').value,
        requiredBloodType: document.getElementById('form-blood-type').value,
        componentType: document.getElementById('form-component-type').value,
        unitsRequested: parseInt(document.getElementById('form-units-requested').value, 10),
        urgencyTier: document.getElementById('form-urgency-tier').value,
        latitude: parseFloat(document.getElementById('form-lat').value || 40.7128),
        longitude: parseFloat(document.getElementById('form-lon').value || -74.0060),
        clinicalNotesEncrypted: document.getElementById('form-clinical-notes').value || 'Trauma Code Red Order'
    };

    try {
        const response = await BDCN_API.createDispatchOrder(payload);
        if (response.ok) {
            // Close modal & reload table
            const modalEl = document.getElementById('codeRedModal');
            const modalInstance = bootstrap.Modal.getInstance(modalEl);
            if (modalInstance) modalInstance.hide();
            await loadDispatchGrid();
            window.location.reload();
        } else {
            alertBox.innerText = response.data.error || 'Failed to allocate inventory.';
            alertBox.classList.remove('d-none');
        }
    } catch (err) {
        alertBox.innerText = 'Network communication failure: ' + err.message;
        alertBox.classList.remove('d-none');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerText = '🚀 Dispatch Order & Reserve Units';
    }
}

async function loadDispatchGrid() {
    try {
        const res = await BDCN_API.listDispatchRequests();
        const tbody = document.getElementById('dispatch-tbody');
        if (!tbody || !res.requests) return;

        if (res.requests.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center py-4 text-muted">All trauma queues clear. Regional supply stabilized.</td></tr>`;
            return;
        }

        let html = '';
        res.requests.forEach(req => {
            const urgencyBadge = req.urgencyTier === 'CODE_RED'
                ? '<span class="badge badge-code-red">CODE RED</span>'
                : (req.urgencyTier === 'URGENT' ? '<span class="badge badge-urgent">URGENT</span>' : '<span class="badge badge-routine">ROUTINE</span>');

            html += `
                <tr>
                    <td><code>${req.requestId}</code></td>
                    <td>${req.requestingHospitalId}</td>
                    <td><span class="badge bg-danger">${req.requiredBloodType}</span> <small class="text-muted">${req.componentType}</small></td>
                    <td><strong>${req.unitsRequested}</strong></td>
                    <td>${urgencyBadge}</td>
                    <td><span class="badge bg-secondary status-badge">${req.status}</span></td>
                    <td><span class="timer-countdown">${req.leaseSecondsRemaining}s</span></td>
                    <td><small class="text-muted">${req.createdAt}</small></td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    } catch (err) {
        console.error('Error reloading dispatch grid:', err);
    }
}
