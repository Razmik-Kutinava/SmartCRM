/** Память последнего голосового поиска лидов + overlay «открой её». */
import { get, writable } from 'svelte/store';
import { readLeadsCache } from '$lib/leadsStorage.js';

/** @type {import('svelte/store').Writable<{ query: string, leads: Array<{ id: number, company: string }> }>} */
export const voiceLeadFocus = writable({ query: '', leads: [] });

/** @type {import('svelte/store').Writable<{ id: number, company: string } | null>} */
export const voiceLeadOverlay = writable(null);

/** @param {string} s */
export function companyNorm(s) {
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
 * Запомнить матчи из кэша списка по строке поиска (не ждём монтирования /leads/list).
 * @param {string} query
 */
export function rememberVoiceLeadsFromCache(query) {
	const q = companyNorm(query);
	if (q.length < 2) return;
	const all = readLeadsCache() || [];
	const matched = all.filter((l) => {
		const name = companyNorm(l?.company);
		return name.includes(q) || q.includes(name);
	});
	if (matched.length) {
		rememberVoiceLeads(matched, query);
		return;
	}
	const token = q.split(/\s+/).find((t) => t.length >= 4) || q;
	rememberVoiceLeads(
		all.filter((l) => companyNorm(l?.company).includes(token)),
		query,
	);
}

/**
 * @param {number} id
 * @param {string} [company]
 */
export function openVoiceLeadOverlay(id, company = '') {
	const n = Number(id);
	if (Number.isNaN(n) || n <= 0) return;
	voiceLeadOverlay.set({ id: n, company: String(company || '') });
}

export function closeVoiceLeadOverlay() {
	voiceLeadOverlay.set(null);
}

/**
 * @param {Record<string, unknown>} slots
 * @param {Record<string, unknown>} [payload]
 * @returns {number | null}
 */
export function resolveVoiceOpenLeadId(slots = {}, payload = {}) {
	const merged = { ...payload, ...slots };
	const focus = get(voiceLeadFocus);

	// «открой третий / лид № 5» — индекс из запомненного списка после «найди лид»
	// (порядок как на экране; важнее lead_id с бэка, если списки разошлись)
	const idxRaw = merged.selected_index;
	if (idxRaw != null && String(idxRaw).trim() !== '') {
		const idx = Number(idxRaw);
		if (Number.isInteger(idx) && idx >= 0 && focus.leads?.[idx]?.id) {
			return Number(focus.leads[idx].id);
		}
	}

	const lidRaw = merged.lead_id ?? merged.id;
	if (lidRaw != null && String(lidRaw).trim() !== '') {
		const n = Number(lidRaw);
		if (!Number.isNaN(n) && n > 0) return n;
	}

	const ref = String(merged.ref || '').toLowerCase();
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
			const partial = pool.filter((l) => {
				const name = companyNorm(l.company);
				return name.includes(company) || company.includes(name);
			});
			if (partial.length === 1 && partial[0]?.id) return Number(partial[0].id);
			if (partial.length > 1) {
				const best = partial.find((l) => companyNorm(l.company).startsWith(company)) || partial[0];
				if (best?.id) return Number(best.id);
			}
		}
	}

	if (!company && focus.leads?.[0]?.id) {
		return focus.leads[0].id;
	}
	return null;
}
