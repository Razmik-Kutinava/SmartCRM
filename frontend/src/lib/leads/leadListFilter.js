/** Фильтрация и сортировка списка лидов (/leads/list). */
import { leadPriorityTier } from '$lib/crmStages.js';

export const SORT_OPTIONS = [
	{ id: 'score_desc', label: 'Балл ↓' },
	{ id: 'score_asc', label: 'Балл ↑' },
	{ id: 'priority_desc', label: 'Приоритет ↓' },
	{ id: 'company_asc', label: 'Компания А–Я' },
];

const STAGE_ALIASES = {
	переговоры: 'Переговоры',
	новый: 'Новый',
	квалифицирован: 'Квалифицирован',
	выигран: 'Выигран',
	проигран: 'Проигран',
};

function normalizeStage(raw) {
	const low = String(raw || '').trim().toLowerCase();
	return STAGE_ALIASES[low] || String(raw || '').trim();
}

/** Маппинг слотов Hermes list_leads → состояние UI списка. */
export function leadListViewFromVoiceSlots(slots = {}) {
	const f = String(slots.filter || 'all').toLowerCase();
	const q = String(slots.query || '').trim();
	const out = {
		filterStage: 'all',
		filterPriority: 'all',
		sortBy: 'score_desc',
		search: q,
		filterIndustry: '',
		filterCity: '',
	};
	if (f === 'hot' || f === 'горячих') {
		out.filterPriority = 'high';
		out.sortBy = 'priority_desc';
	} else if (f === 'cold' || f === 'холодных') {
		out.filterPriority = 'low';
		out.sortBy = 'score_asc';
	} else if (f === 'new' || f === 'новых') {
		out.filterStage = 'Новый';
	} else if (f === 'won' || f === 'выигранных') {
		out.filterStage = 'Выигран';
	}
	if (slots.stage) out.filterStage = normalizeStage(slots.stage);
	if (slots.industry) out.filterIndustry = String(slots.industry).trim();
	if (slots.city) out.filterCity = String(slots.city).trim();
	return out;
}

/** Применить view из voice_action.payload.filter */
export function applyVoiceListFilter(view = {}) {
	return {
		filterStage: view.filterStage ?? 'all',
		filterPriority: view.filterPriority ?? 'all',
		sortBy: view.sortBy ?? 'score_desc',
		search: view.search ?? '',
		filterIndustry: view.industry ?? view.filterIndustry ?? '',
		filterCity: view.city ?? view.filterCity ?? '',
	};
}

export const PRIORITY_FILTERS = [
	{ id: 'all', label: 'Все приоритеты' },
	{ id: 'critical', label: 'Критический' },
	{ id: 'high', label: 'Высокий' },
	{ id: 'medium', label: 'Средний' },
	{ id: 'low', label: 'Низкий' },
];

const PRIORITY_RANK = { critical: 4, high: 3, medium: 2, low: 1 };

export function priorityRank(tierKey) {
	return PRIORITY_RANK[tierKey] ?? 0;
}

export function leadMatchesSearch(lead, query) {
	const q = String(query || '').trim().toLowerCase();
	if (!q) return true;
	const hay = [
		lead.company,
		lead.contact,
		lead.description,
		lead.city,
		lead.industry,
		lead.email,
		lead.phone,
	]
		.map((x) => String(x || '').toLowerCase())
		.join(' ');
	return hay.includes(q);
}

/** @param {Array<Record<string, unknown>>} leads */
function fieldContains(leadVal, filterVal) {
	const f = String(filterVal || '').trim().toLowerCase();
	if (!f) return true;
	return String(leadVal || '').toLowerCase().includes(f);
}

export function filterLeads(
	leads,
	{ search = '', filterStage = 'all', filterPriority = 'all', filterIndustry = '', filterCity = '' },
	config = null,
) {
	return leads.filter((l) => {
		if (filterStage !== 'all' && l.stage !== filterStage) return false;
		if (filterPriority !== 'all') {
			const tier = leadPriorityTier(l.score, config);
			if (tier.key !== filterPriority) return false;
		}
		if (!fieldContains(l.industry, filterIndustry)) return false;
		if (!fieldContains(l.city, filterCity)) return false;
		return leadMatchesSearch(l, search);
	});
}

/** @param {Array<Record<string, unknown>>} leads */
export function sortLeads(leads, sortBy = 'score_desc', config = null) {
	const rows = [...leads];
	const scoreOf = (l) => {
		const n = Number(l.score);
		return Number.isFinite(n) ? n : 0;
	};
	const companyOf = (l) => String(l.company || '').toLocaleLowerCase('ru');

	switch (sortBy) {
		case 'score_asc':
			return rows.sort((a, b) => scoreOf(a) - scoreOf(b));
		case 'priority_desc':
			return rows.sort((a, b) => {
				const ta = leadPriorityTier(a.score, config);
				const tb = leadPriorityTier(b.score, config);
				const dr = priorityRank(tb.key) - priorityRank(ta.key);
				if (dr !== 0) return dr;
				return scoreOf(b) - scoreOf(a);
			});
		case 'company_asc':
			return rows.sort((a, b) => companyOf(a).localeCompare(companyOf(b), 'ru'));
		case 'score_desc':
		default:
			return rows.sort((a, b) => scoreOf(b) - scoreOf(a));
	}
}

export function applyLeadListView(leads, opts, config = null) {
	const filtered = filterLeads(leads, opts, config);
	return sortLeads(filtered, opts.sortBy || 'score_desc', config);
}
