/** Комментарии, аудит и касания карточки лида (через apiFetch + X-API-Key). */
import { apiFetch, apiPost } from '$lib/api.js';

export async function loadLeadCardActivity(leadId) {
	const n = Number(leadId);
	if (!leadId || Number.isNaN(n)) {
		return { comments: [], audit: [], communications: [] };
	}
	try {
		const [cr, ra, rc] = await Promise.all([
			apiFetch(`/api/leads/${n}/comments?limit=40`),
			apiFetch(`/api/leads/${n}/audit?limit=35`),
			apiFetch(`/api/leads/${n}/communications?limit=40`),
		]);
		return {
			comments: cr.ok ? await cr.json() : [],
			audit: ra.ok ? await ra.json() : [],
			communications: rc.ok ? await rc.json() : [],
		};
	} catch {
		return { comments: [], audit: [], communications: [] };
	}
}

export async function postLeadComment(leadId, body, author = 'Менеджер') {
	const r = await apiPost(`/api/leads/${leadId}/comments`, { body: body.trim(), author });
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}

export async function postLeadCommunication(leadId, { communicationType, content, actor = 'Менеджер' }) {
	const r = await apiPost(`/api/leads/${leadId}/communications`, {
		communicationType,
		content: content.trim(),
		actor,
	});
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}
