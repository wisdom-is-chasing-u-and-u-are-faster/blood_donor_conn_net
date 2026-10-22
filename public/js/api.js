// BDCN Client-Side API Layer (ARCH-5065)
// Connects UI forms, buttons, and views to backend REST endpoints

const BDCN_API = {
  baseUrl: '/api/v1',

  async checkHealth() {
    try {
      const res = await fetch('/health');
      return await res.json();
    } catch (err) {
      console.error('Health check failed:', err);
      return { status: 'error', message: err.message };
    }
  },

  async loginSocial(provider) {
    try {
      const res = await fetch(`${this.baseUrl}/auth/social`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider })
      });
      const data = await res.json();
      if (res.ok) {
        BDCN_API.showToast(`Logged in successfully via ${provider.toUpperCase()}`, 'success');
        setTimeout(() => { window.location.href = 'dashboard.html'; }, 1000);
      } else {
        BDCN_API.showToast(data.message || 'Social login failed', 'danger');
      }
      return data;
    } catch (err) {
      console.error('Social login error:', err);
      BDCN_API.showToast('Network error during social authentication', 'danger');
    }
  },

  async getHotspots(radius = 50, bloodType = 'All') {
    try {
      const query = new URLSearchParams({ radius, blood_type: bloodType });
      const res = await fetch(`${this.baseUrl}/donors/hotspots?${query.toString()}`);
      return await res.json();
    } catch (err) {
      console.error('Failed to load donor hotspots:', err);
      return { total_clusters: 0, clusters: [] };
    }
  },

  async uploadDocument(formData) {
    try {
      const res = await fetch(`${this.baseUrl}/documents/upload`, {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      if (res.ok) {
        BDCN_API.showToast('Document uploaded successfully for administrator verification!', 'success');
        setTimeout(() => { window.location.href = 'dashboard.html'; }, 1500);
      } else {
        BDCN_API.showToast(data.message || 'Upload failed', 'danger');
      }
      return data;
    } catch (err) {
      console.error('Upload error:', err);
      BDCN_API.showToast('Network error during document upload', 'danger');
    }
  },

  async getVerifications() {
    try {
      const res = await fetch(`${this.baseUrl}/admin/verifications`);
      return await res.json();
    } catch (err) {
      console.error('Failed to fetch pending verifications:', err);
      return { total_pending: 0, items: [] };
    }
  },

  async reviewVerification(docId, action) {
    try {
      const res = await fetch(`${this.baseUrl}/admin/verifications/${docId}/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action })
      });
      const data = await res.json();
      if (res.ok) {
        BDCN_API.showToast(`Verification case ${action.toUpperCase()}ED successfully`, 'success');
      } else {
        BDCN_API.showToast(data.message || 'Action failed', 'danger');
      }
      return data;
    } catch (err) {
      console.error('Review action error:', err);
      BDCN_API.showToast('Network error processing review', 'danger');
    }
  },

  async getAuditLogs() {
    try {
      const res = await fetch(`${this.baseUrl}/audit/logs`);
      return await res.json();
    } catch (err) {
      console.error('Failed to fetch audit logs:', err);
      return { logs: [] };
    }
  },

  showToast(message, type = 'info') {
    let container = document.getElementById('bdcn-toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'bdcn-toast-container';
      container.style.cssText = 'position: fixed; bottom: 20px; right: 20px; z-index: 9999; display: flex; flex-direction: column; gap: 10px;';
      document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    const bgColor = type === 'success' ? '#2e7d32' : type === 'danger' ? '#c62828' : '#1565c0';
    toast.style.cssText = `background: ${bgColor}; color: #fff; padding: 12px 20px; border-radius: 6px; box-shadow: 0 4px 12px rgba(0,0,0,0.2); font-family: sans-serif; font-size: 14px; transition: opacity 0.3s ease;`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }
};

// Initialize interactive DOM listeners on page load
document.addEventListener('DOMContentLoaded', () => {
  // 1. Social Login Handlers
  document.querySelectorAll('.btn-google').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      BDCN_API.loginSocial('google');
    });
  });
  document.querySelectorAll('.btn-apple').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      BDCN_API.loginSocial('apple');
    });
  });
  document.querySelectorAll('.btn-facebook').forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      BDCN_API.loginSocial('facebook');
    });
  });

  // 2. Document Upload Form Handler
  const uploadForm = document.querySelector('#upload form');
  if (uploadForm) {
    uploadForm.onsubmit = async (e) => {
      e.preventDefault();
      const fileInput = uploadForm.querySelector('input[type="file"]');
      const docType = uploadForm.querySelector('select')?.value || 'Donor ID Card';
      const consent = uploadForm.querySelector('#consent')?.checked || false;

      if (!fileInput || !fileInput.files[0]) {
        BDCN_API.showToast('Please select a document file to upload.', 'danger');
        return;
      }
      if (!consent) {
        BDCN_API.showToast('Consent is required to submit documents for review.', 'danger');
        return;
      }

      const formData = new FormData();
      formData.append('document', fileInput.files[0]);
      formData.append('document_type', docType);
      formData.append('consent', consent);
      formData.append('user_email', 'current_user@bdcn.org');

      await BDCN_API.uploadDocument(formData);
    };
  }

  // 3. Map View Hotspot Population
  const mapPlaceholder = document.querySelector('.map-placeholder');
  if (mapPlaceholder) {
    BDCN_API.getHotspots().then(data => {
      if (data && data.clusters && data.clusters.length > 0) {
        let html = '<div style="padding: 16px; background: rgba(0,0,0,0.03); border-radius: 8px;">';
        html += '<h4 style="margin-top:0;">Clustered Donor Hotspots (Privacy Coarse Centroids)</h4>';
        html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px;">';
        data.clusters.forEach(c => {
          html += `
            <div style="background:#fff; border:1px solid #ddd; border-radius:6px; padding:12px; box-shadow:0 1px 3px rgba(0,0,0,0.05);">
              <strong style="color:#C8102E;">📍 ${c.district}</strong>
              <div style="font-size:12px; color:#666; margin:4px 0;">Cluster Center: [${c.coarse_latitude}, ${c.coarse_longitude}]</div>
              <div style="font-size:13px; font-weight:bold;">👥 ${c.donor_count} Active Donors</div>
              <div style="font-size:12px; color:#444;">Types: ${Array.isArray(c.primary_blood_types) ? c.primary_blood_types.join(', ') : c.primary_blood_types}</div>
              <div style="font-size:11px; margin-top:4px; color:${c.urgency_level === 'High' ? '#c62828' : '#2e7d32'};">Urgency: ${c.urgency_level}</div>
            </div>`;
        });
        html += '</div></div>';
        mapPlaceholder.innerHTML = html;
      }
    });
  }

  // 4. Admin Review Actions (Approve / Reject buttons)
  document.querySelectorAll('.doc-list-item').forEach((item, idx) => {
    const approveBtn = item.querySelector('.btn-primary');
    const rejectBtn = item.querySelector('.btn-outline');
    const viewBtn = item.querySelector('.btn-secondary');

    if (approveBtn) {
      approveBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        const docId = item.dataset.docId || `doc-10${idx + 1}`;
        await BDCN_API.reviewVerification(docId, 'approve');
        approveBtn.disabled = true;
        approveBtn.textContent = 'Approved ✓';
        if (rejectBtn) rejectBtn.remove();
      });
    }

    if (rejectBtn) {
      rejectBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        const docId = item.dataset.docId || `doc-10${idx + 1}`;
        await BDCN_API.reviewVerification(docId, 'reject');
        rejectBtn.disabled = true;
        rejectBtn.textContent = 'Rejected ✗';
        if (approveBtn) approveBtn.remove();
      });
    }

    if (viewBtn) {
      viewBtn.addEventListener('click', (e) => {
        e.preventDefault();
        BDCN_API.showToast('Displaying secure encrypted document preview...', 'info');
      });
    }
  });
});
