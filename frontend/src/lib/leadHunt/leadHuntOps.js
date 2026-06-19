/** Ops API — автономный поиск лидов (lead hunt). */

const API = '';

export async function fetchLeadHuntConfig() {
	const r = await fetch(`${API}/api/ops/lead-hunt/config`);
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}

export async function saveLeadHuntConfig(cfg) {
	const r = await fetch(`${API}/api/ops/lead-hunt/config`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(cfg)
	});
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}

export async function fetchLeadHuntStatus() {
	const r = await fetch(`${API}/api/ops/lead-hunt/status`);
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}

export async function fetchLeadHuntIcp() {
	const r = await fetch(`${API}/api/ops/lead-hunt/icp`);
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}

export async function refreshLeadHuntIcp() {
	const r = await fetch(`${API}/api/ops/lead-hunt/icp/refresh`, { method: 'POST' });
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}

export async function runLeadHunt() {
	const r = await fetch(`${API}/api/ops/lead-hunt/run`, { method: 'POST' });
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}

export async function fetchLeadHuntCandidates(status = 'pending') {
	const r = await fetch(`${API}/api/ops/lead-hunt/candidates?status=${encodeURIComponent(status)}`);
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}

export async function approveLeadHuntCandidate(id) {
	const r = await fetch(`${API}/api/ops/lead-hunt/candidates/${id}/approve`, { method: 'POST' });
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}

export async function rejectLeadHuntCandidate(id, note = '') {
	const r = await fetch(`${API}/api/ops/lead-hunt/candidates/${id}/reject`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ note })
	});
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}

export async function fetchLeadHuntNotifications(unreadOnly = false) {
	const q = unreadOnly ? '?unread_only=true' : '';
	const r = await fetch(`${API}/api/ops/lead-hunt/notifications${q}`);
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}

export async function markLeadHuntNotificationsRead(all = true, notificationId = null) {
	const r = await fetch(`${API}/api/ops/lead-hunt/notifications/read`, {
		method: 'PATCH',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(all ? { all: true } : { notification_id: notificationId })
	});
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}

export function companyLabel(c) {
	const co = c?.company || c;
	return co?.name || co?.name_short || co?.company || '—';
}
