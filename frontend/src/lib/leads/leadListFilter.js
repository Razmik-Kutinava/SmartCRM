/** Фильтрация и сортировка списка лидов (/leads/list). */
import { leadPriorityTier } from '$lib/crmStages.js';

export const SORT_OPTIONS = [
	{ id: 'score_desc', label: 'Балл ↓' },
	{ id: 'score_asc', label: 'Балл ↑' },
	{ id: 'priority_desc', label: 'Приоритет ↓' },
	{ id: 'company_asc', label: 'Компания А–Я' },
];

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
export function filterLeads(leads, { search = '', filterStage = 'all', filterPriority = 'all' }, config = null) {
	return leads.filter((l) => {
		if (filterStage !== 'all' && l.stage !== filterStage) return false;
		if (filterPriority !== 'all') {
			const tier = leadPriorityTier(l.score, config);
			if (tier.key !== filterPriority) return false;
		}
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
