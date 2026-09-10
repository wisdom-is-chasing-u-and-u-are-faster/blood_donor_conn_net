/**
 * BDCN API Client - Client-Side REST Wrapper
 */
const BDCN_API = {
    async checkEligibility(donorId, donationType = "WHOLE_BLOOD", targetDate = null) {
        let url = `/v1/donors/${encodeURIComponent(donorId)}/eligibility?donation_type=${encodeURIComponent(donationType)}`;
        if (targetDate) {
            url += `&target_date=${encodeURIComponent(targetDate)}`;
        }
        const resp = await fetch(url);
        return await resp.json();
    },

    async reserveInventory(hospitalId, encounterId, dinNumber) {
        const resp = await fetch("/v1/inventory/reserve", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                hospital_id: hospitalId,
                clinical_encounter_id: encounterId,
                din_number: dinNumber
            })
        });
        return await resp.json();
    },

    async findSpatialCandidates(lat, lon, radiusKm = 15.0, aboType = null, rhFactor = null) {
        let url = `/v1/spatial/candidates?latitude=${lat}&longitude=${lon}&radius_km=${radiusKm}`;
        if (aboType) url += `&abo_type=${encodeURIComponent(aboType)}`;
        if (rhFactor) url += `&rh_factor=${encodeURIComponent(rhFactor)}`;
        const resp = await fetch(url);
        return await resp.json();
    },

    async createEmergencyDispatch(payload) {
        const resp = await fetch("/v1/emergency/dispatch", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        return await resp.json();
    },

    async reconcileLeases() {
        const resp = await fetch("/v1/inventory/reconcile", { method: "POST" });
        return await resp.json();
    },

    async verifyAuditIntegrity() {
        const resp = await fetch("/v1/audit/verify");
        return await resp.json();
    }
};

window.BDCN_API = BDCN_API;
