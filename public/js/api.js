/**
 * BDCN API Client Layer — public/js/api.js
 * Interacts with backend REST endpoints matching api_contract.json
 */

const BDCNApi = {
  baseUrl: "/api/v1",

  async health() {
    try {
      const res = await fetch("/health");
      return await res.json();
    } catch (err) {
      console.error("Health check error:", err);
      throw err;
    }
  },

  async socialLogin(provider, credentials = {}) {
    try {
      const res = await fetch(`${this.baseUrl}/auth/social-login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: provider,
          access_token: credentials.token || "mock-token-xyz",
          email: credentials.email || `user@${provider}.com`,
          name: credentials.name || `Social User (${provider})`
        })
      });
      return await res.json();
    } catch (err) {
      console.error(`Social login failed for ${provider}:`, err);
      throw err;
    }
  },

  async getMapClusters() {
    try {
      const res = await fetch(`${this.baseUrl}/map/clusters`);
      return await res.json();
    } catch (err) {
      console.error("Failed to fetch map clusters:", err);
      throw err;
    }
  },

  async getProfile() {
    try {
      const res = await fetch(`${this.baseUrl}/profile`);
      return await res.json();
    } catch (err) {
      console.error("Failed to fetch profile:", err);
      throw err;
    }
  },

  async uploadDocument(file, documentType = "Medical Clearance", notes = "") {
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("document_type", documentType);
      formData.append("notes", notes);

      const res = await fetch(`${this.baseUrl}/documents/upload`, {
        method: "POST",
        body: formData
      });
      return await res.json();
    } catch (err) {
      console.error("Document upload failed:", err);
      throw err;
    }
  },

  async getAchievements() {
    try {
      const res = await fetch(`${this.baseUrl}/achievements`);
      return await res.json();
    } catch (err) {
      console.error("Failed to fetch achievements:", err);
      throw err;
    }
  },

  async shareAchievement(achievementId, platform = "twitter") {
    try {
      const res = await fetch(`${this.baseUrl}/achievements/share`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ achievement_id: achievementId, platform })
      });
      return await res.json();
    } catch (err) {
      console.error("Failed to share achievement:", err);
      throw err;
    }
  },

  async getDashboardRequests() {
    try {
      const res = await fetch(`${this.baseUrl}/dashboard/requests`);
      return await res.json();
    } catch (err) {
      console.error("Failed to fetch dashboard requests:", err);
      throw err;
    }
  },

  async updateSettings(settings) {
    try {
      const res = await fetch(`${this.baseUrl}/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings)
      });
      return await res.json();
    } catch (err) {
      console.error("Failed to update settings:", err);
      throw err;
    }
  }
};

window.BDCNApi = BDCNApi;
