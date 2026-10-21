/**
 * Blood Donor Connection Network — Client-Side API & Event Wiring Module
 * Connects frontend mockups and UI forms directly to REST endpoints in api_contract.json.
 */

const API_BASE = '/api/v1';

const BDCN_API = {
  // Authentication
  async socialLogin(provider, email = null, name = null, role = 'donor') {
    const res = await fetch(`${API_BASE}/auth/social`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        provider,
        token: 'mock-oauth-token-' + Date.now(),
        email: email || `${provider.toLowerCase()}.user@example.com`,
        name: name || `${provider} User`,
        role
      })
    });
    return res.json();
  },

  async emailLogin(email, password, role = 'donor') {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, role })
    });
    return res.json();
  },

  // Donor Profile
  async getDonorProfile() {
    const res = await fetch(`${API_BASE}/donors/profile`);
    return res.json();
  },

  async updateDonorProfile(profileData) {
    const res = await fetch(`${API_BASE}/donors/profile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profileData)
    });
    return res.json();
  },

  // Recipient Discovery & Privacy-Preserving Hotspots
  async searchDonors(bloodType = 'Any', location = '') {
    const params = new URLSearchParams();
    if (bloodType && bloodType !== 'Any') params.append('blood_type', bloodType);
    if (location) params.append('location', location);
    const res = await fetch(`${API_BASE}/donors/search?${params.toString()}`);
    return res.json();
  },

  async getHotspots() {
    const res = await fetch(`${API_BASE}/donors/hotspots`);
    return res.json();
  },

  // Connection Requests & Medical Necessity Documents
  async submitRequest(requestData) {
    const res = await fetch(`${API_BASE}/requests`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestData)
    });
    return res.json();
  },

  async getRequests() {
    const res = await fetch(`${API_BASE}/requests`);
    return res.json();
  },

  async getRequestDetails(requestId) {
    const res = await fetch(`${API_BASE}/requests/${requestId}`);
    return res.json();
  },

  // District Admin Verification & 2-Hour Reminders
  async verifyRequest(requestId, action, notes = '') {
    const res = await fetch(`${API_BASE}/admin/requests/${requestId}/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, notes })
    });
    return res.json();
  },

  async getPendingRequests() {
    const res = await fetch(`${API_BASE}/admin/requests/pending`);
    return res.json();
  },

  // Notifications
  async getNotifications() {
    const res = await fetch(`${API_BASE}/notifications`);
    return res.json();
  }
};

