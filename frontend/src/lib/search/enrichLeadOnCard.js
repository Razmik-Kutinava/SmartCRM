/** One-click enrich на карточке лида → enrich-lead → PATCH. */
import { apiPost } from '$lib/api.js';
import { apiUpdateLead } from '$lib/leadsStorage.js';
import { enrichedToLeadPatch, enrichResultToLeadPatch, leadToEnrichPayload } from '$lib/search/enrichLeadApply.js';

export async function enrichLeadOnCard(lead, { force = false } = {}) {
	if (!lead?.id) throw new Error('Нет лида');
	const payload = leadToEnrichPayload(lead);
	if (!payload?.company?.trim()) throw new Error('Укажите название компании');

	const r = await apiPost('/api/search/enrich-lead', { lead: payload, force });
	const data = await r.json();
	if (!r.ok || data.ok === false) {
		throw new Error(data.detail || data.error || `HTTP ${r.status}`);
	}

	const patch = enrichResultToLeadPatch(data, lead);
	if (!Object.keys(patch).length) {
		return { data, patch: {}, applied: false };
	}

	await apiUpdateLead(lead.id, patch);
	return { data, patch, applied: true };
}
