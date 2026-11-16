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
});
