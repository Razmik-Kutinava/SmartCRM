import { apiFetch } from './api.js';

const EMAIL_API = '/api/email';

async function emailJson(path, options = {}) {
	const r = await apiFetch(`${EMAIL_API}${path}`, options);
	if (!r.ok) {
		const text = await r.text().catch(() => '');
		throw new Error(`${r.status} ${text}`);
	}
	return r.json();
}

export async function fetchEmailAccounts() {
	return emailJson('/accounts');
}

export async function connectEmailAccount(body) {
	return emailJson('/accounts/connect', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body),
	});
}

export async function syncEmailAccount(accountId) {
	return emailJson(`/accounts/${accountId}/sync`, { method: 'POST' });
}

export async function deleteEmailAccount(accountId, purge = true) {
	return emailJson(`/accounts/${accountId}?purge=${purge}`, { method: 'DELETE' });
}

export async function syncAllEmailAccounts() {
	return emailJson('/sync', { method: 'POST' });
}

export async function fetchLeadEmails(leadId) {
	const r = await apiFetch(`/api/leads/${leadId}/email`);
	if (!r.ok) throw new Error('Ошибка загрузки писем лида');
	return r.json();
}

export async function sendEmail(body) {
	return emailJson('/send', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body),
	});
}

export async function sendLeadEmail(body) {
	return sendEmail(body);
}

export async function replyToEmail(body) {
	return emailJson('/reply', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body),
	});
}

export async function createCampaign(body) {
	return emailJson('/campaigns', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body),
	});
}

export async function previewCampaignSegment(segment) {
	return emailJson('/campaigns/segment-preview', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ segment }),
	});
}

export async function previewCampaignLlm(body) {
	return emailJson('/campaigns/preview-llm', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body),
	});
}

export async function testCampaignSend(body) {
	return emailJson('/campaigns/test-send', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body),
	});
}

export async function startNurtureLlm(body) {
	return emailJson('/nurture/start-llm', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body),
	});
}

export async function previewNurtureLlm(body) {
	return emailJson('/nurture/preview-llm', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body),
	});
}

export async function testNurtureSend(body) {
	return emailJson('/nurture/test-send', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body),
	});
}

export async function startNurtureChain(leadId, accountId) {
	return emailJson('/nurture/start', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ lead_id: leadId, account_id: accountId }),
	});
}

export async function fetchNurtureChains(leadId) {
	const q = leadId ? `?lead_id=${leadId}` : '';
	return emailJson(`/nurture/chains${q}`);
}

export async function relinkOrphanEmails(accountId) {
	const q = accountId ? `?account_id=${accountId}` : '';
	return emailJson(`/relink-orphans${q}`, { method: 'POST' });
}

export async function fetchEmailCampaigns() {
	return emailJson('/campaigns');
}

export async function bindEmailToLead(body) {
	return emailJson('/bind-lead', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body),
	});
}

export async function fetchEmailThreads(params = {}) {
	const query = new URLSearchParams(params).toString();
	return emailJson(`/threads?${query}`);
}

export async function fetchEmailSyncStatus() {
	return emailJson('/sync/status');
}

export async function startEmailBackfill(reset = false) {
	const q = reset ? '?reset=true' : '';
	return emailJson(`/backfill/start${q}`, { method: 'POST' });
}

export async function pauseEmailBackfill() {
	return emailJson('/backfill/pause', { method: 'POST' });
}

export async function fetchEmailConfigStatus() {
	return emailJson('/config/status');
}

export async function fetchThreadMessages(threadId) {
	return emailJson(`/threads/${threadId}/messages`);
}

export async function analyzeEmailThread(threadId, body = {}) {
	return emailJson(`/threads/${threadId}/analyze`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body),
	});
}

export async function archiveEmail(emailId) {
	return emailJson('/archive', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ email_id: emailId }),
	});
}
