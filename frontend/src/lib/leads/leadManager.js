/** Менеджер лида — зеркало core/lead_manager.py */

const BLANK = new Set(['', '—', '-', '–', 'я', 'Я']);

function clean(val) {
	const s = String(val ?? '').trim();
	return BLANK.has(s) ? '' : s;
}

/** @param {Record<string, unknown> | null | undefined} lead */
export function bitrixExtraFromLead(lead) {
	return lead?.bitrixExtra && typeof lead.bitrixExtra === 'object' ? lead.bitrixExtra : {};
}

/** @param {Record<string, unknown> | null | undefined} lead */
export function leadManagerNames(lead) {
	/** @type {string[]} */
	const names = [];
	const extra = bitrixExtraFromLead(lead);
	const mgr = clean(extra.manager);
	if (mgr && !names.includes(mgr)) names.push(mgr);
	const resp = clean(lead?.responsible);
	if (resp && !names.includes(resp)) names.push(resp);
	return names;
}

/** @param {Record<string, unknown> | null | undefined} lead */
export function leadManagerLabel(lead) {
	const names = leadManagerNames(lead);
	return names[0] || '';
}

function normalizeManagerKey(name) {
	return String(name || '').trim().toLowerCase().replace(/\s+/g, ' ');
}

/** @param {Record<string, unknown> | null | undefined} lead */
export function leadMatchesManagerFilter(lead, filterName) {
	if (!filterName || filterName === 'all') return true;
	const key = normalizeManagerKey(filterName);
	return leadManagerNames(lead).some((n) => normalizeManagerKey(n) === key);
}
