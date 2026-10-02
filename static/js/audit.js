/**
 * static/js/audit.js — Event Handlers for HIPAA WORM Audit Log Viewer
 */

async function runCryptographicVerification() {
    const banner = document.getElementById('integrity-banner');
    const title = document.getElementById('integrity-title');
    const subtitle = document.getElementById('integrity-subtitle');
    const totalBadge = document.getElementById('total-records-badge');

    title.innerText = 'Verifying SHA-256 hash chaining...';

    try {
        const res = await BDCN_API.verifyAuditLedger();
        if (res.verified) {
            banner.className = 'alert alert-success d-flex justify-content-between align-items-center mb-4';
            title.innerText = '✅ Ledger Cryptographic Chain: VALID';
            subtitle.innerText = `Verified ${res.totalRecordsChecked} records. 0 hash collisions or tampering breaks detected.`;
        } else {
            banner.className = 'alert alert-danger d-flex justify-content-between align-items-center mb-4';
            title.innerText = '⚠️ Ledger Cryptographic Chain: COMPROMISED';
            subtitle.innerText = `Detected ${res.tamperedRecordsCount} tampered records!`;
        }
        totalBadge.innerText = `${res.totalRecordsChecked} Records Verified`;
    } catch (err) {
        banner.className = 'alert alert-danger d-flex justify-content-between align-items-center mb-4';
        title.innerText = 'Verification Error';
        subtitle.innerText = err.message;
    }
}

async function loadAuditTable() {
    try {
        const res = await BDCN_API.getAuditLogs();
        const tbody = document.getElementById('audit-tbody');
        if (!tbody || !res.auditLogs) return;

        let html = '';
        res.auditLogs.forEach(log => {
            html += `
                <tr>
                    <td><code>${log.auditId}</code></td>
                    <td><span class="badge bg-primary">${log.actionType}</span></td>
                    <td><small>${log.actorUserId}</small></td>
                    <td><span class="badge bg-light text-dark border">${log.resourceType}</span></td>
                    <td>
                        <small class="text-muted d-block font-monospace" style="font-size: 0.7rem;">Cur: ${log.payloadHashSha256.substring(0, 16)}...</small>
                        <small class="text-muted d-block font-monospace" style="font-size: 0.7rem;">Prv: ${log.previousHashSha256.substring(0, 16)}...</small>
                    </td>
                    <td><small class="text-muted">${log.timestamp}</small></td>
                </tr>
            `;
        });
        tbody.innerHTML = html;
    } catch (err) {
        console.error('Error refreshing audit ledger:', err);
    }
}
