/** Ф3: API сокращения черновика. */
import { apiPost } from '$lib/api.js';

/**
 * @param {{ subject?: string, body?: string }} draft
 * @returns {Promise<{ subject: string, body: string }>}
 */
export async function reviseVoiceDraft(draft) {
	const r = await apiPost('/api/voice/revise-draft', {
		subject: draft.subject || '',
		body: draft.body || '',
	});
	const data = await r.json();
	if (!r.ok) {
		throw new Error(data.detail || data.error || `HTTP ${r.status}`);
	}
	return {
		subject: String(data.subject || draft.subject || ''),
		body: String(data.body || ''),
	};
}
