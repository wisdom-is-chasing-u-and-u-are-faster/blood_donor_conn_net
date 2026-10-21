/**
 * Blood Donor Connection Network (BDCN) Client-Side API Module
 * Wires UI components, forms, and interactive views directly to backend REST endpoints.
 */

const API_BASE = '/api/v1';

const api = {
  auth: {
    async social(provider, email = '', name = '') {
      const res = await fetch(`${API_BASE}/auth/social`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, email, name })
      });
      return await res.json();
    },
    async me() {
      const res = await fetch(`${API_BASE}/auth/me`);
      return await res.json();
    },
    async logout() {
      const res = await fetch(`${API_BASE}/auth/logout`, { method: 'POST' });
      return await res.json();
    }
  },

  donors: {
    async list(radius = 50, bloodType = 'All') {
      const res = await fetch(`${API_BASE}/donors?radius=${encodeURIComponent(radius)}&blood_type=${encodeURIComponent(bloodType)}`);
      return await res.json();
    },
    async getHotspots(radius = 50, bloodType = 'All') {
      const res = await fetch(`${API_BASE}/donors/hotspots?radius=${encodeURIComponent(radius)}&blood_type=${encodeURIComponent(bloodType)}`);
      return await res.json();
    },
    async saveProfile(profileData) {
      const res = await fetch(`${API_BASE}/donors/profile`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profileData)
      });
      return await res.json();
    },
    async share(badgeName, platform = 'twitter') {
      const res = await fetch(`${API_BASE}/donors/share`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ badge_name: badgeName, platform })
      });
      return await res.json();
    }
  },

  requests: {
    async list(status = 'All', district = 'All') {
      const res = await fetch(`${API_BASE}/requests?status=${encodeURIComponent(status)}&district=${encodeURIComponent(district)}`);
      return await res.json();
    },
    async create(data) {
      let options = {};
      if (data instanceof FormData) {
        options = {
          method: 'POST',
          body: data
        };
      } else {
        options = {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        };
      }
      const res = await fetch(`${API_BASE}/requests`, options);
      return await res.json();
    }
  },

  admin: {
    async verify(requestId, action, notes = '') {
      const res = await fetch(`${API_BASE}/admin/requests/${requestId}/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, notes })
      });
      return await res.json();
    }
  },

  notifications: {
    async list() {
      const res = await fetch(`${API_BASE}/notifications`);
      return await res.json();
    }
  }
};

// Initialize interactive DOM event listeners when document is ready
document.addEventListener('DOMContentLoaded', () => {
  // Proximity slider listener
  const proximitySlider = document.getElementById('proximity-slider');
  const proximityValue = document.getElementById('proximity-value');
  if (proximitySlider && proximityValue) {
    proximitySlider.addEventListener('input', (e) => {
      proximityValue.textContent = `${e.target.value} km`;
    });
    proximitySlider.addEventListener('change', async (e) => {
      try {
        const hotspots = await api.donors.getHotspots(e.target.value);
        console.log('Updated donor hotspots for radius', e.target.value, hotspots);
      } catch (err) {
        console.error('Failed to load hotspots', err);
      }
    });
  }

  // Blood Request form submission wiring
  const requestForm = document.querySelector('#request-form form') || document.querySelector('form#request-form');
  if (requestForm) {
    requestForm.addEventListener('submit', async (e) => {
      // Allow standard form submission if targeting flask route or handle async
      const submitBtn = requestForm.querySelector('button[type="submit"]');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Submitting Blood Request...';
      }
    });
  }

  // Profile management form submission wiring
  const profileForm = document.querySelector('#profile-management form');
  if (profileForm) {
    profileForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const formData = {
        full_name: document.getElementById('full-name')?.value || '',
        email: document.getElementById('email')?.value || '',
        phone: document.getElementById('phone')?.value || '',
        blood_type: document.getElementById('blood-type-profile')?.value || 'O+',
        location: document.getElementById('location')?.value || 'Downtown'
      };
      try {
        const result = await api.donors.saveProfile(formData);
        alert(result.message || 'Profile saved successfully!');
      } catch (err) {
        alert('Failed to save profile: ' + err.message);
      }
    });
  }

  // Social Auth button bindings
  const socialButtons = document.querySelectorAll('.social-login-btn, [data-social-provider]');
  socialButtons.forEach(btn => {
    btn.addEventListener('click', async (e) => {
      const provider = btn.getAttribute('data-social-provider') || btn.innerText.toLowerCase();
      if (provider.includes('google')) {
        window.location.href = '/login/social/google';
      } else if (provider.includes('apple')) {
        window.location.href = '/login/social/apple';
      } else if (provider.includes('facebook')) {
        window.location.href = '/login/social/facebook';
      }
    });
  });
});

window.bdcnApi = api;
