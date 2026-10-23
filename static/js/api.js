/**
 * BDCN Client-Side API Helper Layer
 * Connects frontend forms, buttons, and views to /api/v1 REST endpoints.
 */

const BDCN_API = {
  baseUrl: '',

  async checkHealth() {
    try {
      const res = await fetch(`${this.baseUrl}/health`);
      return await res.json();
    } catch (e) {
      console.error('Health check failed', e);
      return { status: 'error', message: e.message };
    }
  },

  async loginSocial(provider, email, name, h3_index = '872830828ffffff') {
    try {
      const res = await fetch(`${this.baseUrl}/api/v1/auth/social`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, email, name, h3_index })
      });
      return await res.json();
    } catch (e) {
      console.error('Social login error', e);
      return { status: 'error', message: e.message };
    }
  },

  async submitBloodRequest(data) {
    try {
      const res = await fetch(`${this.baseUrl}/api/v1/requests`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      return await res.json();
    } catch (e) {
      console.error('Request submission error', e);
      return { status: 'error', message: e.message };
    }
  },

  async getNearbyRequests(h3_index = '872830828ffffff') {
    try {
      const res = await fetch(`${this.baseUrl}/api/v1/requests/nearby?h3=${encodeURIComponent(h3_index)}`);
      return await res.json();
    } catch (e) {
      console.error('Fetch nearby requests error', e);
      return { status: 'error', requests: [] };
    }
  },

  async adjudicateRequest(requestId, action, reason = '') {
    try {
      const res = await fetch(`${this.baseUrl}/api/v1/admin/adjudicate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request_id: requestId, action, reason })
      });
      return await res.json();
    } catch (e) {
      console.error('Adjudication error', e);
      return { status: 'error', message: e.message };
    }
  },

  async logDonation(donorId, donationType, donationDate) {
    try {
      const res = await fetch(`${this.baseUrl}/api/v1/donations/log`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ donor_id: donorId, donation_type: donationType, donation_date: donationDate })
      });
      return await res.json();
    } catch (e) {
      console.error('Log donation error', e);
      return { status: 'error', message: e.message };
    }
  },

  async getBadges() {
    try {
      const res = await fetch(`${this.baseUrl}/api/v1/gamification/badges`);
      return await res.json();
    } catch (e) {
      console.error('Get badges error', e);
      return { status: 'error', badges: [] };
    }
  }
};

window.BDCN_API = BDCN_API;
