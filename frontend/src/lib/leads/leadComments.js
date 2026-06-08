/** Комментарии к лиду (apiFetch + X-API-Key). */
import { apiFetch, apiPost } from '$lib/api.js';

export async function fetchLeadComments(leadId, limit = 40) {
	const n = Number(leadId);
	if (!leadId || Number.isNaN(n)) return [];
	const r = await apiFetch(`/api/leads/${n}/comments?limit=${limit}`);
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}

export async function createLeadComment(leadId, body, author = 'Менеджер') {
	const text = String(body ?? '').trim();
	if (!text) throw new Error('Пустой комментарий');
	const r = await apiPost(`/api/leads/${leadId}/comments`, { body: text, author });
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}
