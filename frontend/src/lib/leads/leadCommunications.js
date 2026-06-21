/** Лог касаний лида: звонок, встреча, письмо (apiFetch + X-API-Key). */
import { apiFetch, apiPost } from '$lib/api.js';
import { ACTIVITY_TYPES, activityTypeLabel, communicationTypeLabel } from '$lib/leads/leadActivityTypes.js';

export { ACTIVITY_TYPES, activityTypeLabel, communicationTypeLabel };

/** @deprecated */
export const COMMUNICATION_TYPES = ACTIVITY_TYPES;

export async function fetchLeadCommunications(leadId, limit = 40) {
	const n = Number(leadId);
	if (!leadId || Number.isNaN(n)) return [];
	const r = await apiFetch(`/api/leads/${n}/communications?limit=${limit}`);
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}

export async function createLeadCommunication(
	leadId,
	{ communicationType, content, actor = 'Менеджер', occurredAt = null },
) {
	const text = String(content ?? '').trim();
	if (!text) throw new Error('Пустое описание');
	const body = { communicationType, content: text, actor };
	if (occurredAt) body.occurredAt = occurredAt;
	const r = await apiPost(`/api/leads/${leadId}/communications`, body);
	if (!r.ok) throw new Error(await r.text());
	return r.json();
}
