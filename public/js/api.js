/**
 * QuantumLeap Investment Portal — Client API Layer
 * Connects UI views directly to backend REST endpoints defined in api_contract.json
 */

const QuantumAPI = {
  baseUrl: '',

  async request(endpoint, options = {}) {
    const defaultHeaders = {
      'Content-Type': 'application/json',
      'Accept': 'application/json'
    };

    const config = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers
      }
    };

    try {
      const response = await fetch(endpoint, config);
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.message || data.error || `HTTP error ${response.status}`);
      }
      return data;
    } catch (err) {
      console.error(`[QuantumAPI] Error on ${endpoint}:`, err);
      throw err;
    }
  },

  // Health Probe
  async getHealth() {
    return this.request('/health', { method: 'GET' });
  },

  // Auth Endpoints
  async register(username, email, password, full_name) {
    return this.request('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, email, password, full_name })
    });
  },

  async login(username, password) {
    return this.request('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
  },

  async logout() {
    return this.request('/api/v1/auth/logout', { method: 'POST' });
  },

  // Dashboard & Accounts
  async getDashboard() {
    return this.request('/api/v1/dashboard', { method: 'GET' });
  },

  async getAccounts() {
    return this.request('/api/v1/accounts', { method: 'GET' });
  },

  async getAccount(accountId) {
    return this.request(`/api/v1/accounts/${accountId}`, { method: 'GET' });
  },

  async getTransactions(accountId) {
    return this.request(`/api/v1/accounts/${accountId}/transactions`, { method: 'GET' });
  },

  // Inter-Account Fund Transfers
  async transferFunds(fromAccountId, toAccountId, amount, memo = '') {
    return this.request('/api/v1/transfers', {
      method: 'POST',
      body: JSON.stringify({
        from_account_id: parseInt(fromAccountId),
        to_account_id: parseInt(toAccountId),
        amount: parseFloat(amount),
        memo: memo
      })
    });
  },

  // Support & Contact
  async getSupport() {
    return this.request('/api/v1/support', { method: 'GET' });
  },

  async submitContact(name, email, message) {
    return this.request('/api/v1/contact', {
      method: 'POST',
      body: JSON.stringify({ name, email, message })
    });
  }
};

// Automatic interactive form handling and DOM listeners
document.addEventListener('DOMContentLoaded', () => {
  // Transfer Form handler
  const transferForm = document.getElementById('transfer-form');
  if (transferForm) {
    transferForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const statusEl = document.getElementById('transfer-status');
      const fromAcc = document.getElementById('from_account_id').value;
      const toAcc = document.getElementById('to_account_id').value;
      const amount = document.getElementById('amount').value;
      const memo = document.getElementById('memo') ? document.getElementById('memo').value : '';

      if (fromAcc === toAcc) {
        if (statusEl) {
          statusEl.textContent = 'Cannot transfer to the same account.';
          statusEl.className = 'alert alert-error';
          statusEl.style.display = 'block';
        }
        return;
      }

      try {
        if (statusEl) {
          statusEl.textContent = 'Processing transfer...';
          statusEl.className = 'alert alert-info';
          statusEl.style.display = 'block';
        }
        const res = await QuantumAPI.transferFunds(fromAcc, toAcc, amount, memo);
        if (statusEl) {
          statusEl.textContent = res.message || 'Transfer completed successfully!';
          statusEl.className = 'alert alert-success';
        }
        setTimeout(() => {
          window.location.href = '/dashboard';
        }, 1200);
      } catch (err) {
        if (statusEl) {
          statusEl.textContent = err.message || 'Transfer failed.';
          statusEl.className = 'alert alert-error';
        }
      }
    });
  }

  // Contact Form handler
  const contactForm = document.getElementById('contact-form');
  if (contactForm) {
    contactForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = document.getElementById('name').value;
      const email = document.getElementById('email').value;
      const message = document.getElementById('message').value;
      const statusEl = document.getElementById('contact-status');

      try {
        if (statusEl) {
          statusEl.textContent = 'Sending message...';
          statusEl.className = 'alert alert-info';
          statusEl.style.display = 'block';
        }
        const res = await QuantumAPI.submitContact(name, email, message);
        if (statusEl) {
          statusEl.textContent = res.message || 'Thank you! Your message has been received.';
          statusEl.className = 'alert alert-success';
        }
        contactForm.reset();
      } catch (err) {
        if (statusEl) {
          statusEl.textContent = err.message || 'Failed to send message.';
          statusEl.className = 'alert alert-error';
        }
      }
    });
  }
});

if (typeof window !== 'undefined') {
  window.QuantumAPI = QuantumAPI;
}
