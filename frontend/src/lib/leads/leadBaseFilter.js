/** Фильтр «База» в списке лидов. Зеркало: backend/tests/lib/lead_base_filter.py */

export const BITRIX_BASE_ID = '__bitrix__';

/**
 * @param {object} lead
 * @param {string | null | undefined} filterBase — all | __bitrix__ | метка source
 */
export function leadMatchesBaseFilter(lead, filterBase) {
	const fb = String(filterBase || 'all').trim();
	if (!fb || fb === 'all') return true;
	if (fb === BITRIX_BASE_ID) {
		const bx = lead?.bitrixLeadId ?? lead?.bitrix_lead_id;
		return bx != null && bx !== '';
	}
	const needle = fb.toLowerCase();
	return String(lead?.source || '')
		.trim()
		.toLowerCase() === needle;
}
