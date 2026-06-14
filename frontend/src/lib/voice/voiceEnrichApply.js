/** Применить enrich из voice modal → PATCH карточки лида. */
import { apiUpdateLead } from '$lib/leadsStorage.js';
import { enrichedToLeadPatch } from '$lib/search/enrichLeadApply.js';

/**
 * @param {Record<string, unknown>} modal
 */
export async function applyVoiceEnrich(modal) {
	const payload = modal?.payload || {};
	const leadId = payload.lead_id ?? modal?.slots?.lead_id;
	if (!leadId) throw new Error('Нет lead_id для обогащения');

	const patch = payload.patch_preview && Object.keys(payload.patch_preview).length
		? payload.patch_preview
		: enrichedToLeadPatch(/** @type {Record<string, string>} */ (payload.enriched || {}));

	if (!Object.keys(patch).length) {
		return { applied: false, patch: {} };
	}

	await apiUpdateLead(Number(leadId), patch);
	return { applied: true, patch };
}