// Wire Interactive UI Elements on Page Load
document.addEventListener('DOMContentLoaded', () => {
  // 1. Login Page Wiring
  const googleBtn = document.getElementById('btn-login-google');
  if (googleBtn) {
    googleBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      const user = await BDCN_API.socialLogin('Google');
      alert(`Authenticated with Google as ${user.name} (${user.role})`);
      window.location.href = '/donor-dashboard';
    });
  }

  const appleBtn = document.getElementById('btn-login-apple');
  if (appleBtn) {
    appleBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      const user = await BDCN_API.socialLogin('Apple');
      alert(`Authenticated with Apple as ${user.name} (${user.role})`);
      window.location.href = '/donor-dashboard';
    });
  }

  const facebookBtn = document.getElementById('btn-login-facebook');
  if (facebookBtn) {
    facebookBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      const user = await BDCN_API.socialLogin('Facebook');
      alert(`Authenticated with Facebook as ${user.name} (${user.role})`);
      window.location.href = '/donor-dashboard';
    });
  }

  const loginForm = document.getElementById('form-login');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('email')?.value || 'donor@example.com';
      const password = document.getElementById('password')?.value || 'secret';
      const user = await BDCN_API.emailLogin(email, password);
      alert(`Signed in as ${user.email}`);
      window.location.href = '/donor-dashboard';
    });
  }

  // 2. Donor Dashboard Wiring
  const donorProfileForm = document.getElementById('form-donor-profile');
  if (donorProfileForm) {
    // Populate existing profile
    BDCN_API.getDonorProfile().then((data) => {
      if (data && data.name) {
        const nameInput = document.getElementById('donor-name');
        if (nameInput) nameInput.value = data.name;
        const bloodSelect = document.getElementById('blood-type');
        if (bloodSelect && data.blood_type) bloodSelect.value = data.blood_type;
        const locInput = document.getElementById('donor-location');
        if (locInput && data.location) locInput.value = data.location;
      }
    });

    donorProfileForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const bloodType = document.getElementById('blood-type')?.value;
      const location = document.getElementById('donor-location')?.value;
      const available = document.getElementById('donor-availability') ? document.getElementById('donor-availability').checked : true;
      const res = await BDCN_API.updateDonorProfile({ blood_type: bloodType, location, available });
      alert('Donor profile updated successfully!');
    });
  }

  // 3. Recipient Search & Map Hotspots Wiring
  const bloodFilter = document.getElementById('search-blood-type');
  const mapContainer = document.querySelector('.map-container');
  if (bloodFilter && mapContainer) {
    const renderHotspots = async () => {
      const selected = bloodFilter.value;
      const data = await BDCN_API.getHotspots();
      const filtered = selected === 'Any' 
        ? data.hotspots 
        : (data.hotspots || []).filter(h => h.blood_types.includes(selected));

      let html = '<div class="hotspots-grid" style="display:flex; flex-direction:column; gap:12px; margin-top:16px;">';
      if (filtered && filtered.length > 0) {
        filtered.forEach(h => {
          html += `
            <div class="card" style="padding:12px; border-left:4px solid var(--primary-color);">
              <strong>${h.district}</strong>: ${h.donor_count} Donors Available (Masked centroid: ${h.latitude}, ${h.longitude})
              <div class="text-color-light">Types: ${h.blood_types}</div>
            </div>`;
        });
      } else {
        html += '<p class="text-color-light">No donor clusters found for selected blood type.</p>';
      }
      html += '</div>';
      mapContainer.innerHTML = html;
    };

    bloodFilter.addEventListener('change', renderHotspots);
    renderHotspots();
  }

  // 4. Request Form Wiring
  const requestForm = document.getElementById('form-request-connection');
  if (requestForm) {
    requestForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const message = document.getElementById('request-message')?.value || '';
      const fileInput = document.getElementById('medical-doc');
      const docName = fileInput?.files?.[0]?.name || 'hospital_letter.pdf';
      const payload = {
        recipient_id: 'REC-9876',
        blood_type: 'O-',
        location: 'San Francisco, CA',
        message,
        document_name: docName,
        document_base64: 'bW9jay1kb2N1bWVudC1jb250ZW50'
      };
      const res = await BDCN_API.submitRequest(payload);
      alert(`Request ${res.request_id} submitted for administrator review!`);
      window.location.href = '/admin-dashboard';
    });
  }

  // 5. Admin Dashboard Wiring
  const adminTableBody = document.getElementById('admin-requests-tbody');
  if (adminTableBody) {
    BDCN_API.getPendingRequests().then((data) => {
      if (data && data.requests) {
        let rows = '';
        data.requests.forEach(req => {
          const isWarning = req.reminder_active || req.hours_pending >= 2;
          rows += `
            <tr class="${isWarning ? 'alert-warning' : ''}">
              <td>${req.request_id} ${isWarning ? '<span style="color:var(--danger-color); font-weight:bold;">[2h+ ALERT]</span>' : ''}</td>
              <td>${req.submitted_at} (${req.hours_pending}h ago)</td>
              <td><span class="badge ${req.status === 'Approved' ? 'badge-success' : 'badge-warning'}">${req.status}</span></td>
              <td><a href="/admin-request-details?id=${req.request_id}" class="btn btn-secondary">Review</a></td>
            </tr>`;
        });
        adminTableBody.innerHTML = rows;
      }
    });
  }

  // 6. Admin Request Details Wiring
  const approveBtn = document.getElementById('btn-approve-request');
  const rejectBtn = document.getElementById('btn-reject-request');
  const requestId = new URLSearchParams(window.location.search).get('id') || 'REQ-10234';

  if (approveBtn) {
    approveBtn.addEventListener('click', async () => {
      const res = await BDCN_API.verifyRequest(requestId, 'Approve', 'Verified medical certificate valid.');
      alert(`Request ${requestId} Approved. Notification sent to recipient.`);
      window.location.href = '/admin-dashboard';
    });
  }

  if (rejectBtn) {
    rejectBtn.addEventListener('click', async () => {
      const res = await BDCN_API.verifyRequest(requestId, 'Reject', 'Insufficient medical necessity proof.');
      alert(`Request ${requestId} Rejected.`);
      window.location.href = '/admin-dashboard';
    });
  }
});
