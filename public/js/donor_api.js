/**
 * Client-Side API Helper for BDCN Donor Portal & Emergency Dispatch
 * Handles async fetch requests against REST API endpoints defined in api_contract.json
 */

const BDCN_API = {
    baseUrl: '/api/v1',

    // Ingest emergency clinical requisition (HL7 FHIR SupplyRequest format)
    async submitEmergencyRequest(payload) {
        try {
            const response = await fetch(`${this.baseUrl}/clinical/emergency-requests`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            return await response.json();
        } catch (error) {
            console.error('Error submitting emergency request:', error);
            throw error;
        }
    },

    // List active emergency requests
    async getEmergencyRequests() {
        try {
            const response = await fetch(`${this.baseUrl}/clinical/emergency-requests`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching emergency requests:', error);
            throw error;
        }
    },

    // Submit voluntary donor response (confirm / decline)
    async respondToEmergency(requestId, donorId, action) {
        try {
            const response = await fetch(`${this.baseUrl}/donors/emergency-responses`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    request_id: requestId,
                    donor_id: donorId,
                    action: action
                })
            });
            return await response.json();
        } catch (error) {
            console.error('Error submitting donor response:', error);
            throw error;
        }
    },

    // Retrieve unique digital check-in pass
    async getCheckInPass(passId) {
        try {
            const response = await fetch(`${this.baseUrl}/donors/check-in-pass/${passId}`);
            return await response.json();
        } catch (error) {
            console.error('Error fetching check-in pass:', error);
            throw error;
        }
    }
};

window.BDCN_API = BDCN_API;
