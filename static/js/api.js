/**
 * Client API Helper for BDCN Platform (Variant A)
 */
const BDCN_API = {
  async checkHealth() {
    const res = await fetch('/health');
    return res.json();
  },

  async loginSocial(provider, username, role) {
    const res = await fetch('/api/v1/auth/social', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider, username, role })
    });
    return res.json();
  },

  async uploadVerification(data) {
    const res = await fetch('/api/v1/verifications/upload', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    return res.json();
  },

  async getVerifications() {
    const res = await fetch('/api/v1/admin/verifications');
    return res.json();
  },

  async verifyAction(id, action, notes) {
    const res = await fetch(`/api/v1/admin/verifications/${id}/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, notes })
    });
    return res.json();
  },

  async getHotspots() {
    const res = await fetch('/api/v1/donors/hotspots');
    return res.json();
  },

  async getMessages() {
    const res = await fetch('/api/v1/messages');
    return res.json();
  },

  async sendMessage(recipient, content) {
    const res = await fetch('/api/v1/messages/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ recipient, content })
    });
    return res.json();
  },

  async shareAchievement(badgeId, platform) {
    const res = await fetch('/api/v1/achievements/share', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ badge_id: badgeId, platform })
    });
    return res.json();
  }
};

window.BDCN_API = BDCN_API;
