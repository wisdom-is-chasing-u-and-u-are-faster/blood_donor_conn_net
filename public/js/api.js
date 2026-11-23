/**
 * Blood Donor Connection Network (BDCN) Client API Layer
 * Interfaces with RESTful endpoints defined in api_contract.json
 */

const BDCN_API = {
    baseUrl: '/api/v1',

    async checkHealth() {
        try {
            const res = await fetch('/health');
            return await res.json();
        } catch (err) {
            console.error('Health check failed:', err);
            return { status: 'error', message: err.toString() 
    async getDonorAvailability(username = '') {
        try {
            const url = username ? `${this.baseUrl}/donors/availability?username=${encodeURIComponent(username)}` : `${this.baseUrl}/donors/availability`;
            const res = await fetch(url);
            return await res.json();
        } catch (err) {
            console.error('Failed to get donor availability:', err);
            return { status: 'error', message: err.toString() };
        }
    },

    async updateDonorAvailability(status) {
        try {
            const res = await fetch(`${this.baseUrl}/donors/availability`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status })
            });
            return await res.json();
        } catch (err) {
            console.error('Failed to update donor availability:', err);
            return { status: 'error', message: err.toString() };
        }
    },

    async commitToRequest(requestId, eta = 'Within 1 hour') {
        try {
            const res = await fetch(`${this.baseUrl}/requests/${requestId}/commit`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ eta })
            });
            return await res.json();
        } catch (err) {
            console.error('Failed to commit to request:', err);
            return { status: 'error', message: err.toString() };
        }
    },

    async getRequestCommitments(requestId) {
        try {
            const res = await fetch(`${this.baseUrl}/requests/${requestId}/commitments`);
            return await res.json();
        } catch (err) {
            console.error('Failed to get request commitments:', err);
            return { status: 'error', commitments: [] };
        }
    },

    async getUrgentRequests() {
        try {
            const res = await fetch(`${this.baseUrl}/requests/urgent`);
            return await res.json();
        } catch (err) {
            console.error('Failed to get urgent requests:', err);
            return { status: 'error', requests: [] };
        }
    }
};
        }
    },

    async socialLogin(provider, token = 'mock-token') {
        try {
            const res = await fetch(`${this.baseUrl}/auth/social`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider, token })
            });
            return await res.json();
        } catch (err) {
            console.error('Social login failed:', err);
            return { status: 'error', message: err.toString() };
        }
    },

    async getDonorHotspots(radius = 50, bloodType = 'All') {
        try {
            const params = new URLSearchParams({ radius, blood_type: bloodType });
            const res = await fetch(`${this.baseUrl}/donors/hotspots?${params.toString()}`);
            return await res.json();
        } catch (err) {
            console.error('Failed to fetch donor hotspots:', err);
            return { status: 'error', hotspots: [] };
        }
    },

    async submitBloodRequest(requestData) {
        try {
            const res = await fetch(`${this.baseUrl}/requests`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(requestData)
            });
            return await res.json();
        } catch (err) {
            console.error('Failed to submit blood request:', err);
            return { status: 'error', message: err.toString() };
        }
    },

    async verifyBloodRequest(requestId, action) {
        try {
            const res = await fetch(`${this.baseUrl}/admin/requests/${requestId}/verify`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action })
            });
            return await res.json();
        } catch (err) {
            console.error(`Failed to verify request ${requestId}:`, err);
            return { status: 'error', message: err.toString() };
        }
    }
};

