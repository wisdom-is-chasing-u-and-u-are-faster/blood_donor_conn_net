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
            return { status: 'error', message: err.toString() };
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
});
