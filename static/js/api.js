// Client-side API integration module for BloodConnect BDCN Platform
// Wires form inputs and filter controls directly to backend REST endpoints

const BloodConnectAPI = {
    // REQ-F-005: Evaluate donor eligibility pre-screening
    async evaluatePrescreening(payload) {
        try {
            const response = await fetch('/api/v1/prescreening/evaluate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error evaluating prescreening:', error);
            throw error;
        }
    },

    // REQ-F-020: Filter compatible donors for hospital dashboard
    async filterDonors(bloodGroup = 'A+', verifiedOnly = true, page = 1, perPage = 10) {
        try {
            const params = new URLSearchParams({
                blood_group: bloodGroup,
                verified_only: verifiedOnly ? 'true' : 'false',
                page: page.toString(),
                per_page: perPage.toString()
            });
            const response = await fetch(`/api/v1/dashboard/donors/filter?${params.toString()}`);
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error filtering donors:', error);
            throw error;
        }
    }
};

window.BloodConnectAPI = BloodConnectAPI;
