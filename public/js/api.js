/**
 * Blood Donor Connection Network (BDCN)
 * Client-Side API Integration Layer
 */

const API_BASE = '/api/v1';

const apiClient = {
  // Health check
  async checkHealth() {
    try {
      const res = await fetch('/health');
      return await res.json();
    } catch (err) {
      console.error('Health check failed:', err);
      return { status: 'error', error: err.message };
    }
  },

  // Social Authentication
  async authenticateSocial(provider) {
    try {
      const res = await fetch(`${API_BASE}/auth/social/${provider}`);
      return await res.json();
    } catch (err) {
      console.error(`Social auth failed for ${provider}:`, err);
      throw err;
    }
  },

  // Hotspots proximity query
  async getHotspots(radius = 50, bloodType = 'All') {
    try {
      const res = await fetch(`${API_BASE}/donors/hotspots?radius=${radius}&blood_type=${encodeURIComponent(bloodType)}`);
      return await res.json();
    } catch (err) {
      console.error('Failed to fetch donor hotspots:', err);
      return { hotspots: [] };
    }
  },

  // Fallback District List
  async getDistricts() {
    try {
      const res = await fetch(`${API_BASE}/districts`);
      return await res.json();
    } catch (err) {
      console.error('Failed to fetch districts:', err);
      return { districts: [] };
    }
  },

  // Create blood donation request
  async createRequest(formData) {
    try {
      const res = await fetch(`${API_BASE}/requests`, {
        method: 'POST',
        body: formData
      });
      return await res.json();
    } catch (err) {
      console.error('Failed to create blood request:', err);
      throw err;
    }
  },

  // Get active blood requests for donors
  async getRequests(status = 'All') {
    try {
      const res = await fetch(`${API_BASE}/requests?status=${encodeURIComponent(status)}`);
      return await res.json();
    } catch (err) {
      console.error('Failed to fetch active requests:', err);
      return { requests: [] };
    }
  },

  // Gamification & Badges
  async getGamificationStats() {
    try {
      const res = await fetch(`${API_BASE}/donor/gamification`);
      return await res.json();
    } catch (err) {
      console.error('Failed to fetch gamification stats:', err);
      return null;
    }
  },

  // Social badge sharing
  async shareBadge(badgeName, platform = 'twitter') {
    try {
      const res = await fetch(`${API_BASE}/donor/share-badge`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ badge_name: badgeName, platform: platform })
      });
      return await res.json();
    } catch (err) {
      console.error(`Failed to share badge ${badgeName}:`, err);
      throw err;
    }
  }
};

// Auto-wire form handlers upon DOM readiness
document.addEventListener('DOMContentLoaded', () => {
  // Wire Recipient Request Form if present
  const requestForm = document.querySelector('form[action*="recipient"]') || document.querySelector('#recipient-request-form');
  if (requestForm) {
    requestForm.addEventListener('submit', async (e) => {
      // Normal browser submit works, or API enhancement
      console.log('Blood request submission initiated');
    });
  }

  // Wire Map Filter Search Button if present
  const searchMapBtn = document.querySelector('#donor-discovery-map button') || document.querySelector('.btn-search-hotspots');
  if (searchMapBtn) {
    searchMapBtn.addEventListener('click', async (e) => {
      const radiusSelect = document.querySelector('#radius-filter');
      const bloodGroupSelect = document.querySelector('#map-blood-group');
      const radius = radiusSelect ? radiusSelect.value : 50;
      const bloodType = bloodGroupSelect ? bloodGroupSelect.value : 'All';
      console.log(`Filtering hotspots with radius=${radius}km, blood_type=${bloodType}`);
      const data = await apiClient.getHotspots(radius, bloodType);
      console.log('Hotspots received:', data);
    });
  }

  // Wire Badge Share Buttons if present
  const shareButtons = document.querySelectorAll('.btn-share-badge, button.btn-ghost');
  shareButtons.forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const badgeTitle = btn.closest('.card')?.querySelector('h3')?.innerText || 'Achievement';
      console.log(`Sharing badge: ${badgeTitle}`);
      try {
        await apiClient.shareBadge(badgeTitle);
        btn.innerText = 'Shared!';
        setTimeout(() => { btn.innerText = 'Share'; }, 3000);
      } catch (err) {
        console.error('Share error:', err);
      }
    });
  });
});

window.apiClient = apiClient;
