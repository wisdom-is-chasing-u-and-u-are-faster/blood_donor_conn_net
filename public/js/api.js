/**
 * Blood Donor Connection Network (BDCN) Client API Layer
 * Interfaces with RESTful endpoints defined in api_contract.json
 * Extended for ARCH-9275: Emergency Donor Availability & Response Tracking
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
    },

    // =========================================================================
    // ARCH-9275: Emergency Donor Availability & Response Tracking
    // =========================================================================

    /**
     * Retrieve current donor availability status and cooldown details.
     */
    async getDonorAvailability(username = null) {
        try {
            const query = username ? `?username=${encodeURIComponent(username)}` : '';
            const res = await fetch(`${this.baseUrl}/donors/availability${query}`);
            return await res.json();
        } catch (err) {
            console.error('Failed to fetch donor availability:', err);
            return { status: 'error', message: err.toString() };
        }
    },

    /**
     * Update donor availability status ('Available' or 'Unavailable').
     */
    async updateDonorAvailability(status, username = null) {
        try {
            const res = await fetch(`${this.baseUrl}/donors/availability`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status, username })
            });
            return await res.json();
        } catch (err) {
            console.error('Failed to update donor availability:', err);
            return { status: 'error', message: err.toString() };
        }
    },

    /**
     * Log a completed donation (triggering 56-day cooldown).
     */
    async logDonation(donationDate = null, donorId = null) {
        try {
            const res = await fetch(`${this.baseUrl}/donors/log-donation`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ donation_date: donationDate, donor_id: donorId })
            });
            return await res.json();
        } catch (err) {
            console.error('Failed to log donation:', err);
            return { status: 'error', message: err.toString() };
        }
    },

    /**
     * Fetch all blood requests with live commitment tallies.
     */
    async getBloodRequests(username = null) {
        try {
            const query = username ? `?username=${encodeURIComponent(username)}` : '';
            const res = await fetch(`${this.baseUrl}/requests${query}`);
            return await res.json();
        } catch (err) {
            console.error('Failed to fetch blood requests:', err);
            return { status: 'error', requests: [] };
        }
    },

    /**
     * Commit to donate for a specific blood request with an optional ETA.
     */
    async commitToRequest(requestId, eta = 'unspecified', username = null) {
        try {
            const res = await fetch(`${this.baseUrl}/requests/${requestId}/commitments`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ eta, username })
            });
            return await res.json();
        } catch (err) {
            console.error(`Failed to commit to request ${requestId}:`, err);
            return { status: 'error', message: err.toString() };
        }
    },

    /**
     * Get list of commitments for a request (anonymized names + ETAs).
     */
    async getRequestCommitments(requestId, role = 'admin', hospital = null) {
        try {
            const params = new URLSearchParams({ role });
            if (hospital) params.append('hospital', hospital);
            const res = await fetch(`${this.baseUrl}/requests/${requestId}/commitments?${params.toString()}`);
            return await res.json();
        } catch (err) {
            console.error(`Failed to fetch commitments for request ${requestId}:`, err);
            return { status: 'error', commitments: [] };
        }
    }
};

// Initialize interactive listeners when DOM is loaded
document.addEventListener('DOMContentLoaded', async () => {
    console.log('BDCN Client API Layer active with ARCH-9275 Availability & Response Tracking.');

    // 1. Availability Toggle Wireup (Donor Dashboard)
    const toggleInputs = document.querySelectorAll('.availability-toggle input[type="checkbox"], #availability-toggle-input');
    toggleInputs.forEach(input => {
        input.addEventListener('change', async (e) => {
            const newStatus = input.checked ? 'Available' : 'Unavailable';
            const res = await BDCN_API.updateDonorAvailability(newStatus);
            if (res.status === 'success') {
                console.log('Availability updated:', res.availability_status);
                // Refresh or update UI indicator if present
                const badge = document.getElementById('status-badge');
                if (badge) {
                    badge.innerText = newStatus;
                    badge.className = `badge bg-${newStatus === 'Available' ? 'success' : 'secondary'}`;
                }
            } else {
                alert(`Cannot change status: ${res.message}`);
                // Revert toggle state
                input.checked = !input.checked;
            }
        });
    });

    // 2. "I Can Donate" Commit Button & Modal Wireup (Donor Requests)
    const commitButtons = document.querySelectorAll('.btn-commit-donate, [data-action="commit-donate"]');
    commitButtons.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const reqId = btn.getAttribute('data-request-id') || 1;
            const etaSelect = document.getElementById('eta-select') || document.querySelector('select[name="eta"]');
            const eta = etaSelect ? etaSelect.value : 'within 1 hour';

            btn.disabled = true;
            btn.innerText = 'Committing...';

            const res = await BDCN_API.commitToRequest(reqId, eta);
            if (res.status === 'success') {
                btn.innerText = 'Committed ✓';
                btn.classList.remove('btn-danger', 'btn-primary');
                btn.classList.add('btn-success');
                alert(res.message);
                // Update tally count badge if present
                const tallyEl = document.querySelector(`[data-tally-for="${reqId}"]`) || document.getElementById(`tally-${reqId}`);
                if (tallyEl && res.committed_donor_count !== undefined) {
                    tallyEl.innerText = `${res.committed_donor_count} Donors Committed`;
                }
            } else {
                btn.disabled = false;
                btn.innerText = 'I Can Donate';
                alert(`Commitment failed: ${res.message}`);
            }
        });
    });

    // 3. Request Form Submission Wireup
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
});

// Export for node/test environments if module exists
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BDCN_API;
}
