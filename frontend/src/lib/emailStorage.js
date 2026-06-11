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

export async function fetchThreadMessages(threadId) {
	return emailJson(`/threads/${threadId}/messages`);
}

export async function archiveEmail(emailId) {
	return emailJson('/archive', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ email_id: emailId }),
	});
}
