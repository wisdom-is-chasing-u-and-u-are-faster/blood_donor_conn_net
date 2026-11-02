// Client-side API helper for DonorMatch & BDCN platform
const API = {
  baseUrl: '',

  async checkHealth() {
    const res = await fetch(`${this.baseUrl}/health`);
    return res.json();
  },

  async evaluatePreScreening(formData) {
    const res = await fetch(`${this.baseUrl}/api/v1/prescreening/evaluate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(formData)
    });
    return res.json();
  },

  async getUrgentMatches(bloodType = 'all') {
    const res = await fetch(`${this.baseUrl}/api/v1/donors/urgent-match?blood_type=${encodeURIComponent(bloodType)}`);
    return res.json();
  },

  async submitTransaction(idempotencyKey, payload, role = 'Operator') {
    const res = await fetch(`${this.baseUrl}/api/v1/transactions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Idempotency-Key': idempotencyKey,
        'X-User-Role': role
      },
      body: JSON.stringify(payload)
    });
    return res.json();
  },

  async getDonors() {
    const res = await fetch(`${this.baseUrl}/api/v1/donors`);
    return res.json();
  }
};

window.DonorMatchAPI = API;
