/** Импорт lookalike-кандидатов после approve в voice modal. */
import { apiPost } from '$lib/api.js';

/**
 * @param {Array<Record<string, unknown>>} similarLeads
 * @returns {Promise<{ count: number, created: unknown[], skipped: unknown[] }>}
 */
export async function importLookalikeLeads(similarLeads) {
	if (!Array.isArray(similarLeads) || similarLeads.length === 0) {
		throw new Error('Нет кандидатов для импорта');
	}
	const leads = similarLeads.slice(0, 20).map((row) => ({
		company: String(row.company || '').trim(),
		inn: row.inn ? String(row.inn) : null,
		city: row.city ? String(row.city) : '—',
		industry: row.industry ? String(row.industry) : '—',
		score: Number(row.score) || 50,
		matched_by: Array.isArray(row.matched_by) ? row.matched_by : [],
	}));
	const r = await apiPost('/api/leads/lookalike-import', { leads });
	if (!r.ok) {
		const detail = await r.text().catch(() => '');
		throw new Error(detail || `HTTP ${r.status}`);
	}
	return r.json();
}
