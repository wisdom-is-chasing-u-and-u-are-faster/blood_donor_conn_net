/**
 * static/js/api.js — BDCN Client-Side API Communication Module
 * Connects UI consoles dynamically to the Flask REST endpoints in api_contract.json.
 */

const BDCN_API = {
    baseUrl: '/api/v1',

    async getHealth() {
        const res = await fetch('/health');
        return res.json();
    },

    // 1. Emergency Dispatch Endpoints
    async listDispatchRequests() {
        const res = await fetch(`${this.baseUrl}/dispatch/emergency-requests`);
        return res.json();
    },

    async createDispatchOrder(payload) {
        const res = await fetch(`${this.baseUrl}/dispatch/emergency-requests`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        return { ok: res.ok, status: res.status, data };
    },

    async getDispatchDetails(requestId) {
        const res = await fetch(`${this.baseUrl}/dispatch/emergency-requests/${requestId}`);
        return res.json();
    },

    // 2. Blood Inventory & FEFO Endpoints
    async getInventorySummary() {
        const res = await fetch(`${this.baseUrl}/inventory/blood-units`);
        return res.json();
    },

    async registerBloodUnit(payload) {
        const res = await fetch(`${this.baseUrl}/inventory/blood-units`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return res.json();
    },

    async reserveInventory(payload) {
        const res = await fetch(`${this.baseUrl}/inventory/blood-units/reserve`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        return { ok: res.ok, status: res.status, data };
    },

    // 3. Donor Geospatial Matching & Broadcast Endpoints
    async searchProximityDonors(payload) {
        const res = await fetch(`${this.baseUrl}/donors/proximity-search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return res.json();
    },

    async broadcastAlert(payload) {
        const res = await fetch(`${this.baseUrl}/donors/broadcast`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        return res.json();
    },

    // 4. HIPAA Audit Log Endpoints
    async getAuditLogs() {
        const res = await fetch(`${this.baseUrl}/audit/logs`);
        return res.json();
    },

    async verifyAuditLedger() {
        const res = await fetch(`${this.baseUrl}/audit/verify`, {
            method: 'POST'
        });
        return res.json();
    }
};
