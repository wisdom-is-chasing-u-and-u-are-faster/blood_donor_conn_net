// public/js/api.js - Client API helper for BDCN Platform
// Supporting all endpoints defined in api_contract.json

const BDCN_API = {
    async signup(fullName, email, password, role = 'donor') {
        const res = await fetch('/api/v1/auth/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ full_name: fullName, email, password, role })
        });
        return res.json();
    },

    async login(email, password) {
        const res = await fetch('/api/v1/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        return res.json();
    },

    async socialLogin(provider, email, name) {
        const res = await fetch('/api/v1/auth/social', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ provider, email, name })
        });
        return res.json();
    },

    async getDonorProfile() {
        const res = await fetch('/api/v1/donors/profile');
        return res.json();
    },

    async updateDonorProfile(profileData) {
        const res = await fetch('/api/v1/donors/profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(profileData)
        });
        return res.json();
    },

    async updateAvailability(status) {
        const res = await fetch('/api/v1/donors/availability', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ availability_status: status })
        });
        return res.json();
    },

    async submitRequest(requestData) {
        const res = await fetch('/api/v1/requests', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        return res.json();
    },

    async getRequests() {
        const res = await fetch('/api/v1/requests');
        return res.json();
    },

    async getRequestDetails(id) {
        const res = await fetch(`/api/v1/requests/${id}`);
        return res.json();
    },

    async adminRequestAction(id, action) {
        const res = await fetch(`/api/v1/admin/requests/${id}/action`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action })
        });
        return res.json();
    },

    async pledgeRequest(id, donorName, donorPhone) {
        const res = await fetch(`/api/v1/requests/${id}/pledge`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ donor_name: donorName, donor_phone: donorPhone })
        });
        return res.json();
    },

    async getMessages(requestId) {
        const url = requestId ? `/api/v1/messages?request_id=${requestId}` : '/api/v1/messages';
        const res = await fetch(url);
        return res.json();
    },

    async sendMessage(requestId, senderRole, content) {
        const res = await fetch('/api/v1/messages', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ request_id: requestId, sender_role: senderRole, content })
        });
        return res.json();
    }
};

window.BDCN_API = BDCN_API;
