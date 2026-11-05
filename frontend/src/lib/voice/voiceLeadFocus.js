/** Память последнего голосового поиска лидов — для «открой её». */
import { get, writable } from 'svelte/store';
import { readLeadsCache } from '$lib/leadsStorage.js';

/** @type {import('svelte/store').Writable<{ query: string, leads: Array<{ id: number, company: string }> }>} */
export const voiceLeadFocus = writable({ query: '', leads: [] });

/** @param {string} s */
function companyNorm(s) {
	return String(s || '')
		.toLowerCase()
		.replace(/[«»"'`]/g, '')
		.replace(/\b(ооо|оао|зао|пао|ип|llc|ltd)\b/gi, '')
		.replace(/\s+/g, ' ')
		.trim();
}

/**
 * @param {Array<Record<string, unknown>>} leads
 * @param {string} [query]
 */
export function rememberVoiceLeads(leads, query = '') {
	const list = (Array.isArray(leads) ? leads : [])
		.filter((l) => l && l.id != null)
		.slice(0, 10)
		.map((l) => ({
			id: Number(l.id),
			company: String(l.company || ''),
		}))
		.filter((l) => !Number.isNaN(l.id));
	voiceLeadFocus.set({
		query: String(query || ''),
		leads: list,
	});
}

/**
 * @param {Record<string, unknown>} slots
 * @param {Record<string, unknown>} [payload]
 * @returns {number | null}
 */
export function resolveVoiceOpenLeadId(slots = {}, payload = {}) {
	const merged = { ...payload, ...slots };
	const lidRaw = merged.lead_id ?? merged.id;
	if (lidRaw != null && String(lidRaw).trim() !== '') {
		const n = Number(lidRaw);
		if (!Number.isNaN(n) && n > 0) return n;
	}

	const ref = String(merged.ref || '').toLowerCase();
	const focus = get(voiceLeadFocus);
	if (ref === 'last' || ref === 'prev' || ref === 'previous') {
		const first = focus.leads?.[0];
		if (first?.id) return first.id;
	}

	const company = companyNorm(merged.company || '');
	if (company.length >= 2) {
		const pools = [focus.leads || [], readLeadsCache() || []];
		for (const pool of pools) {
			const exact = pool.find((l) => companyNorm(l.company) === company);
			if (exact?.id) return Number(exact.id);
			const partial = pool.filter((l) => companyNorm(l.company).includes(company));
			if (partial.length === 1 && partial[0]?.id) return Number(partial[0].id);
		}
	}

	if (!company && focus.leads?.[0]?.id) {
		return focus.leads[0].id;
	}
	return null;
}
