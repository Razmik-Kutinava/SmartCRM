/**
 * Сырьё на карточке лида → POST /api/leads/{id}/raw-inbox
 */
import { apiPost } from '../api.js';

/**
 * @param {number|string} leadId
 * @param {string} text
 * @param {{ ingestRag?: boolean }} [opts]
 */
export async function submitRawInbox(leadId, text, opts = {}) {
	const ingest_rag = opts.ingestRag !== false;
	const res = await apiPost(`/api/leads/${leadId}/raw-inbox`, {
		text,
		ingest_rag
	});
	const body = await res.json().catch(() => ({}));
	if (!res.ok) {
		const detail = body?.detail || res.statusText || 'Ошибка сырья';
		throw new Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
	}
	return body;
}

/** @param {Record<string, any>|null|undefined} lead */
export function rawInboxFromLead(lead) {
	const checko = lead?.checko || {};
	const inbox = checko?.analyses?.raw_inbox || {};
	return {
		brief: String(inbox.brief || '').trim(),
		chunks: Array.isArray(inbox.chunks) ? inbox.chunks : []
	};
}
