/** Сохранение фильтров /leads/list — зеркало backend/tests/lib/test_lead_list_filter_state.py */

export const LEADS_LIST_FILTER_STORAGE_KEY = 'smartcrm_leads_list_filters';

export const LEADS_LIST_FILTER_DEFAULTS = {
	search: '',
	filterStage: 'all',
	filterPriority: 'all',
	filterScoreRisk: 'all',
	filterIndustry: '',
	filterCity: '',
	filterEmployeesBand: 'all',
	filterOkvedSection: 'all',
	filterIndustryBucket: 'all',
	filterTaskDue: 'all',
	filterTaskDueDate: '',
	filterSubscription: 'all',
	filterDeliveryType: 'all',
	filterCoverage: 'all',
	filterManager: 'all',
	filterBase: 'all',
	filterMinScore: null,
	groupBy: 'none',
	sortBy: 'my_day',
	collapsedGroupKeys: [],
};

const STRING_KEYS = [
	'search',
	'filterStage',
	'filterPriority',
	'filterScoreRisk',
	'filterIndustry',
	'filterCity',
	'filterEmployeesBand',
	'filterOkvedSection',
	'filterIndustryBucket',
	'filterTaskDue',
	'filterTaskDueDate',
	'filterSubscription',
	'filterDeliveryType',
	'filterCoverage',
	'filterManager',
	'filterBase',
	'groupBy',
	'sortBy',
];

/** @param {unknown} raw */
export function parseLeadsListFilters(raw) {
	if (raw == null || typeof raw !== 'object' || Array.isArray(raw)) {
		return null;
	}
	/** @type {Record<string, unknown>} */
	const src = /** @type {Record<string, unknown>} */ (raw);
	const out = { ...LEADS_LIST_FILTER_DEFAULTS };
	for (const key of STRING_KEYS) {
		const v = src[key];
		if (typeof v === 'string') out[key] = v;
	}
	const minScore = src.filterMinScore;
	if (minScore === null) {
		out.filterMinScore = null;
	} else if (typeof minScore === 'number' && Number.isFinite(minScore)) {
		out.filterMinScore = minScore;
	} else if (typeof minScore === 'string' && minScore.trim() !== '') {
		const n = Number(minScore);
		if (Number.isFinite(n)) out.filterMinScore = n;
	}
	const collapsed = src.collapsedGroupKeys;
	if (Array.isArray(collapsed)) {
		out.collapsedGroupKeys = collapsed.filter((k) => typeof k === 'string');
	}
	return out;
}

/** @param {Partial<typeof LEADS_LIST_FILTER_DEFAULTS>} state */
export function serializeLeadsListFilters(state) {
	return {
		search: state.search ?? '',
		filterStage: state.filterStage ?? 'all',
		filterPriority: state.filterPriority ?? 'all',
		filterScoreRisk: state.filterScoreRisk ?? 'all',
		filterIndustry: state.filterIndustry ?? '',
		filterCity: state.filterCity ?? '',
		filterEmployeesBand: state.filterEmployeesBand ?? 'all',
		filterOkvedSection: state.filterOkvedSection ?? 'all',
		filterIndustryBucket: state.filterIndustryBucket ?? 'all',
		filterTaskDue: state.filterTaskDue ?? 'all',
		filterTaskDueDate: state.filterTaskDueDate ?? '',
		filterSubscription: state.filterSubscription ?? 'all',
		filterDeliveryType: state.filterDeliveryType ?? 'all',
		filterCoverage: state.filterCoverage ?? 'all',
		filterManager: state.filterManager ?? 'all',
		filterBase: state.filterBase ?? 'all',
		filterMinScore: state.filterMinScore ?? null,
		groupBy: state.groupBy ?? 'none',
		sortBy: state.sortBy ?? 'my_day',
		collapsedGroupKeys: Array.isArray(state.collapsedGroupKeys)
			? state.collapsedGroupKeys.filter((k) => typeof k === 'string')
			: [],
	};
}

/** @returns {typeof LEADS_LIST_FILTER_DEFAULTS | null} */
export function readLeadsListFilters() {
	if (typeof sessionStorage === 'undefined') return null;
	try {
		const raw = sessionStorage.getItem(LEADS_LIST_FILTER_STORAGE_KEY);
		if (!raw) return null;
		return parseLeadsListFilters(JSON.parse(raw));
	} catch {
		return null;
	}
}

/** @param {Partial<typeof LEADS_LIST_FILTER_DEFAULTS>} state */
export function writeLeadsListFilters(state) {
	if (typeof sessionStorage === 'undefined') return;
	try {
		sessionStorage.setItem(
			LEADS_LIST_FILTER_STORAGE_KEY,
			JSON.stringify(serializeLeadsListFilters(state)),
		);
	} catch {
		/* квота */
	}
}

export function clearLeadsListFilters() {
	if (typeof sessionStorage === 'undefined') return;
	try {
		sessionStorage.removeItem(LEADS_LIST_FILTER_STORAGE_KEY);
	} catch {
		/* ignore */
	}
}

/** Есть ли сохранённое состояние (ключ в sessionStorage). */
export function hasLeadsListFiltersStorage() {
	if (typeof sessionStorage === 'undefined') return false;
	try {
		return sessionStorage.getItem(LEADS_LIST_FILTER_STORAGE_KEY) != null;
	} catch {
		return false;
	}
}

/** @deprecated используйте hasLeadsListFiltersStorage */
export function hadSavedLeadsListFilters(saved) {
	return hasLeadsListFiltersStorage();
}