// Initialize interactive listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('BDCN Client API Layer active.');

    // Wire Request Form Submission if present
    const requestForm = document.querySelector('form');
    if (requestForm && (document.getElementById('patientName') || document.getElementById('bloodType'))) {
        requestForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitBtn = requestForm.querySelector('button[type="submit"]') || requestForm.querySelector('button');
            const originalText = submitBtn ? submitBtn.innerText : '';
            if (submitBtn) submitBtn.innerText = 'Submitting...';

            const bloodTypeEl = document.getElementById('bloodType');
            const unitsEl = document.getElementById('units');
            const urgencyEl = document.getElementById('urgency');
            const hospitalEl = document.getElementById('hospital');
            const fileEl = document.getElementById('medicalDoc');

            const payload = {
                blood_type: bloodTypeEl ? bloodTypeEl.value : 'O+',
                units: unitsEl ? parseInt(unitsEl.value, 10) || 1 : 1,
                urgency: urgencyEl ? urgencyEl.value : 'Emergency',
                district: hospitalEl ? hospitalEl.value : 'Downtown',
                notes: 'Submitted via Web Requisition Form',
                filename: fileEl && fileEl.files && fileEl.files.length > 0 ? fileEl.files[0].name : 'medical_doc.pdf'
            };

            const result = await BDCN_API.submitBloodRequest(payload);
            if (result.status === 'success') {
                alert(`Blood request #${result.request_id} successfully submitted and sent to District Admin Queue.`);
                requestForm.reset();
            } else {
                alert(`Submission error: ${result.message || 'Unknown error'}`);
            }
            if (submitBtn) submitBtn.innerText = originalText;
        });
    }

    // Wire Admin Approve/Reject buttons
    const approveButtons = document.querySelectorAll('.btn-success');
    approveButtons.forEach((btn, idx) => {
        if (btn.innerText.trim().toLowerCase() === 'approve') {
            btn.addEventListener('click', async (e) => {
                e.preventDefault();
                const reqId = idx + 1;
                btn.disabled = true;
                btn.innerText = 'Approving...';
                const res = await BDCN_API.verifyBloodRequest(reqId, 'approve');
                if (res.status === 'success') {
                    btn.innerText = 'Approved ✓';
                    btn.classList.remove('btn-success');
                    btn.classList.add('btn-secondary');
                } else {
                    btn.disabled = false;
                    btn.innerText = 'Approve';
                }
            });
        }
    });

    const rejectButtons = document.querySelectorAll('.btn-danger');
    rejectButtons.forEach((btn, idx) => {
        if (btn.innerText.trim().toLowerCase() === 'reject') {
            btn.addEventListener('click', async (e) => {
                e.preventDefault();
                const reqId = idx + 1;
                btn.disabled = true;
                btn.innerText = 'Rejecting...';
                const res = await BDCN_API.verifyBloodRequest(reqId, 'reject');
                if (res.status === 'success') {
                    btn.innerText = 'Rejected ✗';
                    btn.classList.remove('btn-danger');
                    btn.classList.add('btn-secondary');
                } else {
                    btn.disabled = false;
                    btn.innerText = 'Reject';
                }
            });
        }
    });

    // Wire Donor Availability Toggle on donor_dashboard.html
    const toggleInput = document.querySelector('.availability-toggle input[type="checkbox"]');
    const statusTextEl = document.querySelector('.status-card .status-text');
    if (toggleInput && statusTextEl) {
        // Load initial state
        BDCN_API.getDonorAvailability().then(data => {
            if (data.status === 'success') {
                if (data.is_in_cooldown) {
                    toggleInput.disabled = true;
                    statusTextEl.className = 'status-text status-cooldown';
                    statusTextEl.innerText = `In Recovery Cooldown (${data.remaining_cooldown_days} days left)`;
                } else if (data.availability_status === 'Available') {
                    toggleInput.checked = true;
                    statusTextEl.className = 'status-text status-available';
                    statusTextEl.innerText = 'Available';
                } else {
                    toggleInput.checked = false;
                    statusTextEl.className = 'status-text status-unavailable';
                    statusTextEl.innerText = 'Unavailable';
                }
            }
        });

        toggleInput.addEventListener('change', async (e) => {
            const newStatus = toggleInput.checked ? 'Available' : 'Unavailable';
            const res = await BDCN_API.updateDonorAvailability(newStatus);
            if (res.status === 'success') {
                statusTextEl.className = newStatus === 'Available' ? 'status-text status-available' : 'status-text status-unavailable';
                statusTextEl.innerText = newStatus;
            } else {
                toggleInput.checked = !toggleInput.checked;
                alert(res.message || 'Failed to update availability status.');
            }
        });
    }

    // Wire Urgent Request Details Donor Commitment Flow
    const commitBtn = document.getElementById('commitBtn');
    const commitModal = document.getElementById('commitModal');
    const confirmCommitBtn = document.getElementById('confirmCommitBtn');
    const etaSelect = document.getElementById('etaSelect');
    const commitView = document.getElementById('commit-view');
    const committedView = document.getElementById('committed-view');

    if (confirmCommitBtn) {
        confirmCommitBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            const eta = etaSelect ? etaSelect.value : 'Within 1 hour';
            confirmCommitBtn.disabled = true;
            confirmCommitBtn.innerText = 'Confirming...';

            // Assume request_id 1 for mockup page or extract from url
            const urlParams = new URLSearchParams(window.location.search);
            const reqId = parseInt(urlParams.get('id') || '1', 10);

            const res = await BDCN_API.commitToRequest(reqId, eta);
            if (res.status === 'success') {
                if (commitModal) commitModal.style.display = 'none';
                if (commitView) commitView.style.display = 'none';
                if (committedView) {
                    committedView.style.display = 'block';
                    const etaEl = committedView.querySelector('.user-eta');
                    if (etaEl) etaEl.innerText = eta;
                }
            } else {
                alert(res.message || 'Unable to record commitment.');
                confirmCommitBtn.disabled = false;
                confirmCommitBtn.innerText = 'Confirm Commitment';
            }
        });
    }

    // Wire Requester Anonymized Commitments Table
    const commitmentsTableBody = document.querySelector('table.table tbody');
    if (commitmentsTableBody && window.location.pathname.includes('urgent_request_details_requester')) {
        const urlParams = new URLSearchParams(window.location.search);
        const reqId = parseInt(urlParams.get('id') || '1', 10);
        BDCN_API.getRequestCommitments(reqId).then(data => {
            if (data.status === 'success' && data.commitments) {
                commitmentsTableBody.innerHTML = '';
                data.commitments.forEach(c => {
                    const row = document.createElement('tr');
                    row.innerHTML = `<td><strong>${c.anonymized_id}</strong></td><td>${c.eta}</td>`;
                    commitmentsTableBody.appendChild(row);
                });
                const totalEl = document.querySelector('.total-committed-count');
                if (totalEl) totalEl.innerText = `${data.total_committed} Donors`;
            }
        });
    }

});
